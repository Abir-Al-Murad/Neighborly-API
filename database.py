import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

Database_URL = os.environ.get("DATABASE_URL")

# Database_URL = "postgresql://postgres:1234@localhost:5432/Neighborly"

# Render gives postgres:// but SQLAlchemy 2.x needs postgresql://
if Database_URL and Database_URL.startswith("postgres://"):
    Database_URL = Database_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(Database_URL) # type: ignore

class Base(DeclarativeBase):
    pass

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()