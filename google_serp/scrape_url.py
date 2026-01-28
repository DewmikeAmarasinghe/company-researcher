import asyncio
import json
from typing import Any, Dict, List, Optional
from pathlib import Path
from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CrawlerRunConfig,
    CacheMode,
    LLMExtractionStrategy,
    AdaptiveCrawler,
    AdaptiveConfig,
    CrawlResult,
    DefaultMarkdownGenerator,
    PruningContentFilter,
    LLMConfig,
)
from pydantic import BaseModel, Field

__current_dir = Path(__file__).parent

class CompanySalesIntelligence(BaseModel):
    company_name: str = Field(..., description="Official company name")
    description: str = Field(..., description="Company description and mission")
   
    financial_info: Optional[Dict[str, Any]] = Field(None, description="Revenue, funding, valuation, growth metrics")
    leadership_team: Optional[List[Dict[str, str]]] = Field(None, description="CEO, executives, key decision makers with titles")
   
    products_services: Optional[List[str]] = Field(None, description="Main products or services offered")
    pricing_model: Optional[str] = Field(None, description="Pricing strategy, tiers, or costs mentioned")
   
    competitors: Optional[List[str]] = Field(None, description="Mentioned competitors or alternatives")
    competitive_advantages: Optional[List[str]] = Field(None, description="Unique selling points or differentiators")
   
    customer_segments: Optional[List[str]] = Field(None, description="Target customers or industries served")
    customer_reviews: Optional[Dict[str, Any]] = Field(None, description="Customer testimonials, case studies, or reviews")
   
    tech_stack: Optional[List[str]] = Field(None, description="Technologies or platforms they use")
    company_size: Optional[str] = Field(None, description="Employee count or company scale")
    headquarters: Optional[str] = Field(None, description="Main office location")
    founded_year: Optional[str] = Field(None, description="Year founded")
   
    contact_info: Optional[Dict[str, str]] = Field(None, description="Email, phone, social media links")
    recent_news: Optional[List[str]] = Field(None, description="Recent announcements or press releases")

async def extract_company_intelligence(url: str, output_file: Optional[str] = None) -> Dict[str, Any]:
    browser_config = BrowserConfig(
        headless=True,
        verbose=True
    )
   
    crawl_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        markdown_generator=DefaultMarkdownGenerator(
            content_filter=PruningContentFilter(
                threshold=0.48,
                threshold_type="fixed",
                min_word_threshold=10
            )
        ),
        excluded_tags=["script", "style", "nav", "footer", "header", "aside", "iframe"],
        word_count_threshold=10,
        keep_data_attributes=False,
    )
   
    adaptive_config = AdaptiveConfig(
        confidence_threshold=0.85,
        max_pages=25,
        top_k_links=4,
        min_gain_threshold=0.05,
        strategy="statistical"
    )
   
    llm_extraction_strategy = LLMExtractionStrategy(
        llm_config=LLMConfig(
            provider="openai/gpt-4o-mini",
            api_token="env:OPENAI_API_KEY"
        ),
        schema=CompanySalesIntelligence.model_json_schema(),
        extraction_type="schema",
        instruction="""Extract comprehensive sales intelligence about this company.
        Focus on information useful for B2B sales teams:
       
        CRITICAL INFORMATION:
        - Financial data (revenue, funding, valuation, growth rate)
        - Leadership team (CEO, CTO, VP Sales, decision makers with full names and titles)
        - Competitors mentioned and how they position against them
        - Pricing information (costs, pricing tiers, models)
        - Customer reviews, testimonials, case studies with specific details
       
        USEFUL CONTEXT:
        - Products and services offered
        - Target customer segments and industries
        - Technology stack they use or mention
        - Company size, location, founding year
        - Recent news or announcements
        - Contact information
       
        Extract only factual information present in the content.
        Do not make assumptions or infer information not explicitly stated.""",
        chunk_token_threshold=4096,
        overlap_rate=0.1,
        apply_chunking=True,
        verbose=True,
    )
   
    async with AsyncWebCrawler(config=browser_config) as crawler:
        crawler.crawl_config = crawl_config
        crawler.extraction_strategy = llm_extraction_strategy
        
        adaptive = AdaptiveCrawler(crawler, adaptive_config)
       
        result = await adaptive.digest(
            start_url=url,
            query="company financial information revenue funding leadership team CEO executives competitors pricing products customer reviews testimonials"
        )
       
        adaptive.print_stats()
        print(f"Crawled {len(result.crawled_urls)} pages")
        print(f"Achieved {adaptive.confidence:.0%} confidence")
       
        if result.extracted_content:
            try:
                extracted_data = json.loads(result.extracted_content)
            except Exception:
                extracted_data = {}
           
            if output_file and extracted_data:
                output_path = __current_dir / output_file
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(json.dumps(extracted_data, indent=2, ensure_ascii=False))
                print(f"Saved extracted content to {output_file}")
           
            return extracted_data
       
        all_content = []
        for page in adaptive.get_relevant_content(top_k=15):
            all_content.append(page.get('content', ''))
       
        combined_content = '\n\n'.join(all_content)
       
        if combined_content.strip():
            try:
                extracted_list = llm_extraction_strategy.extract(url, combined_content)
                if extracted_list and len(extracted_list) > 0:
                    extracted_data = extracted_list[0] if isinstance(extracted_list, list) else extracted_list
                   
                    if output_file:
                        output_path = __current_dir / output_file
                        with open(output_path, "w", encoding="utf-8") as f:
                            f.write(json.dumps(extracted_data, indent=2, ensure_ascii=False))
                        print(f"Saved extracted content to {output_file}")
                   
                    return extracted_data
            except Exception as e:
                print(f"Manual extraction failed: {str(e)}")
       
        return {}

async def extract_multiple_companies(urls: List[str], output_dir: str = "companies") -> Dict[str, Dict[str, Any]]:
    output_path = __current_dir / output_dir
    output_path.mkdir(exist_ok=True)
   
    tasks = []
    filenames = []
   
    for url in urls:
        domain = url.replace("https://", "").replace("http://", "").split("/")[0].replace("www.", "")
        filename = domain.replace(":", "_").replace(".", "_") + ".json"
        filepath = str(output_path / filename)
        tasks.append(extract_company_intelligence(url, filepath))
        filenames.append(filename)
   
    results = await asyncio.gather(*tasks, return_exceptions=True)
   
    all_results = {}
    for url, result, filename in zip(urls, results, filenames):
        if isinstance(result, Exception):
            print(f"Error extracting {url}: {str(result)}")
            all_results[url] = {"error": str(result)}
        else:
            all_results[url] = result
            print(f"Successfully extracted {url} -> {filename}")
   
    return all_results

async def demo():
    urls = [
        # "https://www.anthropic.com",
        # "https://www.stripe.com",
        "https://www.tesla.com",
    ]
   
    results = await extract_multiple_companies(urls)
    print(f"\nCompleted extraction for {len(results)} companies")

if __name__ == "__main__":
    asyncio.run(demo())