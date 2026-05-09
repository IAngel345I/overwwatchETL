# Usa una imagen oficial de Python
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Instala dependencias del sistema para psycopg2
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copia los requerimientos desde la raiz e instala
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo el proyecto
COPY . .

# Expone el puerto 8052
EXPOSE 8052

# Comando para lanzar la app (ahora buscando dashboard_pro en la raiz)
CMD ["gunicorn", "--bind", "0.0.0.0:8052", "dashboard_pro:server"]
