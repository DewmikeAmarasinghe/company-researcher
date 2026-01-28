import streamlit as st
import asyncio
import os
import json
from summarize import summarize_company

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

if st.button("🚀 Start Research", type="primary", use_container_width=True):
    if not company_name or not base_url or not location:
        st.error("⚠️ Please provide company name, base URL, and location")
    else:
        progress_container = st.container()
        
        with progress_container:
            st.markdown("### 📊 Research Progress")
            
            status_crawl = st.empty()
            status_search = st.empty()
            status_select = st.empty()
            status_scrape = st.empty()
            status_summarize = st.empty()
            
            progress_bar = st.progress(0)
        
        async def run_research():
            status_crawl.info("🌐 Crawling base URL...")
            progress_bar.progress(0.1)
            
            await asyncio.sleep(0.5)
            
            status_search.info("🔍 Searching Google...")
            progress_bar.progress(0.2)
            
            await asyncio.sleep(0.5)
            
            status_select.info("🤖 AI is selecting relevant URLs...")
            progress_bar.progress(0.3)
            
            await summarize_company(
                company_name=company_name,
                base_url=base_url,
                location=location,
                skip_scraping=False
            )
            
            progress_bar.progress(1.0)
            status_crawl.success("✅ Base URL crawled")
            status_search.success("✅ Google search complete")
            status_select.success("✅ URLs selected")
            status_scrape.success("✅ Scraping complete")
            status_summarize.success("✅ Summarization complete")
        
        asyncio.run(run_research())
        
        st.success("🎉 Research Completed Successfully!")
        
        safe_name = "".join(c for c in company_name.lower().replace(" ", "_") if c.isalnum() or c in ["_", "-"])
        report_path = f"results/{safe_name}/summaries/report.md"
        json_path = f"results/{safe_name}/summaries/report.json"
        
        if os.path.exists(report_path):
            with open(report_path, "r", encoding="utf-8") as f:
                report_content = f.read()
            
            st.markdown("---")
            st.markdown("### 📄 Research Report")
            
            tab1, tab2 = st.tabs(["📊 Report", "⚠️ Data Quality"])
            
            with tab1:
                st.markdown(report_content)
                
                col1, col2, col3 = st.columns([2, 6, 2])
                with col2:
                    st.download_button(
                        label="⬇️ Download Report (Markdown)",
                        data=report_content,
                        file_name=f"{company_name}_report.md",
                        mime="text/markdown",
                        use_container_width=True
                    )
            
            with tab2:
                if os.path.exists(json_path):
                    with open(json_path, "r", encoding="utf-8") as f:
                        report_data = json.load(f)
                    
                    summaries = report_data.get("summaries", [])
                    
                    sufficient = [s for s in summaries if s["data_quality"] == "sufficient"]
                    partial = [s for s in summaries if s["data_quality"] == "partial"]
                    insufficient = [s for s in summaries if s["data_quality"] == "insufficient"]
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("✅ Sufficient", len(sufficient))
                    with col2:
                        st.metric("⚠️ Partial", len(partial))
                    with col3:
                        st.metric("✗ Insufficient", len(insufficient))
                    
                    if partial:
                        st.markdown("#### ⚠️ Partial Data Quality")
                        for s in partial:
                            st.warning(f"**{s['category']}** - {s['word_count']} words")
                    
                    if insufficient:
                        st.markdown("#### ✗ Insufficient Data Quality")
                        for s in insufficient:
                            st.error(f"**{s['category']}** - {s['word_count']} words")

st.markdown("---")
st.markdown("### 📚 Recent Reports")

if os.path.exists("results"):
    folders = [f for f in os.listdir("results") if os.path.isdir(os.path.join("results", f))]
    
    if folders:
        for folder in sorted(folders, reverse=True):
            report_path = f"results/{folder}/summaries/report.md"
            
            if os.path.exists(report_path):
                with st.expander(f"📁 {folder.replace('_', ' ').title()}", expanded=False):
                    
                    if st.button("👁️ View Report", key=f"view_{folder}", use_container_width=True):
                        st.session_state[f'show_{folder}'] = True
                    
                    if st.session_state.get(f'show_{folder}'):
                        with open(report_path, "r", encoding="utf-8") as f:
                            content = f.read()
                        
                        st.markdown("---")
                        st.markdown(content)
                        
                        if st.button("✖ Close", key=f"close_{folder}"):
                            st.session_state[f'show_{folder}'] = False
                            st.rerun()
    else:
        st.info("ℹ️ No reports generated yet. Start your first research above!")
else:
    st.info("ℹ️ No reports generated yet. Start your first research above!")

st.markdown("---")
st.markdown('<p style="text-align: center; color: gray; font-size: 1rem;">Made with ❤️ using Streamlit and Crawl4AI</p>', unsafe_allow_html=True)
