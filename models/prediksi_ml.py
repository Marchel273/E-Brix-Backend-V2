import uuid
from extensions import db
from sqlalchemy.dialects.postgresql import UUID, JSONB


class PrediksiML(db.Model):
    """Tabel riwayat prediksi Machine Learning tebu."""
    __tablename__ = "prediksi_ml"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_user = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("users.id_user", ondelete="SET NULL"),
        nullable=True,
    )
    input_params = db.Column(JSONB, nullable=False)
    hasil = db.Column(JSONB, nullable=False)
    analisis_musim = db.Column(JSONB, nullable=True)
    rekomendasi = db.Column(JSONB, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
