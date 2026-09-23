import os
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

class Config:
    # Mendukung DATABASE_URL langsung atau per variabel
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        # Jika database url diawali postgres://, ubah ke postgresql+psycopg2://
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql+psycopg2://", 1)
        elif db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
        SQLALCHEMY_DATABASE_URI = db_url
    else:
        user = os.getenv("DB_USER", "postgres")
        password = os.getenv("DB_PASS", "postgres")
        host = os.getenv("DB_HOST", "localhost")
        port = os.getenv("DB_PORT", "5432")
        name = os.getenv("DB_NAME", "ebrix")
        SQLALCHEMY_DATABASE_URI = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{name}"

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv("SECRET_KEY", "ebrix-super-secret-key-2026")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "ebrix-jwt-secret-key-2026")

    # Waktu expired JWT (jam)
    jwt_hours = int(os.getenv("JWT_EXPIRES_HOURS", 24))
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=jwt_hours)
