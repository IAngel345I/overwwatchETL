# Usa una imagen oficial de Python
FROM python:3.11-slim

# Evita que Python genere archivos .pyc y que el buffer se llene
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Directorio de trabajo
WORKDIR /app

# Instala dependencias del sistema necesarias para psycopg2
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copia los requerimientos e instala
COPY files/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo el proyecto
COPY . .

# Expone el puerto 8052 (el que configuramos en dashboard_pro.py)
EXPOSE 8052

# Comando para lanzar la app con Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8052", "files.dashboard_pro:server"]
