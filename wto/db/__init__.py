# wto/db/__init__.py
from .session import SessionLocal as SA, engine
__all__ = ["SA", "engine", "SessionLocal"]
