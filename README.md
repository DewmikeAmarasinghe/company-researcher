## Lead Extractor

Minimal web crawler project with two separate implementations.

- **If using `uv`**: run `uv sync` to install dependencies from `pyproject.toml`.
- **If using `pip`**: create a venv, then install with `pip install -e .` (or `pip install .`) so `pyproject.toml` is used as the source of dependencies.
- Add your `OPENAI_API_KEY` to .env

---

### Project structure

**Google AI mode**

```text
google_results/
  ... (generated result files)

ai_mode.py
streamlit_ai.py
```

**Manual scraper**

```text
results/
  ... (generated result files)

config.py
utils.py
google_search.py
find_urls.py
scrape.py
summarize.py
streamlit_scrape.py
```

---

### How to run

- **Google AI mode app**
  - `streamlit run streamlit_ai.py`

- **Manual scraper app**
  - `streamlit run streamlit_scrape.py`

---

### AI mode workflow
```mermaid
flowchart TD
    Start([Start: AI-Powered Research]) --> Input[/Input: Company Name, Location/]
    
    Input --> GenQueries[Generate 25 Research Queries]
    
    GenQueries --> Sequential[Sequential Google AI Search Mode]
    
    Sequential --> Q1[Query 1: Founders & Leadership<br/>⏱️ SCRAPE_DELAY + Delay 1s]
    Q1 --> Q2[Query 2: Business Model<br/>⏱️ SCRAPE_DELAY + Delay 1s]
    Q2 --> Dots1[...]
    Dots1 --> Q25[Query 25: Contact Information<br/>⏱️ SCRAPE_DELAY + Delay 1s]
    
    Q25 --> CollectData[Collect All Query Results]
    
    CollectData --> SaveJSON[Save detailed_report.json]
    
    SaveJSON --> GenDetailed[Generate Detailed Markdown Report]
    
    GenDetailed --> SaveDetailed[Save detailed_report.md<br/>with all 25 sections + sources]
    
    SaveDetailed --> PrepareContent[Prepare Full Report Content]
    
    PrepareContent --> AISummary[AI Generates Executive Summary<br/>GPT-5-Nano]
    
    AISummary --> AddSources[Add Sources to Summary]
    
    AddSources --> SaveSummary[Save summary.md]
    
    SaveSummary --> End([End: Reports Generated])
```

---

### Scraper workflow

```mermaid
flowchart TD
    Start([Start: Company Research]) --> Input[/Input: Company Name, Base URL, Location/]
    
    Input --> Crawl[Crawl Base Website]
    Crawl --> Google[Sequential Google Searches]
    
    Google --> Q1[Query: Founders & Leadership]
    Q1 --> Q2[Query: Business Model]
    Q2 --> Qn[Query: ... More Categories]
    
    Qn --> AISelect[AI Selects Best URLs per Category]
    AISelect --> SaveLinks[Save links.json]
    
    SaveLinks --> ParallelScrape{Parallel Web Scraping}
    
    ParallelScrape --> |Thread 1| Scrape1[Scrape URL 1]
    ParallelScrape --> |Thread 2| Scrape2[Scrape URL 2]
    ParallelScrape --> |Thread 3| Scrape3[Scrape URL 3]
    ParallelScrape --> |Thread N| ScrapeN[Scrape URL N]
    
    Scrape1 & Scrape2 & Scrape3 & ScrapeN --> SaveCrawled[Save Markdown Files + metadata.json]
    
    SaveCrawled --> Group[Group Content by Category]
    
    Group --> ParallelSummarize{Parallel AI Summarization}
    
    ParallelSummarize --> |Task 1| Sum1[Summarize Category 1]
    ParallelSummarize --> |Task 2| Sum2[Summarize Category 2]
    ParallelSummarize --> |Task 3| Sum3[Summarize Category 3]
    ParallelSummarize --> |Task N| SumN[Summarize Category N]
    
    Sum1 & Sum2 & Sum3 & SumN --> Collect[Collect All Summaries]
    
    Collect --> FinalReport[AI Generates Final Polished Report]
    
    FinalReport --> AddSources[Add Sources to Reports]
    
    AddSources --> SaveReports[Save summary_report.md & detailed_report.md]
    
    SaveReports --> End([End: Reports Generated])
```