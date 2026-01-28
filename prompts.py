import json

def get_url_selection_prompt(company_name: str, base_url: str, website_urls: list, google_results: dict) -> str:
    return f"""You are a company research assistant analyzing URLs for {company_name} (base URL: {base_url}).

You have been provided with:
1. Website URLs extracted from the company's website
2. All Google search results for each of 25 research categories

Your task is to select the MOST RELEVANT and HIGH-QUALITY URLs for each category.

TARGET: Select 80-120 TOTAL unique URLs across all categories.

URL SELECTION STRATEGY:
- Assess each category's complexity independently
- Simple categories may need 3-5 URLs
- Medium complexity categories may need 5-7 URLs
- Complex categories may need 7-9 URLs
- Use your judgment based on the category's information requirements

PRIORITIZATION RULES (in order):
1. Official company website pages ALWAYS preferred over external sources
2. Main/overview pages over specific/detailed subpages
3. Recent content over old content
4. Authoritative sources (company site, major news outlets) over blogs/forums
5. Comprehensive pages that cover multiple topics over narrow single-topic pages

URL REUSE STRATEGY:
- Reuse the same URL across multiple relevant categories
- Example: An "About Us" page should be used for Founders, History, Mission, Values
- Example: A "Services" page should be used for Products, Services, Business Model
- This reduces total unique URLs while maintaining category coverage

STRICT EXCLUSIONS:
1. NO social media links
2. NO career/jobs/hiring pages (except for Company Culture if highly relevant)
3. NO PDFs or file downloads
4. NO blog posts unless they are official company announcements
5. NO duplicate or very similar URLs
6. NO press release aggregator sites
7. NO low-quality external sources

QUALITY CHECKLIST FOR EACH URL:
- Does this URL provide unique, valuable information?
- Is this the BEST source for this category?
- Can I reuse an already-selected URL instead?
- Will this URL contain substantial, relevant content?

Return your response in JSON format with this exact structure:
{{
  "Founders and Leadership": ["url1", "url2"],
  "Business Model and Revenue": ["url1", "url2"],
  "Products and Services": ["url1", "url2", "url3"],
  ...
}}

REMEMBER: Quality over quantity. Only select URLs that exist in the lists below.

Website URLs ({len(website_urls)} total):
{json.dumps(website_urls, indent=2)}

Google Results by Category:
{json.dumps(google_results, indent=2)}
"""

def get_category_summary_prompt(company_name: str, category: str, content: str) -> str:
    return f"""Extract and present ALL relevant information about {category} for {company_name}.

CRITICAL RULES:
1. Extract facts directly from the content below
2. Do NOT add analysis, interpretation, or external knowledge
3. Do NOT repeat the category name in your output
4. Focus on concrete, specific details from the provided content
5. Aim for 300-350 words
6. If multiple sources say the same thing, mention it ONCE
7. Avoid repeating information that likely appears in other categories

FORMATTING REQUIREMENTS:
- Use bullet points (markdown format with -) for all content
- Use **bold** for important terms, names, key metrics, numbers, dates
- Use *italic* for emphasis on specific insights
- Use `code formatting` for technical terms, technologies, product names
- Do NOT use prefixes like "Fact:", "Note:", "Key:", "Strategic:", etc.
- Present information directly and naturally
- Be specific with numbers, dates, names, concrete details
- Make the summary visually appealing with proper markdown formatting

CONTENT EXTRACTION:
1. Extract all relevant facts about {category}
2. Include quantitative data (numbers, percentages, dates)
3. Include names, titles, organizations mentioned
4. Include specific programs, products, or initiatives
5. Include any unique or differentiating information

Content from sources:
{content}

Extract comprehensive information (300-350 words):"""

def get_final_report_prompt(company_name: str, detailed_summaries: dict) -> str:
    summaries_text = ""
    for category, summary in detailed_summaries.items():
        summaries_text += f"\n\n### {category}\n{summary}"
    
    return f"""You are creating a polished company research report for {company_name}.

You will receive 25 detailed category summaries (300-350 words each). Your task:
1. Create concise, polished summaries (120-150 words) for each category
2. Maintain all key facts and specific details
3. Ensure consistent writing style and tone across all categories
4. Remove redundancies between categories
5. Assign data quality scores based on content depth and completeness
6. Do NOT include category names in the summary text itself

FORMATTING FOR EACH SUMMARY:
- Use bullet points (markdown format with -)
- Use **bold** for key terms, names, metrics
- Use *italic* for emphasis
- Present information clearly and naturally
- DO NOT use prefixes like "Fact:", "Note:", etc.

DATA QUALITY CRITERIA:
- "sufficient": 250+ words in detailed version, multiple specific facts, comprehensive coverage
- "partial": 150-250 words in detailed version, some facts but notable gaps
- "insufficient": <150 words in detailed version, vague or minimal information

Return ONLY a JSON object in this exact format:
{{
  "Founders and Leadership": {{
    "summary": "concise polished markdown (120-150 words)",
    "data_quality": "sufficient"
  }},
  "Business Model and Revenue": {{
    "summary": "concise polished markdown (120-150 words)",
    "data_quality": "partial"
  }},
  ...
}}

Detailed summaries to polish:
{summaries_text}"""

