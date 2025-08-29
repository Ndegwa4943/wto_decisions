Sample logs I think are beneficial:
 'url': 'https://docs.wto.org/dol2fe/Pages/SS/directdoc.aspx?filename=Q:/G/C/W875.pdf&Open=True'}
Traceback (most recent call last):
  File "C:\Users\Ndegwa\scraping\wto\venv\Lib\site-packages\scrapy\core\scraper.py", line 387, in start_itemproc
    output = await maybe_deferred_to_future(
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        self.itemproc.process_item(item, self.crawler.spider)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "C:\Users\Ndegwa\scraping\wto\venv\Lib\site-packages\twisted\internet\defer.py", line 1092, in _runCallbacks
    current.result = callback(  # type: ignore[misc]
                     ~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
        current.result, *args, **kwargs
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "C:\Users\Ndegwa\scraping\wto\venv\Lib\site-packages\scrapy\utils\defer.py", line 407, in f
    return deferred_from_coro(coro_f(*coro_args, **coro_kwargs))
                              ~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Ndegwa\scraping\wto\wto\pipelines.py", line 36, in process_item
    sha256_hash = item['data'].get('sha256')
                  ~~~~^^^^^^^^
  File "C:\Users\Ndegwa\scraping\wto\venv\Lib\site-packages\scrapy\item.py", line 92, in __getitem__
    return self._values[key]
           ~~~~~~~~~~~~^^^^^
KeyError: 'data'
2025-08-29 09:13:37 [scrapy-playwright] DEBUG: [Context=default] New page created, page count is 1 (1 for all contexts)

Latest Log stats:
2025-08-29 09:40:16 [scrapy.core.engine] INFO: Closing spider (finished)
2025-08-29 09:40:16 [wto_docs] INFO: SQLAlchemy DB session closed.
2025-08-29 09:40:16 [scrapy.statscollectors] INFO: Dumping Scrapy stats:
{'downloader/request_bytes': 1295890,
 'downloader/request_count': 193,
 'downloader/request_method_count/GET': 185,
 'downloader/request_method_count/POST': 8,
 'downloader/response_bytes': 86342108,
 'downloader/response_count': 193,
 'downloader/response_status_count/200': 193,
 'elapsed_time_seconds': 408.54431,
 'finish_reason': 'finished',
 'finish_time': datetime.datetime(2025, 8, 29, 6, 40, 16, 282016, tzinfo=datetime.timezone.utc),
 'items_per_minute': 0.0,
 'log_count/DEBUG': 2158,
 'log_count/ERROR': 176,
 'log_count/INFO': 31,
 'playwright/browser_count': 2,
 'playwright/context_count': 2,
 'playwright/context_count/max_concurrent': 1,
 'playwright/context_count/persistent/False': 2,
 'playwright/context_count/remote/False': 2,
 'playwright/download_count': 176,
 'playwright/page_count': 193,
 'playwright/page_count/closed': 193,
 'playwright/page_count/max_concurrent': 4,
 'playwright/request_count': 703,
 'playwright/request_count/method/GET': 702,
 'playwright/request_count/method/POST': 1,
 'playwright/request_count/navigation': 193,
 'playwright/request_count/resource_type/document': 193,
 'playwright/request_count/resource_type/image': 162,
 'playwright/request_count/resource_type/script': 65,
 'playwright/request_count/resource_type/stylesheet': 282,
 'playwright/request_count/resource_type/xhr': 1,
 'playwright/response_count': 703,
 'playwright/response_count/method/GET': 694,
 'playwright/response_count/method/POST': 9,
 'playwright/response_count/resource_type/document': 193,
 'playwright/response_count/resource_type/image': 162,
 'playwright/response_count/resource_type/script': 65,
 'playwright/response_count/resource_type/stylesheet': 282,
 'playwright/response_count/resource_type/xhr': 1,
 'request_depth_max': 2,
 'response_received_count': 193,
 'responses_per_minute': 28.38235294117647,
 'scheduler/dequeued': 193,
 'scheduler/dequeued/memory': 193,
 'scheduler/enqueued': 193,
 'scheduler/enqueued/memory': 193,
 'start_time': datetime.datetime(2025, 8, 29, 6, 33, 27, 737706, tzinfo=datetime.timezone.utc)}
2025-08-29 09:40:16 [scrapy.core.engine] INFO: Spider closed (finished)
2025-08-29 09:40:16 [scrapy-playwright] INFO: Closing download handler
2025-08-29 09:40:16 [scrapy-playwright] DEBUG: Browser context closed: 'default' (persistent=False, remote=False)
2025-08-29 09:40:16 [scrapy-playwright] INFO: Closing browser
2025-08-29 09:40:16 [scrapy-playwright] DEBUG: Browser disconnected
2025-08-29 09:40:16 [scrapy-playwright] INFO: Closing download handler
2025-08-29 09:40:16 [scrapy-playwright] DEBUG: Browser context closed: 'default' (persistent=False, remote=False)
2025-08-29 09:40:16 [scrapy-playwright] INFO: Closing browser
2025-08-29 09:40:16 [scrapy-playwright] DEBUG: Browser disconnected
(venv) PS C:\Users\Ndegwa\scraping\wto> 