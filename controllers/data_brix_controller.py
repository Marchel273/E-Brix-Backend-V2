import uuid
from datetime import datetime
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import cloudinary.uploader
from sqlalchemy import func
from extensions import db
from models.data_brix import DataBrix
from models.blok_lahan import BlokLahan
from models.user import User
from utils.helpers import allowed_file, make_point_geom, geometry_to_geojson

def _update_blok_rata_brix(id_blok):
    """Update otomatis nilai rata_brix pada blok_lahan."""
    avg_brix = db.session.query(func.avg(DataBrix.nilai_brix)).filter(DataBrix.id_blok == id_blok).scalar()
    blok = db.session.get(BlokLahan, id_blok)
    if blok:
        blok.rata_brix = round(float(avg_brix), 2) if avg_brix is not None else None

@jwt_required()
def create_brix():
    current_user_id = get_jwt_identity()
    user_uuid = uuid.UUID(str(current_user_id))

    if request.is_json:
        data = request.get_json() or {}
        id_blok = data.get("id_blok")
        latitude = data.get("latitude")
        longitude = data.get("longitude")
        nilai_brix = data.get("nilai_brix")
        foto_teks = data.get("foto")
        foto_file = None
        status_sinkron = data.get("status_sinkron", "tersinkron")
        client_uuid_raw = data.get("client_uuid")
        catatan = data.get("catatan")
        timestamp_raw = data.get("timestamp")
    else:
        id_blok = request.form.get("id_blok")
        latitude = request.form.get("latitude")
        longitude = request.form.get("longitude")
        nilai_brix = request.form.get("nilai_brix")
        foto_file = request.files.get("foto")
        foto_teks = request.form.get("foto")
        status_sinkron = request.form.get("status_sinkron", "tersinkron")
        client_uuid_raw = request.form.get("client_uuid")
        catatan = request.form.get("catatan")
        timestamp_raw = request.form.get("timestamp")

    if not id_blok or latitude is None or longitude is None or nilai_brix is None:
        return jsonify({"message": "id_blok, latitude, longitude, dan nilai_brix wajib diisi"}), 400

    try:
        blok_uuid = uuid.UUID(str(id_blok))
        if not db.session.get(BlokLahan, blok_uuid):
            return jsonify({"message": "Blok Lahan tidak ditemukan"}), 404
    except Exception:
        return jsonify({"message": "Format id_blok tidak valid"}), 400

    client_uuid = None
    if client_uuid_raw:
        try:
            client_uuid = uuid.UUID(str(client_uuid_raw))
            if DataBrix.query.filter_by(client_uuid=client_uuid).first():
                return jsonify({"message": "Data dengan client_uuid ini sudah pernah tersinkron (duplikat)"}), 409
        except Exception:
            return jsonify({"message": "Format client_uuid tidak valid"}), 400

    meas_timestamp = datetime.now()
    if timestamp_raw:
        try:
            meas_timestamp = datetime.fromisoformat(str(timestamp_raw).replace("Z", "+00:00"))
        except Exception:
            meas_timestamp = datetime.now()

    foto_url = None
    if foto_file:
        if not allowed_file(foto_file.filename):
            return jsonify({"message": "Format file foto tidak didukung"}), 400
        try:
            upload_result = cloudinary.uploader.upload(
                foto_file, folder="ebrix/data_brix", resource_type="auto"
            )
            foto_url = upload_result.get("secure_url")
        except Exception as e:
            return jsonify({"message": f"Gagal mengunggah foto ke Cloudinary: {str(e)}"}), 500
    elif foto_teks:
        foto_url = foto_teks

    try:
        point_geom = make_point_geom(latitude, longitude)
    except ValueError as ve:
        return jsonify({"message": str(ve)}), 400

    new_data = DataBrix(
        id_blok=blok_uuid,
        id_user=user_uuid,
        latitude=float(latitude),
        longitude=float(longitude),
        nilai_brix=float(nilai_brix),
        foto=foto_url,
        geom=point_geom,
        status_sinkron=status_sinkron,
        client_uuid=client_uuid,
        catatan=catatan,
        timestamp=meas_timestamp
    )

    try:
        db.session.add(new_data)
        db.session.flush()
        _update_blok_rata_brix(blok_uuid)
        db.session.commit()

        return jsonify({
            "message": "Data Brix berhasil ditambahkan",
            "data": {
                "id_data": str(new_data.id_data),
                "id_blok": str(new_data.id_blok),
                "id_user": str(new_data.id_user),
                "latitude": new_data.latitude,
                "longitude": new_data.longitude,
                "nilai_brix": float(new_data.nilai_brix),
                "foto": new_data.foto,
                "geom": geometry_to_geojson(new_data.geom),
                "status_sinkron": new_data.status_sinkron,
                "client_uuid": str(new_data.client_uuid) if new_data.client_uuid else None,
                "catatan": new_data.catatan,
                "timestamp": new_data.timestamp.isoformat()
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Gagal menyimpan data brix: {str(e)}"}), 500

@jwt_required()
def get_all_brix():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    id_blok = request.args.get("id_blok")
    status_sinkron = request.args.get("status_sinkron")

    query = DataBrix.query
    if id_blok:
        try:
            blok_uuid = uuid.UUID(str(id_blok))
            query = query.filter_by(id_blok=blok_uuid)
        except Exception:
            return jsonify({"message": "Format id_blok filter tidak valid"}), 400

    if status_sinkron:
        query = query.filter_by(status_sinkron=status_sinkron)

    query = query.order_by(DataBrix.timestamp.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    result = [{
        "id_data": str(d.id_data),
        "id_blok": str(d.id_blok),
        "id_user": str(d.id_user),
        "latitude": d.latitude,
        "longitude": d.longitude,
        "nilai_brix": float(d.nilai_brix),
        "foto": d.foto,
        "geom": geometry_to_geojson(d.geom),
        "status_sinkron": d.status_sinkron,
        "client_uuid": str(d.client_uuid) if d.client_uuid else None,
        "catatan": d.catatan,
        "timestamp": d.timestamp.isoformat() if d.timestamp else None,
        "created_at": d.created_at.isoformat() if d.created_at else None
    } for d in pagination.items]

    return jsonify({
        "message": "Berhasil mengambil data brix",
        "total": pagination.total,
        "page": pagination.page,
        "pages": pagination.pages,
        "data": result
    }), 200

@jwt_required()
def get_brix_by_id(id):
    try:
        data_uuid = uuid.UUID(str(id))
        data = db.session.get(DataBrix, data_uuid)
    except Exception:
        return jsonify({"message": "Format ID data brix tidak valid"}), 400

    if not data:
        return jsonify({"message": "Data Brix tidak ditemukan"}), 404

    return jsonify({
        "message": "Berhasil mengambil data brix",
        "data": {
            "id_data": str(data.id_data),
            "id_blok": str(data.id_blok),
            "id_user": str(data.id_user),
            "latitude": data.latitude,
            "longitude": data.longitude,
            "nilai_brix": float(data.nilai_brix),
            "foto": data.foto,
            "geom": geometry_to_geojson(data.geom),
            "status_sinkron": data.status_sinkron,
            "client_uuid": str(data.client_uuid) if data.client_uuid else None,
            "catatan": data.catatan,
            "timestamp": data.timestamp.isoformat() if data.timestamp else None,
            "created_at": data.created_at.isoformat() if data.created_at else None
        }
    }), 200

@jwt_required()
def update_brix(id):
    try:
        data_uuid = uuid.UUID(str(id))
        data_brix = db.session.get(DataBrix, data_uuid)
    except Exception:
        return jsonify({"message": "Format ID data brix tidak valid"}), 400

    if not data_brix:
        return jsonify({"message": "Data Brix tidak ditemukan"}), 404

    if request.is_json:
        data = request.get_json() or {}
        foto_file = None
        foto_teks = data.get("foto")
    else:
        data = request.form
        foto_file = request.files.get("foto")
        foto_teks = request.form.get("foto")

    if "id_blok" in data:
        try:
            blok_uuid = uuid.UUID(str(data["id_blok"]))
            if not db.session.get(BlokLahan, blok_uuid):
                return jsonify({"message": "Blok Lahan tidak ditemukan"}), 404
            data_brix.id_blok = blok_uuid
        except Exception:
            return jsonify({"message": "Format id_blok tidak valid"}), 400

    lat_changed = False
    if "latitude" in data:
        data_brix.latitude = float(data["latitude"])
        lat_changed = True
    if "longitude" in data:
        data_brix.longitude = float(data["longitude"])
        lat_changed = True
    if lat_changed:
        data_brix.geom = make_point_geom(data_brix.latitude, data_brix.longitude)

    if "nilai_brix" in data:
        data_brix.nilai_brix = float(data["nilai_brix"])
    if "status_sinkron" in data:
        data_brix.status_sinkron = data["status_sinkron"]
    if "catatan" in data:
        data_brix.catatan = data["catatan"]

    if foto_file:
        if not allowed_file(foto_file.filename):
            return jsonify({"message": "Format file tidak didukung"}), 400
        try:
            upload_result = cloudinary.uploader.upload(
                foto_file, folder="ebrix/data_brix", resource_type="auto"
            )
            data_brix.foto = upload_result.get("secure_url")
        except Exception as e:
            return jsonify({"message": f"Gagal upload foto: {str(e)}"}), 500
    elif foto_teks:
        data_brix.foto = foto_teks

    try:
        db.session.flush()
        _update_blok_rata_brix(data_brix.id_blok)
        db.session.commit()
        return jsonify({
            "message": "Data Brix berhasil diupdate",
            "data": {
                "id_data": str(data_brix.id_data),
                "id_blok": str(data_brix.id_blok),
                "nilai_brix": float(data_brix.nilai_brix),
                "foto": data_brix.foto
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Gagal mengupdate data brix: {str(e)}"}), 500

@jwt_required()
def delete_brix(id):
    try:
        data_uuid = uuid.UUID(str(id))
        data_brix = db.session.get(DataBrix, data_uuid)
    except Exception:
        return jsonify({"message": "Format ID data brix tidak valid"}), 400

    if not data_brix:
        return jsonify({"message": "Data Brix tidak ditemukan"}), 404

    blok_uuid = data_brix.id_blok
    try:
        db.session.delete(data_brix)
        db.session.flush()
        _update_blok_rata_brix(blok_uuid)
        db.session.commit()
        return jsonify({"message": "Data Brix berhasil dihapus"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Gagal menghapus data brix: {str(e)}"}), 500

@jwt_required()
def sync_batch():
    """Endpoint untuk sinkronisasi batch data pengukuran offline dari mobile."""
    current_user_id = get_jwt_identity()
    user_uuid = uuid.UUID(str(current_user_id))

    data = request.get_json() or {}
    items = data.get("items", [])

    if not isinstance(items, list) or len(items) == 0:
        return jsonify({"message": "Daftar items pengukuran wajib dikirimkan dalam bentuk array"}), 400

    synced_count = 0
    skipped_count = 0
    errors = []

    for idx, item in enumerate(items):
        client_uuid_raw = item.get("client_uuid")
        if client_uuid_raw:
            try:
                c_uuid = uuid.UUID(str(client_uuid_raw))
                if DataBrix.query.filter_by(client_uuid=c_uuid).first():
                    skipped_count += 1
                    continue
            except Exception:
                c_uuid = None
        else:
            c_uuid = None

        id_blok = item.get("id_blok")
        if not id_blok:
            errors.append(f"Item #{idx}: id_blok kosong")
            continue

        try:
            b_uuid = uuid.UUID(str(id_blok))
            if not db.session.get(BlokLahan, b_uuid):
                errors.append(f"Item #{idx}: Blok {id_blok} tidak ditemukan")
                continue
        except Exception:
            errors.append(f"Item #{idx}: Format id_blok tidak valid")
            continue

        lat = item.get("latitude")
        lon = item.get("longitude")
        nilai = item.get("nilai_brix")
        if lat is None or lon is None or nilai is None:
            errors.append(f"Item #{idx}: latitude/longitude/nilai_brix kosong")
            continue

        ts = datetime.now()
        if item.get("timestamp"):
            try:
                ts = datetime.fromisoformat(str(item["timestamp"]).replace("Z", "+00:00"))
            except Exception:
                ts = datetime.now()

        point_geom = make_point_geom(lat, lon)
        new_record = DataBrix(
            id_blok=b_uuid,
            id_user=user_uuid,
            latitude=float(lat),
            longitude=float(lon),
            nilai_brix=float(nilai),
            foto=item.get("foto"),
            geom=point_geom,
            status_sinkron="tersinkron",
            client_uuid=c_uuid,
            catatan=item.get("catatan"),
            timestamp=ts
        )
        db.session.add(new_record)
        synced_count += 1

    try:
        db.session.commit()
        return jsonify({
            "message": "Sinkronisasi batch selesai",
            "summary": {
                "total_sent": len(items),
                "synced": synced_count,
                "skipped_duplicates": skipped_count,
                "errors_count": len(errors),
                "errors": errors
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Gagal menyimpan data sinkronisasi: {str(e)}"}), 500