"""
Migración: Agregar campos is_investment e investment_id a subscriptions
"""
from sqlalchemy import text
from app.database import engine

def upgrade():
    """Agregar las nuevas columnas a la tabla subscriptions"""
    with engine.connect() as conn:
        # Verificar si las columnas ya existen antes de agregarlas
        # SQLite no tiene ALTER COLUMN, así que usamos un enfoque diferente
        conn.execute(text("""
            ALTER TABLE subscriptions 
            ADD COLUMN is_investment BOOLEAN DEFAULT 0
        """))
        
        conn.execute(text("""
            ALTER TABLE subscriptions 
            ADD COLUMN investment_id INTEGER
        """))
        
        conn.commit()
        print("✅ Campos is_investment e investment_id agregados a subscriptions")

if __name__ == "__main__":
    try:
        upgrade()
    except Exception as e:
        # Si las columnas ya existen, SQLite lanzará un error pero está bien
        if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
            print("⚠️ Las columnas ya existen, omitiendo migración")
        else:
            print(f"❌ Error en migración: {e}")
            raise

