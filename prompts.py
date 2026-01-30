import json

def get_url_selection_prompt(company_name: str, base_url: str, website_urls: list, google_results: dict) -> str:
    return f"""You are a company research assistant analyzing URLs for {company_name} (base URL: {base_url}).

You have been provided with:
1. Website URLs extracted from the company's website
2. All Google search results for each of research categories

Your task is to select the MOST RELEVANT and HIGH-QUALITY URLs for each category.

URL SELECTION STRATEGY:
- Considering the url name and its hypothesized density of information, about the topic(category), choose appropriate number of websites for each category
- Must aim for this amount of urls:
  - Simple categories -> 5-7 URLs
  - Medium complexity categories -> 7-9 URLs
  - Complex categories -> 9-11 URLs
- Use your judgment based on the category's information requirements
- Same website can be selected for multiple categories if it contain relevant information for each of those categories

PRIORITIZATION RULES (in order):
1. Official company website pages ALWAYS preferred over external sources
2. Main/overview pages over specific/detailed subpages
3. Recent content over old content
4. Authoritative sources (company site, major news outlets) over blogs/forums by indidviduals
5. Comprehensive pages that cover about the topic

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

def get_category_summary_prompt(company_name: str, category: str, query: str, content: str) -> str:
    return f"""Based on this search query: "{query}"

Extract relevant information for {company_name}.

CRITICAL RULES:
1. Extract information based on what the query is asking for from the content below
2. Maximum 200-250 words - be as minimal as possible while maintaining quality
3. Do NOT add analysis, interpretation
4. Do NOT repeat the category name in your output
5. Do NOT include contact information (addresses, emails, phone numbers) unless the query specifically asks for it
6. Focus on concrete, specific details from the provided content
7. If multiple sources say the same thing, mention it ONCE

FORMATTING REQUIREMENTS:
- Use bullet points (markdown format with -) for content
- When listing multiple related items (programs, products, features), use sub-bullets:
  - Main category or grouping
    - Item 1
    - Item 2
    - Item 3
- Use **bold** for important terms, names, key metrics, numbers, dates
- Use *italic* for emphasis on specific insights
- Use `code formatting` for technical terms, technologies, product names
- Do NOT use prefixes like "Fact:", "Note:", "Key:", "Strategic:", etc.
- Present information directly and naturally

CONTENT EXTRACTION:
1. Extract only the most relevant facts based on the query
2. Include quantitative data (numbers, percentages, dates) when present
3. Include names, titles, organizations when relevant
4. Include specific programs, products, or initiatives
5. Skip generic or redundant information

Content from sources:
{content}

Extract consise, quality information (maximum 250 words):"""

def get_final_report_prompt(company_name: str, detailed_summaries: dict) -> str:
    summaries_text = ""
    for category, summary in detailed_summaries.items():
        summaries_text += f"\n\n## {category}\n{summary}"
    
    return f"""You are creating a comprehensive company research report for {company_name}.

Below is a complete research report with detailed information across multiple categories.

Your task:
1. REORGANIZE FIRST: Review all content and move misplaced information to appropriate categories
   - Example: Financial metrics mentioned in "Founders and Leadership" → move to "Financial Performance"
   - Example: Partnership details in "Products and Services" → move to "Partnerships"
   Ensure each category contains only relevant information before summarizing.
2. Create clear, polished summaries (150-200 words) for EACH category
3. Maintain all key facts and specific details
4. Ensure consistent writing style and tone across all categories
5. Remove redundancies between categories
6. Do NOT include contact information in any summaries unless it is the Contact Information category

FORMATTING REQUIREMENTS:
- Use bullet points (markdown format with -) for all content 
- Do not use paragraphs or commas to show related items
- When listing multiple related items (programs, products, features), use sub-bullets:
  - Main category or grouping
    - Item 1
    - Item 2
    - Item 3
- Use **bold** for important terms, names, key metrics, numbers, dates
- Use *italic* for emphasis on specific insights
- Use `code formatting` for technical terms, technologies, product names
- Do NOT use prefixes like "Fact:", "Note:", "Key:", "Strategic:", etc.

OUTPUT FORMAT:
Create a complete markdown report with ALL categories.
Use this exact structure:

## 1. Founders and Leadership
- bullet points here

## 2. Business Model and Revenue
- bullet points here

## 3. Products and Services
- bullet points here

Continue for ALL categories in the input below.

Research Report:
{summaries_text}"""