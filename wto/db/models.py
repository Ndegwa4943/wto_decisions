# file: wto/db/models.py

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, LargeBinary, JSON
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.dialects.postgresql import JSONB 
from sqlalchemy.sql import func                    # for server default

Base = declarative_base()

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True)
    url = Column(String, nullable=False)
    scraper = Column(String, nullable=False)
    version = Column(String, nullable=False)
    name = Column(String, nullable=False)
    timestamp = Column(DateTime)
    path = Column(String)  # ltree-style
    data = Column(JSONB, nullable=False)     # replace JSON with JSONB
    ingested_at = Column(DateTime, nullable=False, server_default=func.now()) 

    # 1:1 relationship with the blob
    blob = relationship("ScraperBlobStore", uselist=False, back_populates="document", cascade="all, delete")

class ScraperBlobStore(Base):
    __tablename__ = "scraper_blob_store"

    id = Column(Integer, primary_key=True)
    file_content_type = Column(String, nullable=False)
    source_file = Column(LargeBinary, nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), unique=True)

    document = relationship("Document", back_populates="blob")