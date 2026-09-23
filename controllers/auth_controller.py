import uuid
import random
import string
from datetime import datetime, timedelta
from flask import request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from extensions import db, bcrypt
from models.user import User
from models.petani import Petani

def register():
    data = request.get_json() or {}
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role", "petani")

    if not username or not email or not password:
        return jsonify({"message": "username, email, dan password wajib diisi"}), 400

    if role not in ["admin", "petani"]:
        return jsonify({"message": "Role harus 'admin' atau 'petani'"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"message": "Username sudah digunakan"}), 409

    if User.query.filter_by(email=email).first():
        return jsonify({"message": "Email sudah terdaftar"}), 409

    hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")
    new_user = User(
        username=username,
        email=email,
        password=hashed_pw,
        role=role,
        status="aktif"
    )

    try:
        db.session.add(new_user)
        db.session.flush()

        if role == "petani":
            nama = data.get("nama", username)
            nomor_telepon = data.get("nomor_telepon")
            alamat = data.get("alamat")
            new_petani = Petani(
                id_user=new_user.id_user,
                nama=nama,
                nomor_telepon=nomor_telepon,
                alamat=alamat
            )
            db.session.add(new_petani)

        db.session.commit()
        access_token = create_access_token(identity=str(new_user.id_user))

        return jsonify({
            "message": "Registrasi berhasil",
            "access_token": access_token,
            "data": {
                "id_user": str(new_user.id_user),
                "username": new_user.username,
                "email": new_user.email,
                "role": new_user.role,
                "status": new_user.status
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Terjadi kesalahan saat registrasi: {str(e)}"}), 500

def login():
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"message": "Email dan password wajib diisi"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not bcrypt.check_password_hash(user.password, password):
        return jsonify({"message": "Email atau password salah"}), 401

    if user.status == "nonaktif":
        return jsonify({"message": "Akun Anda telah dinonaktifkan"}), 403

    access_token = create_access_token(identity=str(user.id_user))
    return jsonify({
        "message": "Login berhasil",
        "access_token": access_token,
        "data": {
            "id_user": str(user.id_user),
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "status": user.status
        }
    }), 200

@jwt_required()
def get_profile():
    user_id = get_jwt_identity()
    try:
        user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        user = db.session.get(User, user_uuid)
    except Exception:
        user = None

    if not user:
        return jsonify({"message": "User tidak ditemukan"}), 404

    profile_data = {
        "id_user": str(user.id_user),
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "status": user.status,
        "created_at": user.created_at.isoformat() if user.created_at else None
    }

    if user.petani:
        profile_data["petani"] = {
            "id_petani": str(user.petani.id_petani),
            "nama": user.petani.nama,
            "nomor_telepon": user.petani.nomor_telepon,
            "alamat": user.petani.alamat
        }

    return jsonify({
        "message": "Berhasil mengambil profil",
        "data": profile_data
    }), 200

def request_otp():
    data = request.get_json() or {}
    email = data.get("email")

    if not email:
        return jsonify({"message": "Email wajib diisi"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"message": "Email tidak terdaftar"}), 404

    otp = "".join(random.choices(string.digits, k=6))
    user.reset_otp = otp
    user.otp_expiry = datetime.now() + timedelta(minutes=15)

    try:
        db.session.commit()
        return jsonify({
            "message": "Kode OTP reset password berhasil dibuat (berlaku 15 menit)",
            "otp_demo": otp
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Gagal membuat OTP: {str(e)}"}), 500

def reset_password():
    data = request.get_json() or {}
    email = data.get("email")
    otp = data.get("otp")
    new_password = data.get("new_password")

    if not email or not otp or not new_password:
        return jsonify({"message": "Email, OTP, dan password baru wajib diisi"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"message": "User tidak ditemukan"}), 404

    if not user.reset_otp or user.reset_otp != otp:
        return jsonify({"message": "Kode OTP salah"}), 400

    if user.otp_expiry and datetime.now() > user.otp_expiry:
        return jsonify({"message": "Kode OTP telah kadaluarsa"}), 400

    user.password = bcrypt.generate_password_hash(new_password).decode("utf-8")
    user.reset_otp = None
    user.otp_expiry = None

    try:
        db.session.commit()
        return jsonify({"message": "Password berhasil diubah. Silakan login kembali."}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Gagal mereset password: {str(e)}"}), 500
