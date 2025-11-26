#!/bin/bash
# Script de inicio para el backend Monea

# Crear directorio de datos si no existe
mkdir -p /app/data
mkdir -p /app/logs

# Verificar que la base de datos tenga permisos de escritura
chmod -R 755 /app/data

# Iniciar la aplicación
exec uvicorn app.main:app --host 0.0.0.0 --port 8002

