import uuid
from flask import request, jsonify
from flask_jwt_extended import jwt_required
from extensions import db
from models.petani import Petani
from models.user import User

@jwt_required()
def create_petani():
    data = request.get_json() or {}
    id_user = data.get("id_user")
    nama = data.get("nama")
    nomor_telepon = data.get("nomor_telepon")
    alamat = data.get("alamat")

    if not id_user or not nama:
        return jsonify({"message": "id_user dan nama wajib diisi"}), 400

    try:
        user_uuid = uuid.UUID(str(id_user))
        user = db.session.get(User, user_uuid)
    except Exception:
        return jsonify({"message": "Format id_user tidak valid"}), 400

    if not user:
        return jsonify({"message": "User tidak ditemukan"}), 404

    if user.petani:
        return jsonify({"message": "User ini sudah memiliki profil petani"}), 409

    new_petani = Petani(
        id_user=user_uuid,
        nama=nama,
        nomor_telepon=nomor_telepon,
        alamat=alamat
    )

    try:
        db.session.add(new_petani)
        db.session.commit()
        return jsonify({
            "message": "Data Petani berhasil ditambahkan",
            "data": {
                "id_petani": str(new_petani.id_petani),
                "id_user": str(new_petani.id_user),
                "nama": new_petani.nama,
                "nomor_telepon": new_petani.nomor_telepon,
                "alamat": new_petani.alamat
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Gagal menambahkan data petani: {str(e)}"}), 500

@jwt_required()
def get_all_petani():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    pagination = Petani.query.paginate(page=page, per_page=per_page, error_out=False)
    result = [{
        "id_petani": str(p.id_petani),
        "id_user": str(p.id_user),
        "nama": p.nama,
        "nomor_telepon": p.nomor_telepon,
        "alamat": p.alamat,
        "created_at": p.created_at.isoformat() if p.created_at else None
    } for p in pagination.items]

    return jsonify({
        "message": "Berhasil mengambil semua data petani",
        "total": pagination.total,
        "page": pagination.page,
        "pages": pagination.pages,
        "data": result
    }), 200

@jwt_required()
def get_petani_by_id(id):
    try:
        petani_uuid = uuid.UUID(str(id))
        petani = db.session.get(Petani, petani_uuid)
    except Exception:
        return jsonify({"message": "Format ID petani tidak valid"}), 400

    if not petani:
        return jsonify({"message": "Petani tidak ditemukan"}), 404

    return jsonify({
        "message": "Berhasil mengambil data petani",
        "data": {
            "id_petani": str(petani.id_petani),
            "id_user": str(petani.id_user),
            "nama": petani.nama,
            "nomor_telepon": petani.nomor_telepon,
            "alamat": petani.alamat,
            "created_at": petani.created_at.isoformat() if petani.created_at else None,
            "updated_at": petani.updated_at.isoformat() if petani.updated_at else None
        }
    }), 200

@jwt_required()
def update_petani(id):
    try:
        petani_uuid = uuid.UUID(str(id))
        petani = db.session.get(Petani, petani_uuid)
    except Exception:
        return jsonify({"message": "Format ID petani tidak valid"}), 400

    if not petani:
        return jsonify({"message": "Petani tidak ditemukan"}), 404

    data = request.get_json() or {}
    if "nama" in data:
        petani.nama = data["nama"]
    if "nomor_telepon" in data:
        petani.nomor_telepon = data["nomor_telepon"]
    if "alamat" in data:
        petani.alamat = data["alamat"]

    try:
        db.session.commit()
        return jsonify({
            "message": "Data Petani berhasil diupdate",
            "data": {
                "id_petani": str(petani.id_petani),
                "id_user": str(petani.id_user),
                "nama": petani.nama,
                "nomor_telepon": petani.nomor_telepon,
                "alamat": petani.alamat
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Gagal mengupdate petani: {str(e)}"}), 500

@jwt_required()
def delete_petani(id):
    try:
        petani_uuid = uuid.UUID(str(id))
        petani = db.session.get(Petani, petani_uuid)
    except Exception:
        return jsonify({"message": "Format ID petani tidak valid"}), 400

    if not petani:
        return jsonify({"message": "Petani tidak ditemukan"}), 404

    try:
        db.session.delete(petani)
        db.session.commit()
        return jsonify({"message": "Data Petani berhasil dihapus beserta seluruh data terkait"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Gagal menghapus petani: {str(e)}"}), 500

# ── Admin Petani Endpoints (untuk Web Dashboard) ──

def get_admin_petani_pending():
    users = User.query.filter(User.role == "petani", User.status == "pending").all()
    result = [{
        "id_user": str(u.id_user),
        "nama": u.petani.nama if u.petani else u.username,
        "email": u.email,
        "nomor_telepon": u.petani.nomor_telepon if (u.petani and u.petani.nomor_telepon) else "-",
        "alamat": u.petani.alamat if (u.petani and u.petani.alamat) else "-",
        "status": u.status
    } for u in users]
    return jsonify({"status": "success", "data": result}), 200

def get_admin_petani_approved():
    users = User.query.filter(User.role == "petani", User.status.in_(["aktif", "approved", "active"])).all()
    result = [{
        "id_user": str(u.id_user),
        "nama": u.petani.nama if u.petani else u.username,
        "email": u.email,
        "nomor_telepon": u.petani.nomor_telepon if (u.petani and u.petani.nomor_telepon) else "-",
        "alamat": u.petani.alamat if (u.petani and u.petani.alamat) else "-",
        "status": u.status
    } for u in users]
    return jsonify({"status": "success", "data": result}), 200

def get_admin_petani_inactive():
    users = User.query.filter(User.role == "petani", User.status.in_(["nonaktif", "inactive", "rejected"])).all()
    result = [{
        "id_user": str(u.id_user),
        "nama": u.petani.nama if u.petani else u.username,
        "email": u.email,
        "nomor_telepon": u.petani.nomor_telepon if (u.petani and u.petani.nomor_telepon) else "-",
        "alamat": u.petani.alamat if (u.petani and u.petani.alamat) else "-",
        "status": u.status
    } for u in users]
    return jsonify({"status": "success", "data": result}), 200

def review_admin_petani(id_user):
    data = request.get_json() or {}
    action = data.get("action")
    try:
        user_uuid = uuid.UUID(str(id_user))
        user = db.session.get(User, user_uuid)
    except Exception:
        return jsonify({"message": "Format id_user tidak valid"}), 400

    if not user:
        return jsonify({"message": "User tidak ditemukan"}), 404

    if action in ["approve", "activate"]:
        user.status = "aktif"
    elif action in ["reject", "deactivate"]:
        user.status = "nonaktif"
    else:
        return jsonify({"message": f"Action '{action}' tidak dikenal"}), 400

    try:
        db.session.commit()
        return jsonify({"status": "success", "message": f"Status user berhasil diubah ke {user.status}"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 500

def edit_admin_petani(id_user):
    data = request.get_json() or {}
    try:
        user_uuid = uuid.UUID(str(id_user))
        user = db.session.get(User, user_uuid)
    except Exception:
        return jsonify({"message": "Format id_user tidak valid"}), 400

    if not user:
        return jsonify({"message": "User tidak ditemukan"}), 404

    if not user.petani:
        new_petani = Petani(
            id_user=user.id_user,
            nama=data.get("nama") or user.username,
            nomor_telepon=data.get("nomor_telepon"),
            alamat=data.get("alamat")
        )
        db.session.add(new_petani)
    else:
        if "nama" in data:
            user.petani.nama = data["nama"]
        if "nomor_telepon" in data:
            user.petani.nomor_telepon = data["nomor_telepon"]
        if "alamat" in data:
            user.petani.alamat = data["alamat"]

    try:
        db.session.commit()
        return jsonify({"status": "success", "message": "Profil berhasil diperbarui"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 500

def delete_admin_petani(id_user):
    try:
        user_uuid = uuid.UUID(str(id_user))
        user = db.session.get(User, user_uuid)
    except Exception:
        return jsonify({"message": "Format id_user tidak valid"}), 400

    if not user:
        return jsonify({"message": "User tidak ditemukan"}), 404

    try:
        db.session.delete(user)
        db.session.commit()
        return jsonify({"status": "success", "message": "User berhasil dihapus"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 500

