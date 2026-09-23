import uuid
from datetime import datetime
from flask import request, jsonify
from flask_jwt_extended import jwt_required
from extensions import db
from models.blok_lahan import BlokLahan
from models.lahan import Lahan
from models.jenis_tebu import JenisTebu
from utils.helpers import geojson_to_wkbelement, geometry_to_geojson

@jwt_required()
def create_blok_lahan():
    data = request.get_json() or {}
    id_lahan = data.get("id_lahan")
    id_tebu = data.get("id_tebu")
    nama_blok = data.get("nama_blok")
    tanggal_tanam_raw = data.get("tanggal_tanam")
    geom_data = data.get("geom")

    if not id_lahan or not nama_blok or not geom_data:
        return jsonify({"message": "id_lahan, nama_blok, dan geom (Polygon) wajib diisi"}), 400

    try:
        lahan_uuid = uuid.UUID(str(id_lahan))
        if not db.session.get(Lahan, lahan_uuid):
            return jsonify({"message": "Lahan tidak ditemukan"}), 404
    except Exception:
        return jsonify({"message": "Format id_lahan tidak valid"}), 400

    tebu_uuid = None
    if id_tebu:
        try:
            tebu_uuid = uuid.UUID(str(id_tebu))
            if not db.session.get(JenisTebu, tebu_uuid):
                return jsonify({"message": "Jenis Tebu tidak ditemukan"}), 404
        except Exception:
            return jsonify({"message": "Format id_tebu tidak valid"}), 400

    tanggal_tanam = None
    if tanggal_tanam_raw:
        try:
            tanggal_tanam = datetime.strptime(str(tanggal_tanam_raw), "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"message": "Format tanggal_tanam harus YYYY-MM-DD"}), 400

    try:
        wkb_geom = geojson_to_wkbelement(geom_data)
    except ValueError as ve:
        return jsonify({"message": str(ve)}), 400

    new_blok = BlokLahan(
        id_lahan=lahan_uuid,
        id_tebu=tebu_uuid,
        nama_blok=nama_blok,
        tanggal_tanam=tanggal_tanam,
        geom=wkb_geom
    )

    try:
        db.session.add(new_blok)
        db.session.commit()
        return jsonify({
            "message": "Data Blok Lahan berhasil ditambahkan",
            "data": {
                "id_blok": str(new_blok.id_blok),
                "id_lahan": str(new_blok.id_lahan),
                "id_tebu": str(new_blok.id_tebu) if new_blok.id_tebu else None,
                "nama_blok": new_blok.nama_blok,
                "rata_brix": float(new_blok.rata_brix) if new_blok.rata_brix is not None else None,
                "tanggal_tanam": new_blok.tanggal_tanam.isoformat() if new_blok.tanggal_tanam else None,
                "geom": geometry_to_geojson(new_blok.geom)
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Gagal menambahkan blok lahan: {str(e)}"}), 500

@jwt_required()
def get_all_blok_lahan():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    id_lahan = request.args.get("id_lahan")

    query = BlokLahan.query
    if id_lahan:
        try:
            lahan_uuid = uuid.UUID(str(id_lahan))
            query = query.filter_by(id_lahan=lahan_uuid)
        except Exception:
            return jsonify({"message": "Format id_lahan filter tidak valid"}), 400

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    result = [{
        "id_blok": str(b.id_blok),
        "id_lahan": str(b.id_lahan),
        "id_tebu": str(b.id_tebu) if b.id_tebu else None,
        "nama_blok": b.nama_blok,
        "rata_brix": float(b.rata_brix) if b.rata_brix is not None else None,
        "tanggal_tanam": b.tanggal_tanam.isoformat() if b.tanggal_tanam else None,
        "geom": geometry_to_geojson(b.geom),
        "created_at": b.created_at.isoformat() if b.created_at else None
    } for b in pagination.items]

    return jsonify({
        "message": "Berhasil mengambil semua data blok lahan",
        "total": pagination.total,
        "page": pagination.page,
        "pages": pagination.pages,
        "data": result
    }), 200

@jwt_required()
def get_blok_lahan_by_id(id):
    try:
        blok_uuid = uuid.UUID(str(id))
        blok = db.session.get(BlokLahan, blok_uuid)
    except Exception:
        return jsonify({"message": "Format ID blok tidak valid"}), 400

    if not blok:
        return jsonify({"message": "Blok Lahan tidak ditemukan"}), 404

    return jsonify({
        "message": "Berhasil mengambil data blok lahan",
        "data": {
            "id_blok": str(blok.id_blok),
            "id_lahan": str(blok.id_lahan),
            "id_tebu": str(blok.id_tebu) if blok.id_tebu else None,
            "nama_blok": blok.nama_blok,
            "rata_brix": float(blok.rata_brix) if blok.rata_brix is not None else None,
            "tanggal_tanam": blok.tanggal_tanam.isoformat() if blok.tanggal_tanam else None,
            "geom": geometry_to_geojson(blok.geom),
            "created_at": blok.created_at.isoformat() if blok.created_at else None,
            "updated_at": blok.updated_at.isoformat() if blok.updated_at else None
        }
    }), 200

@jwt_required()
def update_blok_lahan(id):
    try:
        blok_uuid = uuid.UUID(str(id))
        blok = db.session.get(BlokLahan, blok_uuid)
    except Exception:
        return jsonify({"message": "Format ID blok tidak valid"}), 400

    if not blok:
        return jsonify({"message": "Blok Lahan tidak ditemukan"}), 404

    data = request.get_json() or {}
    if "id_lahan" in data:
        try:
            lahan_uuid = uuid.UUID(str(data["id_lahan"]))
            if not db.session.get(Lahan, lahan_uuid):
                return jsonify({"message": "Lahan tidak ditemukan"}), 404
            blok.id_lahan = lahan_uuid
        except Exception:
            return jsonify({"message": "Format id_lahan tidak valid"}), 400

    if "id_tebu" in data:
        if data["id_tebu"] is None:
            blok.id_tebu = None
        else:
            try:
                tebu_uuid = uuid.UUID(str(data["id_tebu"]))
                if not db.session.get(JenisTebu, tebu_uuid):
                    return jsonify({"message": "Jenis Tebu tidak ditemukan"}), 404
                blok.id_tebu = tebu_uuid
            except Exception:
                return jsonify({"message": "Format id_tebu tidak valid"}), 400

    if "nama_blok" in data:
        blok.nama_blok = data["nama_blok"]
    if "rata_brix" in data:
        blok.rata_brix = data["rata_brix"]
    if "tanggal_tanam" in data:
        if data["tanggal_tanam"]:
            try:
                blok.tanggal_tanam = datetime.strptime(str(data["tanggal_tanam"]), "%Y-%m-%d").date()
            except ValueError:
                return jsonify({"message": "Format tanggal_tanam harus YYYY-MM-DD"}), 400
        else:
            blok.tanggal_tanam = None

    if "geom" in data:
        try:
            blok.geom = geojson_to_wkbelement(data["geom"])
        except ValueError as ve:
            return jsonify({"message": str(ve)}), 400

    try:
        db.session.commit()
        return jsonify({
            "message": "Data Blok Lahan berhasil diupdate",
            "data": {
                "id_blok": str(blok.id_blok),
                "id_lahan": str(blok.id_lahan),
                "id_tebu": str(blok.id_tebu) if blok.id_tebu else None,
                "nama_blok": blok.nama_blok,
                "rata_brix": float(blok.rata_brix) if blok.rata_brix is not None else None,
                "tanggal_tanam": blok.tanggal_tanam.isoformat() if blok.tanggal_tanam else None,
                "geom": geometry_to_geojson(blok.geom)
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Gagal mengupdate blok lahan: {str(e)}"}), 500

@jwt_required()
def delete_blok_lahan(id):
    try:
        blok_uuid = uuid.UUID(str(id))
        blok = db.session.get(BlokLahan, blok_uuid)
    except Exception:
        return jsonify({"message": "Format ID blok tidak valid"}), 400

    if not blok:
        return jsonify({"message": "Blok Lahan tidak ditemukan"}), 404

    try:
        db.session.delete(blok)
        db.session.commit()
        return jsonify({"message": "Data Blok Lahan berhasil dihapus beserta data brix terkait"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Gagal menghapus blok lahan: {str(e)}"}), 500
