from app import create_app
from extensions import db
from sqlalchemy import text

# Import semua model agar SQLAlchemy mengenalinya
from models.user import User
from models.petani import Petani
from models.jenis_tebu import JenisTebu
from models.lahan import Lahan
from models.blok_lahan import BlokLahan
from models.data_brix import DataBrix
from models.prediksi import Prediksi

app = create_app()

with app.app_context():
    print("==================================================")
    print("E-BRIX DATABASE RESET & MIGRATION (PostgreSQL)")
    print("==================================================")
    
    print("\n1. Mengaktifkan ekstensi PostGIS & UUID...")
    try:
        db.session.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
        db.session.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'))
        db.session.commit()
        print("   Ekstensi postgis dan uuid-ossp aktif.")
    except Exception as e:
        db.session.rollback()
        print(f"   Peringatan aktivasi ekstensi: {e}")

    print("\n2. Menghapus tabel lama...")
    try:
        db.drop_all()
        print("   Semua tabel berhasil dihapus.")
    except Exception as e:
        print(f"   Error saat drop table: {e}")

    print("\n3. Membuat tabel baru berdasarkan model PostgreSQL...")
    try:
        db.create_all()
        print("   Semua tabel berhasil dibuat ulang!")
    except Exception as e:
        print(f"   Error saat create table: {e}")

    print("\nSelesai! Database siap digunakan.")