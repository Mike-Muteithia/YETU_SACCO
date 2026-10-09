from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base

# Initialize SQLite database
engine = create_engine('sqlite:///yetu_sacco.db', echo=False)
Base.metadata.create_all(engine)

SessionLocal = sessionmaker(bind=engine)

def get_session():
    return SessionLocal()