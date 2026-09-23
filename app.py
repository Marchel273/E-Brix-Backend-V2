import os
from flask import Flask, jsonify
from flask_cors import CORS
import cloudinary
import cloudinary.uploader
import cloudinary.api
from config import Config
from extensions import db, jwt, bcrypt

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    bcrypt.init_app(app)

    cors_origins = os.getenv("CORS_ORIGINS", "*")
    if cors_origins == "*":
        CORS(app)
    else:
        origins_list = [o.strip() for o in cors_origins.split(",") if o.strip()]
        CORS(app, origins=origins_list)

    # Konfigurasi Cloudinary (jika ada)
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME")
    if cloud_name:
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=os.getenv("CLOUDINARY_API_KEY"),
            api_secret=os.getenv("CLOUDINARY_API_SECRET"),
            secure=True
        )

    # Import dan daftarkan blueprints
    from routes.auth_route import auth_bp
    from routes.petani_route import petani_bp
    from routes.jenis_tebu_route import jenis_tebu_bp
    from routes.lahan_route import lahan_bp
    from routes.blok_lahan_route import blok_lahan_bp
    from routes.data_brix_route import data_brix_bp
    from routes.prediksi_route import prediksi_bp
    from routes.export_route import export_bp
    from routes.rekomendasi_route import rekomendasi_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(petani_bp)
    app.register_blueprint(jenis_tebu_bp)
    app.register_blueprint(lahan_bp)
    app.register_blueprint(blok_lahan_bp)
    app.register_blueprint(data_brix_bp)
    app.register_blueprint(prediksi_bp)
    app.register_blueprint(export_bp)
    app.register_blueprint(rekomendasi_bp)

    # JWT error handlers
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({"message": "Token otentikasi tidak ditemukan. Silakan login terlebih dahulu."}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({"message": "Token otentikasi tidak valid."}), 401

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({"message": "Token otentikasi telah kadaluarsa. Silakan login kembali."}), 401

    # Global error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"message": "Resource atau endpoint tidak ditemukan"}), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({"message": "Method HTTP tidak diizinkan untuk endpoint ini"}), 405

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({"message": "Terjadi kesalahan internal pada server"}), 500

    @app.route("/", methods=["GET"])
    def index():
        return jsonify({
            "message": "Selamat datang di API E-Brix (PostgreSQL + PostGIS Edition)",
            "status": "online",
            "version": "2.0.0"
        }), 200

    return app

app = create_app()

if __name__ == "__main__":
    host = os.getenv("FLASK_HOST", "0.0.0.0")
    port = int(os.getenv("FLASK_PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "true").lower() in ["true", "1", "yes"]
    app.run(host=host, port=port, debug=debug)