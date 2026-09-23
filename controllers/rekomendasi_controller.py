import uuid
from flask import jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy import func
from extensions import db
from models.blok_lahan import BlokLahan
from models.lahan import Lahan
from models.jenis_tebu import JenisTebu
from models.data_brix import DataBrix

@jwt_required()
def get_rekomendasi_panen(id):
    """Memberikan rekomendasi kesiapan panen berdasarkan perbandingan rata-rata brix dan ambang panen varietas."""
    try:
        blok_uuid = uuid.UUID(str(id))
        blok = db.session.get(BlokLahan, blok_uuid)
    except Exception:
        return jsonify({"message": "Format ID blok tidak valid"}), 400

    if not blok:
        return jsonify({"message": "Blok Lahan tidak ditemukan"}), 404

    rata_brix = float(blok.rata_brix) if blok.rata_brix is not None else None
    tebu = db.session.get(JenisTebu, blok.id_tebu) if blok.id_tebu else None
    ambang_panen = float(tebu.ambang_panen) if (tebu and tebu.ambang_panen is not None) else 18.0  # default standar brix panen

    if rata_brix is None:
        status = "Belum Ada Data Pengukuran"
        level = "unknown"
        selisih = None
        rekomendasi_teks = "Silakan lakukan pengukuran kadar gula (brix) di lapangan terlebih dahulu."
    elif rata_brix >= ambang_panen:
        status = "Siap Panen"
        level = "high"
        selisih = round(rata_brix - ambang_panen, 2)
        rekomendasi_teks = f"Kadar brix rata-rata ({rata_brix}°Bx) telah memenuhi/melebihi ambang panen ({ambang_panen}°Bx). Blok disarankan segera dipanen."
    elif rata_brix >= ambang_panen * 0.85:
        status = "Hampir Siap"
        level = "medium"
        selisih = round(rata_brix - ambang_panen, 2)
        rekomendasi_teks = f"Kadar brix rata-rata ({rata_brix}°Bx) mendekati ambang panen ({ambang_panen}°Bx). Pantau kembali dalam 1-2 minggu."
    else:
        status = "Belum Siap"
        level = "low"
        selisih = round(rata_brix - ambang_panen, 2)
        rekomendasi_teks = f"Kadar brix rata-rata ({rata_brix}°Bx) masih di bawah ambang panen ({ambang_panen}°Bx). Tanaman masih dalam masa pematangan."

    return jsonify({
        "message": "Berhasil mengambil rekomendasi panen",
        "data": {
            "id_blok": str(blok.id_blok),
            "nama_blok": blok.nama_blok,
            "varietas_tebu": tebu.nama_varietas if tebu else "Belum Ditetapkan",
            "rata_brix": rata_brix,
            "ambang_panen": ambang_panen,
            "selisih_brix": selisih,
            "status_panen": status,
            "level_kesiapan": level,
            "rekomendasi": rekomendasi_teks
        }
    }), 200

@jwt_required()
def get_rekomendasi_by_lahan(id):
    """Mengambil status rekomendasi panen untuk semua blok dalam satu lahan."""
    try:
        lahan_uuid = uuid.UUID(str(id))
        lahan = db.session.get(Lahan, lahan_uuid)
    except Exception:
        return jsonify({"message": "Format ID lahan tidak valid"}), 400

    if not lahan:
        return jsonify({"message": "Lahan tidak ditemukan"}), 404

    bloks = BlokLahan.query.filter_by(id_lahan=lahan_uuid).all()
    summary = {"total_blok": len(bloks), "siap_panen": 0, "hampir_siap": 0, "belum_siap": 0, "tanpa_data": 0}
    list_rekomendasi = []

    for b in bloks:
        rata_brix = float(b.rata_brix) if b.rata_brix is not None else None
        tebu = db.session.get(JenisTebu, b.id_tebu) if b.id_tebu else None
        ambang = float(tebu.ambang_panen) if (tebu and tebu.ambang_panen is not None) else 18.0

        if rata_brix is None:
            status = "Belum Ada Data"
            level = "unknown"
            summary["tanpa_data"] += 1
        elif rata_brix >= ambang:
            status = "Siap Panen"
            level = "high"
            summary["siap_panen"] += 1
        elif rata_brix >= ambang * 0.85:
            status = "Hampir Siap"
            level = "medium"
            summary["hampir_siap"] += 1
        else:
            status = "Belum Siap"
            level = "low"
            summary["belum_siap"] += 1

        list_rekomendasi.append({
            "id_blok": str(b.id_blok),
            "nama_blok": b.nama_blok,
            "varietas": tebu.nama_varietas if tebu else "-",
            "rata_brix": rata_brix,
            "ambang_panen": ambang,
            "status": status,
            "level": level
        })

    return jsonify({
        "message": "Berhasil mengambil ringkasan rekomendasi lahan",
        "lahan": {
            "id_lahan": str(lahan.id_lahan),
            "nama_lahan": lahan.nama_lahan
        },
        "summary": summary,
        "data": list_rekomendasi
    }), 200

@jwt_required()
def get_statistik_brix(id):
    """Menghitung ringkasan statistik kadar brix pada blok lahan (avg, min, max, count, 5 data terbaru)."""
    try:
        blok_uuid = uuid.UUID(str(id))
        blok = db.session.get(BlokLahan, blok_uuid)
    except Exception:
        return jsonify({"message": "Format ID blok tidak valid"}), 400

    if not blok:
        return jsonify({"message": "Blok Lahan tidak ditemukan"}), 404

    stats = db.session.query(
        func.count(DataBrix.id_data).label("total"),
        func.avg(DataBrix.nilai_brix).label("avg"),
        func.min(DataBrix.nilai_brix).label("min"),
        func.max(DataBrix.nilai_brix).label("max")
    ).filter(DataBrix.id_blok == blok_uuid).first()

    recent_measurements = DataBrix.query.filter_by(id_blok=blok_uuid).order_by(
        DataBrix.timestamp.desc()
    ).limit(5).all()

    recent_list = [{
        "id_data": str(d.id_data),
        "nilai_brix": float(d.nilai_brix),
        "latitude": d.latitude,
        "longitude": d.longitude,
        "timestamp": d.timestamp.isoformat() if d.timestamp else None
    } for d in recent_measurements]

    return jsonify({
        "message": "Berhasil mengambil statistik brix",
        "data": {
            "id_blok": str(blok.id_blok),
            "nama_blok": blok.nama_blok,
            "total_sampel": stats.total if stats else 0,
            "rata_rata_brix": round(float(stats.avg), 2) if (stats and stats.avg is not None) else None,
            "brix_terendah": float(stats.min) if (stats and stats.min is not None) else None,
            "brix_tertinggi": float(stats.max) if (stats and stats.max is not None) else None,
            "data_terbaru": recent_list
        }
    }), 200
