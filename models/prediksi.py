from extensions import db
from datetime import datetime

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
