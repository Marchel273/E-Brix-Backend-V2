import uuid
from extensions import db
from sqlalchemy.dialects.postgresql import UUID
from geoalchemy2 import Geometry

class BlokLahan(db.Model):
    __tablename__ = "blok_lahan"

    id_blok = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id_lahan = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("lahan.id_lahan", ondelete="CASCADE"),
        nullable=False,
    )
    id_tebu = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("jenis_tebu.id_tebu"),
        nullable=True,
    )
    nama_blok = db.Column(db.String(100), nullable=False)
    rata_brix = db.Column(db.Numeric(5, 2), nullable=True)
    tanggal_tanam = db.Column(db.Date, nullable=True)
    geom = db.Column(Geometry(geometry_type="Polygon", srid=4326), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    updated_at = db.Column(
        db.DateTime, nullable=False, server_default=db.func.now(), onupdate=db.func.now()
    )

    # Relationships
    data_brix_list = db.relationship("DataBrix", backref="blok_lahan", cascade="all, delete-orphan")
