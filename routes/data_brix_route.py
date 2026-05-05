from flask import Blueprint, request, jsonify
from extensions import db
from model import DataBrix, Blok

data_brix_bp = Blueprint("data_brix", __name__)

@data_brix_bp.route("/data-brix", methods=["POST"])
def create_brix():
    data = request.get_json()
    if not data or not data.get("id_blok"):
        return jsonify({"message": "id_blok wajib diisi"}), 400
    
    # Validasi foto wajib diisi untuk data_brix
    if not data.get("foto"):
        return jsonify({"message": "foto wajib diisi"}), 400

    if not Blok.query.get(data.get("id_blok")):
        return jsonify({"message": "Blok tidak ditemukan"}), 404

    new_data = DataBrix(
        id_blok=data.get("id_blok"),
        latitude=data.get("latitude"),
        longitude=data.get("longitude"),
        nilai_brix=data.get("nilai_brix"),
        foto=data.get("foto") # Wajib
    )
    db.session.add(new_data)
    db.session.commit()

    return jsonify({
        "message": "Data Brix berhasil ditambahkan",
        "data": {
            "id_data": new_data.id_data, "id_blok": new_data.id_blok,
            "latitude": new_data.latitude, "longitude": new_data.longitude,
            "nilai_brix": new_data.nilai_brix, "foto": new_data.foto
        }
    }), 201

@data_brix_bp.route("/data-brix", methods=["GET"])
def get_all_brix():
    datas = DataBrix.query.all()
    result = [{
        "id_data": d.id_data, "id_blok": d.id_blok, "latitude": d.latitude,
        "longitude": d.longitude, "nilai_brix": d.nilai_brix, "foto": d.foto, "timestamp": d.timestamp
    } for d in datas]
    return jsonify({"message": "Berhasil mengambil semua data brix", "total": len(result), "data": result})

@data_brix_bp.route("/data-brix/<int:id>", methods=["GET"])
def get_brix_by_id(id):
    data = DataBrix.query.get(id)
    if not data:
        return jsonify({"message": "Data Brix tidak ditemukan"}), 404
    return jsonify({
        "message": "Berhasil mengambil data brix",
        "data": {
            "id_data": data.id_data, "id_blok": data.id_blok, "latitude": data.latitude,
            "longitude": data.longitude, "nilai_brix": data.nilai_brix, "foto": data.foto, "timestamp": data.timestamp
        }
    })

@data_brix_bp.route("/data-brix/<int:id>", methods=["PUT"])
def update_brix(id):
    data_brix = DataBrix.query.get(id)
    if not data_brix:
        return jsonify({"message": "Data Brix tidak ditemukan"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"message": "Body JSON tidak boleh kosong"}), 400

    if "id_blok" in data:
        if not Blok.query.get(data["id_blok"]): return jsonify({"message": "Blok tidak ditemukan"}), 404
        data_brix.id_blok = data["id_blok"]

    if "latitude" in data: data_brix.latitude = data["latitude"]
    if "longitude" in data: data_brix.longitude = data["longitude"]
    if "nilai_brix" in data: data_brix.nilai_brix = data["nilai_brix"]
    if "foto" in data: data_brix.foto = data["foto"]

    db.session.commit()
    return jsonify({
        "message": "Data Brix berhasil diupdate",
        "data": {
            "id_data": data_brix.id_data, "id_blok": data_brix.id_blok, "latitude": data_brix.latitude,
            "longitude": data_brix.longitude, "nilai_brix": data_brix.nilai_brix, "foto": data_brix.foto
        }
    })

@data_brix_bp.route("/data-brix/<int:id>", methods=["DELETE"])
def delete_brix(id):
    data_brix = DataBrix.query.get(id)
    if not data_brix:
        return jsonify({"message": "Data Brix tidak ditemukan"}), 404

    db.session.delete(data_brix)
    db.session.commit()
    return jsonify({"message": "Data Brix berhasil dihapus", "catatan": "Data prediksi terkait ikut terhapus"})