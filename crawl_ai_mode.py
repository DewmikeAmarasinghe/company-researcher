import asyncio
from urllib.parse import quote_plus
from crawl4ai import AsyncWebCrawler, UndetectedAdapter
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator


async def crawl_google_ai_mode(query: str):
    encoded_query = quote_plus(query)
    url = f"https://www.google.com/search?q={encoded_query}&udm=50"

    browser_config = BrowserConfig(
        headless=False,
    )

    run_cfg = CrawlerRunConfig(
        delay_before_return_html=5,
        scan_full_page=True,
        exclude_internal_links=True,
        exclude_external_links=False,
        exclude_social_media_links=False,
        excluded_tags=['header', 'footer', 'form', 'nav', 'aside', 'script', 'style'],
        keep_data_attributes=True,
        process_iframes=True,
        exclude_external_images=True,
        markdown_generator=DefaultMarkdownGenerator(
            content_filter=PruningContentFilter(
                threshold=0.5, threshold_type="fixed"
            ),
            options={
                "ignore_links": True,
                "ignore_images": True,
                "escape_html": True,
                "include_sup_sub": True,
            },
        ),
        target_elements=[
            'div[data-container-id="main-col"]'
        ]
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
        result = await crawler.arun(url, config=run_cfg)

    return result


if __name__ == "__main__":
    query = "who are the founders and the current leadership of hsenidmobile solutions company"
    query = "what is the revenue model of the hsenidmobile solutions company"
    query = "what are the products and services currently sold by hsenidmobile company sri lanka"
    crawl_result = asyncio.run(crawl_google_ai_mode(query))

    print(len(crawl_result.markdown))
    print(crawl_result.markdown)
    print("\n\n\n", crawl_result.links)