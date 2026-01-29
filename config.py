import os

API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = "openai/gpt-5-nano"

DELAY_BETWEEN_QUERIES = 1

BROWSER_HEADLESS = False
ENABLE_STEALTH = True

SCRAPE_DELAY = 5

CATEGORIES = {
    "Founders and Leadership": {
        "query": "{company} {location} about company founders CEO leadership team",
        "enabled": True
    },
    "Business Model and Revenue": {
        "query": "{company} {location} business model revenue streams pricing strategy",
        "enabled": True
    },
    "Products and Services": {
        "query": "{company} {location} products services offerings complete list",
        "enabled": True
    },
    "Company History": {
        "query": "{company} {location} company history founding story timeline milestones",
        "enabled": True
    },
    "Competitive Landscape": {
        "query": "{company} {location} competitors alternatives market",
        "enabled": True
    },
    "Market Position": {
        "query": "{company} {location} market share industry position ranking",
        "enabled": True
    },
    "Recent News and Updates": {
        "query": "{company} {location} news press releases 2024 2025 2026",
        "enabled": True
    },
    "Organizational Structure": {
        "query": "{company} {location} organizational structure management departments",
        "enabled": True
    },
    "Achievements and Recognition": {
        "query": "{company} {location} achievements awards recognition certifications",
        "enabled": True
    },
    "Customer Base": {
        "query": "{company} {location} target customers client base industries served",
        "enabled": True
    },
    "Mission and Values": {
        "query": "{company} {location} mission vision values culture",
        "enabled": True
    },
    "Technology Stack": {
        "query": "{company} {location} technology stack software infrastructure",
        "enabled": True
    },
    "Partnerships": {
        "query": "{company} {location} partnerships alliances collaborations",
        "enabled": True
    },
    "Company Size": {
        "query": "{company} {location} employees headcount team size offices locations",
        "enabled": True
    },
    "Future Plans": {
        "query": "{company} {location} expansion plans growth strategy roadmap",
        "enabled": True
    },
    "Awards and Certifications": {
        "query": "{company} {location} industry awards certifications accolades",
        "enabled": True
    },
    "Financial Performance": {
        "query": "{company} {location} financial performance revenue funding valuation",
        "enabled": True
    },
    "Challenges and Opportunities": {
        "query": "{company} {location} challenges opportunities",
        "enabled": True
    },
    "Company Culture": {
        "query": "{company} {location} work culture employee reviews workplace",
        "enabled": True
    },
    "Customer Reviews": {
        "query": "{company} {location} customer testimonials reviews ratings feedback",
        "enabled": True
    },
    "Innovation and R&D": {
        "query": "{company} {location} innovation R&D research development",
        "enabled": True
    },
    "Social Responsibility": {
        "query": "{company} {location} CSR sustainability social responsibility",
        "enabled": True
    },
    "Case Studies": {
        "query": "{company} {location} case studies success stories projects",
        "enabled": True
    },
    "Pricing Information": {
        "query": "{company} {location} pricing packages plans costs",
        "enabled": True
    },
    "Contact Information": {
        "query": "contact information address email phone locations of {company} {location}",
        "enabled": True
    }
}

SOCIAL_MEDIA_DOMAINS = [
    'facebook.com', 'twitter.com', 'x.com', 'instagram.com', 
    'linkedin.com', 'youtube.com', 'tiktok.com', 'pinterest.com',
    'reddit.com', 'snapchat.com', 'whatsapp.com', 'telegram.org',
    'discord.com', 'twitch.tv', 'vimeo.com', 'tumblr.com'
]

def get_enabled_categories():
    return [name for name, config in CATEGORIES.items() if config["enabled"]]

def get_search_queries(company_name: str, location: str = "") -> dict:
    location_str = f" {location}" if location else ""
    
    return {
        name: config["query"].format(company=company_name, location=location_str)
        for name, config in CATEGORIES.items() if config["enabled"]
    }

def get_category_query(category: str, company_name: str, location: str = "") -> str:
    location_str = f" {location}" if location else ""
    
    if category in CATEGORIES:
        return CATEGORIES[category]["query"].format(company=company_name, location=location_str)
    return ""
