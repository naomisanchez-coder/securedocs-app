from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Configuración de conexión a PostgreSQL
# Formato: postgresql://usuario:contraseña@localhost:5432/nombre_bd
DATABASE_URL = "postgresql://postgres:isabel123@localhost:5432/securedocs_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()