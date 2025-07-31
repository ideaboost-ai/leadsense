from dotenv import load_dotenv
from agents import Agent, Runner, trace, Tool
from agents.mcp import MCPServerStdio
from pydantic import BaseModel, Field
import asyncio
import os

load_dotenv(override=True)

# --- START SECTOR IDENTIFICATION AGENT --- #
class RecomendedSectorItem(BaseModel):
    name: str = Field(description="The sector name used for a web search")
    justification: str = Field(description="Your reasoning for why this sector is important")

class RecomendedSectorList(BaseModel): 
    recomended_sectors: list [RecomendedSectorItem] = Field(description="A list of recomended sectors") 

    def concatenate_sectors(self) -> str:
        return ", ".join(item.name for item in self.recomended_sectors)

async def sector_identification_agent(company_profile: dict) -> RecomendedSectorList:
    print("Identifing sectors...")
    INSTRUCTIONS = """You are a business development expert helping a small AI company
                       identify the most promising business sectors to target for automation and AI integration.
                       Given the company profile, recommend 2–3 sectors or niches the company should target. 
                       For each recommendation, include a short justification for why this sector is a good 
                       fit based on the company's size, location, and services.
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

async def lead_discovery_agent(recomended_sectors: RecomendedSectorList) -> LeadDiscoveryOutput:    
    print("Generate queries...")
    INSTRUCTIONS = """You are a lead generation assistant. Your job is to create intelligent web 
                      search queries that can help find small businesses in a specific sector.
                      For each sector, generate 2–3 search queries in both English and German that 
                      can help discover potential leads (e.g., small companies, service providers)."""

    agent = Agent(
        name="LeadDiscoveryAgent",
        instructions=INSTRUCTIONS,
        model="gpt-4o-mini",
        output_type=LeadDiscoveryOutput,
    )

    result = await Runner.run(agent, f"Sectors to generate queries for:\n{recomended_sectors.concatenate_sectors()}")
    return result.final_output
# --- END LEAD DISCOVERY AGENT --- #

# --- START LEAD SEARCH AGENT --- #
async def run_searches_agent(lead_discovery_output: LeadDiscoveryOutput):
    print("Running searches...")
    env = {"BRAVE_API_KEY": os.getenv("BRAVE_API_KEY")}
    params = {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-brave-search"], "env": env}

    INSTRUCTIONS = """You are a web search execution agent helping identify small businesses that
                      are potential leads for a B2B automation consultancy. Your goal is to find company websites,
                      business directories, or listings of small to mid-sized businesses operating in sectors 
                      provided by the user. These companies should be suitable leads for process automation and
                      AI integration.
                      You will be given structured search queries in English and German.

                        Instructions:
                        1. Execute each search query using the web.
                        2. For each query, return 3–5 high-relevance results.
                        3. Results should prioritize:
                            - Small company websites
                            - Swiss or German businesses
                            - Business listings (e.g., directories, professional networks)
                            - Pages that suggest the company is real and active
                        4. For each result, include:
                            - Title of the result
                            - URL
                            - Short description or snippet
                        5. Do NOT include ads or irrelevant blog posts.
                        6. Prioritize professional, business-related content.
                        7. Output a JSON list of results grouped by search query.
                        """ 
    REQUEST = f"""Here are search queries you need to execute: {lead_discovery_output.concatenate_queries()}"""

    async with MCPServerStdio(params=params, client_session_timeout_seconds=30) as mcp_server:
        agent = Agent(name="agent", instructions=INSTRUCTIONS, model="gpt-4o-mini", mcp_servers=[mcp_server])
        result = await Runner.run(agent, REQUEST)
        return result.final_output
# --- END LEAD SEARCH AGENT --- #

async def main():
    company_profile = {
        "company_name": "AutoAI Solutions",
        "location": "Zurich, Switzerland",
        "team_size": 5,
        "core_services": ["process automation", "AI integration"],
        "languages": ["English", "German"]
    }

    with trace("Lead Search"):
        recomended_sectors = await sector_identification_agent(company_profile)
        print(recomended_sectors)
        search_queries = await lead_discovery_agent(recomended_sectors)
        print(search_queries)
        leads = await run_searches_agent(search_queries)
        print(leads)

if __name__ == "__main__":
    asyncio.run(main())





