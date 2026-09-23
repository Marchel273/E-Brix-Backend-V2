import uuid
from flask import request, jsonify
from flask_jwt_extended import jwt_required
from extensions import db
from models.prediksi import Prediksi
from models.data_brix import DataBrix

@jwt_required()
def create_prediksi():
    data = request.get_json() or {}
    id_data = data.get("id_data")
    hasil_prediksi = data.get("hasil_prediksi")
    confidence_score = data.get("confidence_score")

    if not id_data or not hasil_prediksi:
        return jsonify({"message": "id_data dan hasil_prediksi wajib diisi"}), 400

    try:
        data_uuid = uuid.UUID(str(id_data))
        if not db.session.get(DataBrix, data_uuid):
            return jsonify({"message": "Data Brix tidak ditemukan"}), 404
    except Exception:
        return jsonify({"message": "Format id_data tidak valid"}), 400

    new_prediksi = Prediksi(
        id_data=data_uuid,
        hasil_prediksi=hasil_prediksi,
        confidence_score=float(confidence_score) if confidence_score is not None else None
    )

    try:
        db.session.add(new_prediksi)
        db.session.commit()
        return jsonify({
            "message": "Data Prediksi berhasil ditambahkan",
            "data": {
                "id_prediksi": str(new_prediksi.id_prediksi),
                "id_data": str(new_prediksi.id_data),
                "hasil_prediksi": new_prediksi.hasil_prediksi,
                "confidence_score": float(new_prediksi.confidence_score) if new_prediksi.confidence_score is not None else None,
                "created_at": new_prediksi.created_at.isoformat() if new_prediksi.created_at else None
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Gagal menambahkan prediksi: {str(e)}"}), 500

@jwt_required()
def get_all_prediksi():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    id_data = request.args.get("id_data")

    query = Prediksi.query
    if id_data:
        try:
            data_uuid = uuid.UUID(str(id_data))
            query = query.filter_by(id_data=data_uuid)
        except Exception:
            return jsonify({"message": "Format id_data filter tidak valid"}), 400

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    result = [{
        "id_prediksi": str(p.id_prediksi),
        "id_data": str(p.id_data),
        "hasil_prediksi": p.hasil_prediksi,
        "confidence_score": float(p.confidence_score) if p.confidence_score is not None else None,
        "created_at": p.created_at.isoformat() if p.created_at else None
    } for p in pagination.items]

    return jsonify({
        "message": "Berhasil mengambil data prediksi",
        "total": pagination.total,
        "page": pagination.page,
        "pages": pagination.pages,
        "data": result
    }), 200

@jwt_required()
def get_prediksi_by_id(id):
    try:
        pred_uuid = uuid.UUID(str(id))
        prediksi = db.session.get(Prediksi, pred_uuid)
    except Exception:
        return jsonify({"message": "Format ID prediksi tidak valid"}), 400

    if not prediksi:
        return jsonify({"message": "Data Prediksi tidak ditemukan"}), 404

    return jsonify({
        "message": "Berhasil mengambil data prediksi",
        "data": {
            "id_prediksi": str(prediksi.id_prediksi),
            "id_data": str(prediksi.id_data),
            "hasil_prediksi": prediksi.hasil_prediksi,
            "confidence_score": float(prediksi.confidence_score) if prediksi.confidence_score is not None else None,
            "created_at": prediksi.created_at.isoformat() if prediksi.created_at else None,
            "updated_at": prediksi.updated_at.isoformat() if prediksi.updated_at else None
        }
    }), 200

@jwt_required()
def update_prediksi(id):
    try:
        pred_uuid = uuid.UUID(str(id))
        prediksi = db.session.get(Prediksi, pred_uuid)
    except Exception:
        return jsonify({"message": "Format ID prediksi tidak valid"}), 400

    if not prediksi:
        return jsonify({"message": "Data Prediksi tidak ditemukan"}), 404

    data = request.get_json() or {}
    if "id_data" in data:
        try:
            data_uuid = uuid.UUID(str(data["id_data"]))
            if not db.session.get(DataBrix, data_uuid):
                return jsonify({"message": "Data Brix tidak ditemukan"}), 404
            prediksi.id_data = data_uuid
        except Exception:
            return jsonify({"message": "Format id_data tidak valid"}), 400

    if "hasil_prediksi" in data:
        prediksi.hasil_prediksi = data["hasil_prediksi"]
    if "confidence_score" in data:
        prediksi.confidence_score = float(data["confidence_score"]) if data["confidence_score"] is not None else None

    try:
        db.session.commit()
        return jsonify({
            "message": "Data Prediksi berhasil diupdate",
            "data": {
                "id_prediksi": str(prediksi.id_prediksi),
                "id_data": str(prediksi.id_data),
                "hasil_prediksi": prediksi.hasil_prediksi,
                "confidence_score": float(prediksi.confidence_score) if prediksi.confidence_score is not None else None
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Gagal mengupdate prediksi: {str(e)}"}), 500

@jwt_required()
def delete_prediksi(id):
    try:
        pred_uuid = uuid.UUID(str(id))
        prediksi = db.session.get(Prediksi, pred_uuid)
    except Exception:
        return jsonify({"message": "Format ID prediksi tidak valid"}), 400

    if not prediksi:
        return jsonify({"message": "Data Prediksi tidak ditemukan"}), 404

    try:
        db.session.delete(prediksi)
        db.session.commit()
        return jsonify({"message": "Data Prediksi berhasil dihapus"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Gagal menghapus prediksi: {str(e)}"}), 500