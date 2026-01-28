import asyncio
import json
import time
from pathlib import Path

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig, UndetectedAdapter, CacheMode
from crawl4ai.deep_crawling import BestFirstCrawlingStrategy
from crawl4ai.deep_crawling.filters import DomainFilter, FilterChain, URLPatternFilter
from crawl4ai.deep_crawling.scorers import KeywordRelevanceScorer
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy


async def crawl_company_website(start_url):
    start_time = time.perf_counter()

    scorer = KeywordRelevanceScorer(
        keywords=[
            "about","company","mission","description","leadership","team","ceo",
            "founder","products","services","pricing","plans","competitors",
            "alternatives","technology","stack","customers","testimonials","reviews",
            "case-studies","news","press","funding","investors","contact","hq",
            "headquarters","location","size","employees","founded"
        ],
        weight=0.7
    )

    include_filter = URLPatternFilter(patterns=[
        "*about*","*team*","*leadership*","*products*","*services*","*pricing*",
        "*features*","*competitors*","*tech*","*stack*","*customers*","*testimonials*",
        "*reviews*","*case-studies*","*news*","*press*","*media*","*investors*",
        "*funding*","*contact*","*careers*","*jobs*","*home*"
    ])

    domain = start_url.split("//")[1].split("/")[0]
    filter_chain = FilterChain([DomainFilter([domain]), include_filter])

    md_gen = DefaultMarkdownGenerator(
        content_filter=PruningContentFilter(
            threshold=0.45, 
            threshold_type="fixed"
        ),
        options={
            "ignore_links": True,
            "escape_html": True
        },
    )

    strategy = BestFirstCrawlingStrategy(
        max_depth=2,
        include_external=True,
        filter_chain=filter_chain,
        url_scorer=scorer,
        max_pages=50
    )

    run_cfg = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        deep_crawl_strategy=strategy,
        exclude_external_links=True,
        exclude_social_media_links=False,
        # process_iframes=True,
        # remove_overlay_elements=True,
        # excluded_tags=["nav", "footer"],
        wait_until="domcontentloaded",
        exclude_all_images=True,
        # word_count_threshold=50,
        markdown_generator=md_gen,
    )

    browser_config = BrowserConfig(
        headless=True, 
        verbose=False,
        enable_stealth=True,
        extra_args=["--disable-blink-features=AutomationControlled"],
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
        results = await crawler.arun(start_url, config=run_cfg)

    elapsed = time.perf_counter() - start_time

    crawled_urls = []
    relevant_pages = []
    total_chars = 0

    for r in results:
        crawled_urls.append(r.url)

        markdown = r.markdown or ""
        md_len = len(markdown)
        total_chars += md_len

        if md_len > 0:
            relevant_pages.append({
                "url": r.url,
                "markdown_length": md_len,
                "content": markdown
            })

    output = {
        "start_url": start_url,
        "crawled_urls": crawled_urls,
        "confidence": None,
        "pages_crawled": len(crawled_urls),
        "total_content_chars": total_chars,
        "elapsed_time": elapsed,
        "relevant_pages": relevant_pages
    }

    return output


if __name__ == "__main__":
    start_url = "https://hsenidmobile.com/"
    # start_url = "https://www.apple.com/"
    data = asyncio.run(crawl_company_website(start_url))
    Path("results").mkdir(exist_ok=True)
    with open(Path("results") / "crawled_data.json","w",encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
