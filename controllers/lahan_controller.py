from flask import request, jsonify
from extensions import db
from models.lahan import Lahan
from models.blok import Blok
import cloudinary.uploader

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_lahan():
    if request.is_json:
        data = request.get_json() or {}
        nama_lahan = data.get("nama_lahan")
        tipe = data.get("tipe")
        foto_teks = data.get("foto")
        foto_file = None
    else:
        nama_lahan = request.form.get("nama_lahan")
        tipe = request.form.get("tipe")
        foto_file = request.files.get("foto")
        foto_teks = None

    if not nama_lahan:
        return jsonify({"message": "nama_lahan wajib diisi"}), 400

    foto_url = None
    if foto_file: # Jika upload via Form-Data
        if not allowed_file(foto_file.filename):
            return jsonify({"message": "Format file tidak didukung. Hanya menerima PNG, JPG, JPEG, dan PDF"}), 400
        try:
            upload_result = cloudinary.uploader.upload(
                foto_file, folder="agrikultur/lahan", resource_type="auto"
            )
            foto_url = upload_result.get("secure_url")
        except Exception as e:
            return jsonify({"message": f"Gagal mengunggah file ke cloud: {str(e)}"}), 500
    elif foto_teks: # Jika kirim link via JSON
        foto_url = foto_teks

    new_lahan = Lahan(nama_lahan=nama_lahan, tipe=tipe, foto=foto_url)
    db.session.add(new_lahan)
    db.session.commit()

    return jsonify({
        "message": "Data Lahan berhasil ditambahkan",
        "data": {
            "id_lahan": new_lahan.id_lahan, "nama_lahan": new_lahan.nama_lahan,
            "tipe": new_lahan.tipe, "foto": new_lahan.foto
        }
    }), 201

def get_all_lahan():
    lahans = Lahan.query.all()
    result = [{"id_lahan": l.id_lahan, "nama_lahan": l.nama_lahan, "tipe": l.tipe, "foto": l.foto} for l in lahans]
    return jsonify({"message": "Berhasil mengambil semua data lahan", "total": len(result), "data": result})

def get_lahan_by_id(id):
    lahan = Lahan.query.get(id)
    if not lahan:
        return jsonify({"message": "Lahan tidak ditemukan"}), 404
    return jsonify({
        "message": "Berhasil mengambil data lahan",
        "data": {"id_lahan": lahan.id_lahan, "nama_lahan": lahan.nama_lahan, "tipe": lahan.tipe, "foto": lahan.foto}
    })

def update_lahan(id):
    lahan = Lahan.query.get(id)
    if not lahan:
        return jsonify({"message": "Lahan tidak ditemukan"}), 404

    if request.is_json:
        data = request.get_json() or {}
        foto_file = None
        foto_teks = data.get("foto")
    else:
        data = request.form
        foto_file = request.files.get("foto")
        foto_teks = None

    if "nama_lahan" in data: lahan.nama_lahan = data["nama_lahan"]
    if "tipe" in data: lahan.tipe = data["tipe"]

    if foto_file:
        if not allowed_file(foto_file.filename):
            return jsonify({"message": "Format file tidak didukung"}), 400
        try:
            upload_result = cloudinary.uploader.upload(
                foto_file, folder="agrikultur/lahan", resource_type="auto"
            )
            lahan.foto = upload_result.get("secure_url") 
        except Exception as e:
            return jsonify({"message": f"Gagal mengunggah file ke cloud: {str(e)}"}), 500
    elif foto_teks:
        lahan.foto = foto_teks

    db.session.commit()
    return jsonify({
        "message": "Data Lahan berhasil diupdate",
        "data": {"id_lahan": lahan.id_lahan, "nama_lahan": lahan.nama_lahan, "tipe": lahan.tipe, "foto": lahan.foto}
    })

def delete_lahan(id):
    lahan = Lahan.query.get(id)
    if not lahan:
        return jsonify({"message": "Lahan tidak ditemukan"}), 404

    jumlah_blok = Blok.query.filter_by(id_lahan=id).count()
    db.session.delete(lahan)
    db.session.commit()

    return jsonify({
        "message": "Data Lahan berhasil dihapus",
        "info": {"blok_terhapus": jumlah_blok, "catatan": "Data terkait ikut terhapus karena ON DELETE CASCADE"}
    })