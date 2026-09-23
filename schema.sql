-- =========================================================
-- Skema Database E-BRIX
-- PostgreSQL + PostGIS
-- =========================================================

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE users (
    id_user         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username        VARCHAR(50) UNIQUE NOT NULL,
    email           VARCHAR(100) UNIQUE NOT NULL,
    password        VARCHAR(255) NOT NULL,
    role            VARCHAR(20) NOT NULL DEFAULT 'petani' CHECK (role IN ('admin', 'petani')),
    status          VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'aktif', 'nonaktif')),
    reset_otp       VARCHAR(6),
    otp_expiry      TIMESTAMP,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE petani (
    id_petani       UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    id_user         UUID NOT NULL REFERENCES users(id_user) ON DELETE CASCADE,
    nama            VARCHAR(100) NOT NULL,
    nomor_telepon   VARCHAR(20),
    alamat          TEXT,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE lahan (
    id_lahan        UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    id_petani       UUID NOT NULL REFERENCES petani(id_petani) ON DELETE CASCADE,
    nama_lahan      VARCHAR(100) NOT NULL,
    geom            GEOMETRY(Polygon, 4326) NOT NULL,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE jenis_tebu (
    id_tebu         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    kode_hardware   VARCHAR(20) UNIQUE NOT NULL,
    nama_varietas   VARCHAR(100),
    ambang_panen    NUMERIC(5,2),
    status          VARCHAR(20) NOT NULL DEFAULT 'belum_dikenali'
                        CHECK (status IN ('belum_dikenali', 'terverifikasi')),
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE blok_lahan (
    id_blok         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    id_lahan        UUID NOT NULL REFERENCES lahan(id_lahan) ON DELETE CASCADE,
    id_tebu         UUID REFERENCES jenis_tebu(id_tebu),
    nama_blok       VARCHAR(100) NOT NULL,
    rata_brix       NUMERIC(5,2),
    tanggal_tanam   DATE,
    geom            GEOMETRY(Polygon, 4326) NOT NULL,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE data_brix (
    id_data         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    id_blok         UUID NOT NULL REFERENCES blok_lahan(id_blok) ON DELETE CASCADE,
    id_user         UUID NOT NULL REFERENCES users(id_user),
    latitude        DOUBLE PRECISION NOT NULL,
    longitude       DOUBLE PRECISION NOT NULL,
    nilai_brix      NUMERIC(5,2) NOT NULL,
    foto            VARCHAR(255),
    geom            GEOMETRY(Point, 4326),
    status_sinkron  VARCHAR(20) NOT NULL DEFAULT 'tersinkron'
                        CHECK (status_sinkron IN ('belum_sinkron', 'tersinkron', 'gagal_sinkron')),
    client_uuid     UUID,
    catatan         TEXT,
    "timestamp"     TIMESTAMP NOT NULL,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE (client_uuid)
);

CREATE TABLE prediksi (
    id_prediksi       UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    id_data           UUID NOT NULL REFERENCES data_brix(id_data) ON DELETE CASCADE,
    hasil_prediksi    VARCHAR(255) NOT NULL,
    confidence_score  NUMERIC(5,4),
    created_at        TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_lahan_geom       ON lahan USING GIST (geom);
CREATE INDEX idx_blok_lahan_geom  ON blok_lahan USING GIST (geom);
CREATE INDEX idx_data_brix_geom   ON data_brix USING GIST (geom);
CREATE INDEX idx_data_brix_status_sinkron ON data_brix (status_sinkron);
CREATE INDEX idx_data_brix_id_blok        ON data_brix (id_blok);
CREATE INDEX idx_blok_lahan_id_lahan      ON blok_lahan (id_lahan);
