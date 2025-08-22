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
        
        Extract the following information:
        - company_name: The main company name
        - website_url: The company's main website URL
        - address: Full address if available
        - contact_email: Email address
        - phone_number: Phone number
        - description: Company description or about section
        - automation_proposal: 1-2 sentences on how process automation/AI could help this company
        
        Return as JSON array with one company object:
        [{
            "company_name": "...",
            "website_url": "...",
            "address": "...",
            "contact_email": "...",
            "phone_number": "...",
            "description": "...",
            "automation_proposal": "..."
        }]
        
        Only extract information that is clearly visible in the HTML. Do not guess or fabricate data.
        """
        
        async with MCPServerStdio(params=params, client_session_timeout_seconds=15) as mcp_server:
            agent = Agent(
                name="SingleCompanyScraper",
                instructions=INSTRUCTIONS,
                model="gpt-4o-mini",
                mcp_servers=[mcp_server],
            )
            
            result = await Runner.run(agent, f"Extract company information from this HTML: {html_content[:5000]}", max_turns=2)
            
            # Parse the result and convert to CompanyData objects
            companies = []
            if result.final_output:
                try:
                    if isinstance(result.final_output, str):
                        data = json.loads(result.final_output)
                    else:
                        data = result.final_output
                    
                    if isinstance(data, list):
                        for company_data in data:
                            if isinstance(company_data, dict):
                                company = CompanyData(
                                    company_name=company_data.get('company_name', 'Unknown Company'),
                                    website_url=company_data.get('website_url'),
                                    address=company_data.get('address'),
                                    contact_email=company_data.get('contact_email'),
                                    phone_number=company_data.get('phone_number'),
                                    description=company_data.get('description'),
                                    automation_proposal=company_data.get('automation_proposal'),
                                    source_url=url,
                                    confidence_score=0.8  # High confidence for single company pages
                                )
                                companies.append(company)
                except Exception as e:
                    logger.error(f"Error parsing single company data: {str(e)}")
            
            return companies
            
    except Exception as e:
        logger.error(f"Error scraping single company page {url}: {str(e)}")
        return []

# --- AGGREGATOR PAGE SCRAPING --- #
async def scrape_aggregator_page(html_content: str, url: str) -> List[CompanyData]:
    """
    Extract company information from directory/aggregator pages.
    """
    try:
        if not html_content or len(html_content.strip()) < 100:
            logger.warning(f"HTML content too short for {url}: {len(html_content)} characters")
            return []
            
        params = {"command": "uvx", "args": ["mcp-server-fetch"]}
        
        INSTRUCTIONS = """
        You are a Business Directory Parser. Extract information about multiple companies from a directory or aggregator page.
        
        Look for:
        - Company listings in tables, lists, or cards
        - Business directories
        - Search result pages with multiple companies
        - Local business listings
        
        For each company found, extract:
        - company_name: Company name
        - website_url: Company website (if available)
        - address: Address (if available)
        - contact_email: Email (if available)
        - phone_number: Phone (if available)
        - description: Brief description (if available)
        - automation_proposal: Generic automation proposal
        
        Return as JSON array with multiple company objects:
        [{
            "company_name": "...",
            "website_url": "...",
            "address": "...",
            "contact_email": "...",
            "phone_number": "...",
            "description": "...",
            "automation_proposal": "..."
        }]
        
        Extract up to 10 companies maximum. Only include companies that have at least a name.
        """
        
        async with MCPServerStdio(params=params, client_session_timeout_seconds=15) as mcp_server:
            agent = Agent(
                name="AggregatorScraper",
                instructions=INSTRUCTIONS,
                model="gpt-4o-mini",
                mcp_servers=[mcp_server],
            )
            
            result = await Runner.run(agent, f"Extract multiple companies from this directory page: {html_content[:8000]}", max_turns=2)
            
            # Parse the result and convert to CompanyData objects
            companies = []
            if result.final_output:
                try:
                    if isinstance(result.final_output, str):
                        data = json.loads(result.final_output)
                    else:
                        data = result.final_output
                    
                    if isinstance(data, list):
                        for company_data in data:
                            if isinstance(company_data, dict) and company_data.get('company_name'):
                                company = CompanyData(
                                    company_name=company_data.get('company_name'),
                                    website_url=company_data.get('website_url'),
                                    address=company_data.get('address'),
                                    contact_email=company_data.get('contact_email'),
                                    phone_number=company_data.get('phone_number'),
                                    description=company_data.get('description'),
                                    automation_proposal=company_data.get('automation_proposal'),
                                    source_url=url,
                                    confidence_score=0.6  # Lower confidence for aggregator pages
                                )
                                companies.append(company)
                except Exception as e:
                    logger.error(f"Error parsing aggregator data: {str(e)}")
            
            return companies
            
    except Exception as e:
        logger.error(f"Error scraping aggregator page {url}: {str(e)}")
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
            params = {"command": "uvx", "args": ["mcp-server-fetch"]}
            
            try:
                async with MCPServerStdio(params=params, client_session_timeout_seconds=15) as mcp_server:
                    logger.info(f"Fetching content from: {url}")
                    
                    # First, get the HTML content
                    fetch_agent = Agent(
                        name="ContentFetcher",
                        instructions="Fetch the HTML content of the provided URL. Return only the HTML content.",
                        model="gpt-4o-mini",
                        mcp_servers=[mcp_server],
                    )
                    
                    fetch_result = await Runner.run(fetch_agent, f"Fetch content from: {url}", max_turns=1)
                    
                    if not fetch_result or not fetch_result.final_output:
                        error_msg = f"Failed to fetch content from {url} - no response received"
                        logger.warning(error_msg)
                        return [], False, error_msg
                    
                    html_content = fetch_result.final_output
                    logger.info(f"Successfully fetched {len(html_content)} characters from {url}")
                    
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
                        
            except Exception as mcp_error:
                error_msg = f"MCP server error for {url}: {str(mcp_error)}"
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
