from flask import Flask
from flask_cors import CORS
from config import Config
from extensions import db
import os
# Import cloudinary
import cloudinary
import cloudinary.uploader
import cloudinary.api

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    CORS(app)

# --- KONFIGURASI CLOUDINARY ---
    cloudinary.config( 
        cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME'), 
        api_key = os.getenv('CLOUDINARY_API_KEY'), 
        api_secret = os.getenv('CLOUDINARY_API_SECRET'),
        secure = True
    )
    
    # Import blueprints dari masing-masing file route
    from routes.lahan_route import lahan_bp
    from routes.blok_route import blok_bp
    from routes.data_brix_route import data_brix_bp
    from routes.prediksi_route import prediksi_bp

    # Daftarkan blueprints
    app.register_blueprint(lahan_bp)
    app.register_blueprint(blok_bp)
    app.register_blueprint(data_brix_bp)
    app.register_blueprint(prediksi_bp)

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)