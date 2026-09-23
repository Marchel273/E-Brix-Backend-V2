# E-Brix Backend API (PostgreSQL + PostGIS Edition)

E-Brix merupakan sistem backend RESTful API berbasis multi-platform (Web & Mobile) untuk pemantauan, pengukuran, dan analisis tingkat kematangan tebu (kadar brix) secara digital, geospasial, dan terintegrasi.

---

## 🛠️ Tech Stack

- **Language:** Python 3.10+
- **Framework:** Flask & Flask-CORS
- **Database:** PostgreSQL 16 + PostGIS Extension
- **ORM:** Flask-SQLAlchemy + GeoAlchemy2
- **Authentication:** Flask-JWT-Extended + Flask-Bcrypt
- **Cloud Storage:** Cloudinary
- **Reporting:** ReportLab (PDF) & CSV

---

## 📁 Struktur Direktori

```text
E-Brix-Backend/
├── app.py                      # Application factory & entry point
├── config.py                   # Konfigurasi environment & database
├── extensions.py               # Inisialisasi SQLAlchemy, JWT, Bcrypt
├── reset_db.py                 # Script reset & fresh migration DB
├── requirements.txt            # Daftar dependensi Python
├── .env.example                # Template variabel lingkungan
├── utils/                      # Helper & decorator
│   ├── helpers.py              # File format, GeoJSON & Point converter
│   └── decorators.py           # Role-based decorators (Admin & Petani)
├── models/                     # Model ORM (PostgreSQL + PostGIS)
│   ├── user.py                 # User & authentication
│   ├── petani.py               # Profil detail petani
│   ├── jenis_tebu.py           # Master varietas tebu & hardware code
│   ├── lahan.py                # Data lahan (Polygon boundary)
│   ├── blok_lahan.py           # Data blok lahan (Polygon boundary)
│   ├── data_brix.py            # Data pengukuran brix & offline sync (Point)
│   └── prediksi.py             # Hasil inferensi / prediksi
├── controllers/                # Business logic
│   ├── auth_controller.py      # Register, Login, Profile, OTP Reset
│   ├── petani_controller.py    # CRUD Petani
│   ├── jenis_tebu_controller.py# CRUD Varietas & Auto Register
│   ├── lahan_controller.py     # CRUD Lahan & GeoJSON Polygon
│   ├── blok_lahan_controller.py# CRUD Blok Lahan & GeoJSON Polygon
│   ├── data_brix_controller.py # CRUD Pengukuran, Cloudinary, Sync Batch
│   ├── prediksi_controller.py  # CRUD Prediksi
│   ├── export_controller.py    # Export Data Pengukuran CSV & PDF
│   └── rekomendasi_controller.py # Rekomendasi Panen & Statistik Brix
└── routes/                     # Definisi endpoint (Blueprint)
    ├── auth_route.py
    ├── petani_route.py
    ├── jenis_tebu_route.py
    ├── lahan_route.py
    ├── blok_lahan_route.py
    ├── data_brix_route.py
    ├── prediksi_route.py
    ├── export_route.py
    └── rekomendasi_route.py
```

---

## 🚀 Setup & Instalasi

### 1. Prasyarat
- PostgreSQL 14+ terpasang (dengan ekstensi PostGIS)
- Python 3.10+

### 2. Konfigurasi Environment
Salin file `.env.example` menjadi `.env` lalu sesuaikan kredensial:
```bash
cp .env.example .env
```

### 3. Install Dependensi
```bash
pip install -r requirements.txt
```

### 4. Inisialisasi Database
Jalankan skrip berikut untuk inisialisasi tabel:
```bash
python reset_db.py
```

### 5. Jalankan Server
```bash
python app.py
```
Server akan berjalan di `http://localhost:5000`.

---

## 📋 Daftar API Endpoints

### 🔐 1. Otentikasi (`/auth`)
| Method | Endpoint | Deskripsi | Auth |
|---|---|---|:---:|
| `POST` | `/auth/register` | Mendaftarkan akun user (admin / petani) | Publik |
| `POST` | `/auth/login` | Login dan mendapatkan JWT token | Publik |
| `GET` | `/auth/profile` | Mengambil detail profil user & petani | JWT |
| `POST` | `/auth/request-otp` | Meminta kode OTP 6-digit untuk reset password | Publik |
| `POST` | `/auth/reset-password` | Mereset password dengan kode OTP | Publik |

### 👨‍🌾 2. Petani (`/petani`)
| Method | Endpoint | Deskripsi | Auth |
|---|---|---|:---:|
| `POST` | `/petani` | Membuat profil petani baru | JWT |
| `GET` | `/petani` | Mengambil semua profil petani (pagination) | JWT |
| `GET` | `/petani/<id>` | Mengambil detail petani by ID | JWT |
| `PUT` | `/petani/<id>` | Mengupdate profil petani | JWT |
| `DELETE` | `/petani/<id>` | Menghapus petani & seluruh datanya | JWT |

### 🌾 3. Jenis Tebu (`/jenis-tebu`)
| Method | Endpoint | Deskripsi | Auth |
|---|---|---|:---:|
| `POST` | `/jenis-tebu` | Menambahkan master varietas tebu | JWT |
| `GET` | `/jenis-tebu` | Mengambil daftar varietas tebu | JWT |
| `GET` | `/jenis-tebu/<id>` | Mengambil varietas by ID | JWT |
| `PUT` | `/jenis-tebu/<id>` | Update varietas & verifikasi admin | JWT |
| `DELETE` | `/jenis-tebu/<id>` | Menghapus varietas tebu | JWT |

### 🗺️ 4. Lahan (`/lahan`)
| Method | Endpoint | Deskripsi | Auth |
|---|---|---|:---:|
| `POST` | `/lahan` | Membuat lahan baru (GeoJSON Polygon) | JWT |
| `GET` | `/lahan` | Mengambil daftar lahan (opsional filter `id_petani`) | JWT |
| `GET` | `/lahan/<id>` | Detail lahan beserta geometri | JWT |
| `PUT` | `/lahan/<id>` | Update lahan dan koordinat batas | JWT |
| `DELETE` | `/lahan/<id>` | Hapus lahan beserta seluruh blok terkait | JWT |

### 📐 5. Blok Lahan (`/blok-lahan`)
| Method | Endpoint | Deskripsi | Auth |
|---|---|---|:---:|
| `POST` | `/blok-lahan` | Membuat sub-blok lahan (GeoJSON Polygon) | JWT |
| `GET` | `/blok-lahan` | Mengambil daftar blok (opsional filter `id_lahan`) | JWT |
| `GET` | `/blok-lahan/<id>` | Detail blok lahan | JWT |
| `PUT` | `/blok-lahan/<id>` | Update blok lahan | JWT |
| `DELETE` | `/blok-lahan/<id>` | Hapus blok lahan & data pengukuran | JWT |

### 📊 6. Data Brix (`/data-brix`)
| Method | Endpoint | Deskripsi | Auth |
|---|---|---|:---:|
| `POST` | `/data-brix` | Input pengukuran brix (mendukung foto & multipart) | JWT |
| `GET` | `/data-brix` | Mengambil riwayat pengukuran brix | JWT |
| `GET` | `/data-brix/<id>` | Detail pengukuran brix | JWT |
| `PUT` | `/data-brix/<id>` | Update data pengukuran | JWT |
| `DELETE` | `/data-brix/<id>` | Hapus data pengukuran | JWT |
| `POST` | `/data-brix/sync` | **Sinkronisasi batch offline mobile** (deduplikasi `client_uuid`) | JWT |

### 🤖 7. Prediksi (`/prediksi`)
| Method | Endpoint | Deskripsi | Auth |
|---|---|---|:---:|
| `POST` | `/prediksi` | Simpan hasil prediksi model ML | JWT |
| `GET` | `/prediksi` | Daftar hasil prediksi | JWT |
| `GET` | `/prediksi/<id>` | Detail prediksi by ID | JWT |
| `PUT` | `/prediksi/<id>` | Update data prediksi | JWT |
| `DELETE` | `/prediksi/<id>` | Hapus data prediksi | JWT |

### 📄 8. Export Laporan (`/export`)
| Method | Endpoint | Deskripsi | Auth |
|---|---|---|:---:|
| `GET` | `/export/data-brix/csv` | Download laporan pengukuran format **CSV** | JWT |
| `GET` | `/export/data-brix/pdf` | Download laporan pengukuran lengkap format **PDF** | JWT |

### 🔔 9. Rekomendasi Panen & Statistik (`/rekomendasi`, `/statistik`)
| Method | Endpoint | Deskripsi | Auth |
|---|---|---|:---:|
| `GET` | `/rekomendasi/blok/<id>` | Rekomendasi kesiapan panen blok tebu | JWT |
| `GET` | `/rekomendasi/lahan/<id>` | Ringkasan status panen seluruh blok di satu lahan | JWT |
| `GET` | `/statistik/blok/<id>` | Ringkasan statistik (rata-rata, min, max, sampel) | JWT |

---

## 👥 Tim Pengembang
- Machelino Bambi Christian Siagian (607062400036)
