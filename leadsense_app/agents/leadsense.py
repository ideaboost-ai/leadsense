from dotenv import load_dotenv
from agents import Agent, Runner, trace, Tool, AgentOutputSchema
from agents.mcp import MCPServerStdio
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional
from pprint import pprint
import asyncio
import os
import httpx
import json
from openai import AsyncOpenAI
from .tools import scrape_website, google_search, extract_company_linkedin_profile, reflection, tools, tool_map

load_dotenv(override=True)

# --- START SECTOR IDENTIFICATION AGENT --- #
class RecomendedSectorItem(BaseModel):
    name: str = Field(description="The sector name used for a web search")
    justification: str = Field(description="Your reasoning for why this sector is important")
    order: int = Field(description="The order of the sector in the list")

class RecomendedSectorList(BaseModel): 
    recomended_sectors: list [RecomendedSectorItem] = Field(description="A list of recomended sectors") 

    def concatenate_sectors(self) -> str:
        return ", ".join(item.name for item in self.recomended_sectors)

async def sector_identification_agent(company_profile: dict) -> RecomendedSectorList:
    print("Identifing sectors...")
    INSTRUCTIONS = """You are a business development expert helping a small AI company
                       identify the most promising business sectors to target for automation and AI integration.
                       Given the company profile, recommend 1 sectors or niches the company should target. 
                       For each recommendation, include a short justification for why this sector is a good 
                       fit based on the company's size, location, and services. Please be creative and think
                       outside the box.
                    """
    agent = Agent(
        name="SectorIdentificationAgent",
        instructions=INSTRUCTIONS,
        model="gpt-4o-mini",
        output_type=RecomendedSectorList,
    )

    result = await Runner.run(agent, f"Company profile: {company_profile}")
    return result.final_output
# --- END SECTOR IDENTIFICATION AGENT --- #

# --- START LEAD DISCOVERY AGENT --- #
class WebSearchQuery(BaseModel):
    language: str  # "English" or "German"
    query: str
    order: int

class LeadDiscoveryItem(BaseModel):
    sector: str
    queries: list[WebSearchQuery]

class LeadDiscoveryOutput(BaseModel):
    searches: list[LeadDiscoveryItem]

    def concatenate_queries(self) -> str:
        return ', '.join(
            query.query
            for item in self.searches
            for query in item.queries
        )

async def lead_discovery_agent(recomended_sectors: RecomendedSectorList, company_profile: dict) -> LeadDiscoveryOutput:    
    print("Generate queries...")
    INSTRUCTIONS = """You are a lead generation assistant. Your job is to create intelligent web 
                      search queries that can help find small businesses in a specific sector.
                      For each sector, generate 1 search queries in both English and German that 
                      can help discover potential leads (e.g., small companies, service providers).  
                      Order them by relevance to the company profile. Prioritize local leads, small companies
                      and startups without dedicated IT departments.
                    """

    agent = Agent(
        name="LeadDiscoveryAgent",
        instructions=INSTRUCTIONS,
        model="gpt-4o-mini",
        output_type=LeadDiscoveryOutput,
    )

    result = await Runner.run(agent, f"""
                        Sectors to generate queries for:\n{recomended_sectors.concatenate_sectors()}.
                        Company profile: {company_profile}. 
                        Make sure queries are created with the cosideration of company location to 
                        target local leads.
                        Pick top 2 relevant sectors to generate queries for.""")
    return result.final_output
# --- END LEAD DISCOVERY AGENT --- #

# --- LEAD SCRAPING AGENT --- #
class SearchResultItem(BaseModel):
    Title: str
    URL: HttpUrl
    Description: str
    Order: int

class LeadDiscoveryResults(BaseModel):
    results: list[SearchResultItem]

    def get_concatenated_urls(self) -> str:
        urls: list[str] = []
        for item in self.results:
            urls.append(str(item.URL))  # Convert HttpUrl to string if needed
        return ", ".join(urls)

class CompanyLead(BaseModel):
    company_name: str
    website_url: str
    description: str
    linkedin_info: Optional[dict] = None
    lead_reasoning: str
    sector: str
    location: str
    confidence_score: float  # 0-1

class LeadScrapingResults(BaseModel):
    leads: list[CompanyLead]
    total_searched: int
    total_found: int
    sectors_covered: list[str]

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def run_lead_scraping_agent(search_queries: LeadDiscoveryOutput, tool_map, company_profile: dict) -> LeadScrapingResults:
    """
    Enhanced lead scraping agent that researches companies, extracts data, and evaluates lead quality.
    """
    INSTRUCTIONS = """You are a lead research specialist. Your job is to:

1. **Search for companies** using the provided queries
2. **Analyze search results** to identify individual companies vs aggregator pages
3. **Scrape company pages** to extract detailed information
4. **Extract LinkedIn data** for each company using the extract_company_linkedin_profile tool
5. **Evaluate lead quality** based on our company profile and provide reasoning
6. **Return structured data** with company details and lead reasoning

For aggregator pages (like "Top 10 companies in Zurich"), extract multiple companies.
For single company pages, extract detailed information about that company.

Always use reflection before finalizing results to ensure comprehensive research.

IMPORTANT: You must return a JSON object with this exact structure:
{
    "leads": [
        {
            "company_name": "Company Name",
            "website_url": "https://company.com",
            "description": "Company description",
            "linkedin_info": {"data": "from linkedin"},
            "lead_reasoning": "Why this is a good lead",
            "sector": "Financial Services",
            "location": "Zurich, Switzerland",
            "confidence_score": 0.85
        }
    ],
    "total_searched": 10,
    "total_found": 5,
    "sectors_covered": ["Financial Services", "Healthcare"]
}"""

    messages = [
        {"role": "system", "content": f"{INSTRUCTIONS}\n\nOur company profile: {company_profile}"},
        {"role": "user", "content": f"Research leads using these queries: {search_queries.concatenate_queries()}\n\nSectors to focus on: {[item.sector for item in search_queries.searches]}"}
    ]

    all_leads = []
    searched_urls = set()
    max_iterations = 10  # Prevent infinite loops
    iteration = 0

    while iteration < max_iterations:
        iteration += 1
        print(f"**[INFO] Lead scraping iteration {iteration}/{max_iterations}**")

        response = await client.chat.completions.create(
            model="gpt-4o-mini", 
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )

        response_message = response.choices[0].message
        messages.append(response_message)

        if not response_message.tool_calls:
            # Try to parse the final response as structured data
            try:
                content = response_message.content
                # Look for JSON structure in the response
                if "{" in content and "}" in content:
                    # Extract JSON from the response
                    start = content.find("{")
                    end = content.rfind("}") + 1
                    json_str = content[start:end]
                    result_data = json.loads(json_str)
                    
                    # Convert to LeadScrapingResults
                    leads = []
                    for lead_data in result_data.get("leads", []):
                        lead = CompanyLead(
                            company_name=lead_data.get("company_name", ""),
                            website_url=lead_data.get("website_url", ""),
                            description=lead_data.get("description", ""),
                            linkedin_info=lead_data.get("linkedin_info"),
                            lead_reasoning=lead_data.get("lead_reasoning", ""),
                            sector=lead_data.get("sector", ""),
                            location=lead_data.get("location", ""),
                            confidence_score=lead_data.get("confidence_score", 0.5)
                        )
                        leads.append(lead)
                    
                    return LeadScrapingResults(
                        leads=leads,
                        total_searched=result_data.get("total_searched", len(searched_urls)),
                        total_found=result_data.get("total_found", len(leads)),
                        sectors_covered=result_data.get("sectors_covered", [item.sector for item in search_queries.searches])
                    )
                else:
                    # Fallback: return empty results
                    print("**[WARNING] Could not parse structured results from response**")
                    return LeadScrapingResults(
                        leads=[],
                        total_searched=len(searched_urls),
                        total_found=0,
                        sectors_covered=[item.sector for item in search_queries.searches]
                    )
            except Exception as e:
                print(f"**[ERROR] Failed to parse results: {e}**")
                return LeadScrapingResults(
                    leads=[],
                    total_searched=len(searched_urls),
                    total_found=0,
                    sectors_covered=[item.sector for item in search_queries.searches]
                )

        for tool_call in response_message.tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            
            print(f'**[INFO] Calling tool: {function_name} with args {function_args}**')
            
            # Check if the tool exists in tool_map
            if function_name not in tool_map:
                print(f'**[WARNING] Tool "{function_name}" not found in tool_map. Available tools: {list(tool_map.keys())}**')
                error_response = f"Tool '{function_name}' is not available. Please use one of the available tools: {list(tool_map.keys())}"
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": json.dumps({"error": error_response})
                })
                continue
            
            function_call = tool_map[function_name]
            try:
                # Try to call as async first
                function_response = await function_call(**function_args)
            except TypeError:
                # If it fails, call as sync function
                function_response = function_call(**function_args)
            except Exception as e:
                # Handle any other errors during function execution
                print(f'**[ERROR] Tool "{function_name}" failed with error: {str(e)}**')
                function_response = {"error": f"Tool execution failed: {str(e)}"}

            print(f'**[FUNCTION CALL RESULT] {function_name}: {str(function_response)[:200]}...**')

            # Track searched URLs for google_search calls
            if function_name == "google_search":
                searched_urls.add(f"search: {function_args.get('query', '')}")

            messages.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": function_name,
                "content": json.dumps(function_response)
            })

    # If we reach here, return empty results
    print("**[WARNING] Max iterations reached, returning empty results**")
    return LeadScrapingResults(
        leads=[],
        total_searched=len(searched_urls),
        total_found=0,
        sectors_covered=[item.sector for item in search_queries.searches]
    )

# --- END LEAD SCRAPING AGENT --- #

# --- START EMAIL PROPOSAL AGENT --- #
async def generate_email_proposal(company_lead: CompanyLead, company_profile: dict) -> str:
    INSTRUCTIONS = """You are a business development specialist. Your job is to draft a personalized email proposal
                      for automation and AI integration services to a potential client based on their profile and needs.
                      Use the company lead information and our company profile to create a compelling proposal.
                      The email should be concise, professional, and highlight how our services can benefit their business.
                      It shouldn't be too long, just a few paragraphs.
                   """
    prompt = f"""
                Company Lead Info: {company_lead}
                Our Company Profile: {company_profile}
                Draft a personalized email proposal for automation and AI integration services.
             """
    agent = Agent(
        name="EmailProposalAgent",
        instructions=INSTRUCTIONS,
        model="gpt-4o-mini",
        output_type=str,
    )

    result = await Runner.run(agent, prompt)
    return result.final_output

# --- END EMAIL PROPOSAL AGENT --- #

# --- START LINKEDIN MESSAGE AGENT --- #
async def generate_linkedin_message(company_lead: CompanyLead, company_profile: dict) -> str:
    INSTRUCTIONS = """You are a professional networking specialist. Your job is to draft a personalized LinkedIn message
                      for connecting with potential clients. The message should be professional, concise, and focused on
                      building a business relationship. Use the company lead information and our company profile to create
                      a compelling connection request message that highlights mutual business interests and potential collaboration.
                      Keep it under 300 characters to fit LinkedIn's connection request limit.
                   """
    prompt = f"""
                Company Lead Info: {company_lead}
                Our Company Profile: {company_profile}
                Draft a personalized LinkedIn connection request message for automation and AI integration services.
             """
    agent = Agent(
        name="LinkedInMessageAgent",
        instructions=INSTRUCTIONS,
        model="gpt-4o-mini",
        output_type=str,
    )

    result = await Runner.run(agent, prompt)
    return result.final_output

# --- END LINKEDIN MESSAGE AGENT --- #

async def main():
    company_profile = {
        "company_name": "AutoAI Solutions",
        "location": "Zurich, Switzerland",
        "description": "IdeaBoost offers tailored software solutions including custom dev, AI integration, web/mobile apps, cloud services (AWS), and UI/UX design to support business growth.",
        "team_size": 5,
        "core_services": ["process automation", "AI integration"],
        "languages": ["English", "German"]
    }

    with trace("Lead Search"):
        recomended_sectors = await sector_identification_agent(company_profile)
        pprint(recomended_sectors.model_dump())
        search_queries = await lead_discovery_agent(recomended_sectors, company_profile)
        pprint(search_queries.model_dump())
        leads = await run_lead_scraping_agent(search_queries, tool_map, company_profile)
        
        print(f"\n=== LEAD SCRAPING RESULTS ===")
        print(f"Total searched: {leads.total_searched}")
        print(f"Total found: {leads.total_found}")
        print(f"Sectors covered: {leads.sectors_covered}")
        print(f"\n=== LEADS FOUND ===")
        
        for i, lead in enumerate(leads.leads, 1):
            print(f"\n{i}. {lead.company_name}")
            print(f"   Website: {lead.website_url}")
            print(f"   Sector: {lead.sector}")
            print(f"   Location: {lead.location}")
            print(f"   Confidence: {lead.confidence_score:.2f}")
            print(f"   Description: {lead.description[:100]}...")
            print(f"   Reasoning: {lead.lead_reasoning[:100]}...")
            if lead.linkedin_info:
                print(f"   LinkedIn: Data available")
            print()
        
if __name__ == "__main__":
    asyncio.run(main())





