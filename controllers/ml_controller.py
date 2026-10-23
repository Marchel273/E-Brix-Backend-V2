import os
import json
from flask import request, jsonify
from services.ebrix_ml_engine import ml_engine, MODEL_DIR, BASE_DIR

# Riwayat prediksi (history file)
HISTORY_FILE = os.path.join(BASE_DIR, "prediction_history.json")


def _load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def _save_history(history):
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("[ML History] Error saving history:", e)


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
    """
    try:
        data = request.get_json() or {}
        result = ml_engine.infer_multi_target(data)

        # Simpan otomatis ke riwayat prediksi
        history = _load_history()
        history_entry = {
            "id": len(history) + 1,
            "timestamp": data.get("timestamp") or "",
            "input": data,
            "hasil": result.get("multi_target_details", {}),
            "summary": result.get("hasil_prediksi", "")
        }
        history.append(history_entry)
        _save_history(history)

        return jsonify({
            "success": True,
            "message": "Inferensi Multi-Target berhasil",
            "prediksi": result.get("multi_target_details", {}),
            "summary": result.get("hasil_prediksi", ""),
            "confidence_score": result.get("confidence_score")
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


# ─────────────────────────────────────────────────────────────────
# 3. History Management Endpoints
# ─────────────────────────────────────────────────────────────────
def get_prediction_history():
    """Mengambil seluruh riwayat prediksi."""
    history = _load_history()
    return jsonify({
        "success": True,
        "total": len(history),
        "history": list(reversed(history))
    }), 200


def delete_prediction_history(entry_id):
    """Menghapus entri riwayat prediksi tertentu."""
    history = _load_history()
    updated = [h for h in history if h.get("id") != entry_id]
    _save_history(updated)
    return jsonify({
        "success": True,
        "message": f"Riwayat ID {entry_id} berhasil dihapus"
    }), 200


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
