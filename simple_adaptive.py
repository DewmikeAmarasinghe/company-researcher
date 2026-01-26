import asyncio
import json
import time
from pathlib import Path
from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CrawlerRunConfig,
    AdaptiveCrawler,
    AdaptiveConfig,
    UndetectedAdapter,
    DefaultMarkdownGenerator,
    PruningContentFilter
)
from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy

async def adaptive_crawl_single(query: str, start_url: str, task_id: str):
    print(f"Task {task_id}: Research Query: {query}")
    print(f"Task {task_id}: Starting crawl for {start_url}\n")
    
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
    
    crawler_config = CrawlerRunConfig(
        exclude_external_links=True,
        exclude_social_media_links=True, 
        only_text=True,
        # excluded_tags=['header', 'footer', 'nav', 'aside', 'script', 'style'], 
        word_count_threshold=50, 
        markdown_generator=DefaultMarkdownGenerator(
            content_filter=PruningContentFilter(
                threshold=0.45, 
                min_word_threshold=10
            )
        ),
        capture_console_messages=True,
    )
    
    adaptive_config = AdaptiveConfig(
        strategy="statistical",
        max_pages=10,
        confidence_threshold=0.8, 
        top_k_links=3,
        min_gain_threshold=0.05
    )
    
    async with AsyncWebCrawler(
        crawler_strategy=crawler_strategy,
        config=browser_config
    ) as crawler:
        adaptive = AdaptiveCrawler(crawler, adaptive_config)
        
        print(f"Task {task_id}: Starting adaptive crawl...")
        start_time = time.time()
        
        result = await adaptive.digest(
            start_url=start_url,
            query=query
        )
        
        elapsed = time.time() - start_time
        
        print(f"\nTask {task_id}: Crawling Complete in {elapsed:.1f} seconds!\n")
        
        confidence = adaptive.confidence
        conf_percentage = int(confidence * 100)
        
        print(f"Task {task_id}: Confidence Level: {conf_percentage}%")
        print(f"Task {task_id}: Pages Crawled: {len(result.crawled_urls)}")
        print(f"Task {task_id}: Knowledge Base Size: {len(adaptive.state.knowledge_base)} documents")
        
        total_content = 0
        for doc in adaptive.state.knowledge_base:
            if hasattr(doc, 'markdown') and doc.markdown and hasattr(doc.markdown, 'raw_markdown'):
                total_content += len(doc.markdown.raw_markdown)
        
        print(f"Task {task_id}: Total Content: {total_content:,} chars")
        if len(result.crawled_urls) > 0:
            print(f"Task {task_id}: Time per Page: {elapsed / len(result.crawled_urls):.2f}s")
        
        print(f"Task {task_id}: Most Relevant Pages Found:")
        relevant_pages = adaptive.get_relevant_content(top_k=10)
        
        results = []
        for i, page in enumerate(relevant_pages, 1):
            print(f"Task {task_id}: \n{i}. {page['url']}")
            print(f"Task {task_id}:    Relevance: {page['score']:.2%}")
            
            content = page['content'] or ""
            if content:
                sentences = [s.strip() for s in content.split('.') if s.strip()]
                if sentences:
                    print(f"Task {task_id}:    Key insight: {sentences[0][:150]}...")
            
            results.append({
                'url': page['url'],
                'score': page['score'],
                'content': content
            })
        
        results_dir = Path("results")
        results_dir.mkdir(exist_ok=True)
        
        output_file = results_dir / f"{task_id}_crawl_results.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump({
                'task_id': task_id,
                'query': query,
                'start_url': start_url,
                'crawled_urls': list(result.crawled_urls),
                'confidence': confidence,
                'pages_crawled': len(result.crawled_urls),
                'total_content_chars': total_content,
                'elapsed_time': elapsed,
                'relevant_pages': results
            }, f, indent=2, ensure_ascii=False)
        
        print(f"Task {task_id}: Results saved to: {output_file}\n")
        
        return {
            'task_id': task_id,
            'query': query,
            'start_url': start_url,
            'result': {
                'crawled_urls': list(result.crawled_urls),
                'confidence': confidence,
                'pages_crawled': len(result.crawled_urls),
                'total_content_chars': total_content,
                'elapsed_time': elapsed,
                'relevant_pages': results
            }
        }

async def adaptive_crawl_batch(tasks: dict):
    print(f"Starting batch adaptive crawl for {len(tasks)} tasks\n")
    
    coroutines = [
        adaptive_crawl_single(query, start_url, task_id)
        for task_id, (query, start_url) in tasks.items()
    ]
    
    results = await asyncio.gather(*coroutines, return_exceptions=True)
    
    successful_results = []
    failed_results = []
    
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            task_id = list(tasks.keys())[i]
            print(f"Task {task_id} failed with error: {result}")
            failed_results.append({
                'task_id': task_id,
                'error': str(result)
            })
        else:
            successful_results.append(result)
    
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)  # Ensure directory exists
    
    summary_file = results_dir / "batch_summary.json"
    
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump({
            'total_tasks': len(tasks),
            'successful_tasks': len(successful_results),
            'failed_tasks_count': len(failed_results),
            'tasks': list(tasks.keys()),
            'successful_results': successful_results,
            'failed_tasks': failed_results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"Batch crawl completed!")
    print(f"Successful: {len(successful_results)}, Failed: {len(failed_results)}")
    print(f"Summary saved to: {summary_file}")
    
    return successful_results, failed_results

async def main():
    tasks = {
        "hsenidmobile_company_info": (
            "company information hsenid mobile official company name description financial info leadership team products services pricing model competitors competitive advantages customer segments customer reviews tech stack company size headquarters founded year contact info recent news",
            "https://hsenidmobile.com/"
        ),
        "nasa_company_info": (
            "company information NASA official company name description financial info leadership team products services pricing model competitors competitive advantages customer segments customer reviews tech stack company size headquarters founded year contact info recent news",
            "https://www.nasa.gov"
        ),
        "apple_company_info": (
            "company information Apple Inc official company name description financial info leadership team products services pricing model competitors competitive advantages customer segments customer reviews tech stack company size headquarters founded year contact info recent news",
            "https://www.apple.com"
        )
    }
    
    await adaptive_crawl_batch(tasks)

if __name__ == "__main__":
    asyncio.run(main())