
import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig


async def main():
    browser_config = BrowserConfig()
    run_config = CrawlerRunConfig()

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url="https://www.google.com/search?aep=1&fbs=ADc_l-aN0CWEZBOHjofHoaMMDiKpaEWjvZ2Py1XXV8d8KvlI3ppPEReeCOS7s1VbbZz2TLsHwpSX8VU1h5wlQRdyYz8mo-EfBnr_ahtOZYiF6Te-Qu9ygxN1-c4kTmc7m8dItcyjxGI9WCRBhTLMXfRXMS1dhR8jazxhaudxS5WEJBOp9G6ATOoQlGZz0RPY0_96eMV3lKLrhCZ0Y3kb6a4UBH0IQs8rzQ&ntc=1&q=apple&sa=X&sca_esv=3236b0192813a1a3&udm=50&ved=2ahUKEwiC0db0_KCSAxVrTmwGHaRyO4kQ2J8OegQIGRAE&mstk=AUtExfBWBNdO5YE2iD4294CDIhKiH1E5jdw0henrs795_NfEZpaQ3_RQmxgtOipWCVDBDCqdXX2K4BqITRFePUJxj2YGJ6sw7G7t4X2R-u8tzLPdK5PU6fseY5z61iwj8Wqdim6XNRgeuhbgQdLXYiZXHpR3xkbUThpfI7mWRj515W5hUQLFw4dWKZsrw7LO1P3BzsSBsfwpLq9wvo7cQK3bXMWtXDsjh-m29ybPngRCQn2QjUdJIx6PkVtfTQ&csuir=1",
            config=run_config,
        )
       

        print(result.markdown)


if __name__ == "__main__":
    asyncio.run(main())
