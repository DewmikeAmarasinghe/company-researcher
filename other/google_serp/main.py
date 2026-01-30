import asyncio
import json
import re
from pathlib import Path
from urllib.parse import quote_plus, urlparse
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

class CompanyWebsiteDiscoverer:
    
    def __init__(self, company_name, company_website, output_dir="company_data"):
        self.company_name = company_name
        self.company_website = company_website
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.discovered_websites = []
        self.crawled_data = []
    
    async def search_google(self):
        print(f"🔍 Searching Google for: {self.company_name}")
        
        queries = [
            f"{self.company_name} official website",
            f"{self.company_name} products",
            f"{self.company_name} about company",
            f"site:{self.company_website}",
        ]
        
        discovered_urls = set()
        
        browser_config = BrowserConfig(headless=True, verbose=False)
        
        async with AsyncWebCrawler(config=browser_config) as crawler:
            for query in queries:
                print(f"  Searching: {query}")
                search_url = f"https://www.google.com/search?q={quote_plus(query)}"
                
                config = CrawlerRunConfig(
                    cache_mode=CacheMode.BYPASS,
                    word_count_threshold=10
                )
                
                result = await crawler.arun(url=search_url, config=config)
                
                if result.success:
                    urls = self._extract_urls_from_markdown(result.markdown)
                    discovered_urls.update(urls)
                
                await asyncio.sleep(2)
        
        relevant_urls = self._filter_relevant_urls(list(discovered_urls))
        self.discovered_websites = relevant_urls
        
        print(f"✅ Found {len(relevant_urls)} relevant websites")
        return relevant_urls
    
    def _extract_urls_from_markdown(self, markdown_content):
        url_pattern = r'https?://[^\s\)\]<>"]+'
        urls = re.findall(url_pattern, markdown_content)
        
        cleaned_urls = []
        for url in urls:
            url = url.split('&')[0] if '&' in url else url
            cleaned_urls.append(url)
        
        return list(set(cleaned_urls))
    
    def _filter_relevant_urls(self, urls):
        skip_domains = [
            'facebook.com', 'twitter.com', 'linkedin.com', 'instagram.com',
            'youtube.com', 'google.com', 'reddit.com', 'wikipedia.org'
        ]
        
        filtered_urls = []
        company_domain = self.company_website.replace('www.', '').replace('https://', '').replace('http://', '')
        company_keywords = set(self.company_name.lower().split())
        
        for url in urls:
            if any(domain in url.lower() for domain in skip_domains):
                continue
            
            parsed = urlparse(url)
            domain = parsed.netloc.lower().replace('www.', '')
            
            score = 0
            if company_domain in domain:
                score += 100
            if any(keyword in url.lower() for keyword in company_keywords):
                score += 50
            
            if score > 0 or len(filtered_urls) < 15:
                filtered_urls.append((score, url))
        
        filtered_urls.sort(reverse=True, key=lambda x: x[0])
        return [url for score, url in filtered_urls[:15]]
    
    async def crawl_discovered_websites(self, urls=None):
        if urls is None:
            urls = self.discovered_websites
        
        if not urls:
            print("❌ No URLs to crawl")
            return []
        
        print(f"\n🕷️  Crawling {len(urls)} websites...")
        
        browser_config = BrowserConfig(headless=True, verbose=False)
        crawl_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            word_count_threshold=50
        )
        
        results = []
        
        async with AsyncWebCrawler(config=browser_config) as crawler:
            for i, url in enumerate(urls, 1):
                print(f"  [{i}/{len(urls)}] Crawling: {url}")
                
                try:
                    result = await crawler.arun(url=url, config=crawl_config)
                    
                    if result.success:
                        url_slug = urlparse(url).netloc.replace('.', '_')
                        md_filename = self.output_dir / f"{url_slug}.md"
                        
                        with open(md_filename, 'w', encoding='utf-8') as f:
                            f.write(f"# {result.metadata.get('title', 'Untitled')}\n\n")
                            f.write(f"**URL**: {url}\n\n")
                            f.write("---\n\n")
                            f.write(result.markdown)
                        
                        results.append({
                            'url': url,
                            'title': result.metadata.get('title', 'Untitled'),
                            'markdown_file': str(md_filename),
                            'success': True
                        })
                        
                        print(f"    ✅ Saved to: {md_filename}")
                    else:
                        print(f"    ❌ Failed")
                        results.append({'url': url, 'success': False})
                
                except Exception as e:
                    print(f"    ❌ Error: {str(e)}")
                    results.append({'url': url, 'success': False})
                
                await asyncio.sleep(1)
        
        self.crawled_data = results
        
        summary_path = self.output_dir / "crawl_summary.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump({
                'company_name': self.company_name,
                'company_website': self.company_website,
                'total_urls_crawled': len(results),
                'successful_crawls': sum(1 for r in results if r['success']),
                'results': results
            }, f, indent=2)
        
        print(f"\n✅ Crawling complete!")
        print(f"📊 Successfully crawled: {sum(1 for r in results if r['success'])}/{len(results)}")
        print(f"💾 Summary saved to: {summary_path}")
        
        return results


async def main():
    discoverer = CompanyWebsiteDiscoverer(
        company_name="Tesla",
        company_website="tesla.com",
        output_dir="tesla_data"
        # company_name="ceylon cold stores",
        # company_website="https://www.elephanthouse.lk",
        # output_dir="elephant_house"
    )
    
    urls = await discoverer.search_google()
    
    if urls:
        results = await discoverer.crawl_discovered_websites(urls)
    
    print("\n✨ All done!")


if __name__ == "__main__":
    asyncio.run(main())