"""
Aplicación principal FastAPI
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.api import (
    auth, accounts, categories, transactions, credit_cards, 
    budgets, goals, investments, analytics,
    recurring_transactions, alerts, subscriptions, can_spend, exports
)

# Crear aplicación
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="API para gestión financiera personal",
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar orígenes
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(accounts.router, prefix="/api/accounts", tags=["accounts"])
app.include_router(categories.router, prefix="/api/categories", tags=["categories"])
app.include_router(transactions.router, prefix="/api/transactions", tags=["transactions"])
app.include_router(credit_cards.router, prefix="/api/credit-cards", tags=["credit-cards"])
app.include_router(budgets.router, prefix="/api/budgets", tags=["budgets"])
app.include_router(goals.router, prefix="/api/goals", tags=["goals"])
app.include_router(investments.router, prefix="/api/investments", tags=["investments"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(recurring_transactions.router, prefix="/api/recurring-transactions", tags=["recurring-transactions"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["alerts"])
app.include_router(subscriptions.router, prefix="/api/subscriptions", tags=["subscriptions"])
app.include_router(can_spend.router, prefix="/api/can-i-spend", tags=["can-i-spend"])
app.include_router(exports.router, prefix="/api/exports", tags=["exports"])


@app.on_event("startup")
async def startup_event():
    """Inicializar base de datos al arrancar"""
    init_db()


@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "name": settings.APP_NAME,
        "version": settings.VERSION,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check"""
    return {"status": "healthy"}

