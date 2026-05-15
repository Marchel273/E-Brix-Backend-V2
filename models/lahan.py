from extensions import db
from datetime import datetime

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
