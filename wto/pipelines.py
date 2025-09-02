# wto/pipelines.py
import logging, os
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
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
        except Exception:
            self.session.rollback()
            raise
        finally:
            self.session.close()
            spider.logger.info("SQLAlchemy DB session closed.")

    def process_item(self, item, spider):
        # minimal guard: require bytes + name + url
        required = ("source_file", "file_content_type", "name", "url")
        if not all(k in item for k in required):
            spider.logger.warning("Skipping item: missing required fields")
            return item
        if not isinstance(item["source_file"], (bytes, bytearray, memoryview)):
            spider.logger.warning("Skipping item: source_file not bytes-like")
            return item

        try:
            # DB de-dup by sha256, if present skip insertion
            sha256 = (item.get("data") or {}).get("sha256")
            if sha256:
                existing = (
                    self.session.query(Document)
                    .filter(text("data->>'sha256' = :sha256"))
                    .params(sha256=sha256)
                    .first()
                )
                if existing:
                    spider.logger.info(f"DB DUPLICATE SKIPPED: {item['name']}")
                    return item

            doc = Document(
                url=item["url"],
                name=item.get("name"),
                path=item.get("path"),
                scraper=item.get("scraper"),
                timestamp=item.get("timestamp"),
                version=item.get("version"),
                data=item.get("data"),
            )
            blob = ScraperBlobStore(
                file_content_type=item["file_content_type"],
                source_file=bytes(item["source_file"]),
                document=doc,
            )

            self.session.add(doc)
            self.session.commit()
            spider.logger.info(f"DB OK: {doc.name} -> id={doc.id}")
            if hasattr(spider, "crawler"):
                spider.crawler.stats.inc_value("db/saved_items")

        except SQLAlchemyError:
            self.session.rollback()
            logger.exception("SQLAlchemy insert failed")
            if hasattr(spider, "crawler"):
                spider.crawler.stats.inc_value("db/save_errors")
        return item


