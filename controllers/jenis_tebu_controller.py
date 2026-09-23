import uuid
from flask import request, jsonify
from flask_jwt_extended import jwt_required
from extensions import db
from models.jenis_tebu import JenisTebu

def auto_register_hardware(kode_hardware):
    """Helper untuk otomatis mendaftarkan varietas tebu jika kode hardware belum dikenal."""
    if not kode_hardware:
        return None
    existing = JenisTebu.query.filter_by(kode_hardware=kode_hardware).first()
    if existing:
        return existing
    new_tebu = JenisTebu(
        kode_hardware=kode_hardware,
        status="belum_dikenali"
    )
    db.session.add(new_tebu)
    db.session.flush()
    return new_tebu

@jwt_required()
def create_jenis_tebu():
    data = request.get_json() or {}
    kode_hardware = data.get("kode_hardware")
    nama_varietas = data.get("nama_varietas")
    ambang_panen = data.get("ambang_panen")
    status = data.get("status", "belum_dikenali")

    if not kode_hardware:
        return jsonify({"message": "kode_hardware wajib diisi"}), 400

    if JenisTebu.query.filter_by(kode_hardware=kode_hardware).first():
        return jsonify({"message": "Kode hardware sudah terdaftar"}), 409

    new_tebu = JenisTebu(
        kode_hardware=kode_hardware,
        nama_varietas=nama_varietas,
        ambang_panen=ambang_panen,
        status=status
    )

    try:
        db.session.add(new_tebu)
        db.session.commit()
        return jsonify({
            "message": "Data Jenis Tebu berhasil ditambahkan",
            "data": {
                "id_tebu": str(new_tebu.id_tebu),
                "kode_hardware": new_tebu.kode_hardware,
                "nama_varietas": new_tebu.nama_varietas,
                "ambang_panen": float(new_tebu.ambang_panen) if new_tebu.ambang_panen is not None else None,
                "status": new_tebu.status
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Gagal menambahkan jenis tebu: {str(e)}"}), 500

@jwt_required()
def get_all_jenis_tebu():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    status_filter = request.args.get("status")

    query = JenisTebu.query
    if status_filter:
        query = query.filter_by(status=status_filter)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    result = [{
        "id_tebu": str(t.id_tebu),
        "kode_hardware": t.kode_hardware,
        "nama_varietas": t.nama_varietas,
        "ambang_panen": float(t.ambang_panen) if t.ambang_panen is not None else None,
        "status": t.status,
        "created_at": t.created_at.isoformat() if t.created_at else None
    } for t in pagination.items]

    return jsonify({
        "message": "Berhasil mengambil data jenis tebu",
        "total": pagination.total,
        "page": pagination.page,
        "pages": pagination.pages,
        "data": result
    }), 200

@jwt_required()
def get_jenis_tebu_by_id(id):
    try:
        tebu_uuid = uuid.UUID(str(id))
        tebu = db.session.get(JenisTebu, tebu_uuid)
    except Exception:
        return jsonify({"message": "Format ID jenis tebu tidak valid"}), 400

    if not tebu:
        return jsonify({"message": "Jenis Tebu tidak ditemukan"}), 404

    return jsonify({
        "message": "Berhasil mengambil data jenis tebu",
        "data": {
            "id_tebu": str(tebu.id_tebu),
            "kode_hardware": tebu.kode_hardware,
            "nama_varietas": tebu.nama_varietas,
            "ambang_panen": float(tebu.ambang_panen) if tebu.ambang_panen is not None else None,
            "status": tebu.status,
            "created_at": tebu.created_at.isoformat() if tebu.created_at else None,
            "updated_at": tebu.updated_at.isoformat() if tebu.updated_at else None
        }
    }), 200

@jwt_required()
def update_jenis_tebu(id):
    try:
        tebu_uuid = uuid.UUID(str(id))
        tebu = db.session.get(JenisTebu, tebu_uuid)
    except Exception:
        return jsonify({"message": "Format ID jenis tebu tidak valid"}), 400

    if not tebu:
        return jsonify({"message": "Jenis Tebu tidak ditemukan"}), 404

    data = request.get_json() or {}
    if "kode_hardware" in data:
        tebu.kode_hardware = data["kode_hardware"]
    if "nama_varietas" in data:
        tebu.nama_varietas = data["nama_varietas"]
    if "ambang_panen" in data:
        tebu.ambang_panen = data["ambang_panen"]
    if "status" in data:
        if data["status"] not in ["belum_dikenali", "terverifikasi"]:
            return jsonify({"message": "Status harus 'belum_dikenali' atau 'terverifikasi'"}), 400
        tebu.status = data["status"]

    try:
        db.session.commit()
        return jsonify({
            "message": "Data Jenis Tebu berhasil diupdate",
            "data": {
                "id_tebu": str(tebu.id_tebu),
                "kode_hardware": tebu.kode_hardware,
                "nama_varietas": tebu.nama_varietas,
                "ambang_panen": float(tebu.ambang_panen) if tebu.ambang_panen is not None else None,
                "status": tebu.status
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Gagal mengupdate jenis tebu: {str(e)}"}), 500

@jwt_required()
def delete_jenis_tebu(id):
    try:
        tebu_uuid = uuid.UUID(str(id))
        tebu = db.session.get(JenisTebu, tebu_uuid)
    except Exception:
        return jsonify({"message": "Format ID jenis tebu tidak valid"}), 400

    if not tebu:
        return jsonify({"message": "Jenis Tebu tidak ditemukan"}), 404

    try:
        db.session.delete(tebu)
        db.session.commit()
        return jsonify({"message": "Data Jenis Tebu berhasil dihapus"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Gagal menghapus jenis tebu: {str(e)}"}), 500
