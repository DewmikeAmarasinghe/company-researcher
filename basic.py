from crawl4ai import AsyncWebCrawler, UndetectedAdapter
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
import asyncio
import os

async def crawl_company(company_name: str, url: str):
    browser_config = BrowserConfig(
        headless=False,
    )


    async with AsyncWebCrawler(config=browser_config) as crawler:

        run_config = CrawlerRunConfig(
            delay_before_return_html=3,
            scan_full_page=True,
            exclude_internal_links=False,
            exclude_external_links=False,
            exclude_social_media_links=False,
            excluded_tags=['header', 'footer', 'form', 'nav', 'aside', 'script', 'style'],
            keep_data_attributes=True,
            remove_overlay_elements=True,
            # process_iframes=True,
            exclude_external_images=True,
            cache_mode=CacheMode.BYPASS,
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
        )

        results = await crawler.arun(url, run_config)

        return results

async def main():
    company = "hsenidmobile"
    urls = [
        "https://hsenidmobile.com/about-us",
        "https://hsenidmobile.com/",
        "https://hsenidmobile.com/contact",
        "https://hsenidmobile.com/talk-to-an-expert",
    ]
    # company = "Mintpay (Pvt) Ltd."
    # urls = [
    #     "https://mintpay.lk/",
    #     "https://mintpay.lk/business",
    #     "https://mintpay.lk/press",
    #     "https://mintpay.lk/terms",
    #     "https://mintpay.lk/policy",
    #     "https://mintpay.lk/support",
    #     "https://merchant.mintpay.lk/"
    # ]
    # company = "AOD South Asia (Pvt) Ltd"
    # urls = [
    #     "https://www.aod.lk/pages/about-us",
    #     "https://www.aod.lk/pages/aod-northumbria-a-powerful-partnership-for-design",
    #     "https://www.aod.lk/pages/industry-testimonials",
    #     "https://www.aod.lk/pages/location",
    #     "https://www.aod.lk/blogs/news",
    #     "https://www.facebook.com/AODSrilanka",
    #     "https://www.instagram.com/aod_design",
    #     "https://www.linkedin.com/school/aod/posts?feedview=all"
    # ]
    result = await crawl_company(company, urls[0])
    print(result.markdown)


if __name__ == "__main__":
    asyncio.run(main())
