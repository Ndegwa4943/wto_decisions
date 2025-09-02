# wto/items.py
import scrapy

class WtoDocumentItem(scrapy.Item):
    url = scrapy.Field()               # The URL of the document
    name = scrapy.Field()              # The name of the scraper used
    path = scrapy.Field()              # e.g. "wto.docs.legal"
    scraper = scrapy.Field()           # e.g. "wto_docs"
    version = scrapy.Field()           # package/spider version string
    timestamp = scrapy.Field()         # optional, DB default also fine
    data = scrapy.Field()              # dict/jsonb; include sha256 here

    # Fields for the 'scraper_blob_store' table
    source_file = scrapy.Field()       # bytes (the PDF)
    file_content_type = scrapy.Field() # e.g. "application/pdf"
