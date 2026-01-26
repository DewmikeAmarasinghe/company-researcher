from crawl4ai import AsyncWebCrawler, UndetectedAdapter
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
import asyncio
import os

async def crawl_company(company_name: str, urls: list[str]):
    browser_config = BrowserConfig(
        headless=True,
    )

    undetected_adapter = UndetectedAdapter()

    crawler_strategy = AsyncPlaywrightCrawlerStrategy(
        browser_config=browser_config,
        browser_adapter=undetected_adapter
    )

    async with AsyncWebCrawler(
        crawler_strategy=crawler_strategy,
        config=browser_config
    ) as crawler:

        run_config = CrawlerRunConfig(
            delay_before_return_html=5,
            scan_full_page=True,
            # exclude_internal_links=False,
            # exclude_external_links=False,
            # exclude_social_media_links=False,
            excluded_tags=['header', 'footer', 'form', 'nav', 'aside', 'script', 'style'],
            keep_data_attributes=True,
            process_iframes=True,
            exclude_external_images=True,
            cache_mode=CacheMode.BYPASS,
            markdown_generator=DefaultMarkdownGenerator(
                content_filter=PruningContentFilter(
                    threshold=0.5, threshold_type="fixed"
                ),
                options={
                    # "ignore_links": True,
                    "ignore_images": True,
                    "escape_html": True,
                    "include_sup_sub": True,
                },
            ),
        )

        results = await crawler.arun_many(urls, run_config)

        base_folder = f"crawled/{company_name}"
        os.makedirs(base_folder, exist_ok=True)

        for url, result in zip(urls, results):
            if result and result.success:
                md = result.markdown
                print(url, "len:", len(md))

                from urllib.parse import urlparse
                parsed = urlparse(url)
                filename = parsed.netloc + parsed.path
                filename = filename.replace("/", "__").strip("_")
                filepath = f"{base_folder}/{filename}.md"

                with open(filepath, "w") as f:
                    f.write(md)

                print("saved:", filepath)
            else:
                print("failed:", url)



async def main():
    company = "hSenidMobile"
    urls = [
        "https://hsenidmobile.com/",
        "https://hsenidmobile.com/about-us",
        "https://hsenidmobile.com/contact",
        "https://hsenidmobile.com/talk-to-an-expert",
    ]
    await crawl_company(company, urls)


if __name__ == "__main__":
    asyncio.run(main())
