from app import create_app
from extensions import db

# Import dari folder 'models' dan masing-masing filenya
from models.lahan import Lahan
from models.blok import Blok
from models.data_brix import DataBrix
from models.prediksi import Prediksi

app = create_app()

with app.app_context():
    print("Menghapus semua tabel lama...")
    db.drop_all()  # Menghapus semua tabel di database
    
    print("Membuat ulang tabel baru berdasarkan model...")
    db.create_all()  # Membuat ulang tabel baru
    
    print("Selesai! Database berhasil di-reset (Fresh Migrate).")