from dotenv import load_dotenv
from agents import Agent, Runner, trace, Tool, AgentOutputSchema
from agents.mcp import MCPServerStdio
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
import asyncio
import os
import httpx
import json
import re
from urllib.parse import urlparse
import logging
from bs4 import BeautifulSoup
from .fetcher import fetch_html_content
from .helper import extract_json_string

load_dotenv(override=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- PYDANTIC MODELS FOR STRUCTURED DATA --- #
class CompanyData(BaseModel):
    company_name: str
    website_url: Optional[str] = None
    address: Optional[str] = None
    contact_email: Optional[str] = None
    phone_number: Optional[str] = None
    description: Optional[str] = None
    automation_proposal: Optional[str] = None
    source_url: str = Field(description="The URL where this company was found")
    confidence_score: float = Field(description="Confidence in data quality (0.0-1.0)", ge=0.0, le=1.0)

class ScrapingResult(BaseModel):
    companies: List[CompanyData] = Field(description="List of extracted company data")
    total_urls_processed: int = Field(description="Total number of URLs attempted")
    successful_scrapes: int = Field(description="Number of successfully scraped URLs")
    failed_scrapes: int = Field(description="Number of failed scrapes")
    errors: List[str] = Field(description="List of error messages")

# --- PAGE TYPE DETECTION --- #
async def detect_page_type(html_content: str, url: str) -> str:
    """
    Detect if page is single company or aggregator.
    Returns: 'single_company' or 'aggregator'
    """
    try:
        # Convert to lowercase for easier pattern matching
        html_lower = html_content.lower()
        
        # Patterns that suggest aggregator/directory pages
        aggregator_patterns = [
            r'business\s+directory',
            r'company\s+list',
            r'search\s+results',
            r'find\s+companies',
            r'business\s+listing',
            r'companies\s+in',
            r'local\s+business',
            r'yellow\s+pages',
            r'business\s+guide',
            r'company\s+directory',
            r'<table[^>]*class[^>]*listing',
            r'<div[^>]*class[^>]*listing',
            r'<ul[^>]*class[^>]*results',
            r'<div[^>]*class[^>]*results',
            r'<div[^>]*class[^>]*company-list',
            r'<div[^>]*class[^>]*business-list'
        ]
        
        # Count potential company mentions
        company_mentions = len(re.findall(r'\b(company|business|firm|enterprise|corporation|inc|llc|gmbh|ag)\b', html_lower))
        
        # Check for aggregator patterns
        aggregator_score = 0
        for pattern in aggregator_patterns:
            if re.search(pattern, html_lower):
                aggregator_score += 1
        
        # Check for multiple contact sections or addresses
        contact_sections = len(re.findall(r'(contact|address|phone|email)', html_lower))
        
        # Decision logic
        if aggregator_score >= 2 or company_mentions > 10 or contact_sections > 5:
            logger.info(f"Detected aggregator page: {url} (score: {aggregator_score}, mentions: {company_mentions})")
            return 'aggregator'
        else:
            logger.info(f"Detected single company page: {url}")
            return 'single_company'
            
    except Exception as e:
        logger.warning(f"Error detecting page type for {url}: {str(e)}")
        # Default to single company if detection fails
        return 'single_company'

# --- SINGLE COMPANY PAGE SCRAPING --- #
async def scrape_single_company_page(html_content: str, url: str) -> List[CompanyData]:
    """
    Extract detailed information from a single company website.
    """
    try:
        if not html_content or len(html_content.strip()) < 100:
            logger.warning(f"HTML content too short for {url}: {len(html_content)} characters")
            return []
            
        params = {"command": "uvx", "args": ["mcp-server-fetch"]}
        
        INSTRUCTIONS = """
        You are a Company Information Extractor. Extract structured information about a single company from the provided HTML.

        RULES:
        - The provided HTML snippet may be partial or simplified. DO NOT ask for more HTML.
        - Output ONLY a JSON array with exactly one object.
        - Do not include code fences, language labels, or commentary.
        - Only extract information that is clearly visible in the HTML. Do not guess or fabricate data.

        Each object must contain:
        - company_name (string, required)
        - website_url (string or null)
        - address (string or null)
        - contact_email (string or null)
        - phone_number (string or null)
        - description (string or null)
        - automation_proposal (string, generic suggestion)
        """

        async with MCPServerStdio(params=params, client_session_timeout_seconds=15) as mcp_server:
            agent = Agent(
                name="SingleCompanyScraper",
                instructions=INSTRUCTIONS,
                model="gpt-4o-mini",
                mcp_servers=[mcp_server],
            )
            
            user_msg = (
                "Extract one company object from the following HTML. "
                "Return ONLY a JSON array with one object.\n\n"
                f"{html_content[:5000]}"
            )

            result = await Runner.run(agent, user_msg, max_turns=1)
            
            companies: List[CompanyData] = []
            if result.final_output:
                try:
                    raw = result.final_output if isinstance(result.final_output, str) else json.dumps(result.final_output)
                    clean = extract_json_string(raw)
                    data = json.loads(clean)

                    if isinstance(data, list) and data:
                        company_data = data[0]
                        if isinstance(company_data, dict):
                            companies.append(CompanyData(
                                company_name=company_data.get('company_name', 'Unknown Company'),
                                website_url=company_data.get('website_url'),
                                address=company_data.get('address'),
                                contact_email=company_data.get('contact_email'),
                                phone_number=company_data.get('phone_number'),
                                description=company_data.get('description'),
                                automation_proposal=company_data.get('automation_proposal'),
                                source_url=url,
                                confidence_score=0.8  # Higher confidence for single-company pages
                            ))
                except Exception as e:
                    logger.error(f"Error parsing single company data: {str(e)}")
            
            return companies
            
    except Exception as e:
        logger.error(f"Error scraping single company page {url}: {str(e)}")
        return []

def preprocess_html_for_listings(html: str, budget: int = 12000) -> str:
    """
    Preprocess HTML to focus on listing sections.
    """

    soup = BeautifulSoup(html, "html.parser")

    # Remove noise
    for tag in soup(["script", "style", "noscript", "template"]):
        tag.decompose()
    for sel in ["header", "nav", "footer", "#cookie", ".cookie", ".banner", ".breadcrumbs"]:
        for t in soup.select(sel):
            t.decompose()

    # Collect common listing containers (generic)
    containers = soup.select(",".join([
        "ul li", "ol li", "table tr", "div", "section", "article"
    ]))

    candidates = [str(c) for c in containers if c.get_text(strip=True)]
    joined = "\n".join(candidates)
    return joined[:budget]

# --- AGGREGATOR PAGE SCRAPING --- #
async def scrape_aggregator_page(html_content: str, url: str) -> List[CompanyData]:
    """
    Extract company information from directory/aggregator pages.
    """
    try:
        if not html_content or len(html_content.strip()) < 100:
            logger.warning(f"HTML content too short for {url}: {len(html_content)} characters")
            return []

        trimmed = preprocess_html_for_listings(html_content)
        logger.info(f"[{url}] Preprocessed HTML for listings: {len(trimmed)} characters")

        params = {"command": "uvx", "args": ["mcp-server-fetch"]}

        INSTRUCTIONS = """
        You are a Business Directory Parser. Extract multiple companies from a directory or aggregator page.

        RULES:
        - The provided HTML snippet may be incomplete or simplified. DO NOT ask for more HTML.
        - Ignore headers, navigation, scripts, and styles.
        - If no companies are found, return [].
        - Output ONLY a JSON array of up to 10 objects, no commentary.

        Each object must contain:
        - company_name (string, required)
        - website_url (string or null)
        - address (string or null)
        - contact_email (string or null)
        - phone_number (string or null)
        - description (string or null)
        - automation_proposal (string, generic suggestion)
        """

        async with MCPServerStdio(params=params, client_session_timeout_seconds=15) as mcp_server:
            agent = Agent(
                name="AggregatorScraper",
                instructions=INSTRUCTIONS,
                model="gpt-4o-mini",
                mcp_servers=[mcp_server],
            )

            user_msg = (
                "Extract up to 10 companies from the following content. "
                "Return ONLY a JSON array.\n\n"
                f"{trimmed}"
            )

            result = await Runner.run(agent, user_msg, max_turns=1)

            companies: List[CompanyData] = []
            if result.final_output:
                try:
                    logger.info(f"[{url}] Aggregator scrape output: {result.final_output[:500]}...")
                    raw = result.final_output if isinstance(result.final_output, str) else json.dumps(result.final_output)
                    clean = extract_json_string(raw)
                    data = json.loads(clean)

                    if isinstance(data, list):
                        for company_data in data:
                            if isinstance(company_data, dict) and company_data.get("company_name"):
                                companies.append(CompanyData(
                                    company_name=company_data.get("company_name"),
                                    website_url=company_data.get("website_url"),
                                    address=company_data.get("address"),
                                    contact_email=company_data.get("contact_email"),
                                    phone_number=company_data.get("phone_number"),
                                    description=company_data.get("description"),
                                    automation_proposal=company_data.get("automation_proposal"),
                                    source_url=url,
                                    confidence_score=0.6
                                ))
                except Exception as e:
                    logger.error(f"[{url}] Error parsing aggregator data: {str(e)}")

            return companies

    except Exception as e:
        logger.error(f"[{url}] Error scraping aggregator page {url}: {str(e)}")
        return []

# --- FALLBACK: SEARCH METADATA EXTRACTION --- #
def extract_from_search_metadata(search_result) -> CompanyData:
    """
    Fallback: Extract basic company info from search result metadata.
    """
    try:
        # Extract company name from title or URL
        company_name = search_result.Title
        if not company_name and search_result.URL:
            parsed = urlparse(str(search_result.URL))
            company_name = parsed.netloc.replace('www.', '').split('.')[0]
            company_name = company_name.replace('-', ' ').replace('_', ' ').title()
        
        if not company_name:
            company_name = "Unknown Company"
        
        return CompanyData(
            company_name=company_name,
            website_url=str(search_result.URL),
            address=None,
            contact_email=None,
            phone_number=None,
            description=search_result.Description or "Company found through web search",
            automation_proposal=f"Potential automation opportunities for {company_name} based on search results",
            source_url=str(search_result.URL),
            confidence_score=0.3  # Low confidence for metadata-only data
        )
        
    except Exception as e:
        logger.error(f"Error extracting from search metadata: {str(e)}")
        return CompanyData(
            company_name="Unknown Company",
            website_url=str(search_result.URL),
            source_url=str(search_result.URL),
            confidence_score=0.1
        )

# --- MAIN ENHANCED SCRAPER FUNCTION --- #
async def run_enhanced_company_scraper_agent(lead_discovery_result) -> ScrapingResult:
    """
    Enhanced company scraper that handles both single company pages and aggregators.
    Processes URLs in parallel with intelligent page type detection.
    """
    logger.info("Starting enhanced company scraper...")
    
    # Extract URLs from search results
    try:
        urls = lead_discovery_result.get_concatenated_urls()
        logger.info(f"Raw URLs from search results: {urls}")
        
        if not urls or not urls.strip():
            logger.warning("No URLs found in search results")
            return ScrapingResult(
                companies=[],
                total_urls_processed=0,
                successful_scrapes=0,
                failed_scrapes=0,
                errors=["No URLs found in search results"]
            )
        
        url_list = [url.strip() for url in urls.split(',') if url.strip()]
        logger.info(f"Parsed {len(url_list)} URLs from search results")
        
        # Limit to first 5 URLs for performance
        limited_urls = url_list[:5]
        logger.info(f"Processing {len(limited_urls)} URLs (limited from {len(url_list)} total)")
        
        if not limited_urls:
            logger.warning("No valid URLs to process after filtering")
            return ScrapingResult(
                companies=[],
                total_urls_processed=0,
                successful_scrapes=0,
                failed_scrapes=0,
                errors=["No valid URLs to process"]
            )
            
    except Exception as e:
        error_msg = f"Error extracting URLs from search results: {type(e).__name__}: {str(e)}"
        logger.error(error_msg)
        return ScrapingResult(
            companies=[],
            total_urls_processed=0,
            successful_scrapes=0,
            failed_scrapes=0,
            errors=[error_msg]
        )

    async def process_single_url(url: str) -> tuple[list[CompanyData], bool, str]:
        """
        Process a single URL and return (companies, success, error_message)
        """
        try:
            # Validate URL
            if not url or not url.strip():
                error_msg = "Empty or invalid URL provided"
                logger.error(error_msg)
                return [], False, error_msg
            
            url = url.strip()
            logger.info(f"Starting to process URL: {url}")
            
            # Fetch the webpage content
            try:
                html_content = await fetch_html_content(url)
                
                if not html_content:
                    error_msg = f"Failed to fetch content from {url} - no response received"
                    logger.warning(error_msg)
                    return [], False, error_msg
                
                logger.info(f"Successfully fetched {len(html_content)} characters from {url}")
                logger.info(f"Fetched content from {url}: {html_content[0:100]}...")
                
                # Detect page type
                logger.info(f"Detecting page type for: {url}")
                page_type = await detect_page_type(html_content, url)
                logger.info(f"Page type detected as: {page_type} for {url}")
                
                # Scrape based on page type
                if page_type == 'single_company':
                    logger.info(f"Scraping single company page: {url}")
                    companies = await scrape_single_company_page(html_content, url)
                else:  # aggregator
                    logger.info(f"Scraping aggregator page: {url}")
                    companies = await scrape_aggregator_page(html_content, url)
                
                if companies:
                    logger.info(f"Successfully extracted {len(companies)} companies from {url}")
                    return companies, True, ""
                else:
                    error_msg = f"No companies extracted from {url} - page type: {page_type}"
                    logger.warning(error_msg)
                    return [], False, error_msg
                    
            except Exception as fetch_error:
                error_msg = f"HTTP request error for {url}: {str(fetch_error)}"
                logger.error(error_msg)
                return [], False, error_msg
                    
        except asyncio.TimeoutError:
            error_msg = f"Timeout processing {url} (15 seconds exceeded)"
            logger.warning(error_msg)
            return [], False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error processing {url}: {type(e).__name__}: {str(e)}"
            logger.error(error_msg, exc_info=True)  # Include full traceback
            return [], False, error_msg

    # Process URLs in parallel
    tasks = [process_single_url(url) for url in limited_urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Collect results
    all_companies = []
    successful_scrapes = 0
    failed_scrapes = 0
    errors = []
    
    for i, result in enumerate(results):
        try:
            if isinstance(result, Exception):
                url = limited_urls[i] if i < len(limited_urls) else "unknown"
                error_msg = f"Exception processing URL {url}: {type(result).__name__}: {str(result)}"
                logger.error(error_msg)
                errors.append(error_msg)
                failed_scrapes += 1
            else:
                companies, success, error_msg = result
                if success:
                    all_companies.extend(companies)
                    successful_scrapes += 1
                    logger.info(f"Successfully processed URL {i+1}/{len(limited_urls)}")
                else:
                    failed_scrapes += 1
                    if error_msg:
                        logger.warning(f"Failed to process URL {i+1}/{len(limited_urls)}: {error_msg}")
                        errors.append(error_msg)
        except Exception as e:
            url = limited_urls[i] if i < len(limited_urls) else "unknown"
            error_msg = f"Error processing result for URL {url}: {type(e).__name__}: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
            failed_scrapes += 1
    
    # If no companies found through scraping, fallback to search metadata
    if not all_companies and lead_discovery_result.results:
        logger.info("No companies found through scraping, using search metadata fallback")
        for result in lead_discovery_result.results[:3]:  # Limit to 3 results
            try:
                company_data = extract_from_search_metadata(result)
                all_companies.append(company_data)
            except Exception as e:
                logger.error(f"Error in fallback extraction: {str(e)}")
    
    # Remove duplicates based on company name and website
    unique_companies = []
    seen = set()
    for company in all_companies:
        key = (company.company_name.lower(), company.website_url)
        if key not in seen:
            seen.add(key)
            unique_companies.append(company)
    
    logger.info(f"Enhanced scraper completed: {len(unique_companies)} unique companies found")
    
    return ScrapingResult(
        companies=unique_companies,
        total_urls_processed=len(limited_urls),
        successful_scrapes=successful_scrapes,
        failed_scrapes=failed_scrapes,
        errors=errors
    )

# --- UTILITY FUNCTION FOR INTEGRATION --- #
def convert_to_original_format(scraping_result: ScrapingResult) -> list[dict]:
    """
    Convert ScrapingResult to the original format expected by the system.
    This allows easy integration without changing existing code.
    """
    original_format = []
    for company in scraping_result.companies:
        original_format.append({
            "company_name": company.company_name,
            "website_url": company.website_url,
            "address": company.address,
            "contact_email": company.contact_email,
            "phone_number": company.phone_number,
            "description": company.description,
            "automation_proposal": company.automation_proposal
        })
    return original_format

# --- CONVENIENCE FUNCTION FOR DIRECT REPLACEMENT --- #
async def run_enhanced_company_scraper_agent_original_format(lead_discovery_result) -> list[dict]:
    """
    Enhanced company scraper that returns data in the original format.
    This function can be used as a direct replacement for the original scraper.
    """
    result = await run_enhanced_company_scraper_agent(lead_discovery_result)
    return convert_to_original_format(result)
