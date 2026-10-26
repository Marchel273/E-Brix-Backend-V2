from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models.prediksi_ml import PrediksiML
from ml_engine import run_prediction


@jwt_required(optional=True)
def ml_predict():
    """Endpoint prediksi cerdas tebu — menerima input, mengembalikan prediksi,
    dan menyimpan ke PostgreSQL sebagai riwayat."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Input JSON tidak ditemukan"}), 400

        result = run_prediction(data)

        # Simpan ke database PostgreSQL
        user_id = None
        try:
            identity = get_jwt_identity()
            if identity:
                import uuid
                user_id = uuid.UUID(str(identity))
        except Exception:
            pass

        entry = PrediksiML(
            id_user=user_id,
            input_params=data,
            hasil=result['prediksi'],
            analisis_musim=result['analisis_musim'],
            rekomendasi=result['rekomendasi'],
        )
        db.session.add(entry)
        db.session.commit()

        # Tambahkan id ke response agar frontend bisa referensi
        result['id'] = entry.id

        return jsonify(result)

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 400


@jwt_required(optional=True)
def ml_history():
    """Mengambil seluruh riwayat prediksi ML dari PostgreSQL."""
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 50, type=int)

        pagination = PrediksiML.query.order_by(
            PrediksiML.created_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)

        history = []
        for entry in pagination.items:
            history.append({
                "id": entry.id,
                "timestamp": entry.created_at.strftime('%Y-%m-%d %H:%M:%S') if entry.created_at else None,
                "input": entry.input_params,
                "hasil": entry.hasil,
                "analisis_musim": entry.analisis_musim,
                "rekomendasi": entry.rekomendasi,
            })

        return jsonify({
            "success": True,
            "history": history,
            "total": pagination.total,
            "page": pagination.page,
            "pages": pagination.pages,
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@jwt_required(optional=True)
def ml_delete_history(entry_id):
    """Hapus satu entri riwayat prediksi berdasarkan ID."""
    try:
        entry = db.session.get(PrediksiML, entry_id)
        if not entry:
            return jsonify({"success": False, "error": "Entri tidak ditemukan"}), 404

        db.session.delete(entry)
        db.session.commit()
        return jsonify({"success": True, "message": "Riwayat prediksi berhasil dihapus"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@jwt_required(optional=True)
def ml_clear_history():
    """Hapus seluruh riwayat prediksi ML."""
    try:
        deleted = PrediksiML.query.delete()
        db.session.commit()
        return jsonify({"success": True, "message": f"{deleted} entri riwayat dihapus"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
