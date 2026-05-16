import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

Database_URL = os.environ.get("DATABASE_URL")

# If no DATABASE_URL provided, fall back to a local sqlite file for local development.
if not Database_URL:
    Database_URL = "sqlite:///./neighborly.db"

# Render gives postgres:// but SQLAlchemy 2.x needs postgresql://
if Database_URL and Database_URL.startswith("postgres://"):
    Database_URL = Database_URL.replace("postgres://", "postgresql://", 1)

# For sqlite, ensure the correct connect args
if Database_URL.startswith("sqlite"):
    engine = create_engine(Database_URL, connect_args={"check_same_thread": False})  # type: ignore
else:
    engine = create_engine(Database_URL)  # type: ignore

class Base(DeclarativeBase):
    pass

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()