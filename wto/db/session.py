# file: wto/db/session.py

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

PGUSER = os.getenv("PGUSER")
PGPASSWORD = os.getenv("PGPASSWORD")
PGDATABASE = os.getenv("PGDATABASE")
PGHOST = os.getenv("PGHOST", "localhost")
PGPORT = os.getenv("PGPORT", "5432")

# Connection string: SQLAlchemy + Postgres + psycopg2
DB_URL = f"postgresql+psycopg2://{PGUSER}:{PGPASSWORD}@{PGHOST}:{PGPORT}/{PGDATABASE}"

# Engine = connection to DB (resilient pool)
engine = create_engine(
    DB_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    pool_recycle=1800,
    connect_args={
        # TCP keepalives (psycopg2)
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5,
    },
)

# SessionLocal = short-lived session factory
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
