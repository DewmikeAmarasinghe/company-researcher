import streamlit as st
import asyncio
import os
import json
import shutil
from datetime import datetime
from ai_mode import (
    generate_queries, 
    get_query_titles,
    crawl_single_query,
    generate_detailed_report,
    generate_summary_from_report,
    add_sources_to_summary
)
from crawl4ai import AsyncWebCrawler, UndetectedAdapter
from crawl4ai.async_configs import BrowserConfig
from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy

st.set_page_config(
    page_title="Company Research Tool",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown('<h1 style="font-size: 3rem;">🔍 Company Research Tool</h1>', unsafe_allow_html=True)

st.markdown("---")

col1, col2 = st.columns([1, 1])

with col1:
    company_name = st.text_input("Company Name *", placeholder="e.g., Basecamp")

with col2:
    location = st.text_input("Location *", placeholder="e.g., USA")

st.markdown("---")

if st.button("🚀 Start Research", type="primary", width="stretch"):
    if not company_name or not location:
        st.error("⚠️ Please provide both company name and location")
    else:
        safe_company_name = company_name.replace(' ', '_').replace(',', '').replace('(', '').replace(')', '').lower()
        company_folder = f"google_results/{safe_company_name}"
        
        progress_bar = st.progress(0)
        status_box = st.empty()
        
        queries = generate_queries(company_name, location)
        query_titles = get_query_titles()
        total_queries = len(queries)
        
        st.markdown('<h2 style="font-size: 2rem;">📊 Research Progress</h2>', unsafe_allow_html=True)
        progress_table = st.empty()
        progress_section = st.container()
        
        async def run_research():
            if os.path.exists(company_folder):
                shutil.rmtree(company_folder)
            os.makedirs(company_folder, exist_ok=True)
            
            browser_config = BrowserConfig(headless=True)
            undetected_adapter = UndetectedAdapter()
            crawler_strategy = AsyncPlaywrightCrawlerStrategy(
                browser_config=browser_config,
                browser_adapter=undetected_adapter
            )
            
            query_results = []
            progress_data = []
            
            async with AsyncWebCrawler(crawler_strategy=crawler_strategy, config=browser_config) as crawler:
                for idx, (query, title) in enumerate(zip(queries, query_titles), 1):
                    progress = idx / total_queries
                    progress_bar.progress(progress)
                    
                    status_box.info(f"**Querying for:** {title}")
                    
                    result = await crawl_single_query(crawler, query)
                    
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
                    
                    query_results.append(query_data)
                    
                    status_icon = "✅" if result.success else "❌"
                    chars = len(result.markdown) if result.success else 0
                    links_count = len(external_links)
                    
                    progress_data.insert(0, {
                        "Status": status_icon,
                        "Section": title,
                        "Characters": f"{chars:,}",
                        "Links": links_count
                    })
                    
                    progress_table.dataframe(progress_data, width="stretch", hide_index=True)
            
            status_box.info("**Saving detailed report...**")
            
            detailed_json_filename = f"{company_folder}/detailed_report.json"
            with open(detailed_json_filename, "w", encoding="utf-8") as f:
                json.dump(query_results, f, indent=2, ensure_ascii=False)
            
            detailed_report_md = generate_detailed_report(query_results)
            detailed_report_md = f"# Detailed Research Report: {company_name}\n\n**Location:** {location}\n\n**Generated:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}\n\n---\n\n{detailed_report_md}"
            
            detailed_report_filename = f"{company_folder}/detailed_report.md"
            with open(detailed_report_filename, "w", encoding="utf-8") as f:
                f.write(detailed_report_md)
            
            status_box.info("**Generating AI summary...**")
            
            full_report = ""
            for query_data in query_results:
                full_report += query_data['content'] + "\n\n"
            
            summary = generate_summary_from_report(full_report, company_name, location)
            summary_with_sources = add_sources_to_summary(summary, query_results)
            
            summary_filename = f"{company_folder}/summary.md"
            with open(summary_filename, "w", encoding="utf-8") as f:
                f.write(summary_with_sources)
            
            status_box.empty()
            progress_bar.empty()
            progress_table.empty()
            
            return summary_with_sources, detailed_report_md
        
        summary_content, detailed_content = asyncio.run(run_research())
        
        with progress_section:
            st.empty()
        
        st.success("Research Completed Successfully! 🎉")
        
        st.markdown("---")
        
        tab1, tab2 = st.tabs(["📊 Executive Summary", "📄 Detailed Report"])
        
        with tab1:
            col1, col2, col3 = st.columns([2, 6, 2])
            with col2:
                st.markdown(summary_content)
            
            summary_file = f"{company_folder}/summary.md"
            if os.path.exists(summary_file):
                with open(summary_file, "r", encoding="utf-8") as f:
                    st.download_button(
                        label="⬇️ Download Summary",
                        data=f.read(),
                        file_name=f"{company_name}_summary.md",
                        mime="text/markdown",
                        width="stretch"
                    )
        
        with tab2:
            col1, col2, col3 = st.columns([2, 6, 2])

            with col2:
                st.markdown(detailed_content)
            
            detailed_file = f"{company_folder}/detailed_report.md"
            if os.path.exists(detailed_file):
                with open(detailed_file, "r", encoding="utf-8") as f:
                    st.download_button(
                        label="⬇️ Download Detailed Report",
                        data=f.read(),
                        file_name=f"{company_name}_detailed.md",
                        mime="text/markdown",
                        width="stretch"
                    )

st.markdown("---")
st.markdown('<h3 style="font-size: 1.8rem;">📚 Recent Reports</h3>', unsafe_allow_html=True)

if os.path.exists("google_results"):
    folders = [f for f in os.listdir("google_results") if os.path.isdir(os.path.join("google_results", f))]
    
    if folders:
        for folder in sorted(folders):
            with st.expander(f"📁 {folder.replace('_', ' ').title()}", expanded=False):
                
                summary_path = f"google_results/{folder}/summary.md"
                detailed_path = f"google_results/{folder}/detailed_report.md"
                
                view_col1, view_col2 = st.columns(2)
                
                with view_col1:
                    if os.path.exists(summary_path):
                        if st.button("📊 View Summary", key=f"sum_{folder}", width="stretch"):
                            st.session_state[f'view_mode_{folder}'] = 'summary'
                
                with view_col2:
                    if os.path.exists(detailed_path):
                        if st.button("📄 View Detailed Report", key=f"det_{folder}", width="stretch"):
                            st.session_state[f'view_mode_{folder}'] = 'detailed'
                
                if st.session_state.get(f'view_mode_{folder}') == 'summary':
                    with open(summary_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        st.markdown("---")
                        col_a, col_b, col_c = st.columns([2, 6, 2])
                        with col_b:
                            st.markdown(content)
                        if st.button("✖ Close", key=f"close_{folder}"):
                            del st.session_state[f'view_mode_{folder}']
                            st.rerun()
                
                elif st.session_state.get(f'view_mode_{folder}') == 'detailed':
                    with open(detailed_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        st.markdown("---")
                        col_a, col_b, col_c = st.columns([2, 6, 2])
                        with col_b:
                            st.markdown(content)
                        if st.button("✖ Close", key=f"close_{folder}"):
                            del st.session_state[f'view_mode_{folder}']
                            st.rerun()
    else:
        st.info("ℹ️ No reports generated yet. Start your first research above!")
else:
    st.info("ℹ️ No reports generated yet. Start your first research above!")

st.markdown("---")
st.markdown('<p style="text-align: center; color: gray; font-size: 1rem;">Made with ❤️ using Streamlit and Crawl4AI</p>', unsafe_allow_html=True)