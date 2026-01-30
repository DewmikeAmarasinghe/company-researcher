import asyncio
import os
import time
import json
import shutil
from urllib.parse import quote_plus
from crawl4ai import AsyncWebCrawler, UndetectedAdapter
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from litellm import completion

DELAY_BETWEEN_QUERIES = 1


def generate_queries(company_name: str, location: str):
    queries = [
        f"who founded {company_name} in {location} and who is the current CEO leadership team",
        f"what is the business model revenue streams pricing strategy of {company_name} {location}",
        f"complete list of products services offerings by {company_name} {location} with descriptions",
        f"detailed history founding story growth timeline milestones of {company_name} {location}",
        f"who are the direct competitors alternatives to {company_name} in {location} market",
        f"market share industry position ranking of {company_name} in {location} sector",
        f"latest news press releases announcements from {company_name} {location} 2024 2026",
        f"organizational chart management structure departments teams at {company_name} {location}",
        f"major achievements awards recognition certifications won by {company_name} {location}",
        f"target customers client base industries served by {company_name} {location}",
        f"mission statement vision values principles culture of {company_name} {location}",
        f"technology stack software tools platforms infrastructure used by {company_name} {location}",
        f"strategic partnerships alliances collaborations clients of {company_name} {location}",
        f"total employees headcount team size locations offices of {company_name} {location}",
        f"expansion plans growth strategy future roadmap of {company_name} {location}",
        f"industry awards certifications accolades achievements of {company_name} {location}",
        f"annual revenue profit financials funding investment valuation of {company_name} {location}",
        f"business challenges risks opportunities threats facing {company_name} {location} market",
        f"work culture employee reviews workplace environment benefits at {company_name} {location}",
        f"customer testimonials reviews ratings feedback about {company_name} {location} services",
        f"innovation R&D research development initiatives by {company_name} {location}",
        f"social responsibility CSR sustainability initiatives by {company_name} {location}",
        f"case studies success stories projects delivered by {company_name} {location}",
        f"pricing packages plans costs fees charged by {company_name} {location}",
        f"contact information address email phone locations of {company_name} {location}",
    ]
    return queries


def get_query_titles():
    return [
        "Founders and Leadership",
        "Business Model and Revenue",
        "Products and Services",
        "Company History",
        "Competitive Landscape",
        "Market Position",
        "Recent News and Updates",
        "Organizational Structure",
        "Achievements and Recognition",
        "Customer Base",
        "Mission and Values",
        "Technology Stack",
        "Partnerships",
        "Company Size",
        "Future Plans",
        "Awards and Certifications",
        "Financial Performance",
        "Challenges and Opportunities",
        "Company Culture",
        "Customer Reviews",
        "Innovation and R&D",
        "Social Responsibility",
        "Case Studies",
        "Pricing Information",
        "Contact Information",
    ]


async def crawl_single_query(query: str, title: str):
    proxy_cfg = {
        "server": os.getenv("PROXY_SERVER_URL"),
        "username": os.getenv("PROXY_USERNAME"),
        "password": os.getenv("PROXY_PASSWORD")
    }

    browser_config = BrowserConfig(
        headless=False,
        enable_stealth=True
    )

    undetected_adapter = UndetectedAdapter()

    crawler_strategy = AsyncPlaywrightCrawlerStrategy(
        browser_config=browser_config,
        browser_adapter=undetected_adapter
    )

    run_cfg = CrawlerRunConfig(
        proxy_config=proxy_cfg,
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

    url = f"https://www.google.com/search?q={quote_plus(query)}&udm=50"

    async with AsyncWebCrawler(
        crawler_strategy=crawler_strategy,
        config=browser_config
    ) as crawler:
        result = await crawler.arun(url, config=run_cfg)

    external_links = []
    if result.success and hasattr(result, 'links') and result.links:
        links_list = result.links.get('external', [])
        for link in links_list:
            if isinstance(link, dict) and 'href' in link:
                external_links.append(link['href'])
            elif isinstance(link, str):
                external_links.append(link)

    query_data = {
        "query_title": title,
        "content": result.markdown if result.success else "",
        "links": external_links,
        "success": result.success
    }

    if result.success:
        print(f"{title}: ✓ Success - {len(result.markdown)} chars, {len(external_links)} links")
    else:
        print(f"{title}: ✗ Failed")

    return query_data


async def crawl_google_ai_mode_parallel(queries: list, query_titles: list):
    tasks = [crawl_single_query(query, title) for query, title in zip(queries, query_titles)]
    query_results = await asyncio.gather(*tasks)
    return list(query_results)


def generate_detailed_report(query_results: list):
    detailed_report = ""
    for idx, query_data in enumerate(query_results, 1):
        detailed_report += f"## {idx}. {query_data['query_title']}\n\n"
        if query_data['success'] and query_data['content']:
            content = query_data['content'].strip()
            detailed_report += f"{content}\n\n" if content else "*No information available*\n\n"
        else:
            detailed_report += "*Failed to retrieve information*\n\n"
        if query_data['links']:
            detailed_report += "**Sources:**\n\n"
            for link in query_data['links']:
                detailed_report += f"- [{link}]({link})\n"
            detailed_report += "\n"
        detailed_report += "---\n\n"
    return detailed_report


def generate_summary_from_report(report_content: str, company_name: str, location: str):
    print("\nGenerating AI summary of the research report...")
    
    prompt = f"""You are creating a comprehensive executive summary for {company_name}, a company based in {location}.

Below is a complete research report:

{report_content}

Create a well-structured, visually appealing executive summary in markdown format. Your summary MUST follow this exact structure with one section for EACH of the 25 research categories:

# Executive Summary: {company_name}

## 1. Founders and Leadership
- List key points about founders, CEO, and leadership team
- Include names, roles, and relevant background

## 2. Business Model and Revenue
- Revenue streams and pricing strategy
- Business model details

## 3. Products and Services
- Complete list of products/services
- Key features and descriptions

## 4. Company History
- Founding story and timeline
- Major milestones

## 5. Competitive Landscape
- Direct competitors
- Market alternatives

## 6. Market Position
- Market share and ranking
- Industry position

## 7. Recent News and Updates
- Latest developments from 2024-2026
- Recent announcements

## 8. Organizational Structure
- Management structure
- Departments and teams

## 9. Achievements and Recognition
- Major achievements
- Awards and certifications

## 10. Customer Base
- Target customers
- Industries served

## 11. Mission and Values
- Mission statement
- Core values and culture

## 12. Technology Stack
- Technologies used
- Software and platforms

## 13. Partnerships
- Strategic partnerships
- Key collaborations

## 14. Company Size
- Employee count
- Office locations

## 15. Future Plans
- Expansion plans
- Growth strategy

## 16. Awards and Certifications
- Industry awards
- Certifications

## 17. Financial Performance
- Revenue and funding
- Valuation data

## 18. Challenges and Opportunities
- Business challenges
- Market opportunities

## 19. Company Culture
- Work environment
- Employee benefits

## 20. Customer Reviews
- Customer testimonials
- Feedback and ratings

## 21. Innovation and R&D
- Research initiatives
- Innovation projects

## 22. Social Responsibility
- CSR initiatives
- Sustainability efforts

## 23. Case Studies
- Success stories
- Project examples

## 24. Pricing Information
- Pricing packages
- Cost structure

## 25. Contact Information
- Physical locations
- Contact details

IMPORTANT FORMATTING RULES:
- Use bullet points (markdown format with - ) for all content
- Use **bold** for important terms, names, and key metrics
- Use *italic* for emphasis on specific insights
- Use `code formatting` for technical terms, technologies, and product names
- Be specific with numbers, dates, names, and concrete details
- If no information is available for a section, write "- *Information not available in research*"
- Do NOT skip any of the 25 sections
- Keep each point concise but informative
- Extract only factual information present in the report
- Make the summary visually appealing with proper markdown formatting"""

    response = completion(
        model="gemini/gemini-2.5-flash",
        api_key=os.getenv("GEMINI_API_KEY"),
        messages=[{"role": "user", "content": prompt}],
    )
    
    return response.choices[0].message.content


def add_sources_to_summary(summary: str, query_results: list):
    summary_with_sources = summary + "\n\n---\n\n# Research Sources\n\n"
    for idx, query_data in enumerate(query_results, 1):
        if query_data['links']:
            summary_with_sources += f"## {idx}. {query_data['query_title']}\n\n"
            for link in query_data['links']:
                summary_with_sources += f"- [{link}]({link})\n"
            summary_with_sources += "\n"
    return summary_with_sources


async def research_company(company_name: str, location: str):
    safe_company_name = company_name.replace(' ', '_').replace(',', '').replace('(', '').replace(')', '').lower()
    company_folder = f"google_results/{safe_company_name}"
    
    if os.path.exists(company_folder):
        shutil.rmtree(company_folder)
    os.makedirs(company_folder, exist_ok=True)
    
    print(f"Starting comprehensive research for {company_name} in {location}...")
    print(f"Delay between queries: {DELAY_BETWEEN_QUERIES} seconds\n")
    
    queries = generate_queries(company_name, location)
    query_titles = get_query_titles()
    print(f"Generated {len(queries)} research queries\n")
    
    start_time = time.time()
    query_results = await crawl_google_ai_mode_parallel(queries, query_titles)
    end_time = time.time()
    
    successful = sum(1 for r in query_results if r['success'])
    print(f"\nCompleted crawling: {successful}/{len(query_results)} successful\n")
    print(f"Time taken: {end_time - start_time}s\n")
    
    detailed_json_filename = f"{company_folder}/detailed_report.json"
    with open(detailed_json_filename, "w", encoding="utf-8") as f:
        json.dump(query_results, f, indent=2, ensure_ascii=False)
    
    print(f"Detailed data saved to {detailed_json_filename}")
    
    detailed_report_md = generate_detailed_report(query_results)
    
    detailed_report_filename = f"{company_folder}/detailed_report.md"
    with open(detailed_report_filename, "w", encoding="utf-8") as f:
        f.write(detailed_report_md)
    
    print(f"Detailed report saved to {detailed_report_filename}")
    
    full_report = ""
    for query_data in query_results:
        full_report += query_data['content'] + "\n\n"
    
    summary = generate_summary_from_report(full_report, company_name, location)
    
    summary_with_sources = add_sources_to_summary(summary, query_results)
    
    summary_filename = f"{company_folder}/summary.md"
    with open(summary_filename, "w", encoding="utf-8") as f:
        f.write(summary_with_sources)
    
    print(f"Summary saved to {summary_filename}")
    print(f"Summary length: {len(summary_with_sources)} characters")
    
    return query_results, summary_with_sources


async def main():
    company_name = "Mintpay"
    location = "sri lanka"
    
    await research_company(company_name, location)


if __name__ == "__main__":
    asyncio.run(main())