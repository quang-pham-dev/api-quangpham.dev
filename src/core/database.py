from typing import Generator
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Session

# Initialize SQLAlchemy instance
db = SQLAlchemy()


def get_db() -> Session:
    """
    Get database session.
    """
    return db.session
