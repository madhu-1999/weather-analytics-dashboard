from contextlib import contextmanager
import os
from typing import Iterator, Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Read db url from .env file
DATABASE_URL = os.getenv("DB_URL")
if not DATABASE_URL:
    raise ValueError("Critical Error: 'DATABASE_URL' is missing from the .env file.")

engine = create_engine(DATABASE_URL, pool_size=5)

SessionLocal = sessionmaker(autocommit=False, bind=engine)


@contextmanager
def session_scope() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_session() -> Generator[Session, None, None]:
    with session_scope() as db:
        yield db
