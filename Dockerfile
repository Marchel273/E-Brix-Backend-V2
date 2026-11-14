# ============================================================
# Dockerfile E-Brix Backend (Flask + PostGIS + Machine Learning)
# ============================================================

FROM python:3.11-slim

# Mencegah pembuatan file .pyc dan memastikan output log unbuffered (langsung tampil)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependensi sistem yang dibutuhkan untuk psycopg2, geos/shapely, dan curl
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    libgeos-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements dan install paket Python
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy seluruh source code project ke container
COPY . /app/

# Expose port aplikasi Flask
EXPOSE 5000

# Jalankan server menggunakan Gunicorn (Production WSGI)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "3", "--timeout", "120", "app:create_app()"]
