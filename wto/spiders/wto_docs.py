import scrapy
import hashlib
import uuid
from scrapy_playwright.page import PageMethod
from typing import Optional, Tuple
import re

class WTODecisionsSpider(scrapy.Spider):
    name = "wto_docs"

    start_urls = [
        "https://docs.wto.org/dol2fe/Pages/FE_Search/FE_S_S006.aspx?MetaCollection=WTO&TypeList=%22Legal+instrument+(Agreement%2c+Protocol%2c+Treaty-related+communications%2c+Legal+text%2c+Charter%2c+Understanding)%22&RestrictionTypeName=%22U%22+OR+%22D%22&Language=ENGLISH&SearchPage=FE_S_S001&languageUIChanged=true#"
    ]
    
    _last_page_sig: Optional[Tuple[int, int]] = None
    _repeat_guard: int = 0
    _consecutive_no_items: int = 0

    def start_requests(self):
        """
        Initializes the first request to the start URL with Playwright enabled.
        """
        yield scrapy.Request(
            self.start_urls[0],
            meta={
                "playwright": True,
                "playwright_page_methods": [
                    PageMethod("wait_for_selector", ".hitContainer"),
                ],
                "page_number": 1,
            },
            callback=self.parse,
        )

    def parse(self, response):
        """
        Parses the search results page, extracts document links,
        and handles pagination.
        """
        page_number = response.meta.get("page_number", 1)
        self.logger.info(f"📄 Scraping page {page_number}")

        # Check for infinite loop by monitoring the "Displaying X-Y of Z" text
        start_end = self._extract_displaying_range(response)
        total_count = self._extract_total_count(response)
        if start_end:
            if start_end == self._last_page_sig:
                self._repeat_guard += 1
            else:
                self._repeat_guard = 0
            self._last_page_sig = start_end
            if self._repeat_guard >= 3:
                self.logger.error("Stuck on the same page segment repeatedly; stopping to prevent a crawl loop.")
                return

        # Scrape documents from the current page
        documents = response.xpath("//div[contains(@class,'hitContainer')]")
        self.logger.info(f"Found {len(documents)} documents on page {page_number}")
        if not documents:
            self._consecutive_no_items += 1
            if self._consecutive_no_items >= 2:
                self.logger.info("Consecutive pages with no items. Assuming end of results.")
                return
        else:
            self._consecutive_no_items = 0

        yielded_this_page = 0
        for document in documents:
            # Title
            title = document.xpath(".//div[contains(@class,'hitTitle')]//span[@title='Document title']/text()").get()
            # Symbol
            symbol = document.xpath(".//div[@class='hitContainer']/div[@class='hitSymbol']").get()
            # Date (grab any detail text containing a year-like date)
            date = document.xpath(
                ".//div[@class='hitDetail']//text()[contains(., '/20') or contains(., '/19')]"
            ).get()
            # English link
            english_link = document.xpath(
                ".//div[contains(@class, 'hitEnFileLink')]//a[contains(@class, 'FEFileNameLinkResultsCss')]/@href"
            ).get()

            if english_link:
                full_url = response.urljoin(english_link)
                item = {
                    "name": (title or "").strip(),
                    "url": full_url,
                    "data": {"symbol": (symbol or "").strip(), "date": (date or "").strip()},
                    "scraper": self.name,
                    "version": "1.0",
                }
                yield scrapy.Request(full_url, meta={"item": item}, callback=self.parse_document, dont_filter=True)
                yielded_this_page += 1
            else:
                self.logger.warning(f"No English link found for document with title: {title}")

        self.logger.info(f"Yielded {yielded_this_page} items from page {page_number}")

        # Pagination Logic
        next_btn_xpath = "//a[@id='ctl00_MainPlaceHolder_lnkNext']"
        next_btn = response.xpath(next_btn_xpath)
        next_btn_disabled_attr = next_btn.xpath("@disabled").get()
        next_btn_href = next_btn.xpath("@href").get()

        has_next = bool(next_btn) and next_btn_disabled_attr is None and next_btn_href and "__doPostBack" in next_btn_href
        
        info_text = response.xpath("//span[@id='ctl00_MainPlaceHolder_lblInfo']/text()").get() or ""
        self.logger.info(f"Results label: '{info_text}' (parsed={start_end}, total={total_count})")

        should_paginate = has_next or (start_end is not None and total_count is not None and start_end[1] < total_count)
        
        if should_paginate:
            next_page_num = page_number + 1
            self.logger.info(
                f"➡️ Advancing to page {next_page_num} (has_next={has_next}, displaying={start_end}, total={total_count})"
            )
            
            yield scrapy.FormRequest.from_response(
                response,
                formxpath="//form",
                formdata={
                    "__EVENTTARGET": "ctl00$MainPlaceHolder$lnkNext",
                    "__EVENTARGUMENT": "",
                },
                dont_filter=True,
                callback=self.parse,
                meta={
                    "page_number": next_page_num,
                    "playwright": True,
                    "playwright_page_methods": [
                        PageMethod("wait_for_selector", ".hitContainer"),
                    ],
                },
            )
        else:
            self.logger.info("✅ No more pages — finished.")

    def parse_document(self, response):
        """
        Downloads the document and adds it to the item.
        """
        item = response.meta["item"]
        item["source_file"] = response.body
        item["file_content_type"] = response.headers.get("Content-Type").decode("utf-8")
        item["doc_uuid"] = hashlib.sha256(item["source_file"]).hexdigest()
        yield item

    def _extract_displaying_range(self, response):
        """
        Helper method to extract the "Displaying X-Y of Z" numbers for the repeat guard.
        """
        text = response.xpath("//span[@id='ctl00_MainPlaceHolder_lblInfo']/text()").get()
        if text:
            match = re.search(r"Displaying (\d+)-(\d+)", text)
            if match:
                return int(match.group(1)), int(match.group(2))
        return None

    def _extract_total_count(self, response):
        """Extract total count Z from the label 'Displaying X-Y of Z'."""
        text = response.xpath("//span[@id='ctl00_MainPlaceHolder_lblInfo']/text()").get()
        if text:
            match = re.search(r"of (\d+)", text)
            if match:
                return int(match.group(1))
        return None