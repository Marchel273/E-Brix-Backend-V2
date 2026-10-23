# 🌾 E-Brix Backend API

**E-Brix Backend** adalah layanan RESTful API berbasis Python Flask yang menghubungkan perangkat refraktometer lapangan, aplikasi mobile Android, dan Web Dashboard untuk monitoring, pemetaan spasial, dan estimasi kematangan kadar gula (Brix) pada perkebunan tebu.

---

## 🚀 Fitur Utama

- **Autentikasi & Multi-Role**: Manajemen hak akses pengguna dengan role `Admin`, `Operator`, dan `Petani` berbasis JWT.
- **Pemetaan Geospasial (PostGIS)**: Penyimpanan data batas lahan (Polygon) dan titik lokasi sampel pengukuran (Point).
- **Integrasi Scan & Data Brix**: Sinkronisasi data pembacaan refraktometer antara mobile Android dan web dashboard (`/api/scans` & `/data-brix`).
- **Master Varietas Tebu**: Katalog jenis tebu (Bululawang, PS 881, Kidang Kencana, dll.) beserta ambang batas panen.
- **Machine Learning & Agronomic Intelligence (EBrixMLEngine)**:
  - Prediksi Sugarcane Yield (produktivitas ton/ha & quintal/acre) berbasis Tuned Ensemble Model (>90% akurasi).
  - Prediksi kadar Brix (°Brix), rendemen gula kristal, dan volume perahan nira tebu.
  - Klasifikasi risiko penyakit tanaman (High, Medium, Low) & rekomendasi perlakuan.
  - Kalkulasi rendemen standar industri gula Winter-Carp.
  - Simulasi kalender tanam & analisis komparasi musim kemarau vs penghujan.
- **Estimasi & Rekomendasi Panen**: Analisis kematangan tanaman dan rekomendasi waktu tebang optimal per blok lahan.
- **Ekspor Data**: Fitur unduh laporan hasil survei lapangan dalam format CSV dan PDF.

---

## 🛠️ Tech Stack

- **Bahasa & Framework:** Python 3.10+ & Flask (Arsitektur MVC)
- **Database:** PostgreSQL + PostGIS (Geospasial)
- **ORM:** Flask-SQLAlchemy + GeoAlchemy2
- **Keamanan:** Flask-JWT-Extended & Flask-Bcrypt
- **Klien:** Android App (Kotlin) & Web Dashboard E-Brix (PHP)

---

## ⚡ Cara Menjalankan

1. **Install Dependensi:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Inisialisasi & Seeding Data Dummy:**
   ```bash
   python seed_data.py
   ```

3. **Jalankan Server:**
   ```bash
   python app.py
   ```
   *Server berjalan di `http://127.0.0.1:5000` atau via IP Wi-Fi untuk koneksi device fisik.*

---

## 🔐 Kredensial Default (Testing & Demo)

| Role | Username / Email | Password |
|---|---|---|
| **Admin** | `admin` / `admin@ebrix.id` | `admin123` |
| **Operator** | `operator` / `operator@ebrix.id` | `operator123` |
| **Petani** | `petani_tebu` / `petani@ebrix.id` | `petani123` |
