# file: ug_tat/db/models.py

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, LargeBinary, JSON
from sqlalchemy.orm import declarative_base, relationship

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
    data = Column(JSON, nullable=False)    # for metadata searchable in JibuDocs
    ingested_at = Column(DateTime, nullable=True)

    # 1:1 relationship with the blob
    blob = relationship("ScraperBlobStore", uselist=False, back_populates="document", cascade="all, delete")

class ScraperBlobStore(Base):
    __tablename__ = "scraper_blob_store"

    id = Column(Integer, primary_key=True)
    file_content_type = Column(String, nullable=False)
    source_file = Column(LargeBinary, nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), unique=True)

    document = relationship("Document", back_populates="blob")