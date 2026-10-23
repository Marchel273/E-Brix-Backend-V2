import os
import json
from datetime import datetime
from flask import request, jsonify
from extensions import db
from models.riwayat_prediksi import RiwayatPrediksiML
from services.ebrix_ml_engine import ml_engine, MODEL_DIR, BASE_DIR

# File backup riwayat prediksi (JSON)
HISTORY_FILE = os.path.join(BASE_DIR, "prediction_history.json")


def _load_history():
    """Muat riwayat prediksi dari database PostgreSQL (fallback ke JSON jika DB kosong/error)."""
    try:
        records = RiwayatPrediksiML.query.order_by(RiwayatPrediksiML.id.asc()).all()
        if records:
            return [r.to_dict() for r in records]
    except Exception as e:
        print("[ML History] Catatan DB fallback ke JSON:", e)

    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def _save_history_entry(input_data, hasil, analisis_musim=None, rekomendasi=None):
    """Simpan entri prediksi baru ke database PostgreSQL dan file JSON."""
    entry_dict = None
    try:
        new_entry = RiwayatPrediksiML(
            timestamp=datetime.now(),
            input_data=input_data,
            hasil=hasil,
            analisis_musim=analisis_musim,
            rekomendasi=rekomendasi
        )
        db.session.add(new_entry)
        db.session.commit()
        entry_dict = new_entry.to_dict()
    except Exception as e:
        db.session.rollback()
        print("[ML History] Gagal simpan ke DB, fallback ke file:", e)

    # Sinkronkan juga ke JSON backup
    try:
        history = []
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)

        if entry_dict:
            history.append(entry_dict)
        else:
            history.append({
                "id": len(history) + 1,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "input": input_data,
                "hasil": hasil,
                "analisis_musim": analisis_musim,
                "rekomendasi": rekomendasi
            })

        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("[ML History] Gagal simpan backup JSON:", e)

    return entry_dict


# ─────────────────────────────────────────────────────────────────
# 1. Individual Target Prediction Endpoints
# ─────────────────────────────────────────────────────────────────
def predict_brix():
    """Endpoint prediksi kadar Brix."""
    data = request.get_json() or {}
    result = ml_engine.predict_brix(data)
    return jsonify({"message": "Prediksi Brix berhasil", "data": result}), 200


def predict_yield():
    """Endpoint prediksi produktivitas panen tebu (Sugarcane Yield)."""
    data = request.get_json() or {}
    result = ml_engine.predict_yield(data)
    return jsonify({
        "message": "Prediksi Sugarcane Yield berhasil",
        "data": result,
        "target": "yield_quintal_per_acre",
        "unit_conversions": {
            "quintal_per_acre": result.get("predicted_yield_quintal_per_acre"),
            "ton_per_hectare": result.get("predicted_yield_ton_ha")
        }
    }), 200


def predict_sugar():
    """Endpoint prediksi rendemen gula kristal."""
    data = request.get_json() or {}
    result = ml_engine.predict_sugar(data)
    return jsonify({"message": "Prediksi Rendemen Gula berhasil", "data": result}), 200


def predict_nira():
    """Endpoint prediksi volume perahan nira."""
    data = request.get_json() or {}
    result = ml_engine.predict_nira(data)
    return jsonify({"message": "Prediksi Nira berhasil", "data": result}), 200


def predict_duration():
    """Endpoint prediksi sisa hari menuju panen optimal."""
    data = request.get_json() or {}
    result = ml_engine.predict_duration(data)
    return jsonify({"message": "Prediksi Durasi Panen berhasil", "data": result}), 200


def classify_disease():
    """Endpoint klasifikasi keparahan penyakit tanaman tebu."""
    data = request.get_json() or {}
    result = ml_engine.classify_disease(data)
    return jsonify({"message": "Klasifikasi Penyakit berhasil", "data": result}), 200


def calculate_winter_carp():
    """Endpoint kalkulasi rendemen Winter-Carp standar industri gula."""
    data = request.get_json() or {}
    brix = float(data.get("brix", data.get("nilai_brix", 19.5)))
    yield_val = float(data.get("yield_ton_ha", data.get("yield", 85.0)))
    result = ml_engine.calculate_winter_carp(brix, yield_val)
    return jsonify({"message": "Kalkulasi Winter-Carp berhasil", "data": result}), 200


def analyze_seasons():
    """Endpoint analisis pengaruh musim terhadap kematangan tebu."""
    data = request.get_json() or {}
    result = ml_engine.analyze_seasons(data)
    return jsonify({"message": "Analisis Musim berhasil", "data": result}), 200


# ─────────────────────────────────────────────────────────────────
# 2. Complete / Multi-Target Inference (Compatible with ML Project)
# ─────────────────────────────────────────────────────────────────
def infer_multi_target():
    """
    Endpoint inferensi lengkap multi-target:
    Brix, Sugarcane Yield, Sugar, Nira, Duration, Disease, Winter-Carp, Seasons.
    Hasil otomatis disimpan ke tabel PostgreSQL `riwayat_prediksi_ml`.
    """
    try:
        data = request.get_json() or {}
        result = ml_engine.infer_multi_target(data)

        multi_details = result.get("multi_target_details", {})
        winter = multi_details.get("winter_carp", {})
        seasons = multi_details.get("seasons", {})
        disease = multi_details.get("disease", {})
        duration = multi_details.get("duration", {})
        sugar = multi_details.get("sugar", {})
        nira = multi_details.get("nira", {})
        yield_res = multi_details.get("yield", {})
        brix_res = multi_details.get("brix", {})

        # Format hasil identik dengan struktur JSON ML
        hasil_formatted = {
            "hasil_panen": yield_res.get("predicted_yield_quintal_per_acre", yield_res.get("predicted_yield_ton_ha")),
            "kadar_gula_brix": brix_res.get("predicted_brix"),
            "durasi_panen_hari": duration.get("predicted_remaining_days"),
            "durasi_panen_bulan": int(duration.get("predicted_remaining_days", 0) / 30),
            "durasi_panen_sisa_hari": int(duration.get("predicted_remaining_days", 0) % 30),
            "keparahan_penyakit": disease.get("disease_severity_id", disease.get("disease_severity")),
            "keparahan_penyakit_en": disease.get("disease_severity"),
            "kepercayaan_penyakit": round(disease.get("confidence_score", 0.9) * 100, 1),
            "probabilitas_penyakit": disease.get("probability_per_class", {}),
            "perhitungan_gula": {
                "brix": brix_res.get("predicted_brix"),
                "hk_standar_persen": 80,
                "hk_optimis_persen": 85,
                "pol_standar": winter.get("pol_standar"),
                "pol_optimis": winter.get("pol_optimis"),
                "nn_standar": winter.get("nn_standar"),
                "nn_optimis": winter.get("nn_optimis"),
                "nn_cepat": winter.get("nn_cepat"),
                "potensi_gula_standar": winter.get("sugar_yield_ton_ha_standar"),
                "potensi_gula_optimis": winter.get("sugar_yield_ton_ha_optimis")
            },
            "potensi_gula": winter.get("sugar_yield_ton_ha_standar"),
            "potensi_gula_kristal": sugar.get("predicted_sugar_quintal_per_acre"),
            "produksi_nira": nira.get("predicted_nira_liters_per_acre")
        }

        rekomendasi_formatted = {
            "waktu_panen": f"Jadwalkan panen {duration.get('predicted_remaining_days', 0)} hari lagi ({duration.get('urgensi_tebang')}). Rekomendasi tanggal tebang: {duration.get('recommended_harvest_date')}.",
            "tindakan_hasil": yield_res.get("kategori_potensi", ""),
            "tindakan_brix": brix_res.get("kategori", ""),
            "tindakan_penyakit": disease.get("treatment_recommendation", ""),
            "musim_tanam": seasons.get("rekomendasi_agronomi", ""),
            "gula": winter.get("formula_reference", "Winter-Carp Classical Rendemen Equation")
        }

        # Simpan ke PostgreSQL database
        saved_entry = _save_history_entry(
            input_data=data,
            hasil=hasil_formatted,
            analisis_musim=seasons,
            rekomendasi=rekomendasi_formatted
        )

        return jsonify({
            "success": True,
            "message": "Inferensi Multi-Target berhasil dan tersimpan di database",
            "id_riwayat": saved_entry.get("id") if saved_entry else None,
            "prediksi": hasil_formatted,
            "analisis_musim": seasons,
            "rekomendasi": rekomendasi_formatted,
            "summary": result.get("hasil_prediksi", ""),
            "confidence_score": result.get("confidence_score")
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


# ─────────────────────────────────────────────────────────────────
# 3. History Management Endpoints (Database-backed)
# ─────────────────────────────────────────────────────────────────
def get_prediction_history():
    """Mengambil seluruh riwayat prediksi langsung dari database PostgreSQL."""
    try:
        records = RiwayatPrediksiML.query.order_by(RiwayatPrediksiML.id.desc()).all()
        data = [r.to_dict() for r in records]
        return jsonify({
            "success": True,
            "source": "database",
            "total": len(data),
            "history": data
        }), 200
    except Exception as e:
        # Fallback ke JSON jika DB bermasalah
        history = _load_history()
        return jsonify({
            "success": True,
            "source": "fallback_json",
            "error_db": str(e),
            "total": len(history),
            "history": list(reversed(history))
        }), 200


def delete_prediction_history(entry_id):
    """Menghapus entri riwayat prediksi dari database PostgreSQL."""
    try:
        record = RiwayatPrediksiML.query.get(entry_id)
        if record:
            db.session.delete(record)
            db.session.commit()

        # Update juga backup file JSON
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
            history = [h for h in history if h.get("id") != entry_id]
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)

        return jsonify({
            "success": True,
            "message": f"Riwayat ID {entry_id} berhasil dihapus dari database"
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


# ─────────────────────────────────────────────────────────────────
# 4. Model Info & Form Configuration
# ─────────────────────────────────────────────────────────────────
def get_ml_info():
    """Informasi metadata model ensemble dan konfigurasi form ML Engine."""
    metadata_path = os.path.join(MODEL_DIR, "model_metadata.json")
    metadata = {}
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
        except Exception:
            metadata = {}

    models_summary = {
        "model_yield": str(type(ml_engine._model_yield).__name__),
        "model_sugar": str(type(ml_engine._model_sugar).__name__),
        "model_nira": str(type(ml_engine._model_nira).__name__),
        "model_brix": str(type(ml_engine._model_brix).__name__),
        "model_duration": str(type(ml_engine._model_duration).__name__),
        "model_disease": str(type(ml_engine._model_disease).__name__),
    }

    return jsonify({
        "success": True,
        "message": "EBrixMLEngine info",
        "models_summary": models_summary,
        "model_metadata": metadata,
        "form_config": ml_engine.form_config,
        "feature_names": ml_engine._feature_columns,
        "num_cols": ml_engine._num_cols,
        "cat_cols": ml_engine._cat_cols,
        "disease_classes": list(ml_engine._le_disease.classes_)
    }), 200
