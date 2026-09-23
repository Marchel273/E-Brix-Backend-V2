import uuid
from extensions import db
from sqlalchemy.dialects.postgresql import UUID

class User(db.Model):
    __tablename__ = "users"

    id_user = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="petani")
    status = db.Column(db.String(20), nullable=False, default="pending")
    reset_otp = db.Column(db.String(6), nullable=True)
    otp_expiry = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    updated_at = db.Column(
        db.DateTime, nullable=False, server_default=db.func.now(), onupdate=db.func.now()
    )

    # Relationships
    petani = db.relationship("Petani", backref="user", uselist=False, cascade="all, delete-orphan")
    data_brix = db.relationship("DataBrix", backref="user")
