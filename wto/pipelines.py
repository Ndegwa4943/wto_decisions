# file: wto/pipelines.py
"""
Upsert pipeline with:
- strict UUID coercion (avoids invalid UUID errors),
- one transaction for Document + Blob (so they succeed/fail together),
- detailed exception logging,
- optional schema bootstrap (create_all) for first run safety.

If you still see db/save_errors > 0, the log will now print the exact
constraint/typing error from PostgreSQL so we can fix fast.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Dict

from sqlalchemy.exc import SQLAlchemyError, IntegrityError, DataError
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from wto.db.session import SessionLocal, engine
from wto.db.models import Document, ScraperBlobStore, Base

logger = logging.getLogger(__name__)


class WtoPipeline:
    def open_spider(self, spider):
        # Safety: idempotent schema bootstrap (OK when tables already exist)
        try:
            Base.metadata.create_all(bind=engine)
            spider.logger.info("DB schema ensured (create_all).")
        except Exception as exc:  # why: aids first-run, ignore if restricted env
            spider.logger.warning("create_all skipped/failed: %s", exc)

        spider.logger.info("SQLAlchemy pipeline ready (per-item DB sessions).")

    def close_spider(self, spider):
        spider.logger.info("SQLAlchemy pipeline closed.")

    #utils 
    def _coerce_uuid(self, value: Any) -> uuid.UUID:
        if isinstance(value, uuid.UUID):
            return value
        if isinstance(value, (bytes, bytearray, memoryview)):
            return uuid.UUID(bytes=bytes(value))
        # Accept hex digests (e.g., sha256 hexdigest) and derive UUID from first 16 bytes
        try:
            s = str(value)
            if all(c in '0123456789abcdefABCDEF' for c in s) and len(s) in (32, 64):
                raw = bytes.fromhex(s)
                return uuid.UUID(bytes=raw[:16])
            return uuid.UUID(s)
        except Exception:
            # Re-raise as ValueError for consistent handling upstream
            raise ValueError("badly formed UUID or hex digest for UUID derivation")

    # main pipeline 
    def process_item(self, item, spider):
        required = ("source_file", "file_content_type", "name", "url", "doc_uuid")
        if not all(k in item and item[k] for k in required):
            spider.logger.warning("Skipping item: missing required fields %s", required)
            return item
        if not isinstance(item["source_file"], (bytes, bytearray, memoryview)):
            spider.logger.warning("Skipping item: source_file not bytes-like")
            return item

        session = SessionLocal()
        try:
            doc_id = self._coerce_uuid(item["doc_uuid"])  # strict UUID type

            incoming_url = str(item["url"]) if item.get("url") else ""

            # Application-level dedupe by URL: if URL exists, reuse its document_id
            try:
                existing_id = session.execute(
                    select(Document.document_id).where(Document.url == incoming_url)
                ).scalar_one_or_none()
            except Exception:
                existing_id = None

            effective_doc_id = str(existing_id) if existing_id else str(doc_id)

            doc_data: Dict[str, Any] = {
                "document_id": effective_doc_id,
                "url": incoming_url,
                "name": item.get("name") or "",
                "path": item.get("path"),
                "scraper": item.get("scraper") or spider.name,
                "timestamp": item.get("timestamp"),
                "version": item.get("version") or "1.0",
                "data": item.get("data") or {},
            }

            # Implicit transaction begins on first execute; no explicit begin needed

            upsert_doc = (
                insert(Document)
                .values(doc_data)
                .on_conflict_do_update(
                    index_elements=[Document.document_id],
                    set_={
                        "url": doc_data["url"],
                        "name": doc_data["name"],
                        "data": doc_data["data"],
                        "timestamp": doc_data["timestamp"],
                        "version": doc_data["version"],
                        "scraper": doc_data["scraper"],
                    },
                )
            )
            session.execute(upsert_doc)

            upsert_blob = (
                insert(ScraperBlobStore)
                .values(
                    {
                        "document_id": effective_doc_id,
                        "file_content_type": item["file_content_type"],
                        "source_file": bytes(item["source_file"]),
                    }
                )
                .on_conflict_do_update(
                    index_elements=[ScraperBlobStore.document_id],
                    set_={
                        "file_content_type": item["file_content_type"],
                        "source_file": bytes(item["source_file"]),
                    },
                )
            )
            session.execute(upsert_blob)

            session.commit()
            spider.logger.info("DB OK: %s", item.get("name"))
            if hasattr(spider, "crawler"):
                spider.crawler.stats.inc_value("db/saved_items")

        except (IntegrityError, DataError) as exc:  # NOT NULL, FK, UUID, etc.
            session.rollback()
            logger.exception("DB constraint error for %s: %s", item.get("url"), exc)
            if hasattr(spider, "crawler"):
                spider.crawler.stats.inc_value("db/save_errors")
        except SQLAlchemyError as exc:
            session.rollback()
            logger.exception("SQLAlchemy insert failed for %s: %s", item.get("url"), exc)
            if hasattr(spider, "crawler"):
                spider.crawler.stats.inc_value("db/save_errors")
        except Exception as exc:  # last resort
            session.rollback()
            logger.exception("Unexpected DB error for %s: %s", item.get("url"), exc)
            if hasattr(spider, "crawler"):
                spider.crawler.stats.inc_value("db/save_errors")
        finally:
            try:
                session.close()
            except Exception:
                pass
        return item
