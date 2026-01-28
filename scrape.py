from crawl4ai import AsyncWebCrawler, UndetectedAdapter
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from find_urls import discover_company_urls, save_output
from utils import get_company_path
from config import BROWSER_HEADLESS, ENABLE_STEALTH, SCRAPE_DELAY
import asyncio
import os
import json
from urllib.parse import urlparse

async def scrape_company_urls(company_name: str, base_url: str, location: str, skip_url_discovery: bool = False):
    base_path = get_company_path(company_name)
    links_file = f"{base_path}/links.json"
    
    if skip_url_discovery:
        print(f"Reading URLs from: {links_file}")
        if not os.path.exists(links_file):
            print(f"Error: {links_file} not found. Run with skip_url_discovery=False first.")
            return
        
        with open(links_file, "r") as f:
            url_data = json.load(f)
    else:
        print(f"{'='*60}")
        print(f"Starting URL discovery for {company_name}")
        print(f"{'='*60}\n")
        
        url_data = await discover_company_urls(company_name, base_url, location)
        save_output(company_name, url_data)
    
    all_urls_to_scrape = set()
    url_to_categories = {}
    
    for category, urls in url_data["selected_urls"].items():
        for url in urls:
            all_urls_to_scrape.add(url)
            if url not in url_to_categories:
                url_to_categories[url] = []
            url_to_categories[url].append(category)
    
    print(f"\n{'='*60}")
    print(f"Scraping {len(all_urls_to_scrape)} unique URLs...")
    print(f"{'='*60}\n")
    
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
            delay_before_return_html=SCRAPE_DELAY,
            scan_full_page=True,
            exclude_internal_links=False,
            exclude_external_links=False,
            exclude_social_media_links=False,
            excluded_tags=['header', 'footer', 'form', 'nav', 'aside', 'script', 'style'],
            keep_data_attributes=True,
            remove_overlay_elements=True,
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

        results = await crawler.arun_many(list(all_urls_to_scrape), run_config)

        crawled_folder = f"{base_path}/crawled"
        os.makedirs(crawled_folder, exist_ok=True)

        scraped_data = []
        total_chars = 0
        
        for result in results:
            if result and result.success:
                md = result.markdown
                url = result.url
                
                parsed = urlparse(url)
                filename = parsed.netloc + parsed.path
                filename = filename.replace("/", "__").strip("_")
                filepath = f"{crawled_folder}/{filename}.md"

                with open(filepath, "w") as f:
                    f.write(md)

                categories = url_to_categories.get(url, [])
                char_count = len(md)
                total_chars += char_count
                
                scraped_data.append({
                    "url": url,
                    "filepath": filepath,
                    "categories": categories,
                    "length": char_count
                })
                
                print(f"✓ {url} ({char_count} chars) -> {len(categories)} categories")
            else:
                print(f"✗ Failed: {result.url if result else 'unknown'}")
        
        metadata_file = f"{crawled_folder}/metadata.json"
        with open(metadata_file, "w") as f:
            json.dump({
                "company_name": company_name,
                "base_url": base_url,
                "location": location,
                "stats": {
                    "total_scraped": len(scraped_data),
                    "total_failed": len(all_urls_to_scrape) - len(scraped_data),
                    "total_chars": total_chars
                },
                "scraped_urls": scraped_data,
                "url_to_categories": url_to_categories
            }, f, indent=2)
        
        print(f"\n{'='*60}")
        print("Scraping complete!")
        print(f"Total scraped: {len(scraped_data)}/{len(all_urls_to_scrape)}")
        print(f"Total chars: {total_chars}")
        print(f"Results saved to: {crawled_folder}")
        print(f"Metadata saved to: {metadata_file}")
        print(f"{'='*60}")


async def main():
    # company_name = "hSenid Mobile Solutions (Pvt) Ltd"
    # base_url = "https://hsenidmobile.com/"
    # location = "Sri Lanka"
    
    company_name = "AOD South Asia (Pvt) Ltd"
    base_url = "https://www.aod.lk/"
    location = "Sri Lanka"
    
    await scrape_company_urls(
        company_name=company_name,
        base_url=base_url,
        location=location,
        skip_url_discovery=False
    )


if __name__ == "__main__":
    asyncio.run(main())
