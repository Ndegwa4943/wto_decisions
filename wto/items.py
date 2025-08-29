# wto_scraper/items.py

import scrapy

class WtoDocumentItem(scrapy.Item):
    # Fields for the 'documents' table
    url = scrapy.Field()
    scraper = scrapy.Field()
    version = scrapy.Field()
    file_bytes = scrapy.Field()  
    name = scrapy.Field()
    timestamp = scrapy.Field()
    data = scrapy.Field() # This will be a dictionary
    
    # Fields for the 'scraper_blob_store' table
    source_file = scrapy.Field() # This will hold the binary file data
    file_content_type = scrapy.Field()
    