import os
import asyncio
import json
from litellm import completion
from scrape import scrape_company_urls
from utils import get_company_path
from config import API_KEY, MODEL_NAME, get_enabled_categories
from prompts import get_category_summary_prompt, get_final_report_prompt

async def summarize_category(company_name: str, category: str, content: str) -> dict:
    if not content.strip():
        return {
            "category": category,
            "summary": ""
        }
    
    prompt = get_category_summary_prompt(company_name, category, content)

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

async def generate_final_report(company_name: str, detailed_summaries: dict) -> dict:
    prompt = get_final_report_prompt(company_name, detailed_summaries)
    
    response = completion(
        model=MODEL_NAME,
        api_key=API_KEY,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    
    return json.loads(response["choices"][0]["message"]["content"])

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

def assemble_reports(company_name: str, base_url: str, location: str, final_report_data: dict, detailed_summaries: dict, metadata: dict, category_content: dict) -> tuple:
    quality_map = {"sufficient": "✓", "partial": "⚠️", "insufficient": "✗"}
    
    enabled_categories = get_enabled_categories()
    
    summary_report_md = f"""# Company Research Report: {company_name}

**Base URL:** {base_url}  
**Location:** {location}  
**Total URLs Scraped:** {metadata['stats']['total_scraped']}  
**Total Content:** {metadata['stats']['total_chars']:,} characters  

---

"""
    
    detailed_report_md = f"""# Detailed Company Research Report: {company_name}

**Base URL:** {base_url}  
**Location:** {location}  
**Total URLs Scraped:** {metadata['stats']['total_scraped']}  
**Total Content:** {metadata['stats']['total_chars']:,} characters  

---

"""
    
    category_number = 1
    summaries_list = []
    
    for category in enabled_categories:
        if category in final_report_data:
            category_data = final_report_data[category]
            quality_symbol = quality_map.get(category_data["data_quality"], "⚠️")
            
            summary_report_md += f"## {category_number}. {category} {quality_symbol}\n\n"
            summary_report_md += category_data["summary"]
            summary_report_md += "\n\n"
            
            detailed_report_md += f"## {category_number}. {category} {quality_symbol}\n\n"
            if category in detailed_summaries:
                detailed_report_md += detailed_summaries[category]
                detailed_report_md += "\n\n"
            
            if category in category_content and "sources" in category_content[category]:
                sources = category_content[category]["sources"]
                if sources:
                    sources_text = "**Sources:**\n"
                    for source in sources:
                        sources_text += f"- {source}\n"
                    sources_text += "\n"
                    
                    summary_report_md += sources_text
                    detailed_report_md += sources_text
            
            summary_report_md += "---\n\n"
            detailed_report_md += "---\n\n"
            
            summaries_list.append({
                "category": category,
                "summary": category_data["summary"],
                "detailed_summary": detailed_summaries.get(category, ""),
                "data_quality": category_data["data_quality"]
            })
            
            category_number += 1
    
    report_data = {
        "company_name": company_name,
        "base_url": base_url,
        "location": location,
        "stats": metadata["stats"],
        "summaries": summaries_list,
        "summary_report_markdown": summary_report_md,
        "detailed_report_markdown": detailed_report_md
    }
    
    return report_data

def save_reports(company_name: str, report_data: dict):
    base_path = get_company_path(company_name)
    summaries_folder = f"{base_path}/summaries"
    os.makedirs(summaries_folder, exist_ok=True)
    
    json_file = f"{summaries_folder}/report.json"
    with open(json_file, "w") as f:
        json.dump(report_data, f, indent=2)
    
    summary_md_file = f"{summaries_folder}/summary_report.md"
    with open(summary_md_file, "w") as f:
        f.write(report_data["summary_report_markdown"])
    
    detailed_md_file = f"{summaries_folder}/detailed_report.md"
    with open(detailed_md_file, "w") as f:
        f.write(report_data["detailed_report_markdown"])
    
    print(f"Summary report saved to: {summary_md_file}")
    print(f"Detailed report saved to: {detailed_md_file}")
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
    print(f"AI is generating detailed summaries for {len(categories_with_content)} categories...")
    print(f"{'='*60}\n")
    
    tasks = []
    category_list = []
    
    for category in categories_with_content:
        data = category_content[category]
        tasks.append(summarize_category(company_name, category, data["content"]))
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
    
    print(f"\n{'='*60}")
    print("AI is generating final polished report...")
    print(f"{'='*60}\n")
    
    final_report_data = await generate_final_report(company_name, detailed_summaries)
    
    print(f"\n{'='*60}")
    print("Final report generation complete!")
    print(f"{'='*60}\n")
    
    quality_map = {"sufficient": "✓", "partial": "⚠️", "insufficient": "✗"}
    
    for category, data in final_report_data.items():
        quality_symbol = quality_map.get(data["data_quality"], "⚠️")
        word_count = len(data["summary"].split())
        print(f"✓ {category} ({word_count} words) {quality_symbol}")
    
    print(f"\n{'='*60}")
    print("Assembling reports")
    print(f"{'='*60}\n")
    
    report_data = assemble_reports(company_name, base_url, location, final_report_data, detailed_summaries, metadata, category_content)
    save_reports(company_name, report_data)
    
    sufficient = sum(1 for s in report_data["summaries"] if s["data_quality"] == "sufficient")
    partial = sum(1 for s in report_data["summaries"] if s["data_quality"] == "partial")
    insufficient = sum(1 for s in report_data["summaries"] if s["data_quality"] == "insufficient")
    
    print(f"\n{'='*60}")
    print("Summary Generation Complete!")
    print(f"{'='*60}")
    print(f"Total categories: {len(report_data['summaries'])}")
    print(f"Sufficient: {sufficient} | Partial: {partial} | Insufficient: {insufficient}")
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
