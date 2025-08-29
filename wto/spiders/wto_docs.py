#FILE wto/spiders/wto_docs.py
import re
import scrapy
from urllib.parse import urljoin
from scrapy.http import FormRequest
from scrapy_playwright.page import PageMethod
from wto.items import WtoDocumentItem

JS_OPEN_RX = re.compile(r"window\.open\('([^']+)'")

class WtoDocsSpider(scrapy.Spider):
    name = "wto_docs"
    allowed_domains = ["docs.wto.org"]
    start_urls = [
        "https://docs.wto.org/dol2fe/Pages/FE_Search/FE_S_S006.aspx?MetaCollection=WTO&TypeList=%22Decision%22&Language=ENGLISH&SearchPage=FE_S_S001&languageUIChanged=true"
    ]

    # helpers
    def _extract_postback(self, js: str):
        m = re.search(r"__doPostBack\('([^']*)','([^']*)'", js or "")
        return (m.group(1), m.group(2)) if m else (None, None)

    def _id_to_target(self, html_id: str | None) -> str | None:
        return html_id.replace("_", "$") if html_id else None

    def _postback(self, response, target: str, arg: str = "", cb=None, meta=None):
        formdata = {
            "__EVENTTARGET": target,
            "__EVENTARGUMENT": arg,
            "__VIEWSTATE": response.xpath("//input[@id='__VIEWSTATE']/@value").get(""),
            "__VIEWSTATEGENERATOR": response.xpath("//input[@id='__VIEWSTATEGENERATOR']/@value").get(""),
            "__EVENTVALIDATION": response.xpath("//input[@id='__EVENTVALIDATION']/@value").get(""),
        }
        return FormRequest.from_response(
            response,
            formxpath="//form[@id='aspnetForm']",
            formdata=formdata,
            dont_filter=True,
            meta={
                "playwright": True,
                "playwright_page_methods": [
                    PageMethod("wait_for_load_state", "domcontentloaded"),
                    PageMethod(
                        "evaluate",
                        "(()=>{const b=document.querySelector('#onetrust-accept-btn-handler'); if(b) b.click();})()",
                    ),
                    PageMethod(
                        "wait_for_function",
                        """
                        () => {
                          const hasRows = document.querySelectorAll('#ctl00_MainPlaceHolder_dtlDocs a[id*="LinkButton2"]').length>0;
                          const hasPager = !!document.querySelector('#ctl00_MainPlaceHolder_lnkNext');
                          return hasRows || hasPager;
                        }
                        """,
                        timeout=90000,
                    ),
                ],
                **(meta or {}),
            },
            callback=cb,
        )

    # entry
    async def start(self):
        yield scrapy.Request(
            self.start_urls[0],
            meta={
                "playwright": True,
                "playwright_page_methods": [
                    PageMethod("wait_for_load_state", "domcontentloaded"),
                    PageMethod(
                        "evaluate",
                        "(()=>{const b=document.querySelector('#onetrust-accept-btn-handler'); if(b) b.click();})()",
                    ),
                    PageMethod(
                        "wait_for_function",
                        """
                        () => {
                          const hasRows = document.querySelectorAll('#ctl00_MainPlaceHolder_dtlDocs a[id*="LinkButton2"]').length>0;
                          const hasPager = !!document.querySelector('#ctl00_MainPlaceHolder_lnkNext');
                          return hasRows || hasPager;
                        }
                        """,
                        timeout=90000,
                    ),
                ],
            },
            callback=self.parse_results,
        )

    # results page 
    def parse_results(self, response):
        # 1) Queue “All files >>” postbacks
        all_files_links = response.xpath(
            "//a[starts-with(@id,'ctl00_MainPlaceHolder_dtlDocs_') and contains(@id,'_LinkButton2')]/@href"
        ).getall()
        self.logger.info("Found %d 'All files' links on page", len(all_files_links))

        for js in all_files_links:
            target, arg = self._extract_postback(js)
            if target:
                yield self._postback(response, target, arg or "", cb=self.parse_all_files)

        # 2) queue catalogue popups for metadata
        for onclick in response.xpath("//img[@title='Open catalogue record']/parent::a[@onclick]/@onclick").getall():
            m = JS_OPEN_RX.search(onclick)
            if m:
                cat_url = urljoin(response.url, m.group(1))
                yield scrapy.Request(
                    cat_url,
                    meta={
                        "playwright": True,
                        "playwright_page_methods": [PageMethod("wait_for_load_state", "domcontentloaded")],
                    },
                    callback=self.parse_catalogue,
                )

        # 3) Paginate via Next
        next_el = response.xpath("//a[@id='ctl00_MainPlaceHolder_lnkNext']")
        if next_el:
            href_or_onclick = next_el.xpath("./@href | ./@onclick").get("")
            target, arg = self._extract_postback(href_or_onclick)
            if not target:
                target = self._id_to_target(next_el.xpath("./@id").get())
                arg = ""
            is_disabled = next_el.xpath("@disabled or contains(@class,'aspNetDisabled')").get()
            if not is_disabled and target:
                self.logger.info("Paginating: %s %s", target, arg)
                yield self._postback(response, target, arg or "", cb=self.parse_results)
            else:
                self.logger.info("Reached last page.")
        else:
            self.logger.info("No Next link found.")

    # S007 “All files” page
    def parse_all_files(self, response):
        # Primary: anchors rendered on S007
        pdf_links = response.xpath(
            "//a[contains(@class,'FEFileNameLinkResultsCss') and "
            "contains(translate(@href,'PDF','pdf'), '.pdf')]/@href"
        ).getall()

        # Fallback: any .pdf links on the page
        if not pdf_links:
            pdf_links = response.xpath("//a[contains(translate(@href,'PDF','pdf'), '.pdf')]/@href").getall()

        if not pdf_links:
            self.logger.warning("No PDF links on %s", response.url)
            return

        for href in pdf_links:
            url = urljoin(response.url, href)
            yield scrapy.Request(
                url,
                meta={
                    "playwright": True,  # keep Playwright cookies for the file request
                    "playwright_page_methods": [PageMethod("wait_for_load_state", "networkidle")],
                },
                headers={"Referer": response.url},
                callback=self.download_file,
                dont_filter=True,
            )

    # catalogue page (optional)
    def parse_catalogue(self, response):
        meta = {}
        for row in response.xpath("//table//tr[td]"):
            key = row.xpath("normalize-space(td[1]//text())").get("").strip(" :\u00a0")
            if not key:
                continue
            val = row.xpath("normalize-space(string(td[position()>1]))").get("").strip()
            if val:
                meta[key] = val
        # will store/merge this metadata.

    # final file
    def download_file(self, response):
        ctype = response.headers.get(b"Content-Type", b"application/pdf").decode("latin1")
        if ctype.startswith("text/html"):
            self.logger.warning("HTML instead of file at %s; skipping bytes.", response.url)
            item = WtoDocumentItem(url=response.url)
            yield item
            return

        item = WtoDocumentItem()
        item["url"] = response.url
        item["file_content_type"] = ctype
        # Set both keys so the pipeline can compute sha256 either way
        item["source_file"] = response.body
        item["file_bytes"] = response.body
        yield item
