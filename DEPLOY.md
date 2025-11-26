# 🚀 Guía de Despliegue - Backend Monea

Esta guía te ayudará a desplegar el backend de Monea usando Docker.

## 📋 Requisitos Previos

- Docker instalado (versión 20.10 o superior)
- Docker Compose instalado (versión 1.29 o superior)

Verificar instalación:
```bash
docker --version
docker-compose --version
```

## 🏗️ Construcción y Despliegue

### 1. Configurar Variables de Entorno

Crea un archivo `.env` basado en `.env.example`:

```bash
cp .env.example .env
```

**⚠️ IMPORTANTE:** Edita el archivo `.env` y cambia la `SECRET_KEY` por una clave segura:

```bash
# Genera una clave segura
openssl rand -hex 32
```

Copia el resultado y úsalo como `SECRET_KEY` en el archivo `.env`.

### 2. Construir y Levantar los Contenedores

Desde el directorio `/back`, ejecuta:

```bash
docker-compose up -d --build
```

El flag `-d` ejecuta en segundo plano (detached mode) y `--build` construye las imágenes.

### 3. Verificar que el Servicio Está Corriendo

Verifica los logs:
```bash
docker-compose logs -f backend
```

Verifica el estado:
```bash
docker-compose ps
```

Prueba el endpoint de salud:
```bash
curl http://localhost:8002/health
```

O abre en tu navegador:
- API: http://localhost:8002
- Documentación: http://localhost:8002/docs
- Redoc: http://localhost:8002/redoc

## 🔧 Comandos Útiles

### Detener el servicio
```bash
docker-compose down
```

### Detener y eliminar volúmenes (⚠️ elimina la base de datos)
```bash
docker-compose down -v
```

### Ver logs en tiempo real
```bash
docker-compose logs -f backend
```

### Reiniciar el servicio
```bash
docker-compose restart backend
```

### Reconstruir después de cambios
```bash
docker-compose up -d --build
```

### Acceder al contenedor
```bash
docker-compose exec backend bash
```

## 📁 Estructura de Directorios

```
back/
├── data/              # Base de datos SQLite (se crea automáticamente)
├── logs/              # Logs de la aplicación (opcional)
├── app/               # Código de la aplicación
├── Dockerfile         # Configuración de Docker
├── docker-compose.yml # Orquestación de servicios
├── .env               # Variables de entorno (crear desde .env.example)
└── requirements.txt   # Dependencias Python
```

## 🌐 Configuración para Producción

### Variables de Entorno Importantes

1. **SECRET_KEY**: Debe ser una cadena aleatoria segura
2. **DEBUG**: Debe ser `False` en producción
3. **DATABASE_URL**: Por defecto usa SQLite en `./data/nexus_finance.db`

### Cambiar el Puerto

Si necesitas usar otro puerto, edita `docker-compose.yml`:

```yaml
ports:
  - "TU_PUERTO:8002"  # Cambia TU_PUERTO por el que desees
```

Y actualiza el comando en `Dockerfile` si es necesario.

### Configurar CORS para tu Dominio

Edita `app/main.py` y actualiza:

```python
allow_origins=["https://tu-dominio.com", "https://app.tu-dominio.com"]
```

## 🔒 Seguridad

1. ✅ Nunca subas el archivo `.env` al repositorio
2. ✅ Usa una `SECRET_KEY` fuerte y única
3. ✅ Configura `DEBUG=False` en producción
4. ✅ Limita los orígenes CORS a tus dominios
5. ✅ Usa HTTPS en producción
6. ✅ Configura un firewall adecuado

## 📊 Monitoreo

El servicio incluye un endpoint de health check:

```bash
GET http://localhost:8002/health
```

Docker Compose también monitorea la salud del contenedor automáticamente.

## 🐛 Resolución de Problemas

### El contenedor no inicia

1. Verifica los logs: `docker-compose logs backend`
2. Verifica que el puerto 8002 no esté en uso: `lsof -i :8002`
3. Verifica que el archivo `.env` exista y tenga valores válidos

### La base de datos no se persiste

Asegúrate de que el directorio `data/` exista y tenga permisos de escritura:
```bash
mkdir -p data
chmod 755 data
```

### Error de permisos

En algunos sistemas, es necesario ajustar permisos:
```bash
sudo chown -R $USER:$USER data/
```

## 📝 Notas

- La base de datos SQLite se almacena en el volumen `./data`
- Los logs se almacenan en `./logs` (opcional)
- El servicio se reinicia automáticamente si falla (`restart: unless-stopped`)

## 🆘 Soporte

Para más información, consulta la documentación de FastAPI o Docker.

