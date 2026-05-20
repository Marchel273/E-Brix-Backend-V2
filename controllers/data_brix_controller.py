from flask import request, jsonify
from extensions import db
from models.data_brix import DataBrix
from models.blok import Blok
import cloudinary.uploader

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_brix():
    if request.is_json:
        data = request.get_json() or {}
        id_blok = data.get("id_blok")
        latitude = data.get("latitude")
        longitude = data.get("longitude")
        nilai_brix = data.get("nilai_brix")
        foto_teks = data.get("foto")
        foto_file = None
    else:
        id_blok = request.form.get("id_blok")
        latitude = request.form.get("latitude")
        longitude = request.form.get("longitude")
        nilai_brix = request.form.get("nilai_brix")
        foto_file = request.files.get("foto")
        foto_teks = None

    if not id_blok:
        return jsonify({"message": "id_blok wajib diisi"}), 400
    
    if not foto_file and not foto_teks:
        return jsonify({"message": "foto wajib diisi"}), 400

    if not Blok.query.get(id_blok):
        return jsonify({"message": "Blok tidak ditemukan"}), 404

    foto_url = None
    if foto_file:
        if not allowed_file(foto_file.filename):
            return jsonify({"message": "Format file tidak didukung"}), 400
        try:
            upload_result = cloudinary.uploader.upload(
                foto_file, folder="agrikultur/data_brix", resource_type="auto"
            )
            foto_url = upload_result.get("secure_url")
        except Exception as e:
            return jsonify({"message": f"Gagal mengunggah gambar ke cloud: {str(e)}"}), 500
    elif foto_teks:
        foto_url = foto_teks

    new_data = DataBrix(
        id_blok=id_blok, latitude=latitude, longitude=longitude,
        nilai_brix=nilai_brix, foto=foto_url
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

def get_all_brix():
    datas = DataBrix.query.all()
    result = [{
        "id_data": d.id_data, "id_blok": d.id_blok, "latitude": d.latitude,
        "longitude": d.longitude, "nilai_brix": d.nilai_brix, "foto": d.foto, "timestamp": d.timestamp
    } for d in datas]
    return jsonify({"message": "Berhasil mengambil semua data brix", "total": len(result), "data": result})

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

def update_brix(id):
    data_brix = DataBrix.query.get(id)
    if not data_brix:
        return jsonify({"message": "Data Brix tidak ditemukan"}), 404

    if request.is_json:
        data = request.get_json() or {}
        foto_file = None
        foto_teks = data.get("foto")
    else:
        data = request.form
        foto_file = request.files.get("foto")
        foto_teks = None

    if "id_blok" in data:
        if not Blok.query.get(data["id_blok"]): 
            return jsonify({"message": "Blok tidak ditemukan"}), 404
        data_brix.id_blok = data["id_blok"]

    if "latitude" in data: data_brix.latitude = data["latitude"]
    if "longitude" in data: data_brix.longitude = data["longitude"]
    if "nilai_brix" in data: data_brix.nilai_brix = data["nilai_brix"]

    if foto_file:
        if not allowed_file(foto_file.filename):
            return jsonify({"message": "Format file tidak didukung"}), 400
        try:
            upload_result = cloudinary.uploader.upload(
                foto_file, folder="agrikultur/data_brix", resource_type="auto"
            )
            data_brix.foto = upload_result.get("secure_url")
        except Exception as e:
            return jsonify({"message": f"Gagal mengunggah gambar ke cloud: {str(e)}"}), 500
    elif foto_teks:
        data_brix.foto = foto_teks

    db.session.commit()
    return jsonify({
        "message": "Data Brix berhasil diupdate",
        "data": {
            "id_data": data_brix.id_data, "id_blok": data_brix.id_blok, "latitude": data_brix.latitude,
            "longitude": data_brix.longitude, "nilai_brix": data_brix.nilai_brix, "foto": data_brix.foto
        }
    })

def delete_brix(id):
    data_brix = DataBrix.query.get(id)
    if not data_brix:
        return jsonify({"message": "Data Brix tidak ditemukan"}), 404

    db.session.delete(data_brix)
    db.session.commit()
    return jsonify({"message": "Data Brix berhasil dihapus", "catatan": "Data prediksi terkait ikut terhapus"})