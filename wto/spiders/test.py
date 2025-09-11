import scrapy

class TestSpider(scrapy.Spider):
    name = "test_playwright"

    def start_requests(self):
        yield scrapy.Request(
            "https://example.com",
            meta={"playwright": True},
            callback=self.parse,
        )

    async def parse(self, response):
        page = response.meta["playwright_page"]
        title = await page.title()
        self.logger.info(f"Page title: {title}")
        await page.close()
