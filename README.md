# Monea - Backend API

Backend FastAPI para la aplicación de gestión financiera personal Monea.

## 🚀 Despliegue Rápido con Docker (Recomendado)

Para desplegar el backend en un servidor, consulta la [Guía de Despliegue](DEPLOY.md).

**Inicio rápido:**
```bash
# 1. Configurar variables de entorno
cp .env.example .env
# Editar .env y cambiar SECRET_KEY

# 2. Levantar con Docker Compose
docker-compose up -d --build

# El backend estará disponible en http://localhost:8002
```

## 💻 Desarrollo Local

### Instalación

```bash
cd back
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Configuración

Copiar `.env.example` a `.env` y configurar las variables de entorno.

### Ejecución

```bash
uvicorn app.main:app --reload --port 8000
```

La API estará disponible en http://localhost:8000
Documentación interactiva en http://localhost:8000/docs

## Estructura

```
back/
├── app/
│   ├── main.py              # Punto de entrada
│   ├── config.py            # Configuración
│   ├── database.py          # Configuración DB
│   ├── models/              # Modelos SQLAlchemy
│   ├── schemas/             # Schemas Pydantic
│   ├── api/                 # Endpoints
│   ├── services/            # Lógica de negocio
│   ├── repositories/        # Acceso a datos
│   └── utils/               # Utilidades
```

