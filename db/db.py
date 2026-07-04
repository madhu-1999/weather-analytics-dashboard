from contextlib import contextmanager
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from sqlalchemy import inspect

from logger import logger


load_dotenv()

# Read db url from .env file
DATABASE_URL = os.getenv("DB_URL")
if not DATABASE_URL:
    raise ValueError("Critical Error: 'DATABASE_URL' is missing from the .env file.")

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, bind=engine)


@contextmanager
def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Sanity check
inspector = inspect(engine)
tables = inspector.get_table_names()
logger.info(f"Tables in database: {tables}")
logger.info(DATABASE_URL)
