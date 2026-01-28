import os
import asyncio
import json
from litellm import completion
from scrape import scrape_company_urls
from utils import get_company_path
from config import API_KEY, MODEL_NAME, get_enabled_categories
from prompts import get_category_summary_prompt

async def summarize_category(company_name: str, category: str, content: str) -> dict:
    if not content.strip():
        return {
            "category": category,
            "summary": "",
            "word_count": 0,
            "data_quality": "insufficient"
        }
    
    prompt = get_category_summary_prompt(company_name, category, content)

    response = completion(
        model=MODEL_NAME,
        api_key=API_KEY,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    
    result = json.loads(response["choices"][0]["message"]["content"])
    
    summary = result.get("summary", "")
    data_quality = result.get("data_quality", "partial")
    word_count = len(summary.split())
    
    return {
        "category": category,
        "summary": summary,
        "word_count": word_count,
        "data_quality": data_quality
    }

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

def assemble_report(company_name: str, base_url: str, location: str, summaries: list, metadata: dict, category_content: dict) -> dict:
    quality_map = {"sufficient": "✓", "partial": "⚠️", "insufficient": "✗"}
    
    report_md = f"""# Company Research Report: {company_name}

**Base URL:** {base_url}  
**Location:** {location}  
**Total URLs Scraped:** {metadata['stats']['total_scraped']}  
**Total Content:** {metadata['stats']['total_chars']:,} characters  

---

"""
    
    summary_dict = {s["category"]: s for s in summaries}
    
    category_number = 1
    enabled_categories = get_enabled_categories()
    
    for category in enabled_categories:
        if category in summary_dict:
            summary_data = summary_dict[category]
            quality_symbol = quality_map.get(summary_data["data_quality"], "⚠️")
            
            report_md += f"## {category_number}. {category} {quality_symbol}\n\n"
            
            if summary_data["summary"]:
                report_md += summary_data["summary"]
                report_md += "\n\n"
            
            if category in category_content and "sources" in category_content[category]:
                sources = category_content[category]["sources"]
                if sources:
                    report_md += "**Sources:**\n"
                    for source in sources:
                        report_md += f"- {source}\n"
                    report_md += "\n"
            
            report_md += "---\n\n"
            category_number += 1
    
    return {
        "company_name": company_name,
        "base_url": base_url,
        "location": location,
        "stats": metadata["stats"],
        "summaries": summaries,
        "report_markdown": report_md
    }

def save_report(company_name: str, report: dict):
    base_path = get_company_path(company_name)
    summaries_folder = f"{base_path}/summaries"
    os.makedirs(summaries_folder, exist_ok=True)
    
    json_file = f"{summaries_folder}/report.json"
    with open(json_file, "w") as f:
        json.dump(report, f, indent=2)
    
    md_file = f"{summaries_folder}/report.md"
    with open(md_file, "w") as f:
        f.write(report["report_markdown"])
    
    print(f"Report saved to: {md_file}")
    print(f"Data saved to: {json_file}")

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
    print(f"AI is summarizing {len(categories_with_content)} categories...")
    print(f"{'='*60}\n")
    
    tasks = []
    category_list = []
    
    for category in categories_with_content:
        data = category_content[category]
        tasks.append(summarize_category(company_name, category, data["content"]))
        category_list.append(category)
    
    summaries = await asyncio.gather(*tasks)
    
    print(f"\n{'='*60}")
    print("Summarization complete!")
    print(f"{'='*60}\n")
    
    quality_map = {"sufficient": "✓", "partial": "⚠️", "insufficient": "✗"}
    
    for idx, summary in enumerate(summaries):
        category = category_list[idx]
        quality_symbol = quality_map.get(summary["data_quality"], "⚠️")
        print(f"✓ {category} ({summary['word_count']} words) {quality_symbol}")
    
    print(f"\n{'='*60}")
    print("Assembling final report")
    print(f"{'='*60}\n")
    
    report = assemble_report(company_name, base_url, location, summaries, metadata, category_content)
    save_report(company_name, report)
    
    total_words = sum(s["word_count"] for s in summaries)
    
    print(f"\n{'='*60}")
    print("Summary Generation Complete!")
    print(f"{'='*60}")
    print(f"Total categories: {len(summaries)}")
    print(f"Total words: {total_words}")
    print(f"{'='*60}\n")

async def main():
    # company_name = "hSenid Mobile Solutions (Pvt) Ltd"
    # base_url = "https://hsenidmobile.com/"
    # location = "Sri Lanka"
    
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
