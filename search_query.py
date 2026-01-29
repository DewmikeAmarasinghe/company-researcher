from crawl4ai import AsyncWebCrawler, UndetectedAdapter
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from urllib.parse import quote_plus
import asyncio
import json
from utils import is_social_media_url
from config import DELAY_BETWEEN_QUERIES, BROWSER_HEADLESS, ENABLE_STEALTH

async def search_google_by_category(queries: dict) -> dict:
    browser_config = BrowserConfig(
        headless=BROWSER_HEADLESS,
        enable_stealth=ENABLE_STEALTH
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
            exclude_internal_links=True,
            exclude_external_links=False,
            exclude_social_media_links=False,
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

        results_by_category = {}

        for category, query in queries.items():
            url = f"https://www.google.com/search?q={quote_plus(query)}&udm=50"
            result = await crawler.arun(url, run_config)

            # category_urls = []
            # if result and result.success:
            #     external = result.links.get("external", [])
            #     seen = set()
                
            #     for link in external:
            #         link_url = link["href"]
            #         if link_url.startswith(("http://", "https://")) and link_url not in seen and not is_social_media_url(link_url):
            #             seen.add(link_url)
            #             category_urls.append(link_url)
            
            # results_by_category[category] = category_urls
            # print(f"Found {len(category_urls)} URLs for: {category}")
            
            # if list(queries.keys()).index(category) < len(queries) - 1:
            #     await asyncio.sleep(DELAY_BETWEEN_QUERIES)
            print(result.markdown)

        return results_by_category


async def main():
    # company_name = "hSenid Mobile Solutions (Pvt) Ltd"
    # location = "Sri Lanka"

    company_name = "AOD South Asia (Pvt) Ltd"
    location = "Sri Lanka"
    
    queries = {
        "Founders and Leadership": f"who founded {company_name} in {location} and who is the current CEO leadership team, there company website url is https://www.aod.lk/",
        # "Products and Services": f"{company_name} {location} products services offerings",
        # "Contact Information": f"{company_name} {location} contact location address",
    }

    print(f"Searching Google for {len(queries)} categories with {DELAY_BETWEEN_QUERIES}s delay...")
    results = await search_google_by_category(queries)
    
    print("\nResults by category:")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
