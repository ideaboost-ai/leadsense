from dotenv import load_dotenv
from agents import Agent, Runner, trace, Tool, AgentOutputSchema
from agents.mcp import MCPServerStdio
from pydantic import BaseModel, Field, HttpUrl
from pprint import pprint
import asyncio
import os

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
                       Given the company profile, recommend 10 sectors or niches the company should target. 
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
                      For each sector, generate 3 search queries in both English and German that 
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

# --- START LEAD SEARCH AGENT --- #
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

async def run_searches_agent(lead_discovery_output: LeadDiscoveryOutput, company_profile: dict) -> LeadDiscoveryResults:
    print("Running searches...")
    env = {"BRAVE_API_KEY": os.getenv("BRAVE_API_KEY")}
    params = {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-brave-search"], "env": env}

    INSTRUCTIONS = f"""
                    You are a web search agent. Execute the provided search queries and return results.
                    
                    Instructions:
                    1. Execute each search query using the web.
                    2. Return 2-3 high-relevance results total.
                    3. For each result, include: Title, URL, Description
                    4. Output as JSON array of results.
                    5. Focus on business websites and directories.
                    6. Order results by relevance to the company profile: {company_profile}.
                    """ 
    REQUEST = f"""Here are search queries you need to execute: {lead_discovery_output.concatenate_queries()}"""

    async with MCPServerStdio(params=params, client_session_timeout_seconds=30) as mcp_server:
        agent = Agent(
            name="agent",
            instructions=INSTRUCTIONS,
            model="gpt-4o-mini",
            mcp_servers=[mcp_server],
            output_type=AgentOutputSchema(LeadDiscoveryResults, strict_json_schema=False)
        )
        result = await Runner.run(agent, REQUEST, max_turns=100)
        return result.final_output
# --- END LEAD SEARCH AGENT --- #

# --- START COMPANY SCRAPER AGENT --- #
async def run_company_scraper_agent(lead_discovery_result: LeadDiscoveryResults):
    print("Scraping company information...")
    params = {"command": "uvx", "args": ["mcp-server-fetch"]}

    INSTRUCTIONS = """
                        You are a Company Scraper Agent.
                        Your task is to extract structured information about one or more businesses from a webpage.
                        You will receive either:
                        - A direct company website
                        - A business listing page (with multiple companies)
                        For each company, extract:
                        - company_name
                        - website_url
                        - address
                        - contact_email
                        - phone_number
                        - description
                        - automation_proposal (1–2 sentences how a process automation/AI company could help)
                        If the page lists multiple companies, extract this information for each one (up to 10 max).
                        Only return what is visible in the provided HTML. Do not guess or fabricate data.

                        Output JSON format:
                        [
                            {
                                "company_name": "...",
                                "website_url": "...",
                                "address": "...",
                                "contact_email": "...",
                                "phone_number": "...",
                                "description": "...",
                                "automation_proposal": "..."
                            }
                        ]
                    """
    REQUEST = f"""Here are urls to scrap information about companies: {lead_discovery_result.get_concatenated_urls()}"""

    async with MCPServerStdio(params=params, client_session_timeout_seconds=60) as mcp_server:
        agent = Agent(
            name="CompanyScraperAgent",
            instructions=INSTRUCTIONS,
            model="gpt-4o-mini",
            mcp_servers=[mcp_server],
        )
        result = await Runner.run(agent, REQUEST)
        return result.final_output
# --- END COMPANY SCRAPER  AGENT --- #

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
        leads = await run_searches_agent(search_queries, company_profile)
        pprint(leads.model_dump())
        # companies = await run_company_scraper_agent(leads)
        # print(companies)

if __name__ == "__main__":
    asyncio.run(main())





