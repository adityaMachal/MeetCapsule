from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
import os

# Create a data directory if it doesn't exist
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

# Create a local SQLite database file in the data folder
DB_URL = f"sqlite:///{os.path.join(DATA_DIR, 'meetcapsule.db')}"

# engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
# The above line is needed for SQLite to work with FastAPI
engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
