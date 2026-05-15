from extensions import db
from datetime import datetime

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
