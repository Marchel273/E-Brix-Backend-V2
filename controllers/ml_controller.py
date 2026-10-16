from flask import request, jsonify
from services.ebrix_ml_engine import ml_engine


def predict_brix():
    """Endpoint prediksi kadar Brix."""
    data = request.get_json() or {}
    result = ml_engine.predict_brix(data)
    return jsonify({"message": "Prediksi Brix berhasil", "data": result}), 200


def predict_yield():
    """Endpoint prediksi produktivitas panen (Ton/Ha)."""
    data = request.get_json() or {}
    result = ml_engine.predict_yield(data)
    return jsonify({"message": "Prediksi Yield berhasil", "data": result}), 200


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
    """Endpoint klasifikasi penyakit tanaman tebu."""
    data = request.get_json() or {}
    result = ml_engine.classify_disease(data)
    return jsonify({"message": "Klasifikasi Penyakit berhasil", "data": result}), 200


def calculate_winter_carp():
    """Endpoint kalkulasi rendemen Winter-Carp."""
    data = request.get_json() or {}
    brix = float(data.get("brix", data.get("nilai_brix", 19.5)))
    yield_val = float(data.get("yield_ton_ha", data.get("yield", 85.0)))
    result = ml_engine.calculate_winter_carp(brix, yield_val)
    return jsonify({"message": "Kalkulasi Winter-Carp berhasil", "data": result}), 200


def analyze_seasons():
    """Endpoint analisis pengaruh musim terhadap kematangan."""
    data = request.get_json() or {}
    result = ml_engine.analyze_seasons(data)
    return jsonify({"message": "Analisis Musim berhasil", "data": result}), 200


def infer_multi_target():
    """Endpoint inferensi lengkap multi-target (Brix, Yield, Sugar, Nira, Duration, Disease, Winter-Carp, Seasons)."""
    data = request.get_json() or {}
    result = ml_engine.infer_multi_target(data)
    return jsonify({"message": "Inferensi Multi-Target berhasil", "data": result}), 200


def get_ml_info():
    """Informasi model bundle dan konfigurasi form ML Engine."""
    return jsonify({
        "message": "EBrixMLEngine info",
        "models_bundle": ml_engine.models_bundle,
        "form_config": ml_engine.form_config
    }), 200
