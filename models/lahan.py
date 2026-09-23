import uuid
from extensions import db
from sqlalchemy.dialects.postgresql import UUID
from geoalchemy2 import Geometry

class Lahan(db.Model):
    __tablename__ = "lahan"

    id_lahan = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id_petani = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("petani.id_petani", ondelete="CASCADE"),
        nullable=False,
    )
    nama_lahan = db.Column(db.String(100), nullable=False)
    geom = db.Column(Geometry(geometry_type="Polygon", srid=4326), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    updated_at = db.Column(
        db.DateTime, nullable=False, server_default=db.func.now(), onupdate=db.func.now()
    )

    # Relationships
    bloks = db.relationship("BlokLahan", backref="lahan", cascade="all, delete-orphan")
