from flask import request, jsonify
from extensions import db
from models.model import Blok, Lahan, DataBrix

def create_blok():
    data = request.get_json()
    if not data or not data.get("id_lahan") or not data.get("nama_blok"):
        return jsonify({"message": "id_lahan dan nama_blok wajib diisi"}), 400

    if not Lahan.query.get(data.get("id_lahan")):
        return jsonify({"message": "Lahan tidak ditemukan"}), 404

    new_blok = Blok(
        id_lahan=data.get("id_lahan"),
        nama_blok=data.get("nama_blok"),
        foto=data.get("foto") # Optional
    )
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

    data = request.get_json()
    if not data:
        return jsonify({"message": "Body JSON tidak boleh kosong"}), 400

    if "id_lahan" in data:
        if not Lahan.query.get(data["id_lahan"]): return jsonify({"message": "Lahan tidak ditemukan"}), 404
        blok.id_lahan = data["id_lahan"]

    if "nama_blok" in data: blok.nama_blok = data["nama_blok"]
    if "foto" in data: blok.foto = data["foto"]

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
