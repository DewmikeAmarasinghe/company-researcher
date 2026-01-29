import streamlit as st
import asyncio
import os
import json
import time
from litellm import completion
from crawl4ai import AsyncWebCrawler, UndetectedAdapter
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from google_search import search_google_by_category
from utils import is_social_media_url, ensure_company_directories
from config import (
    API_KEY, MODEL_NAME, BROWSER_HEADLESS, ENABLE_STEALTH, 
    SCRAPE_DELAY, get_enabled_categories, get_search_queries, get_category_query
)
from prompts import get_url_selection_prompt, get_category_summary_prompt, get_final_report_prompt
from urllib.parse import urlparse

st.set_page_config(
    page_title="Company Research Tool",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown('<h1 style="font-size: 3rem;">🔍 Company Research Tool</h1>', unsafe_allow_html=True)

st.markdown("---")

col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    company_name = st.text_input("Company Name *", placeholder="e.g., AOD South Asia (Pvt) Ltd")

with col2:
    base_url = st.text_input("Base URL *", placeholder="e.g., https://www.aod.lk/")

with col3:
    location = st.text_input("Location *", placeholder="e.g., Sri Lanka")

st.markdown("---")

async def run_full_research(company_name: str, base_url: str, location: str):
    """Run the complete research pipeline with real-time UI updates"""
    
    progress_placeholder = st.empty()
    
    with progress_placeholder.container():
        # ==================== STEP 1: Crawl Base URL ====================
        with st.status("🌐 Crawling base URL...", expanded=True) as status_crawl:
            async with AsyncWebCrawler(config=BrowserConfig()) as crawler:
                result = await crawler.arun(url=base_url, config=CrawlerRunConfig())
            
            website_urls = []
            for category, items in result.links.items():
                for link in items:
                    url = link["href"]
                    if url.startswith(("http://", "https://")) and url not in website_urls and not is_social_media_url(url):
                        website_urls.append(url)
            
            status_crawl.write(f"Found {len(website_urls)} URLs from website")
            time.sleep(3)
            status_crawl.update(label="✅ Base URL crawled", state="complete", expanded=False)
        
        # ==================== STEP 2: Google Search ====================
        with st.status("🔍 Searching Google (25 queries)...", expanded=True) as status_search:
            search_queries = get_search_queries(company_name, location)
            status_search.write(f"Running {len(search_queries)} search queries...")
            
            google_results = await search_google_by_category(search_queries)
            
            total_google_urls = sum(len(urls) for urls in google_results.values())
            status_search.write(f"Found {total_google_urls} URLs from Google")
            time.sleep(3)
            status_search.update(label="✅ Google search complete", state="complete", expanded=False)
        
        # ==================== STEP 3: AI URL Selection ====================
        with st.status("🤖 AI is selecting relevant URLs...", expanded=True) as status_select:
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
            
            unique_selected = set()
            for urls in selected_urls.values():
                unique_selected.update(urls)
            
            # Save the URL data
            base_path = ensure_company_directories(company_name)
            all_google_urls = set()
            for urls in google_results.values():
                for url in urls:
                    if not is_social_media_url(url):
                        all_google_urls.add(url)
            
            all_available = set(website_urls) | all_google_urls
            pool_urls = all_available - unique_selected
            
            website_pool = [url for url in website_urls if url in pool_urls]
            google_pool = {}
            for category, urls in google_results.items():
                category_pool = [url for url in urls if url in pool_urls and not is_social_media_url(url)]
                if category_pool:
                    google_pool[category] = category_pool
            
            website_domain_urls = sum(1 for url in website_urls if base_url.split('/')[2] in url)
            google_urls_count = len(all_google_urls)
            
            url_data = {
                "company_name": company_name,
                "base_url": base_url,
                "location": location,
                "stats": {
                    "total_selected": len(unique_selected),
                    "total_pool": len(pool_urls),
                    "sources": {
                        "website_urls": website_domain_urls,
                        "google_results": google_urls_count
                    },
                    "categories": len(enabled_categories)
                },
                "selected_urls": selected_urls,
                "url_pool": {
                    "website_urls": website_pool,
                    "google_results": google_pool
                },
                "sources": {
                    "website_urls": website_urls,
                    "google_results_by_category": google_results
                }
            }
            
            links_file = f"{base_path}/links.json"
            with open(links_file, "w") as f:
                json.dump(url_data, f, indent=2)
            
            status_select.write(f"Selected {len(unique_selected)} relevant URLs")
            time.sleep(3)
            status_select.update(label="✅ URLs selected", state="complete", expanded=False)
        
        # ==================== STEP 4: Scrape URLs ====================
        with st.status("🌐 Scraping selected URLs...", expanded=True) as status_scrape:
            all_urls_to_scrape = set()
            url_to_categories = {}
            
            for category, urls in selected_urls.items():
                for url in urls:
                    all_urls_to_scrape.add(url)
                    if url not in url_to_categories:
                        url_to_categories[url] = []
                    url_to_categories[url].append(category)
            
            status_scrape.write(f"Scraping {len(all_urls_to_scrape)} unique URLs...")
            
            browser_config = BrowserConfig(
                headless=BROWSER_HEADLESS,
                enable_stealth=ENABLE_STEALTH
            )
            
            undetected_adapter = UndetectedAdapter()
            
            crawler_strategy = AsyncPlaywrightCrawlerStrategy(
                browser_config=browser_config,
                browser_adapter=undetected_adapter
            )
            
            async with AsyncWebCrawler(
                crawler_strategy=crawler_strategy,
                config=browser_config
            ) as crawler:
                run_config = CrawlerRunConfig(
                    delay_before_return_html=SCRAPE_DELAY,
                    scan_full_page=True,
                    # exclude_internal_links=False,
                    # exclude_external_links=False,
                    # exclude_social_media_links=False,
                    excluded_tags=['header', 'footer', 'form', 'nav', 'aside', 'script', 'style'],
                    # keep_data_attributes=True,
                    # remove_overlay_elements=True,
                    # exclude_external_images=True,
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
                )
                
                results = await crawler.arun_many(list(all_urls_to_scrape), run_config)
                
                crawled_folder = f"{base_path}/crawled"
                os.makedirs(crawled_folder, exist_ok=True)
                
                scraped_data = []
                total_chars = 0
                
                for idx, result in enumerate(results):
                    if result and result.success:
                        md = result.markdown
                        url = result.url
                        
                        parsed = urlparse(url)
                        filename = parsed.netloc + parsed.path
                        filename = filename.replace("/", "__").strip("_")
                        filepath = f"{crawled_folder}/{filename}.md"
                        
                        with open(filepath, "w") as f:
                            f.write(md)
                        
                        categories = url_to_categories.get(url, [])
                        char_count = len(md)
                        total_chars += char_count
                        
                        scraped_data.append({
                            "url": url,
                            "filepath": filepath,
                            "categories": categories,
                            "length": char_count
                        })
                        
                        status_scrape.write(f"✓ Scraped {idx+1}/{len(all_urls_to_scrape)}: {url[:50]}...")
                
                metadata_file = f"{crawled_folder}/metadata.json"
                with open(metadata_file, "w") as f:
                    json.dump({
                        "company_name": company_name,
                        "base_url": base_url,
                        "location": location,
                        "stats": {
                            "total_scraped": len(scraped_data),
                            "total_failed": len(all_urls_to_scrape) - len(scraped_data),
                            "total_chars": total_chars
                        },
                        "scraped_urls": scraped_data,
                        "url_to_categories": url_to_categories
                    }, f, indent=2)
                
                status_scrape.write(f"Scraped {len(scraped_data)}/{len(all_urls_to_scrape)} URLs successfully")
                time.sleep(3)
                status_scrape.update(label="✅ Scraping complete", state="complete", expanded=False)
        
        # ==================== STEP 5: Generate Detailed Summaries ====================
        with st.status("📝 Generating detailed summaries...", expanded=True) as status_detailed:
            # Load metadata and group by category
            with open(metadata_file, "r") as f:
                metadata = json.load(f)
            
            category_content = {}
            url_to_categories_map = metadata["url_to_categories"]
            
            for item in metadata["scraped_urls"]:
                filepath = item["filepath"]
                url = item["url"]
                categories = url_to_categories_map.get(url, [])
                
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
            
            # Generate detailed summaries for each category
            enabled_categories = get_enabled_categories()
            categories_with_content = [cat for cat in enabled_categories if cat in merged_content]
            
            status_detailed.write(f"Generating summaries for {len(categories_with_content)} categories...")
            
            tasks = []
            category_list = []
            
            for category in categories_with_content:
                data = merged_content[category]
                query = get_category_query(category, company_name, location)
                
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
                
                tasks.append(summarize_category(company_name, category, query, data["content"]))
                category_list.append(category)
            
            summaries = await asyncio.gather(*tasks)
            
            for idx, summary in enumerate(summaries):
                category = category_list[idx]
                word_count = len(summary["summary"].split())
                status_detailed.write(f"✓ {category} ({word_count} words)")
            
            detailed_summaries = {s["category"]: s["summary"] for s in summaries}
            
            time.sleep(3)
            status_detailed.update(label="✅ Detailed summaries generated", state="complete", expanded=False)
        
        # ==================== STEP 6: Generate Final Report ====================
        with st.status("📊 Generating final polished report...", expanded=True) as status_final:
            category_sources = {}
            for category in categories_with_content:
                if category in merged_content:
                    category_sources[category] = merged_content[category]["sources"]
            
            prompt = get_final_report_prompt(company_name, detailed_summaries)
            
            response = completion(
                model=MODEL_NAME,
                api_key=API_KEY,
                messages=[{"role": "user", "content": prompt}],
            )
            
            final_report_content = response["choices"][0]["message"]["content"]
            
            # Add sources to report
            final_report_with_sources = final_report_content.strip()
            final_report_with_sources += "\n\n---\n\n# Research Sources\n\n"
            
            for idx, category in enumerate(enabled_categories, 1):
                if category in category_sources and category_sources[category]:
                    final_report_with_sources += f"## {idx}. {category}\n\n"
                    for source in category_sources[category]:
                        final_report_with_sources += f"- {source}\n"
                    final_report_with_sources += "\n"
            
            # Create detailed report with sources
            detailed_report_content = ""
            for category in enabled_categories:
                if category in detailed_summaries:
                    detailed_report_content += f"## {category}\n\n"
                    detailed_report_content += detailed_summaries[category]
                    detailed_report_content += "\n\n---\n\n"
            
            detailed_report_with_sources = detailed_report_content.strip()
            detailed_report_with_sources += "\n\n---\n\n# Research Sources\n\n"
            
            for idx, category in enumerate(enabled_categories, 1):
                if category in category_sources and category_sources[category]:
                    detailed_report_with_sources += f"## {idx}. {category}\n\n"
                    for source in category_sources[category]:
                        detailed_report_with_sources += f"- {source}\n"
                    detailed_report_with_sources += "\n"
            
            # Assemble reports
            
            summary_report_md = f"""# Company Research Report: {company_name}

**Base URL:** {base_url}  
**Location:** {location}  
**Total URLs Scraped:** {metadata['stats']['total_scraped']}  
**Total Content:** {metadata['stats']['total_chars']:,} characters  

---

"""
            summary_report_md += final_report_with_sources
            
            detailed_report_md = f"""# Detailed Company Research Report: {company_name}

**Base URL:** {base_url}  
**Location:** {location}  
**Total URLs Scraped:** {metadata['stats']['total_scraped']}  
**Total Content:** {metadata['stats']['total_chars']:,} characters  

---

"""
            detailed_report_md += detailed_report_with_sources
            
            summaries_list = []
            for category in enabled_categories:
                if category in detailed_summaries:
                    summaries_list.append({
                        "category": category,
                        "summary": detailed_summaries[category]
                    })
            
            report_data = {
                "company_name": company_name,
                "base_url": base_url,
                "location": location,
                "stats": metadata["stats"],
                "summaries": summaries_list,
                "summary_report_markdown": summary_report_md,
                "detailed_report_markdown": detailed_report_md
            }
            
            # Save reports
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
            
            status_final.write(f"Report saved: {len(summaries_list)} categories")
            time.sleep(3)
            status_final.update(label="✅ Final report generated", state="complete", expanded=False)
    
    # Clear the progress section completely
    progress_placeholder.empty()
    
    return report_data

if st.button("🚀 Start Research", type="primary", use_container_width=True):
    if not company_name or not base_url or not location:
        st.error("⚠️ Please provide company name, base URL, and location")
    else:
        # Run the research
        report_data = asyncio.run(run_full_research(company_name, base_url, location))
        
        # Show success message
        st.success("🎉 Research Completed Successfully!")
        
        safe_name = "".join(c for c in company_name.lower().replace(" ", "_") if c.isalnum() or c in ["_", "-"])
        summary_report_path = f"results/{safe_name}/summaries/summary_report.md"
        detailed_report_path = f"results/{safe_name}/summaries/detailed_report.md"
        json_path = f"results/{safe_name}/summaries/report.json"
        
        if os.path.exists(summary_report_path) and os.path.exists(detailed_report_path):
            with open(summary_report_path, "r", encoding="utf-8") as f:
                summary_content = f.read()
            
            with open(detailed_report_path, "r", encoding="utf-8") as f:
                detailed_content = f.read()
            
            st.markdown("---")
            st.markdown("### 📄 Research Reports")
            
            tab1, tab2 = st.tabs(["📊 Executive Summary", "📄 Detailed Report"])
            
            with tab1:
                col1, col2, col3 = st.columns([2, 6, 2])
                with col2:
                    st.markdown(summary_content)
                    st.download_button(
                        label="⬇️ Download Executive Summary",
                        data=summary_content,
                        file_name=f"{company_name}_summary.md",
                        mime="text/markdown",
                        use_container_width=True
                    )
            
            with tab2:
                col1, col2, col3 = st.columns([2, 6, 2])
                with col2:
                    st.markdown(detailed_content)
                    st.download_button(
                        label="⬇️ Download Detailed Report",
                        data=detailed_content,
                        file_name=f"{company_name}_detailed.md",
                        mime="text/markdown",
                        use_container_width=True
                    )

st.markdown("---")
st.markdown("### 📚 Recent Reports")

if os.path.exists("results"):
    folders = [f for f in os.listdir("results") if os.path.isdir(os.path.join("results", f))]
    
    if folders:
        for folder in sorted(folders, reverse=True):
            summary_report_path = f"results/{folder}/summaries/summary_report.md"
            detailed_report_path = f"results/{folder}/summaries/detailed_report.md"
            
            if os.path.exists(summary_report_path):
                with st.expander(f"📁 {folder.replace('_', ' ').title()}", expanded=False):
                    
                    view_col1, view_col2 = st.columns(2)
                    
                    with view_col1:
                        if st.button("📊 View Summary", key=f"sum_{folder}", use_container_width=True):
                            st.session_state[f'view_mode_{folder}'] = 'summary'
                    
                    with view_col2:
                        if os.path.exists(detailed_report_path):
                            if st.button("📄 View Detailed Report", key=f"det_{folder}", use_container_width=True):
                                st.session_state[f'view_mode_{folder}'] = 'detailed'
                    
                    if st.session_state.get(f'view_mode_{folder}') == 'summary':
                        with open(summary_report_path, "r", encoding="utf-8") as f:
                            content = f.read()
                        
                        st.markdown("---")
                        col1, col2, col3 = st.columns([2, 6, 2])
                        with col2:
                            st.markdown(content)
                        
                        if st.button("✖ Close", key=f"close_{folder}"):
                            st.session_state[f'view_mode_{folder}'] = False
                            st.rerun()
                    
                    elif st.session_state.get(f'view_mode_{folder}') == 'detailed':
                        with open(detailed_report_path, "r", encoding="utf-8") as f:
                            content = f.read()
                        
                        st.markdown("---")
                        col1, col2, col3 = st.columns([2, 6, 2])
                        with col2:
                            st.markdown(content)
                        
                        if st.button("✖ Close", key=f"close_{folder}"):
                            st.session_state[f'view_mode_{folder}'] = False
                            st.rerun()
    else:
        st.info("ℹ️ No reports generated yet. Start your first research above!")
else:
    st.info("ℹ️ No reports generated yet. Start your first research above!")