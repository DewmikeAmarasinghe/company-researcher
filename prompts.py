import json

def get_url_selection_prompt(company_name: str, base_url: str, website_urls: list, google_results: dict) -> str:
    return f"""You are a company research assistant analyzing URLs for {company_name} (base URL: {base_url}).

You have been provided with:
1. Website URLs extracted from the company's website
2. All Google search results for each of 25 research categories

Your task is to select the MOST RELEVANT and HIGH-QUALITY URLs for each category.

TARGET: Select 60-100 TOTAL unique URLs across all categories.

URL SELECTION STRATEGY:
- Assess each category's complexity independently
- Simple categories may need 2-4 URLs
- Medium complexity categories may need 3-5 URLs
- Complex categories may need 4-8 URLs
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
    return f"""You are analyzing content about {company_name} for: {category}

CRITICAL RULES:
1. DO NOT include the company name in any headers or titles
2. Use ONLY the category name provided: "{category}"
3. Be as concise as possible while covering key information
4. Aim for 150-200 words maximum
5. Avoid repeating information that likely appears in other categories - focus on category-specific details
6. If multiple sources say the same thing, mention it ONCE

FORMATTING REQUIREMENTS:
- Use bullet points (markdown format with -) for all content
- Use **bold** for important terms, names, key metrics, numbers, dates
- Use *italic* for emphasis on specific insights
- Use `code formatting` for technical terms, technologies, product names
- Do NOT use prefixes like "Fact:", "Note:", "Key:", "Strategic:", etc.
- Present information directly and naturally
- Be specific with numbers, dates, names, concrete details
- Keep each point concise but informative
- Make the summary visually appealing with proper markdown formatting

CONTENT PRIORITIZATION:
1. Unique or differentiating facts first
2. Quantitative data (numbers, percentages, dates)
3. Recent information over historical
4. Specific facts over general statements

Return your response in this JSON format:
{{
  "summary": "Your markdown formatted summary here",
  "data_quality": "sufficient"
}}

Where data_quality is one of:
- "sufficient": enough information for comprehensive answer
- "partial": some information but notable gaps exist
- "insufficient": very limited or unreliable information

Content from sources:
{content}

Provide a well-structured, concise summary (150-200 words) in JSON format following all rules above."""

