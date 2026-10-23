from datetime import datetime
from extensions import db
from sqlalchemy.dialects.postgresql import JSONB

class RiwayatPrediksiML(db.Model):
    """
    Model database PostgreSQL untuk menyimpan riwayat hasil inferensi Machine Learning:
    - input fitur lingkungan & budidaya
    - hasil estimasi yield, brix, nira, gula, durasi, penyakit
    - analisis musim (12 bulan komparasi kemarau vs penghujan)
    - rekomendasi agronomis & formula Winter-Carp
    """
    __tablename__ = "riwayat_prediksi_ml"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.now)
    input_data = db.Column(JSONB, nullable=False)
    hasil = db.Column(JSONB, nullable=False)
    analisis_musim = db.Column(JSONB, nullable=True)
    rekomendasi = db.Column(JSONB, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())

    def to_dict(self):
        """Format dict yang identik dengan schema riwayat prediksi ML."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S") if self.timestamp else "",
            "input": self.input_data,
            "hasil": self.hasil,
            "analisis_musim": self.analisis_musim,
            "rekomendasi": self.rekomendasi
        }
