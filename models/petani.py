import uuid
from extensions import db
from sqlalchemy.dialects.postgresql import UUID

class Petani(db.Model):
    __tablename__ = "petani"

    id_petani = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id_user = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey("users.id_user", ondelete="CASCADE"),
        nullable=False,
    )
    nama = db.Column(db.String(100), nullable=False)
    nomor_telepon = db.Column(db.String(20), nullable=True)
    alamat = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    updated_at = db.Column(
        db.DateTime, nullable=False, server_default=db.func.now(), onupdate=db.func.now()
    )

    # Relationships
    lahans = db.relationship("Lahan", backref="petani", cascade="all, delete-orphan")
