import asyncio
import json
from typing import Any, Dict, List
from pathlib import Path
from urllib.parse import quote

from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CrawlerRunConfig,
    CacheMode,
    JsonCssExtractionStrategy,
    CrawlResult,
)

__current_dir = Path(__file__).parent

async def google_search(query: str, browser_config: BrowserConfig) -> tuple[str, List[Dict[str, Any]]]:
    schema = {
        "name": "Google Organic Results",
        "baseSelector": "#rso .MjjYud .tF2Cxc",
        "fields": [
            {
                "name": "title",
                "selector": "h3.LC20lb",
                "type": "text"
            },
            {
                "name": "link",
                "selector": ".yuRUbf a",
                "type": "attribute",
                "attribute": "href"
            },
            {
                "name": "snippet",
                "selector": ".VwiC3b",
                "type": "text",
                "default": ""
            }
        ]
    }
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        crawl_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            extraction_strategy=JsonCssExtractionStrategy(schema),
            delay_before_return_html=2,
        )
        
        result: CrawlResult = await crawler.arun(
            f"https://www.google.com/search?q={quote(query)}&num=10",
            config=crawl_config
        )
        
        organic_results = []
        if result.success and result.extracted_content:
            extracted_data = json.loads(result.extracted_content)
            
            for idx, item in enumerate(extracted_data, 1):
                if item.get("title") and item.get("link"):
                    organic_item = {
                        "title": item["title"],
                        "link": item["link"],
                        "snippet": item.get("snippet", ""),
                        "position": idx
                    }
                    organic_results.append(organic_item)
        
        return query, organic_results

async def search_multiple(queries: List[str]) -> Dict[str, List[Dict[str, Any]]]:
    browser_config = BrowserConfig(headless=True, verbose=True)
    
    search_dir = __current_dir / "search"
    search_dir.mkdir(exist_ok=True)
    
    tasks = [google_search(query, browser_config) for query in queries]
    results = await asyncio.gather(*tasks)
    
    all_results = {}
    for query, organic_results in results:
        all_results[query] = organic_results
        
        filename = query.replace(" ", "_").replace("/", "_")[:50] + ".json"
        filepath = search_dir / filename
        
        with open(filepath, "w") as f:
            f.write(json.dumps(organic_results, indent=2))
        
        print(f"Saved {len(organic_results)} results for '{query}' to search/{filename}")
    
    return all_results

async def demo():
    queries = [
        "apple inc",
        "python programming",
        "machine learning",
        "web scraping",
        "artificial intelligence"
    ]
    
    results = await search_multiple(queries)
    print(f"\nCompleted {len(results)} searches")

if __name__ == "__main__":
    asyncio.run(demo())