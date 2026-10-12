import uuid
from datetime import datetime, date, timedelta
from app import create_app
from extensions import db, bcrypt
from models.user import User
from models.petani import Petani
from models.jenis_tebu import JenisTebu
from models.lahan import Lahan
from models.blok_lahan import BlokLahan
from models.data_brix import DataBrix
from models.prediksi import Prediksi
from shapely.geometry import Polygon, Point
from geoalchemy2.shape import from_shape
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("==================================================")
    print("  MEMULAI SEEDING DATA DUMMY E-BRIX LENGKAP")
    print("==================================================")

    # ── 0. Update Table Constraint ──────────────────────────────────────
    print("\n[1/6] Memeriksa constraint tabel users...")
    try:
        db.session.execute(text("ALTER TABLE users DROP CONSTRAINT IF EXISTS users_role_check;"))
        db.session.execute(text("ALTER TABLE users ADD CONSTRAINT users_role_check CHECK (role IN ('admin', 'operator', 'petani'));"))
        db.session.commit()
        print("  -> Constraint users_role_check aktif: ('admin', 'operator', 'petani')")
    except Exception as e:
        db.session.rollback()
        print(f"  -> Catatan constraint: {e}")

    # ── 1. Akun Pengguna / Kelola Petugas ──────────────────────────────
    print("\n[2/6] Seeding Pengguna & Petugas...")

    users_data = [
        {
            "username": "admin",
            "email": "admin@ebrix.id",
            "password": "admin123",
            "role": "admin",
            "status": "aktif"
        },
        {
            "username": "operator",
            "email": "operator@ebrix.id",
            "password": "operator123",
            "role": "operator",
            "status": "aktif"
        },
        {
            "username": "petugas1",
            "email": "petugas1@ebrix.id",
            "password": "operator123",
            "role": "operator",
            "status": "aktif"
        },
        {
            "username": "petani_tebu",
            "email": "petani@ebrix.id",
            "password": "petani123",
            "role": "petani",
            "status": "aktif",
            "petani_info": {
                "nama": "Bambang Sugiono",
                "nomor_telepon": "081234567890",
                "alamat": "Jl. Raya Kebun Tebu No. 45, Mojokerto"
            }
        },
        {
            "username": "petani_sukses",
            "email": "petani2@ebrix.id",
            "password": "petani123",
            "role": "petani",
            "status": "aktif",
            "petani_info": {
                "nama": "Sutrisno",
                "nomor_telepon": "089876543210",
                "alamat": "Jl. Perkebunan Mandiri Blok B, Kediri"
            }
        },
        {
            "username": "petani_makmur",
            "email": "petani3@ebrix.id",
            "password": "petani123",
            "role": "petani",
            "status": "aktif",
            "petani_info": {
                "nama": "Joko Wahyudi",
                "nomor_telepon": "085612349876",
                "alamat": "Dusun Candi Tebu Barat, Sidoarjo"
            }
        }
    ]

    user_map = {}
    for ud in users_data:
        u = User.query.filter((User.email == ud["email"]) | (User.username == ud["username"])).first()
        hashed = bcrypt.generate_password_hash(ud["password"]).decode("utf-8")
        if not u:
            u = User(
                username=ud["username"],
                email=ud["email"],
                password=hashed,
                role=ud["role"],
                status=ud["status"]
            )
            db.session.add(u)
            db.session.flush()
            print(f"  [+] User dibuat: {ud['username']} ({ud['email']}) [Role: {ud['role']}]")
        else:
            u.username = ud["username"]
            u.email = ud["email"]
            u.password = hashed
            u.role = ud["role"]
            u.status = ud["status"]
            print(f"  [*] User diupdate: {ud['username']} ({ud['email']}) [Role: {ud['role']}]")

        user_map[ud["username"]] = u

        # Profil Petani
        if "petani_info" in ud:
            p_info = ud["petani_info"]
            petani_rec = Petani.query.filter_by(id_user=u.id_user).first()
            if not petani_rec:
                petani_rec = Petani(
                    id_user=u.id_user,
                    nama=p_info["nama"],
                    nomor_telepon=p_info["nomor_telepon"],
                    alamat=p_info["alamat"]
                )
                db.session.add(petani_rec)
            else:
                petani_rec.nama = p_info["nama"]
                petani_rec.nomor_telepon = p_info["nomor_telepon"]
                petani_rec.alamat = p_info["alamat"]
            user_map[f"petani_{ud['username']}"] = petani_rec

    db.session.commit()

    # ── 2. Jenis Tebu (Varietas Unggul) ─────────────────────────────────
    print("\n[3/6] Seeding Varietas Jenis Tebu...")

    tebu_data = [
        {"kode": "TB-BL001", "nama": "Bululawang (BL)",    "ambang": 18.50, "status": "terverifikasi"},
        {"kode": "TB-PS881", "nama": "PS 881",             "ambang": 19.50, "status": "terverifikasi"},
        {"kode": "TB-KK002", "nama": "Kidang Kencana",     "ambang": 20.00, "status": "terverifikasi"},
        {"kode": "TB-CNN03", "nama": "Cenning",            "ambang": 19.00, "status": "terverifikasi"},
        {"kode": "TB-PS864", "nama": "PS 864",             "ambang": 18.00, "status": "terverifikasi"},
        {"kode": "TB-VMC16", "nama": "VMC 76-16",          "ambang": 20.50, "status": "terverifikasi"},
    ]

    tebu_map = {}
    for td in tebu_data:
        jt = JenisTebu.query.filter_by(kode_hardware=td["kode"]).first()
        if not jt:
            jt = JenisTebu(
                kode_hardware=td["kode"],
                nama_varietas=td["nama"],
                ambang_panen=td["ambang"],
                status=td["status"]
            )
            db.session.add(jt)
            print(f"  [+] Jenis Tebu dibuat: {td['nama']} (Kode: {td['kode']}, Ambang: {td['ambang']}%)")
        else:
            jt.nama_varietas = td["nama"]
            jt.ambang_panen = td["ambang"]
            jt.status = td["status"]
            print(f"  [*] Jenis Tebu diupdate: {td['nama']} (Kode: {td['kode']})")
        tebu_map[td["kode"]] = jt

    db.session.commit()

    # ── 3. Lahan Perkebunan ─────────────────────────────────────────────
    print("\n[4/6] Seeding Lahan Perkebunan...")

    petani_bambang = Petani.query.filter_by(nama="Bambang Sugiono").first()
    petani_sutrisno = Petani.query.filter_by(nama="Sutrisno").first()
    petani_joko = Petani.query.filter_by(nama="Joko Wahyudi").first()

    lahan_data = [
        {
            "petani": petani_bambang,
            "nama": "Lahan Kebun PG Gempolkrep Utara",
            "coords": [(112.445, -7.475), (112.458, -7.475), (112.458, -7.488), (112.445, -7.488), (112.445, -7.475)]
        },
        {
            "petani": petani_sutrisno,
            "nama": "Lahan Kebun PG Candi Barat",
            "coords": [(112.710, -7.450), (112.725, -7.450), (112.725, -7.462), (112.710, -7.462), (112.710, -7.450)]
        },
        {
            "petani": petani_joko,
            "nama": "Lahan Kebun Brantas Selatan",
            "coords": [(112.010, -7.810), (112.025, -7.810), (112.025, -7.822), (112.010, -7.822), (112.010, -7.810)]
        }
    ]

    lahan_map = {}
    for ld in lahan_data:
        l = Lahan.query.filter_by(nama_lahan=ld["nama"]).first()
        poly = Polygon(ld["coords"])
        geom = from_shape(poly, srid=4326)
        if not l:
            l = Lahan(
                id_petani=ld["petani"].id_petani,
                nama_lahan=ld["nama"],
                geom=geom
            )
            db.session.add(l)
            print(f"  [+] Lahan dibuat: {ld['nama']} (Pemilik: {ld['petani'].nama})")
        else:
            l.id_petani = ld["petani"].id_petani
            l.geom = geom
            print(f"  [*] Lahan diupdate: {ld['nama']}")
        lahan_map[ld["nama"]] = l

    db.session.commit()

    # ── 4. Blok Lahan ───────────────────────────────────────────────────
    print("\n[5/6] Seeding Blok Lahan...")

    blok_data = [
        # Lahan Gempolkrep Utara
        {
            "lahan": lahan_map["Lahan Kebun PG Gempolkrep Utara"],
            "tebu": tebu_map["TB-BL001"],
            "nama": "Blok A1 - Bululawang",
            "rata_brix": 19.80,
            "tgl_tanam": date(2025, 10, 15),
            "coords": [(112.445, -7.475), (112.451, -7.475), (112.451, -7.481), (112.445, -7.481), (112.445, -7.475)]
        },
        {
            "lahan": lahan_map["Lahan Kebun PG Gempolkrep Utara"],
            "tebu": tebu_map["TB-PS881"],
            "nama": "Blok A2 - PS 881",
            "rata_brix": 20.50,
            "tgl_tanam": date(2025, 11, 1),
            "coords": [(112.452, -7.475), (112.458, -7.475), (112.458, -7.481), (112.452, -7.481), (112.452, -7.475)]
        },
        # Lahan PG Candi Barat
        {
            "lahan": lahan_map["Lahan Kebun PG Candi Barat"],
            "tebu": tebu_map["TB-KK002"],
            "nama": "Blok B1 - Kidang Kencana",
            "rata_brix": 17.50,
            "tgl_tanam": date(2025, 12, 10),
            "coords": [(112.710, -7.450), (112.717, -7.450), (112.717, -7.456), (112.710, -7.456), (112.710, -7.450)]
        },
        {
            "lahan": lahan_map["Lahan Kebun PG Candi Barat"],
            "tebu": tebu_map["TB-CNN03"],
            "nama": "Blok B2 - Cenning",
            "rata_brix": 19.20,
            "tgl_tanam": date(2025, 11, 20),
            "coords": [(112.718, -7.450), (112.725, -7.450), (112.725, -7.456), (112.718, -7.456), (112.718, -7.450)]
        },
        # Lahan Brantas Selatan
        {
            "lahan": lahan_map["Lahan Kebun Brantas Selatan"],
            "tebu": tebu_map["TB-PS864"],
            "nama": "Blok C1 - PS 864",
            "rata_brix": 16.80,
            "tgl_tanam": date(2026, 1, 5),
            "coords": [(112.010, -7.810), (112.017, -7.810), (112.017, -7.816), (112.010, -7.816), (112.010, -7.810)]
        },
        {
            "lahan": lahan_map["Lahan Kebun Brantas Selatan"],
            "tebu": tebu_map["TB-VMC16"],
            "nama": "Blok C2 - VMC 76-16",
            "rata_brix": 21.20,
            "tgl_tanam": date(2025, 10, 1),
            "coords": [(112.018, -7.810), (112.025, -7.810), (112.025, -7.816), (112.018, -7.816), (112.018, -7.810)]
        }
    ]

    blok_map = {}
    for bd in blok_data:
        b = BlokLahan.query.filter_by(nama_blok=bd["nama"]).first()
        poly = Polygon(bd["coords"])
        geom = from_shape(poly, srid=4326)
        if not b:
            b = BlokLahan(
                id_lahan=bd["lahan"].id_lahan,
                id_tebu=bd["tebu"].id_tebu,
                nama_blok=bd["nama"],
                rata_brix=bd["rata_brix"],
                tanggal_tanam=bd["tgl_tanam"],
                geom=geom
            )
            db.session.add(b)
            print(f"  [+] Blok Lahan dibuat: {bd['nama']} (Rata Brix: {bd['rata_brix']}%)")
        else:
            b.id_lahan = bd["lahan"].id_lahan
            b.id_tebu = bd["tebu"].id_tebu
            b.rata_brix = bd["rata_brix"]
            b.tanggal_tanam = bd["tgl_tanam"]
            b.geom = geom
            print(f"  [*] Blok Lahan diupdate: {bd['nama']}")
        blok_map[bd["nama"]] = b

    db.session.commit()

    # ── 5. Data Brix & Prediksi ─────────────────────────────────────────
    print("\n[6/6] Seeding Data Brix & Prediksi Kematangan...")

    # Sampel pengukuran brix
    sample_points = [
        # Blok A1
        {"blok": "Blok A1 - Bululawang", "lat": -7.4780, "lon": 112.4480, "brix": 19.8, "catatan": "Kondisi tanaman subur, batang padat, siap tebang"},
        {"blok": "Blok A1 - Bululawang", "lat": -7.4795, "lon": 112.4495, "brix": 20.2, "catatan": "Kadar brix optimal, daun pucuk mulai menguning"},
        {"blok": "Blok A1 - Bululawang", "lat": -7.4800, "lon": 112.4505, "brix": 19.5, "catatan": "Sampel tengah blok, rendemen perkiraan 8.5%"},
        # Blok A2
        {"blok": "Blok A2 - PS 881", "lat": -7.4775, "lon": 112.4540, "brix": 20.8, "catatan": "Varietas PS 881 menunjukkan kematangan seragam"},
        {"blok": "Blok A2 - PS 881", "lat": -7.4790, "lon": 112.4560, "brix": 21.4, "catatan": "Brix tinggi, prioritas tebang minggu ke-2"},
        {"blok": "Blok A2 - PS 881", "lat": -7.4805, "lon": 112.4570, "brix": 20.1, "catatan": "Brix stabil > 20, kondisi siap giling PG Gempolkrep"},
        # Blok B1
        {"blok": "Blok B1 - Kidang Kencana", "lat": -7.4520, "lon": 112.7130, "brix": 17.2, "catatan": "Masih fase pematangan akhir, pantau 2 minggu lagi"},
        {"blok": "Blok B1 - Kidang Kencana", "lat": -7.4545, "lon": 112.7150, "brix": 17.8, "catatan": "Peningkatan brix +0.6 per minggu, belum rekomendasi panen"},
        # Blok B2
        {"blok": "Blok B2 - Cenning", "lat": -7.4525, "lon": 112.7210, "brix": 19.1, "catatan": "Cenning masak optimal di bulan ke-11"},
        {"blok": "Blok B2 - Cenning", "lat": -7.4550, "lon": 112.7230, "brix": 19.6, "catatan": "Kadar brix melampaui ambang panen (19.0%)"},
        # Blok C1
        {"blok": "Blok C1 - PS 864", "lat": -7.8120, "lon": 112.0130, "brix": 16.5, "catatan": "Tanam muda, pertumbuhan vegetatif baik"},
        {"blok": "Blok C1 - PS 864", "lat": -7.8145, "lon": 112.0155, "brix": 17.1, "catatan": "Batang sehat, butuh pemupukan susulan N-P-K"},
        # Blok C2
        {"blok": "Blok C2 - VMC 76-16", "lat": -7.8125, "lon": 112.0210, "brix": 21.8, "catatan": "Kadar brix tertinggi di area Brantas Selatan"},
        {"blok": "Blok C2 - VMC 76-16", "lat": -7.8150, "lon": 112.0235, "brix": 22.4, "catatan": "Rekomendasi tebang segera untuk cegah inversi sukrosa"}
    ]

    op_user = user_map["operator"]
    now = datetime.now()

    inserted_samples = 0
    for idx, sp in enumerate(sample_points):
        target_blok = blok_map.get(sp["blok"])
        if not target_blok:
            continue

        existing = DataBrix.query.filter_by(
            id_blok=target_blok.id_blok,
            latitude=sp["lat"],
            longitude=sp["lon"]
        ).first()

        p_geom = make_point_geom(sp["lat"], sp["lon"]) if 'make_point_geom' in locals() else from_shape(Point(sp["lon"], sp["lat"]), srid=4326)
        meas_time = now - timedelta(days=(len(sample_points) - idx), hours=idx * 2)

        if not existing:
            dbrix = DataBrix(
                id_blok=target_blok.id_blok,
                id_user=op_user.id_user,
                latitude=sp["lat"],
                longitude=sp["lon"],
                nilai_brix=sp["brix"],
                geom=p_geom,
                status_sinkron="tersinkron",
                client_uuid=uuid.uuid4(),
                catatan=sp["catatan"],
                timestamp=meas_time
            )
            db.session.add(dbrix)
            db.session.flush()

            # Tambahkan Prediksi Otomatis
            ambang = float(target_blok.jenis_tebu.ambang_panen) if target_blok.jenis_tebu else 19.0
            if sp["brix"] >= ambang:
                pred_label = "Siap Panen Optimal"
                conf = 0.9650
            elif sp["brix"] >= ambang * 0.90:
                pred_label = "Menjelang Masak (Siaga Tebang)"
                conf = 0.9120
            else:
                pred_label = "Belum Masak (Fase Pembesaran)"
                conf = 0.9480

            pred = Prediksi(
                id_data=dbrix.id_data,
                hasil_prediksi=pred_label,
                confidence_score=conf
            )
            db.session.add(pred)
            inserted_samples += 1

    db.session.commit()
    print(f"  [+] {inserted_samples} data sampel brix & prediksi baru berhasil disimpan!")

    print("\n==================================================")
    print("  SEEDING DATA DUMMY BERHASIL SELESAI 100%!")
    print("==================================================")
    print("Daftar Akun Login:")
    print("  1. Admin    : admin / admin@ebrix.id (pw: admin123)")
    print("  2. Operator : operator / operator@ebrix.id (pw: operator123)")
    print("  3. Petugas  : petugas1 / petugas1@ebrix.id (pw: operator123)")
    print("  4. Petani 1 : petani_tebu / petani@ebrix.id (pw: petani123)")
    print("  5. Petani 2 : petani_sukses / petani2@ebrix.id (pw: petani123)")
    print("  6. Petani 3 : petani_makmur / petani3@ebrix.id (pw: petani123)")
