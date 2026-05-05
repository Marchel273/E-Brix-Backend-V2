from extensions import db
from datetime import datetime

# LAHAN
class Lahan(db.Model):
    __tablename__ = "lahan"
    id_lahan = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nama_lahan = db.Column(db.String(100), nullable=False)
    tipe = db.Column(db.String(50))
    foto = db.Column(db.String(255), nullable=True) # Optional
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

# BLOK
class Blok(db.Model):
    __tablename__ = "blok"
    id_blok = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_lahan = db.Column(
        db.Integer,
        db.ForeignKey("lahan.id_lahan", ondelete="CASCADE", onupdate="CASCADE"),
    )
    nama_blok = db.Column(db.String(50), nullable=False)
    foto = db.Column(db.String(255), nullable=True) # Optional
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

# DATA BRIX
class DataBrix(db.Model):
    __tablename__ = "data_brix"
    id_data = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_blok = db.Column(
        db.Integer,
        db.ForeignKey("blok.id_blok", ondelete="CASCADE", onupdate="CASCADE"),
    )
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    nilai_brix = db.Column(db.Float)
    foto = db.Column(db.String(255), nullable=False) # Wajib
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

# PREDIKSI
class Prediksi(db.Model):
    __tablename__ = "prediksi"
    id_prediksi = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_data = db.Column(
        db.Integer,
        db.ForeignKey("data_brix.id_data", ondelete="CASCADE", onupdate="CASCADE"),
    )
    hasil_prediksi = db.Column(db.String(50))
    confidence_score = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )