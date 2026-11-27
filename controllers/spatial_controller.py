import time
import uuid
from flask import request, jsonify

# Cooldown singkat (15 dtk) saat PostgreSQL offline agar pergantian algoritma di peta instan
_db_offline_until = 0.0
from flask_jwt_extended import jwt_required
from shapely.geometry import Point, shape
from shapely.ops import unary_union
from shapely.prepared import prep
from geoalchemy2.shape import to_shape
from extensions import db
from models.data_brix import DataBrix
from models.blok_lahan import BlokLahan
from spatial_engine import interpolate, daily_weather_update


def _parse_uuid(val, strict=True):
    if not val or val == "all":
        return None
    try:
        return uuid.UUID(str(val))
    except Exception:
        if strict:
            raise ValueError(f"ID tidak valid: {val}")
        return None


def _collect_from_db(blok_id, lahan_id):
    """Ambil blok (poligon) dan titik sampel Brix dari PostgreSQL sesuai filter."""
    q_blok = BlokLahan.query
    if blok_id:
        q_blok = q_blok.filter(BlokLahan.id_blok == blok_id)
    elif lahan_id:
        q_blok = q_blok.filter(BlokLahan.id_lahan == lahan_id)
    bloks = q_blok.all()
    blok_ids = [b.id_blok for b in bloks]

    q = DataBrix.query
    if blok_id or lahan_id:
        if not blok_ids:
            return bloks, []
        q = q.filter(DataBrix.id_blok.in_(blok_ids))
    rows = q.all()
    samples = [
        {
            "id": str(r.id_data),
            "lon": float(r.longitude),
            "lat": float(r.latitude),
            "brix": float(r.nilai_brix),
        }
        for r in rows
        if r.longitude is not None and r.latitude is not None and r.nilai_brix is not None
    ]
    return bloks, samples


def _sanitize_client_samples(raw_samples):
    """Validasi dan normalisasi daftar titik sampel Brix yang dikirim oleh frontend."""
    cleaned = []
    if not isinstance(raw_samples, list):
        return cleaned
    for idx, s in enumerate(raw_samples):
        if not isinstance(s, dict):
            continue
        try:
            lon = float(s.get("lon"))
            lat = float(s.get("lat"))
            brix = float(s.get("brix"))
            if not (lon == lon and lat == lat and brix == brix):  # filter NaN
                continue
            entry = {"id": str(s.get("id", idx)), "lon": lon, "lat": lat, "brix": brix}
            if s.get("ndvi") is not None:
                try:
                    ndvi_val = float(s.get("ndvi"))
                    if ndvi_val == ndvi_val:
                        entry["ndvi"] = ndvi_val
                except (TypeError, ValueError):
                    pass
            cleaned.append(entry)
        except (TypeError, ValueError):
            continue
    return cleaned


def _parse_client_polygons(raw_polygons):
    """Konversi daftar GeoJSON geometry/feature poligon blok menjadi objek Shapely."""
    polys = []
    if not isinstance(raw_polygons, list):
        return polys
    for g in raw_polygons:
        if not isinstance(g, dict):
            continue
        geom = g.get("geometry") if g.get("type") == "Feature" else g
        if not isinstance(geom, dict) or not geom.get("type"):
            continue
        try:
            shp = shape(geom)
            if not shp.is_empty:
                polys.append(shp)
        except Exception:
            continue
    return polys


@jwt_required(optional=True)
def spatial_interpolate():
    """
    GET  /ml/spatial/interpolate?blokId=&lahanId=&method=auto|kriging|idw
    POST /ml/spatial/interpolate  body: {blokId, lahanId, method, maxCells, samples, polygons}

    Memprioritaskan data PostgreSQL jika aktif; secara otomatis jatuh kembali ke
    `samples` + `polygons` dari klien jika PostgreSQL sedang offline atau ID demo.
    """
    try:
        body = request.get_json(silent=True) or {}
        raw_blok = body.get("blokId") if request.method == "POST" else request.args.get("blokId")
        raw_lahan = body.get("lahanId") if request.method == "POST" else request.args.get("lahanId")
        method = body.get("method") if request.method == "POST" else request.args.get("method", "auto")
        method = method or "auto"
        raw_max_cells = body.get("maxCells", 1600) if request.method == "POST" else request.args.get("maxCells", 1600, type=int)
        max_cells = min(max(int(raw_max_cells or 1600), 100), 4000)

        client_samples = _sanitize_client_samples(body.get("samples")) if request.method == "POST" else []
        client_polys = _parse_client_polygons(body.get("polygons")) if request.method == "POST" else []

        # Pada GET murni tanpa client samples, tetap validasi UUID secara ketat
        strict_uuid = not bool(client_samples)
        blok_id = _parse_uuid(raw_blok, strict=strict_uuid)
        lahan_id = _parse_uuid(raw_lahan, strict=strict_uuid)

        samples = []
        polys = []
        data_source = "postgresql"

        global _db_offline_until
        # Coba ambil dari PostgreSQL jika tidak ada filter ID non-UUID (mode demo) & DB tidak sedang cooldown offline
        has_demo_id = (raw_blok and raw_blok != "all" and blok_id is None) or (
            raw_lahan and raw_lahan != "all" and lahan_id is None
        )
        if not has_demo_id and (not client_samples or time.time() >= _db_offline_until):
            try:
                bloks, db_samples = _collect_from_db(blok_id, lahan_id)
                _db_offline_until = 0.0
                if db_samples:
                    samples = db_samples
                    for b in bloks:
                        try:
                            polys.append(to_shape(b.geom))
                        except Exception:
                            pass
            except Exception:
                db.session.rollback()
                _db_offline_until = time.time() + 15.0
                if not client_samples:
                    raise

        # Fallback ke sampel peta klien (mis. PostgreSQL offline atau mode demo)
        if not samples and client_samples:
            samples = client_samples
            polys = client_polys
            data_source = "fallback_client"

        bbox, clip_fn = None, None
        if polys:
            area = unary_union(polys)
            bbox = area.bounds
            prepared = prep(area)
            clip_fn = lambda lon, lat: prepared.contains(Point(lon, lat))

        result = interpolate(samples, bbox=bbox, clip_fn=clip_fn, method=method, max_cells=max_cells)
        result["source"] = data_source
        return jsonify(result)
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@jwt_required(optional=True)
def spatial_daily_update():
    """POST /ml/spatial/daily-update  body: {blokId, lahanId, temp_max, temp_min, rainfall_mm, sunshine_hours, days, samples}"""
    try:
        data = request.get_json(silent=True) or {}
        client_samples = _sanitize_client_samples(data.get("samples"))
        strict_uuid = not bool(client_samples) and data.get("mean_brix") is None
        blok_id = _parse_uuid(data.get("blokId"), strict=strict_uuid)
        lahan_id = _parse_uuid(data.get("lahanId"), strict=strict_uuid)

        samples = []
        has_demo_id = (data.get("blokId") and data.get("blokId") != "all" and blok_id is None) or (
            data.get("lahanId") and data.get("lahanId") != "all" and lahan_id is None
        )
        if not has_demo_id:
            try:
                _, samples = _collect_from_db(blok_id, lahan_id)
            except Exception:
                db.session.rollback()
                if not client_samples and data.get("mean_brix") is None:
                    raise

        if not samples and client_samples:
            samples = client_samples

        if samples:
            mean_brix = sum(s["brix"] for s in samples) / len(samples)
            count = len(samples)
        elif data.get("mean_brix") is not None:
            mean_brix = float(data["mean_brix"])
            count = 1
        else:
            return jsonify({"success": False, "error": "Belum ada titik sampel Brix pada area ini"}), 404

        return jsonify({"success": True, "jumlah_sampel": count,
                        "hasil": daily_weather_update(mean_brix, data)})
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
