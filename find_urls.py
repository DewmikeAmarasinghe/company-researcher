import os
import asyncio
import json
from litellm import completion
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig

async def discover_company_urls(company_name: str, base_url: str) -> dict:
    async with AsyncWebCrawler(config=BrowserConfig()) as crawler:
        result = await crawler.arun(url=base_url, config=CrawlerRunConfig())
    
    urls = {
        category: [
            {"url": link["href"], "text": link.get("text", "")}
            for link in items
            if link["href"].startswith(("http://", "https://"))
        ]
        for category, items in result.links.items()
    }
    
    prompt = f"""
You are a company research assistant analyzing URLs extracted from {company_name}'s website (base URL: {base_url}).

You have been provided with a list of URLs along with their associated link text as context. 
The link text helps you understand what each URL represents.

Your task is to select and categorize URLs into two groups:

1. WEBSITE URLS (maximum 20): Main company website pages containing important information such as:
   - Company overview / about / mission / vision / description
   - Leadership / founders / executive team / management
   - Products / services / solutions / offerings / pricing
   - Customer segments / case studies / testimonials / success stories
   - Investors / funding / press releases / news / media
   - Contact information / office locations / regional presence
   - Technology / innovation / research
   
   EXCLUDE: Career pages, job listings, hiring pages, social media links

2. SOCIAL MEDIA URLS: Official company social media profiles that are valuable for scraping company information.
   ONLY include these platforms if found:
   - LinkedIn (company page, NOT individual profiles)
   - Twitter/X (official company account)
   - Facebook (official company page)
   - Instagram (official company account, if B2C focused)
   
   DO NOT include: YouTube, TikTok, Pinterest, Reddit, or personal social media profiles

IMPORTANT INSTRUCTIONS FOR WEBSITE URLS:
1. Analyze the URL structure AND the link text to determine relevance
2. Prioritize main section pages over blog posts or minor pages
3. Exclude duplicate or very similar URLs
4. Do NOT include any career, jobs, or hiring related pages
5. Exclude social media links (those go in the social_media section)

IMPORTANT INSTRUCTIONS FOR SOCIAL MEDIA URLS:
1. Only include OFFICIAL company accounts (check if the URL matches the company name/brand)
2. Only include platforms that typically contain valuable business information
3. Ensure these are profile/page URLs, not individual posts
4. Verify the social media handle/username appears legitimate for this company

REQUIRED OUTPUT FORMAT:
{{
  "urls": [
    "https://example.com/about",
    "https://example.com/products",
    "https://example.com/contact"
  ],
  "social_media": [
    "https://www.linkedin.com/company/example-company",
    "https://twitter.com/examplecompany"
  ]
}}

URLs with context:
{json.dumps(urls, indent=2)}
"""
    
    # response = completion(
    #     model="gpt-5-nano",
    #     api_key=os.getenv("OPENAI_API_KEY"),
    #     messages=[{"role": "user", "content": prompt}],
    #     response_format={"type": "json_object"},
    # )
    
    response = completion(
        model="gemini/gemini-2.5-flash",
        api_key=os.getenv("GEMINI_API_KEY"),
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    
    content_json = json.loads(response["choices"][0]["message"]["content"])
    
    return {
        "company_name": company_name,
        "base_url": base_url,
        "filtered_urls": content_json.get("urls", []),
        "social_media": content_json.get("social_media", []),
        "original_urls": urls,
    }

if __name__ == "__main__":
    # output = asyncio.run(discover_company_urls(
    #     company_name="AOD",
    #     base_url="https://www.aod.lk/"
    # ))
    output = asyncio.run(discover_company_urls(
        company_name="hSenid Mobile Solutions",
        base_url="https://www.hsenidmobile.com/"
    ))
    # output = asyncio.run(discover_company_urls(
    #     company_name="Vision Care Optical Services (Pvt) Ltd",
    #     base_url="https://visioncare.lk/"
    # ))
    # output = asyncio.run(discover_company_urls(
    #     company_name="ceylon cold stores",
    #     base_url="https://www.elephanthouse.lk/"
    # ))
    # output = asyncio.run(discover_company_urls(
    #     company_name="Tesla, Inc",
    #     base_url="https://www.tesla.com/"
    # ))
    print(json.dumps(output, indent=2))