import uuid
from extensions import db
from sqlalchemy.dialects.postgresql import UUID

class JenisTebu(db.Model):
    __tablename__ = "jenis_tebu"

    id_tebu = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    kode_hardware = db.Column(db.String(20), unique=True, nullable=False)
    nama_varietas = db.Column(db.String(100), nullable=True)
    ambang_panen = db.Column(db.Numeric(5, 2), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="belum_dikenali")
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    updated_at = db.Column(
        db.DateTime, nullable=False, server_default=db.func.now(), onupdate=db.func.now()
    )

    # Relationships
    bloks = db.relationship("BlokLahan", backref="jenis_tebu")
