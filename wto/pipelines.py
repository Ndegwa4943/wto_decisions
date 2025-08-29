# wto/pipelines.py
import logging
import os
from sqlalchemy.exc import SQLAlchemyError
from wto.items import WtoDocumentItem
from wto.db.session import SessionLocal
from wto.db.models import Document, ScraperBlobStore

logger = logging.getLogger(__name__)

class PostgresPipeline:
    def open_spider(self, spider):
        self.session = SessionLocal()
        spider.logger.info("SQLAlchemy DB session started.")

    def close_spider(self, spider):
        try:
            self.session.commit()
        except:
            self.session.rollback()
            raise
        finally:
            self.session.close()
            spider.logger.info("SQLAlchemy DB session closed.")

    def process_item(self, item, spider):
        if not isinstance(item, WtoDocumentItem):
            return item

        try:
            # Sanity check: source_file must be bytes
            if not isinstance(item['source_file'], (bytes, bytearray, memoryview)):
                raise TypeError("source_file must be bytes-like")

            # Deduplication: check if a document with the same SHA-256 hash exists in the DB
            sha256_hash = item['data'].get('sha256')
            if sha256_hash:
                existing = self.session.query(Document).filter_by(sha256_checksum=sha256_hash).first()
                if existing:
                    spider.logger.info(f"DB DUPLICATE SKIPPED: {item['name']} (SHA-256 already in DB)")
                    return item

            # DB: Create Document and Blob entry
            doc = Document(
                url=item["url"],
                name=item["name"],
                path=item["path"],
                scraper=item["scraper"],
                timestamp=item["timestamp"],
                version=item["version"],
                data=item["data"],
                sha256_checksum=sha256_hash,
            )

            blob = ScraperBlobStore(
                file_content_type=item['file_content_type'],
                source_file=item['source_file'],
                document=doc
            )

            self.session.add(doc)
            self.session.add(blob)
            self.session.commit()
            spider.logger.info(f"DB OK: {doc.name} -> id={doc.id}")

            # STATS
            if hasattr(spider, "crawler"):
                spider.crawler.stats.inc_value("db/saved_items")

        except SQLAlchemyError:
            self.session.rollback()
            logger.exception("SQLAlchemy insert failed")
            if hasattr(spider, "crawler"):
                spider.crawler.stats.inc_value("db/save_errors")

        return item

