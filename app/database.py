from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

# Create Database Engine
connect_args = {"check_same_thread": False} if "sqlite" in settings.get_database_url else {}

engine = create_engine(
    settings.get_database_url,
    connect_args=connect_args
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """Dependency for providing a SQLAlchemy database session to routes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
