import uuid
from extensions import db
from sqlalchemy.dialects.postgresql import UUID

class Prediksi(db.Model):
    __tablename__ = "prediksi"

    id_prediksi = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id_data = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("data_brix.id_data", ondelete="CASCADE"),
        nullable=False,
    )
    hasil_prediksi = db.Column(db.String(255), nullable=False)
    confidence_score = db.Column(db.Numeric(5, 4), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    updated_at = db.Column(
        db.DateTime, nullable=False, server_default=db.func.now(), onupdate=db.func.now()
    )
