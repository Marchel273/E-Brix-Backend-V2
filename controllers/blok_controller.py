from flask import request, jsonify
from extensions import db
from models.blok import Blok
from models.lahan import Lahan
from models.data_brix import DataBrix
import cloudinary.uploader

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_blok():
    if request.is_json:
        data = request.get_json() or {}
        id_lahan = data.get("id_lahan")
        nama_blok = data.get("nama_blok")
        foto_teks = data.get("foto")
        foto_file = None
    else:
        id_lahan = request.form.get("id_lahan")
        nama_blok = request.form.get("nama_blok")
        foto_file = request.files.get("foto")
        foto_teks = None

    if not id_lahan or not nama_blok:
        return jsonify({"message": "id_lahan dan nama_blok wajib diisi"}), 400

    if not Lahan.query.get(id_lahan):
        return jsonify({"message": "Lahan tidak ditemukan"}), 404

    foto_url = None
    if foto_file:
        if not allowed_file(foto_file.filename):
            return jsonify({"message": "Format file tidak didukung"}), 400
        try:
            upload_result = cloudinary.uploader.upload(
                foto_file, folder="agrikultur/blok", resource_type="auto"
            )
            foto_url = upload_result.get("secure_url")
        except Exception as e:
            return jsonify({"message": f"Gagal mengunggah gambar ke cloud: {str(e)}"}), 500
    elif foto_teks:
        foto_url = foto_teks

    new_blok = Blok(id_lahan=id_lahan, nama_blok=nama_blok, foto=foto_url)
    db.session.add(new_blok)
    db.session.commit()

    return jsonify({
        "message": "Data Blok berhasil ditambahkan",
        "data": {
            "id_blok": new_blok.id_blok, "id_lahan": new_blok.id_lahan, 
            "nama_blok": new_blok.nama_blok, "foto": new_blok.foto
        }
    }), 201

def get_all_blok():
    bloks = Blok.query.all()
    result = [{"id_blok": b.id_blok, "id_lahan": b.id_lahan, "nama_blok": b.nama_blok, "foto": b.foto} for b in bloks]
    return jsonify({"message": "Berhasil mengambil semua data blok", "total": len(result), "data": result})

def get_blok_by_id(id):
    blok = Blok.query.get(id)
    if not blok:
        return jsonify({"message": "Blok tidak ditemukan"}), 404
    return jsonify({
        "message": "Berhasil mengambil data blok",
        "data": {"id_blok": blok.id_blok, "id_lahan": blok.id_lahan, "nama_blok": blok.nama_blok, "foto": blok.foto}
    })

def update_blok(id):
    blok = Blok.query.get(id)
    if not blok:
        return jsonify({"message": "Blok tidak ditemukan"}), 404

    if request.is_json:
        data = request.get_json() or {}
        foto_file = None
        foto_teks = data.get("foto")
    else:
        data = request.form
        foto_file = request.files.get("foto")
        foto_teks = None

    if "id_lahan" in data:
        if not Lahan.query.get(data["id_lahan"]): 
            return jsonify({"message": "Lahan tidak ditemukan"}), 404
        blok.id_lahan = data["id_lahan"]

    if "nama_blok" in data: 
        blok.nama_blok = data["nama_blok"]

    if foto_file:
        if not allowed_file(foto_file.filename):
            return jsonify({"message": "Format file tidak didukung"}), 400
        try:
            upload_result = cloudinary.uploader.upload(
                foto_file, folder="agrikultur/blok", resource_type="auto"
            )
            blok.foto = upload_result.get("secure_url")
        except Exception as e:
            return jsonify({"message": f"Gagal mengunggah gambar ke cloud: {str(e)}"}), 500
    elif foto_teks:
        blok.foto = foto_teks

    db.session.commit()
    return jsonify({
        "message": "Data Blok berhasil diupdate",
        "data": {"id_blok": blok.id_blok, "id_lahan": blok.id_lahan, "nama_blok": blok.nama_blok, "foto": blok.foto}
    })

def delete_blok(id):
    blok = Blok.query.get(id)
    if not blok:
        return jsonify({"message": "Blok tidak ditemukan"}), 404

    jumlah_data = DataBrix.query.filter_by(id_blok=id).count()
    db.session.delete(blok)
    db.session.commit()

    return jsonify({
        "message": "Data Blok berhasil dihapus",
        "info": {"data_brix_terhapus": jumlah_data, "catatan": "Data terkait ikut terhapus karena ON DELETE CASCADE"}
    })