import asyncio
import json
from litellm import completion
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig
from google_search import search_google_by_category
from utils import is_social_media_url, ensure_company_directories
from config import API_KEY, MODEL_NAME, get_enabled_categories, get_search_queries
from prompts import get_url_selection_prompt

async def discover_company_urls(company_name: str, base_url: str, location: str = "") -> dict:
    print(f"Crawling base URL: {base_url}")
    async with AsyncWebCrawler(config=BrowserConfig()) as crawler:
        result = await crawler.arun(url=base_url, config=CrawlerRunConfig())
    
    website_urls = []
    for category, items in result.links.items():
        for link in items:
            url = link["href"]
            if url.startswith(("http://", "https://")) and url not in website_urls and not is_social_media_url(url):
                website_urls.append(url)
    
    print(f"Searching Google for {company_name}...")
    
    search_queries = get_search_queries(company_name, location)
    google_results = await search_google_by_category(search_queries)
    
    print(f"\n{'='*60}")
    print(f"AI is selecting relevant URLs from {len(website_urls)} website URLs and {len(google_results)} search categories...")
    print(f"{'='*60}\n")
    
    prompt = get_url_selection_prompt(company_name, base_url, website_urls, google_results)

    response = completion(
        model=MODEL_NAME,
        api_key=API_KEY,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    
    content_json = json.loads(response["choices"][0]["message"]["content"])
    
    enabled_categories = get_enabled_categories()
    
    selected_urls = {}
    for category in enabled_categories:
        selected_urls[category] = content_json.get(category, [])
    
    all_selected = []
    for urls in selected_urls.values():
        all_selected.extend(urls)
    
    url_pool = {}
    for category in enabled_categories:
        pool = []
        category_google = google_results.get(category, [])
        
        for url in category_google:
            if url not in all_selected:
                pool.append(url)
        
        url_pool[category] = pool
    
    total_selected = sum(len(urls) for urls in selected_urls.values())
    total_pool = sum(len(urls) for urls in url_pool.values())
    
    return {
        "company_name": company_name,
        "base_url": base_url,
        "location": location,
        "stats": {
            "total_selected": total_selected,
            "total_pool": total_pool,
            "website_urls_found": len(website_urls),
            "categories": len(enabled_categories)
        },
        "selected_urls": selected_urls,
        "url_pool": url_pool,
        "sources": {
            "website_urls": website_urls,
            "google_results_by_category": google_results
        }
    }

def save_output(company_name: str, data: dict):
    base_path = ensure_company_directories(company_name)
    filename = f"{base_path}/links.json"
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
    
    print(f"Results saved to: {filename}")
    print(f"Total selected URLs: {data['stats']['total_selected']}")
    print(f"Total pool URLs: {data['stats']['total_pool']}")


async def main():
    company_name = "AOD South Asia (Pvt) Ltd"
    base_url = "https://www.aod.lk/"
    location = "Sri Lanka"

    output = await discover_company_urls(
        company_name=company_name,
        base_url=base_url,
        location=location
    )
    save_output(company_name, output)


if __name__ == "__main__":
    asyncio.run(main())
