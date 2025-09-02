#FILE wto/spiders/wto_docs.py
import scrapy
import re
from ..items import WtoDocumentItem
from scrapy_playwright.page import PageMethod

class WtoDocsSpider(scrapy.Spider):
    name = "wto_docs"
    allowed_domains = ["docs.wto.org"]
    start_urls = ["https://docs.wto.org/dol2fe/Pages/FE_Browse/FE_B_009.aspx"] # The "By topic" page

    def parse(self, response):
        formdata = {
            "__EVENTTARGET": "ctl00$MainPlaceHolder$dlTopLevel$ctl15$OpenTreePreview",
            "__EVENTARGUMENT": ""
        }

        yield scrapy.FormRequest.from_response(
            response,
            formdata=formdata,
            callback=self.parse_subcategories,
            meta={
                "playwright": True,
                "playwright_page_methods": [
                    PageMethod("wait_for_selector", "a[href*='__doPostBack']")
                ]
            }
        )

    def parse_subcategories(self, response):
        with open("subcategory_debug.html", "w", encoding="utf-8") as f:
            f.write(response.text)
        """
        Parses the page with the blue sub-category links and follows each of them.
        """
        subcategory_links = response.xpath("//a[contains(@href, '__doPostBack')]")
        self.logger.info(f"Found {len(subcategory_links)} subcategory links on {response.url}")
        if not subcategory_links:
            self.logger.warning("No subcategory links found! Check your XPath or page structure.")

        for link in subcategory_links:
            onclick_attr = link.xpath(".//@onclick").get() or ""
            nodeclient_match = re.search(r"NodeClientClicked\('(.+?)'\)", onclick_attr)
            if nodeclient_match:
                url_to_follow = nodeclient_match.group(1)
                yield response.follow(
                    url_to_follow,
                    callback=self.parse_document_list,
                    meta={"playwright": True}
                )

    def parse_document_list(self, response):
        with open("document_list_debug.html", "w", encoding="utf-8") as f:
            f.write(response.text)
        """
        Parses the final page with the list of documents, extracts the required data,
        and yields an item for each one.
        """
        # XPath to select each document entry on the page.
        document_entries = response.xpath("//div[contains(@class, 'hitContainer')]")
        
        if not document_entries:
            self.logger.warning("No document entries found on %s", response.url)
        
        for entry in document_entries:
            item = WtoDocumentItem()
            
            # Extract the name, URL, and other data fields
            item['name'] = entry.xpath(".//div[contains(@class, 'hitTitle')]//span[@title='Document title']/text()").get()
            if not item['name']:
                # Fallback: get text within the hitTitle div
                item['name'] = entry.xpath(".//div[contains(@class, 'hitTitle')]//span/text()").get() or entry.xpath(".//div[contains(@class, 'hitTitle')]/text()").get()
            
            file_url = entry.xpath(".//a[@class='FEFileNameLinkResultsCss']/@href").get()

            if file_url:
                full_file_url = response.urljoin(file_url)
                item['file_urls'] = [full_file_url]
            else:
                item['file_urls'] = []

            # 'data' contains document metadata: 
            #   'symbol': the document symbol (str or None)
            #   'date': the document date (str or None)
            # TODO: Add SHA256 hash of the PDF content after downloading
            symbol = entry.xpath(".//a[@class='FECatalogueSymbolPreviewCss']/text()").get()
            date = entry.xpath(".//span[@id='ctl00_MainPlaceHolder_dtlDocs_ctl00_lbl023']/text()").get()
            
            item['data'] = {'symbol': symbol, 'date': date}
            # 'scraper' will be set to the spider's name, which is "wto_docs"
            item['scraper'] = self.name
            item['version'] = '1.0'
            item['url'] = full_file_url if file_url else None

            yield item

