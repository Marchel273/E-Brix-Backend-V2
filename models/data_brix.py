import uuid
from extensions import db
from sqlalchemy.dialects.postgresql import UUID
from geoalchemy2 import Geometry

class DataBrix(db.Model):
    __tablename__ = "data_brix"

    id_data = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id_blok = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("blok_lahan.id_blok", ondelete="CASCADE"),
        nullable=False,
    )
    id_user = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("users.id_user"),
        nullable=False,
    )
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    nilai_brix = db.Column(db.Numeric(5, 2), nullable=False)
    foto = db.Column(db.String(255), nullable=True)
    geom = db.Column(Geometry(geometry_type="Point", srid=4326), nullable=True)
    status_sinkron = db.Column(db.String(20), nullable=False, default="tersinkron")
    client_uuid = db.Column(UUID(as_uuid=True), unique=True, nullable=True)
    catatan = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    updated_at = db.Column(
        db.DateTime, nullable=False, server_default=db.func.now(), onupdate=db.func.now()
    )

    # Relationships
    prediksis = db.relationship("Prediksi", backref="data_brix", cascade="all, delete-orphan")
