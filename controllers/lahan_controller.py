import uuid
from flask import request, jsonify
from flask_jwt_extended import jwt_required
from extensions import db
from models.lahan import Lahan
from models.petani import Petani
from utils.helpers import geojson_to_wkbelement, geometry_to_geojson

@jwt_required()
def create_lahan():
    data = request.get_json() or {}
    id_petani = data.get("id_petani")
    nama_lahan = data.get("nama_lahan")
    geom_data = data.get("geom")

    if not id_petani or not nama_lahan or not geom_data:
        return jsonify({"message": "id_petani, nama_lahan, dan geom (Polygon) wajib diisi"}), 400

    try:
        petani_uuid = uuid.UUID(str(id_petani))
        petani = db.session.get(Petani, petani_uuid)
    except Exception:
        return jsonify({"message": "Format id_petani tidak valid"}), 400

    if not petani:
        return jsonify({"message": "Petani tidak ditemukan"}), 404

    try:
        wkb_geom = geojson_to_wkbelement(geom_data)
    except ValueError as ve:
        return jsonify({"message": str(ve)}), 400

    new_lahan = Lahan(
        id_petani=petani_uuid,
        nama_lahan=nama_lahan,
        geom=wkb_geom
    )

    try:
        db.session.add(new_lahan)
        db.session.commit()

        return jsonify({
            "message": "Data Lahan berhasil ditambahkan",
            "data": {
                "id_lahan": str(new_lahan.id_lahan),
                "id_petani": str(new_lahan.id_petani),
                "nama_lahan": new_lahan.nama_lahan,
                "geom": geometry_to_geojson(new_lahan.geom),
                "created_at": new_lahan.created_at.isoformat() if new_lahan.created_at else None
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Gagal menambahkan lahan: {str(e)}"}), 500

@jwt_required()
def get_all_lahan():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    id_petani = request.args.get("id_petani")

    query = Lahan.query
    if id_petani:
        try:
            petani_uuid = uuid.UUID(str(id_petani))
            query = query.filter_by(id_petani=petani_uuid)
        except Exception:
            return jsonify({"message": "Format id_petani filter tidak valid"}), 400

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    result = [{
        "id_lahan": str(l.id_lahan),
        "id_petani": str(l.id_petani),
        "nama_lahan": l.nama_lahan,
        "geom": geometry_to_geojson(l.geom),
        "created_at": l.created_at.isoformat() if l.created_at else None
    } for l in pagination.items]

    return jsonify({
        "message": "Berhasil mengambil semua data lahan",
        "total": pagination.total,
        "page": pagination.page,
        "pages": pagination.pages,
        "data": result
    }), 200

@jwt_required()
def get_lahan_by_id(id):
    try:
        lahan_uuid = uuid.UUID(str(id))
        lahan = db.session.get(Lahan, lahan_uuid)
    except Exception:
        return jsonify({"message": "Format ID lahan tidak valid"}), 400

    if not lahan:
        return jsonify({"message": "Lahan tidak ditemukan"}), 404

    return jsonify({
        "message": "Berhasil mengambil data lahan",
        "data": {
            "id_lahan": str(lahan.id_lahan),
            "id_petani": str(lahan.id_petani),
            "nama_lahan": lahan.nama_lahan,
            "geom": geometry_to_geojson(lahan.geom),
            "created_at": lahan.created_at.isoformat() if lahan.created_at else None,
            "updated_at": lahan.updated_at.isoformat() if lahan.updated_at else None
        }
    }), 200

@jwt_required()
def update_lahan(id):
    try:
        lahan_uuid = uuid.UUID(str(id))
        lahan = db.session.get(Lahan, lahan_uuid)
    except Exception:
        return jsonify({"message": "Format ID lahan tidak valid"}), 400

    if not lahan:
        return jsonify({"message": "Lahan tidak ditemukan"}), 404

    data = request.get_json() or {}
    if "id_petani" in data:
        try:
            petani_uuid = uuid.UUID(str(data["id_petani"]))
            if not db.session.get(Petani, petani_uuid):
                return jsonify({"message": "Petani tidak ditemukan"}), 404
            lahan.id_petani = petani_uuid
        except Exception:
            return jsonify({"message": "Format id_petani tidak valid"}), 400

    if "nama_lahan" in data:
        lahan.nama_lahan = data["nama_lahan"]

    if "geom" in data:
        try:
            lahan.geom = geojson_to_wkbelement(data["geom"])
        except ValueError as ve:
            return jsonify({"message": str(ve)}), 400

    try:
        db.session.commit()
        return jsonify({
            "message": "Data Lahan berhasil diupdate",
            "data": {
                "id_lahan": str(lahan.id_lahan),
                "id_petani": str(lahan.id_petani),
                "nama_lahan": lahan.nama_lahan,
                "geom": geometry_to_geojson(lahan.geom)
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Gagal mengupdate lahan: {str(e)}"}), 500

@jwt_required()
def delete_lahan(id):
    try:
        lahan_uuid = uuid.UUID(str(id))
        lahan = db.session.get(Lahan, lahan_uuid)
    except Exception:
        return jsonify({"message": "Format ID lahan tidak valid"}), 400

    if not lahan:
        return jsonify({"message": "Lahan tidak ditemukan"}), 404

    try:
        db.session.delete(lahan)
        db.session.commit()
        return jsonify({"message": "Data Lahan dan seluruh blok terkait berhasil dihapus"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Gagal menghapus lahan: {str(e)}"}), 500