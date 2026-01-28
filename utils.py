import os
import shutil
from config import SOCIAL_MEDIA_DOMAINS

def is_social_media_url(url: str) -> bool:
    return any(domain in url.lower() for domain in SOCIAL_MEDIA_DOMAINS)

def get_safe_filename(company_name: str) -> str:
    return "".join(c for c in company_name.lower().replace(" ", "_") if c.isalnum() or c in ["_", "-"])

def get_company_path(company_name: str) -> str:
    safe_name = get_safe_filename(company_name)
    return f"results/{safe_name}"

def ensure_company_directories(company_name: str, clean: bool = False) -> str:
    base_path = get_company_path(company_name)
    
    if clean and os.path.exists(base_path):
        shutil.rmtree(base_path)
    
    os.makedirs(f"{base_path}/crawled", exist_ok=True)
    os.makedirs(f"{base_path}/summaries", exist_ok=True)
    
    return base_path

def validate_company_info(company_name: str, base_url: str, location: str):
    if not company_name or not company_name.strip():
        raise ValueError("Company name cannot be empty")
    
    if not base_url or not base_url.strip():
        raise ValueError("Base URL cannot be empty")
    
    if not base_url.startswith(("http://", "https://")):
        raise ValueError("Base URL must start with http:// or https://")
    
    if not location or not location.strip():
        raise ValueError("Location cannot be empty")
