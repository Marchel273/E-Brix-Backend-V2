import uuid
from datetime import datetime
from flask import request, jsonify
from extensions import db
from models.data_brix import DataBrix
from models.blok_lahan import BlokLahan
from models.user import User
from utils.helpers import make_point_geom

def _get_int_id(d_uuid):
    return d_uuid.int & 0x7FFFFFFF

def _format_scan_dto(d):
    int_id = _get_int_id(d.id_data)
    petak_name = d.blok_lahan.nama_blok if d.blok_lahan else "Blok A"
    brix_val = float(d.nilai_brix)
    lat_val = float(d.latitude)
    lon_val = float(d.longitude)
    time_str = d.timestamp.strftime("%Y-%m-%d %H:%M:%S") if d.timestamp else ""

    return {
        "id": int_id,
        "id_data": str(d.id_data),
        "id_blok": str(d.id_blok),
        "petak": petak_name,
        "foto": d.foto,
        "image_base64": d.foto,
        "nilai_brix": brix_val,
        "brix": str(brix_val),
        "latitude": lat_val,
        "lat": str(lat_val),
        "longitude": lon_val,
        "lon": str(lon_val),
        "timestamp": time_str
    }

def get_scans():
    """GET /api/scans -> Mengembalikan List<ScanDto> (JSON Array) untuk Android"""
    data_list = DataBrix.query.order_by(DataBrix.timestamp.desc()).all()
    results = [_format_scan_dto(d) for d in data_list]
    return jsonify(results), 200

def create_scan():
    """POST /api/scans -> Menyimpan scan dari Android ke database"""
    data = request.get_json() or {}

    petak_name = data.get("petak") or data.get("petakRaw") or "Blok A"
    brix_raw = data.get("brix") or data.get("nilai_brix") or data.get("brixRaw") or 0.0
    lat_raw = data.get("lat") or data.get("latitude") or data.get("latRaw") or -7.5
    lon_raw = data.get("lon") or data.get("longitude") or data.get("lonRaw") or 112.5
    foto_raw = data.get("imageBase64") or data.get("foto")
    timestamp_raw = data.get("timestamp") or data.get("timestampRaw")

    try:
        brix_val = float(brix_raw)
        lat_val = float(lat_raw)
        lon_val = float(lon_raw)
    except Exception:
        brix_val = 0.0
        lat_val = -7.5
        lon_val = 112.5

    # Ambil BlokLahan yang ada atau pertama
    blok = BlokLahan.query.filter_by(nama_blok=petak_name).first()
    if not blok:
        blok = BlokLahan.query.first()

    # Ambil User default
    user = User.query.filter_by(role="petani").first() or User.query.first()

    meas_time = datetime.now()
    if timestamp_raw:
        try:
            meas_time = datetime.fromisoformat(str(timestamp_raw).replace("Z", "+00:00"))
        except Exception:
            meas_time = datetime.now()

    point_geom = make_point_geom(lat_val, lon_val)

    new_brix = DataBrix(
        id_blok=blok.id_blok if blok else None,
        id_user=user.id_user if user else None,
        latitude=lat_val,
        longitude=lon_val,
        nilai_brix=brix_val,
        foto=foto_raw,
        geom=point_geom,
        status_sinkron="tersinkron",
        client_uuid=uuid.uuid4(),
        timestamp=meas_time
    )

    try:
        db.session.add(new_brix)
        db.session.commit()
        return jsonify(_format_scan_dto(new_brix)), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Gagal menyimpan scan: {str(e)}"}), 500

def update_scan(id):
    """PUT /api/scans/<id> -> Memperbarui scan berdasarkan id"""
    data = request.get_json() or {}
    data_list = DataBrix.query.all()
    target = None

    # Cari berdasarkan int_id atau uuid string
    for d in data_list:
        if str(_get_int_id(d.id_data)) == str(id) or str(d.id_data) == str(id):
            target = d
            break

    if not target:
        return jsonify({"message": "Data scan tidak ditemukan"}), 404

    brix_raw = data.get("brix") or data.get("nilai_brix") or data.get("brixRaw")
    lat_raw = data.get("lat") or data.get("latitude") or data.get("latRaw")
    lon_raw = data.get("lon") or data.get("longitude") or data.get("lonRaw")
    foto_raw = data.get("imageBase64") or data.get("foto")

    if brix_raw is not None:
        try:
            target.nilai_brix = float(brix_raw)
        except Exception:
            pass
    if lat_raw is not None:
        try:
            target.latitude = float(lat_raw)
        except Exception:
            pass
    if lon_raw is not None:
        try:
            target.longitude = float(lon_raw)
        except Exception:
            pass
    if foto_raw is not None:
        target.foto = foto_raw

    target.geom = make_point_geom(target.latitude, target.longitude)

    try:
        db.session.commit()
        return jsonify(_format_scan_dto(target)), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Gagal update scan: {str(e)}"}), 500

def delete_scan(id):
    """DELETE /api/scans/<id> -> Menghapus scan"""
    data_list = DataBrix.query.all()
    target = None

    for d in data_list:
        if str(_get_int_id(d.id_data)) == str(id) or str(d.id_data) == str(id):
            target = d
            break

    if not target:
        return jsonify({"message": "Data scan tidak ditemukan"}), 404

    try:
        db.session.delete(target)
        db.session.commit()
        return jsonify({"message": "Data berhasil dihapus"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Gagal menghapus scan: {str(e)}"}), 500
