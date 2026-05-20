from extensions import db
from datetime import datetime

class Blok(db.Model):
    __tablename__ = "blok"
    id_blok = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_lahan = db.Column(
        db.Integer,
        db.ForeignKey("lahan.id_lahan", ondelete="CASCADE", onupdate="CASCADE"),
    )
    nama_blok = db.Column(db.String(50), nullable=False)
    foto = db.Column(db.String(255), nullable=True) # Optional
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(
        db.DateTime, default=datetime.now, onupdate=datetime.now
    )
