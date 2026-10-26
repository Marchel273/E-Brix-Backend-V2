import os
import json
from datetime import datetime
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models.prediksi_ml import PrediksiML
from ml_engine import run_prediction

# File fallback cadangan jika PostgreSQL server belum di-start di environment lokal
FALLBACK_CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "instance")
FALLBACK_CACHE_FILE = os.path.join(FALLBACK_CACHE_DIR, "ml_history_cache.json")


def _read_fallback_history():
    """Membaca riwayat dari cache lokal jika PostgreSQL sedang offline."""
    if not os.path.exists(FALLBACK_CACHE_FILE):
        return []
    try:
        with open(FALLBACK_CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save_fallback_history(entry_dict):
    """Menyimpan entri riwayat ke cache lokal jika PostgreSQL sedang offline."""
    os.makedirs(FALLBACK_CACHE_DIR, exist_ok=True)
    history = _read_fallback_history()
    entry_dict["id"] = (history[0]["id"] + 1) if history else 1
    history.insert(0, entry_dict)
    # Batasi cache lokal maksimal 100 entri
    history = history[:100]
    try:
        with open(FALLBACK_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
    return entry_dict["id"]


def _delete_fallback_history(entry_id=None):
    """Menghapus entri dari cache lokal."""
    if not os.path.exists(FALLBACK_CACHE_FILE):
        return
    history = _read_fallback_history()
    if entry_id is not None:
        history = [h for h in history if h.get("id") != entry_id]
    else:
        history = []
    try:
        with open(FALLBACK_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


@jwt_required(optional=True)
def ml_predict():
    """Endpoint prediksi cerdas tebu — menerima input, mengembalikan inferensi model Ensemble,
    dan menyimpan riwayat ke PostgreSQL (dengan graceful fallback jika DB belum aktif)."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Input JSON tidak ditemukan"}), 400

        result = run_prediction(data)

        # Coba simpan ke database PostgreSQL
        user_id = None
        try:
            identity = get_jwt_identity()
            if identity:
                import uuid
                user_id = uuid.UUID(str(identity))
        except Exception:
            pass

        db_saved = False
        try:
            entry = PrediksiML(
                id_user=user_id,
                input_params=data,
                hasil=result["prediksi"],
                analisis_musim=result.get("analisis_musim"),
                rekomendasi=result.get("rekomendasi"),
            )
            db.session.add(entry)
            db.session.commit()
            result["id"] = entry.id
            db_saved = True
        except Exception:
            db.session.rollback()

        # Jika PostgreSQL sedang tidak aktif, simpan ke cache riwayat lokal
        if not db_saved:
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cache_id = _save_fallback_history({
                "timestamp": now_str,
                "input": data,
                "hasil": result["prediksi"],
                "analisis_musim": result.get("analisis_musim"),
                "rekomendasi": result.get("rekomendasi"),
            })
            result["id"] = cache_id

        return jsonify(result)

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@jwt_required(optional=True)
def ml_history():
    """Mengambil seluruh riwayat prediksi ML dari PostgreSQL (atau fallback jika DB offline)."""
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 50, type=int)

        # 1. Coba ambil dari PostgreSQL
        try:
            pagination = PrediksiML.query.order_by(
                PrediksiML.created_at.desc()
            ).paginate(page=page, per_page=per_page, error_out=False)

            history = []
            for entry in pagination.items:
                history.append({
                    "id": entry.id,
                    "timestamp": entry.created_at.strftime("%Y-%m-%d %H:%M:%S") if entry.created_at else None,
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
                "storage": "postgresql"
            })
        except Exception:
            db.session.rollback()

        # 2. Fallback: Ambil dari cache riwayat lokal jika PostgreSQL tidak aktif
        local_history = _read_fallback_history()
        start = (page - 1) * per_page
        end = start + per_page
        paginated_history = local_history[start:end]

        return jsonify({
            "success": True,
            "history": paginated_history,
            "total": len(local_history),
            "page": page,
            "pages": (len(local_history) + per_page - 1) // per_page if local_history else 1,
            "storage": "local_cache"
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@jwt_required(optional=True)
def ml_delete_history(entry_id):
    """Hapus satu entri riwayat prediksi berdasarkan ID."""
    deleted_from_db = False
    try:
        entry = db.session.get(PrediksiML, entry_id)
        if entry:
            db.session.delete(entry)
            db.session.commit()
            deleted_from_db = True
    except Exception:
        db.session.rollback()

    _delete_fallback_history(entry_id)
    return jsonify({"success": True, "message": "Riwayat prediksi berhasil dihapus"})


@jwt_required(optional=True)
def ml_clear_history():
    """Hapus seluruh riwayat prediksi ML."""
    try:
        PrediksiML.query.delete()
        db.session.commit()
    except Exception:
        db.session.rollback()

    _delete_fallback_history()
    return jsonify({"success": True, "message": "Seluruh riwayat prediksi berhasil dibersihkan"})
