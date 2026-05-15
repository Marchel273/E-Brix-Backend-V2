from flask import request, jsonify
from extensions import db
from models.prediksi import Prediksi
from models.data_brix import DataBrix

def create_prediksi():
    data = request.get_json()
    if not data or not data.get("id_data"):
        return jsonify({"message": "id_data wajib diisi"}), 400

    if not DataBrix.query.get(data.get("id_data")):
        return jsonify({"message": "Data Brix tidak ditemukan"}), 404

    new_prediksi = Prediksi(
        id_data=data.get("id_data"),
        hasil_prediksi=data.get("hasil_prediksi"),
        confidence_score=data.get("confidence_score"),
    )
    db.session.add(new_prediksi)
    db.session.commit()

    return jsonify({
        "message": "Data Prediksi berhasil ditambahkan",
        "data": {
            "id_prediksi": new_prediksi.id_prediksi, "id_data": new_prediksi.id_data,
            "hasil_prediksi": new_prediksi.hasil_prediksi, "confidence_score": new_prediksi.confidence_score
        }
    }), 201

def get_all_prediksi():
    prediksis = Prediksi.query.all()
    result = [{
        "id_prediksi": p.id_prediksi, "id_data": p.id_data,
        "hasil_prediksi": p.hasil_prediksi, "confidence_score": p.confidence_score
    } for p in prediksis]
    return jsonify({"message": "Berhasil mengambil semua data prediksi", "total": len(result), "data": result})

def get_prediksi_by_id(id):
    prediksi = Prediksi.query.get(id)
    if not prediksi:
        return jsonify({"message": "Data Prediksi tidak ditemukan"}), 404
    return jsonify({
        "message": "Berhasil mengambil data prediksi",
        "data": {
            "id_prediksi": prediksi.id_prediksi, "id_data": prediksi.id_data,
            "hasil_prediksi": prediksi.hasil_prediksi, "confidence_score": prediksi.confidence_score
        }
    })

def update_prediksi(id):
    prediksi = Prediksi.query.get(id)
    if not prediksi:
        return jsonify({"message": "Data Prediksi tidak ditemukan"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"message": "Body JSON tidak boleh kosong"}), 400

    if "id_data" in data:
        if not DataBrix.query.get(data["id_data"]): return jsonify({"message": "Data Brix tidak ditemukan"}), 404
        prediksi.id_data = data["id_data"]

    if "hasil_prediksi" in data: prediksi.hasil_prediksi = data["hasil_prediksi"]
    if "confidence_score" in data: prediksi.confidence_score = data["confidence_score"]

    db.session.commit()
    return jsonify({
        "message": "Data Prediksi berhasil diupdate",
        "data": {
            "id_prediksi": prediksi.id_prediksi, "id_data": prediksi.id_data,
            "hasil_prediksi": prediksi.hasil_prediksi, "confidence_score": prediksi.confidence_score
        }
    })

def delete_prediksi(id):
    prediksi = Prediksi.query.get(id)
    if not prediksi:
        return jsonify({"message": "Data Prediksi tidak ditemukan"}), 404

    db.session.delete(prediksi)
    db.session.commit()
    return jsonify({"message": "Data Prediksi berhasil dihapus"})
