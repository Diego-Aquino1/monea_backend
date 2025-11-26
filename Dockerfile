# Dockerfile para el backend de Monea
FROM python:3.11-slim

# Metadatos
LABEL maintainer="Monea Team"
LABEL description="Backend API para aplicación Monea - Gestión Financiera Personal"

# Variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primero para aprovechar cache de Docker
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copiar código de la aplicación
COPY . .

# Crear directorio para la base de datos si no existe
RUN mkdir -p /app/data /app/logs

# Copiar script de inicio
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Exponer puerto
EXPOSE 8002

# Comando por defecto
CMD ["/app/start.sh"]

