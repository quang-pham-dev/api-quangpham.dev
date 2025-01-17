from typing import Generator
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Session

# Initialize SQLAlchemy instance
db = SQLAlchemy()


def get_db() -> Generator[Session, None, None]:
    """
    Get database session.
    """
    try:
        session: Session = db.session
        yield session
    finally:
        session.close()
