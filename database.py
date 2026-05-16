from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker



Database_URL = "postgresql://postgres:1234@localhost:5432/Neighborly"
engine = create_engine(Database_URL)


class Base(DeclarativeBase):
    pass

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
   db = SessionLocal()
   try:
       yield db
   finally:
       db.close()
       