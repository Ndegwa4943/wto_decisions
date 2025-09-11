# file: wto/db/models.py

from sqlalchemy import Column, String, DateTime, ForeignKey, LargeBinary, Text, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import func, text

Base = declarative_base()

class Document(Base):
    __tablename__ = "documents"

    # Existing DB schema: document_id varchar(64) PK
    document_id = Column(String(64), primary_key=True)
    name = Column(Text)
    url = Column(Text)
    scraper = Column(String(50))
    version = Column(String(10))
    data = Column(postgresql.JSONB)
    path = Column(Text)
    timestamp = Column(DateTime(timezone=True))
    ingested_at = Column(DateTime(timezone=True))

    # 1:1 relationship with the blob
    blob = relationship(
        "ScraperBlobStore",
        uselist=False,
        back_populates="document",
        cascade="all, delete",
        foreign_keys="ScraperBlobStore.document_id",
    )

class ScraperBlobStore(Base):
    __tablename__ = "scraper_blob_store"

    # Existing DB schema:
    # id uuid default gen_random_uuid() PK
    id = Column(
        postgresql.UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    timestamp = Column(DateTime(timezone=True))
    file_content_type = Column(String(255), nullable=False)
    source_file = Column(LargeBinary, nullable=False)

    # document_id varchar(64) UNIQUE, FK -> documents.document_id
    document_id = Column(
        String(64),
        ForeignKey("documents.document_id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    document = relationship("Document", back_populates="blob", foreign_keys=[document_id])

    __table_args__ = (
        UniqueConstraint("document_id", name="scraper_blob_store_document_id_unique"),
    )