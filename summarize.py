import os
import asyncio
import json
from litellm import completion
from scrape import scrape_company_urls
from utils import get_company_path
from config import API_KEY, MODEL_NAME, get_enabled_categories, get_category_query
from prompts import get_category_summary_prompt, get_final_report_prompt

async def summarize_category(company_name: str, category: str, query: str, content: str) -> dict:
    if not content.strip():
        return {
            "category": category,
            "summary": ""
        }
    
    prompt = get_category_summary_prompt(company_name, category, query, content)

    response = completion(
        model=MODEL_NAME,
        api_key=API_KEY,
        messages=[{"role": "user", "content": prompt}],
    )
    
    summary = response["choices"][0]["message"]["content"]
    
    return {
        "category": category,
        "summary": summary
    }

async def generate_final_report(company_name: str, detailed_summaries: dict) -> str:
    prompt = get_final_report_prompt(company_name, detailed_summaries)
    
    response = completion(
        model=MODEL_NAME,
        api_key=API_KEY,
        messages=[{"role": "user", "content": prompt}],
    )
    
    return response["choices"][0]["message"]["content"]

def add_sources_to_report(report_content: str, category_sources: dict) -> str:
    report_with_sources = report_content.strip()
    
    report_with_sources += "\n\n---\n\n# Research Sources\n\n"
    
    enabled_categories = get_enabled_categories()
    
    for idx, category in enumerate(enabled_categories, 1):
        if category in category_sources and category_sources[category]:
            report_with_sources += f"## {idx}. {category}\n\n"
            for source in category_sources[category]:
                report_with_sources += f"- {source}\n"
            report_with_sources += "\n"
    
    return report_with_sources

def load_metadata(company_name: str) -> dict:
    base_path = get_company_path(company_name)
    metadata_file = f"{base_path}/crawled/metadata.json"
    
    if not os.path.exists(metadata_file):
        raise FileNotFoundError(f"Metadata file not found: {metadata_file}")
    
    with open(metadata_file, "r") as f:
        return json.load(f)

def group_by_category(metadata: dict) -> dict:
    category_content = {}
    url_to_categories = metadata["url_to_categories"]
    
    for item in metadata["scraped_urls"]:
        filepath = item["filepath"]
        url = item["url"]
        categories = url_to_categories.get(url, [])
        
        if not os.path.exists(filepath):
            continue
        
        with open(filepath, "r") as f:
            content = f.read()
        
        for category in categories:
            if category not in category_content:
                category_content[category] = []
            category_content[category].append({
                "url": url,
                "content": content
            })
    
    merged_content = {}
    for category, items in category_content.items():
        combined = "\n\n---\n\n".join([item["content"] for item in items])
        merged_content[category] = {
            "content": combined,
            "sources": [item["url"] for item in items]
        }
    
    return merged_content

def create_detailed_report_for_llm(detailed_summaries: dict, category_content: dict) -> str:
    detailed_report = ""
    
    enabled_categories = get_enabled_categories()
    
    for category in enabled_categories:
        if category in detailed_summaries:
            detailed_report += f"## {category}\n\n"
            detailed_report += detailed_summaries[category]
            detailed_report += "\n\n---\n\n"
    
    return detailed_report

def save_reports(company_name: str, base_url: str, location: str, summary_report: str, detailed_report: str, metadata: dict):
    base_path = get_company_path(company_name)
    summaries_folder = f"{base_path}/summaries"
    os.makedirs(summaries_folder, exist_ok=True)
    
    header = f"""# Company Research Report: {company_name}

**Base URL:** {base_url}  
**Location:** {location}  
**Total URLs Scraped:** {metadata['stats']['total_scraped']}  
**Total Content:** {metadata['stats']['total_chars']:,} characters  

---

"""
    
    summary_report_full = header + summary_report
    detailed_report_full = header + detailed_report
    
    summary_md_file = f"{summaries_folder}/summary_report.md"
    with open(summary_md_file, "w") as f:
        f.write(summary_report_full)
    
    detailed_md_file = f"{summaries_folder}/detailed_report.md"
    with open(detailed_md_file, "w") as f:
        f.write(detailed_report_full)
    
    print(f"Summary report saved to: {summary_md_file}")
    print(f"Detailed report saved to: {detailed_md_file}")

async def summarize_company(company_name: str, base_url: str, location: str, skip_scraping: bool = False):
    if not skip_scraping:
        print(f"{'='*60}")
        print(f"Starting scraping for {company_name}")
        print(f"{'='*60}\n")
        await scrape_company_urls(company_name, base_url, location, skip_url_discovery=False)
    
    print(f"\n{'='*60}")
    print(f"Loading scraped data for {company_name}")
    print(f"{'='*60}\n")
    
    metadata = load_metadata(company_name)
    category_content = group_by_category(metadata)
    
    enabled_categories = get_enabled_categories()
    categories_with_content = [cat for cat in enabled_categories if cat in category_content]
    
    print(f"Found {len(categories_with_content)} categories with content")
    
    print(f"\n{'='*60}")
    print(f"AI is generating detailed summaries for {len(categories_with_content)} categories...")
    print(f"{'='*60}\n")
    
    tasks = []
    category_list = []
    
    for category in categories_with_content:
        data = category_content[category]
        query = get_category_query(category, company_name, location)
        tasks.append(summarize_category(company_name, category, query, data["content"]))
        category_list.append(category)
    
    summaries = await asyncio.gather(*tasks)
    
    print(f"\n{'='*60}")
    print("Detailed summarization complete!")
    print(f"{'='*60}\n")
    
    for idx, summary in enumerate(summaries):
        category = category_list[idx]
        word_count = len(summary["summary"].split())
        print(f"✓ {category} ({word_count} words)")
    
    detailed_summaries = {s["category"]: s["summary"] for s in summaries}
    
    category_sources = {}
    for category in categories_with_content:
        if category in category_content:
            category_sources[category] = category_content[category]["sources"]
    
    detailed_report_for_llm = create_detailed_report_for_llm(detailed_summaries, category_content)
    
    print(f"\n{'='*60}")
    print("AI is generating final polished report...")
    print(f"{'='*60}\n")
    
    final_report_content = await generate_final_report(company_name, detailed_summaries)
    
    print(f"\n{'='*60}")
    print("Final report generation complete!")
    print(f"{'='*60}\n")
    
    print(f"\n{'='*60}")
    print("Adding sources to reports...")
    print(f"{'='*60}\n")
    
    summary_report_with_sources = add_sources_to_report(final_report_content, category_sources)
    detailed_report_with_sources = add_sources_to_report(detailed_report_for_llm, category_sources)
    
    save_reports(company_name, base_url, location, summary_report_with_sources, detailed_report_with_sources, metadata)
    
    print(f"\n{'='*60}")
    print("Summary Generation Complete!")
    print(f"{'='*60}")
    print(f"Total categories processed: {len(categories_with_content)}")
    print(f"{'='*60}\n")

async def main():
    company_name = "AOD South Asia (Pvt) Ltd"
    base_url = "https://www.aod.lk/"
    location = "Sri Lanka"
    
    await summarize_company(
        company_name=company_name,
        base_url=base_url,
        location=location,
        skip_scraping=True
    )

if __name__ == "__main__":
    asyncio.run(main())