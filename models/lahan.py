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

    def get_geojson(self):
        """Konversi geom PostGIS ke dict GeoJSON."""
        from utils.helpers import geometry_to_geojson
        return geometry_to_geojson(self.geom)

    def calculate_area(self) -> float:
        """Kalkulasi perkiraan luas lahan dalam satuan Hektar (Ha)."""
        if not self.geom:
            return 0.0
        try:
            from geoalchemy2.shape import to_shape
            poly = to_shape(self.geom)
            # 1 derajat lintang/bujur di ekuator ~ 111.32 km = 111320 m
            # Perkiraan konversi derajat persegi ke hektar di wilayah Jawa Timur (~ -7.5 Lat):
            # 1 deg lat ~ 110.574 km, 1 deg lon ~ 110.354 km
            area_m2 = poly.area * (110574.0 * 110354.0)
            return round(area_m2 / 10000.0, 2)
        except Exception:
            return 0.0

    @classmethod
    def create_lahan(cls, id_petani, nama_lahan, geom):
        """Factory method sesuai Class Diagram UML."""
        return cls(id_petani=id_petani, nama_lahan=nama_lahan, geom=geom)
