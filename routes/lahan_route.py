from flask import Blueprint, request, jsonify
from extensions import db
from model import Lahan, Blok

lahan_bp = Blueprint("lahan", __name__)

@lahan_bp.route("/lahan", methods=["POST"])
def create_lahan():
    data = request.get_json()
    if not data or not data.get("nama_lahan"):
        return jsonify({"message": "nama_lahan wajib diisi"}), 400

    new_lahan = Lahan(
        nama_lahan=data.get("nama_lahan"),
        tipe=data.get("tipe"),
        foto=data.get("foto") # Optional
    )
    db.session.add(new_lahan)
    db.session.commit()

    return jsonify({
        "message": "Data Lahan berhasil ditambahkan",
        "data": {
            "id_lahan": new_lahan.id_lahan,
            "nama_lahan": new_lahan.nama_lahan,
            "tipe": new_lahan.tipe,
            "foto": new_lahan.foto
        }
    }), 201

@lahan_bp.route("/lahan", methods=["GET"])
def get_all_lahan():
    lahans = Lahan.query.all()
    result = [{"id_lahan": l.id_lahan, "nama_lahan": l.nama_lahan, "tipe": l.tipe, "foto": l.foto} for l in lahans]
    return jsonify({"message": "Berhasil mengambil semua data lahan", "total": len(result), "data": result})

@lahan_bp.route("/lahan/<int:id>", methods=["GET"])
def get_lahan_by_id(id):
    lahan = Lahan.query.get(id)
    if not lahan:
        return jsonify({"message": "Lahan tidak ditemukan"}), 404
    return jsonify({
        "message": "Berhasil mengambil data lahan",
        "data": {"id_lahan": lahan.id_lahan, "nama_lahan": lahan.nama_lahan, "tipe": lahan.tipe, "foto": lahan.foto}
    })

@lahan_bp.route("/lahan/<int:id>", methods=["PUT"])
def update_lahan(id):
    lahan = Lahan.query.get(id)
    if not lahan:
        return jsonify({"message": "Lahan tidak ditemukan"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"message": "Body JSON tidak boleh kosong"}), 400

    if "nama_lahan" in data: lahan.nama_lahan = data["nama_lahan"]
    if "tipe" in data: lahan.tipe = data["tipe"]
    if "foto" in data: lahan.foto = data["foto"]

    db.session.commit()
    return jsonify({
        "message": "Data Lahan berhasil diupdate",
        "data": {"id_lahan": lahan.id_lahan, "nama_lahan": lahan.nama_lahan, "tipe": lahan.tipe, "foto": lahan.foto}
    })

@lahan_bp.route("/lahan/<int:id>", methods=["DELETE"])
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