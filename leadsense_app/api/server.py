from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import asyncio
import httpx
import json

from ..agents.leadsense import (
    sector_identification_agent, 
    RecomendedSectorList,
    RecomendedSectorItem, 
    lead_discovery_agent,
    CompanyLead,
    generate_email_proposal,
    generate_linkedin_message,
    EmailVersions,
    LinkedInVersions
)
from ..agents.database import DatabaseManager, SectorManager, CompanyProfileManager, LeadManager, SettingsManager, get_or_create_sector


app = FastAPI(title="Leadsense API", version="0.1.0")

# Allow local frontend during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Development: allow all origins
    allow_credentials=False,  # Must be False when using "*"
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"status": "ok"}


class CompanyProfile(BaseModel):
    company_name: str
    location: str
    description: str
    team_size: int
    core_services: List[str]
    languages: List[str]
    special_offer: str = ""


class CompanyProfileResponse(BaseModel):
    id: int
    company_name: str
    location: str
    description: str
    team_size: int
    core_services: List[str]
    languages: List[str]
    special_offer: str
    created_at: str
    updated_at: str


class SectorResponseItem(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    relevance_reason: Optional[str] = None


class LeadResponseItem(BaseModel):
    id: int
    company_name: str
    website_url: Optional[str] = None
    address: Optional[str] = None
    contact_email: Optional[str] = None
    phone_number: Optional[str] = None
    description: Optional[str] = None
    automation_proposal: Optional[str] = None
    discovered_at: str
    discovered_by_profile_id: Optional[int] = None
    discovered_sectors: Optional[List[str]] = None
    status: str
    priority: str
    notes: Optional[str] = None
    automation_email: Optional[Dict] = None
    linkedin_message: Optional[Dict] = None
    company_type: Optional[str] = None
    sector: Optional[str] = None
    location: Optional[str] = None
    pain_points: Optional[List[str]] = None
    proposed_solution: Optional[str] = None
    confidence_score: Optional[float] = None
    created_at: str
    updated_at: str


class SaveLeadRequest(BaseModel):
    lead: dict
    discovered_sectors: List[str]


class UpdateLeadRequest(BaseModel):
    status: str
    priority: str
    notes: str = ""


class IdentifySectorsRequest(BaseModel):
    profile: CompanyProfile
    sector_precision: str = "medium"  # Default to medium precision
    sector_count: int = 1  # Default to 1 sector


@app.post("/sectors/identify", response_model=List[SectorResponseItem])
async def identify_sectors(payload: IdentifySectorsRequest):
    try:
        # Run the agent to identify recommended sectors
        recomended: RecomendedSectorList = await sector_identification_agent(payload.profile.model_dump(), payload.sector_precision, payload.sector_count)

        # Persist or fetch from DB, then return the list
        created_or_existing: List[SectorResponseItem] = []
        with DatabaseManager() as db:
            for item in recomended.recomended_sectors:
                sector = get_or_create_sector(
                    db_manager=db,
                    name=item.name,
                    description=None,
                    relevance_reason=item.justification,
                )
                created_or_existing.append(
                    SectorResponseItem(
                        id=sector["id"],
                        name=sector["name"],
                        description=sector.get("description"),
                        relevance_reason=sector.get("relevance_reason"),
                    )
                )

        return created_or_existing
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sectors", response_model=List[SectorResponseItem])
async def get_sectors():
    try:
        with DatabaseManager() as db:
            sector_manager = SectorManager(db)
            sectors = sector_manager.get_all_sectors()
            return [
                SectorResponseItem(
                    id=s["id"],
                    name=s["name"],
                    description=s.get("description"),
                    relevance_reason=s.get("relevance_reason"),
                )
                for s in sectors
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/company-profiles", response_model=List[CompanyProfileResponse])
async def get_company_profiles():
    """Get all company profiles."""
    try:
        with DatabaseManager() as db:
            profile_manager = CompanyProfileManager(db)
            profiles = profile_manager.get_all_company_profiles()
            return [
                CompanyProfileResponse(
                    id=p["id"],
                    company_name=p["company_name"],
                    location=p["location"],
                    description=p["description"],
                    team_size=p["team_size"],
                    core_services=p["core_services"],
                    languages=p["languages"],
                    special_offer=p.get("special_offer", ""),
                    created_at=p["created_at"],
                    updated_at=p["updated_at"]
                )
                for p in profiles
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/company-profiles/{profile_id}", response_model=CompanyProfileResponse)
async def get_company_profile(profile_id: int):
    """Get a specific company profile by ID."""
    try:
        with DatabaseManager() as db:
            profile_manager = CompanyProfileManager(db)
            profile = profile_manager.get_company_profile_by_id(profile_id)
            
            if not profile:
                raise HTTPException(status_code=404, detail="Company profile not found")
            
            return CompanyProfileResponse(
                id=profile["id"],
                company_name=profile["company_name"],
                location=profile["location"],
                description=profile["description"],
                team_size=profile["team_size"],
                core_services=profile["core_services"],
                languages=profile["languages"],
                special_offer=profile.get("special_offer", ""),
                created_at=profile["created_at"],
                updated_at=profile["updated_at"]
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/company-profiles/{profile_id}", response_model=CompanyProfileResponse)
async def update_company_profile(profile_id: int, profile: CompanyProfile):
    """Update a company profile."""
    try:
        with DatabaseManager() as db:
            profile_manager = CompanyProfileManager(db)
            
            # Check if profile exists
            existing_profile = profile_manager.get_company_profile_by_id(profile_id)
            if not existing_profile:
                raise HTTPException(status_code=404, detail="Company profile not found")
            
            # Update the profile
            success = profile_manager.update_company_profile(profile_id, profile.model_dump())
            if not success:
                raise HTTPException(status_code=500, detail="Failed to update profile")
            
            # Get the updated profile
            updated_profile = profile_manager.get_company_profile_by_id(profile_id)
            return CompanyProfileResponse(
                id=updated_profile["id"],
                company_name=updated_profile["company_name"],
                location=updated_profile["location"],
                description=updated_profile["description"],
                team_size=updated_profile["team_size"],
                core_services=updated_profile["core_services"],
                languages=updated_profile["languages"],
                special_offer=updated_profile.get("special_offer", ""),
                created_at=updated_profile["created_at"],
                updated_at=updated_profile["updated_at"]
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/company-profiles", response_model=CompanyProfileResponse)
async def create_company_profile(profile: CompanyProfile):
    """Create a new company profile."""
    try:
        with DatabaseManager() as db:
            profile_manager = CompanyProfileManager(db)
            profile_id = profile_manager.add_company_profile(profile.model_dump())
            
            # Get the created profile
            created_profile = profile_manager.get_company_profile_by_id(profile_id)
            return CompanyProfileResponse(
                id=created_profile["id"],
                company_name=created_profile["company_name"],
                location=created_profile["location"],
                description=created_profile["description"],
                team_size=created_profile["team_size"],
                core_services=created_profile["core_services"],
                languages=created_profile["languages"],
                special_offer=created_profile.get("special_offer", ""),
                created_at=created_profile["created_at"],
                updated_at=created_profile["updated_at"]
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/leads/saved", response_model=List[LeadResponseItem])
async def get_saved_leads():
    """Get all saved leads from database."""
    try:
        with DatabaseManager() as db:
            lead_manager = LeadManager(db)
            leads = lead_manager.get_all_leads()
            return [
                LeadResponseItem(
                    id=lead["id"],
                    company_name=lead["company_name"],
                    website_url=lead.get("website_url"),
                    address=lead.get("address"),
                    contact_email=lead.get("contact_email"),
                    phone_number=lead.get("phone_number"),
                    description=lead.get("description"),
                    automation_proposal=lead.get("automation_proposal"),
                    discovered_at=lead["discovered_at"],
                    discovered_by_profile_id=lead.get("discovered_by_profile_id"),
                    discovered_sectors=lead.get("discovered_sectors"),
                    status=lead["status"],
                    priority=lead["priority"],
                    notes=lead.get("notes"),
                    automation_email=json.loads(lead.get("automation_email")) if lead.get("automation_email") else None,
                    linkedin_message=json.loads(lead.get("linkedin_message")) if lead.get("linkedin_message") else None,
                    company_type=lead.get("company_type"),
                    sector=lead.get("sector"),
                    location=lead.get("location"),
                    pain_points=lead.get("pain_points"),
                    proposed_solution=lead.get("proposed_solution"),
                    confidence_score=lead.get("confidence_score"),
                    created_at=lead["created_at"],
                    updated_at=lead["updated_at"]
                )
                for lead in leads
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/leads/check-saved")
async def check_lead_saved(company_name: str, website_url: Optional[str] = None):
    """Check if a lead is already saved based on company name and website."""
    try:
        with DatabaseManager() as db:
            lead_manager = LeadManager(db)
            
            # Search for leads with matching company name and website
            search_term = company_name
            if website_url:
                search_term = f"{company_name} {website_url}"
            
            leads = lead_manager.search_leads(search_term)
            
            # Check for exact matches
            for lead in leads:
                if (lead["company_name"].lower() == company_name.lower() and 
                    (not website_url or lead.get("website_url") == website_url)):
                    return {"is_saved": True, "lead_id": lead["id"]}
            
            return {"is_saved": False, "lead_id": None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/leads/save", response_model=LeadResponseItem)
async def save_lead(payload: SaveLeadRequest):
    """Save a lead to the database."""
    try:
        with DatabaseManager() as db:
            lead_manager = LeadManager(db)
            profile_manager = CompanyProfileManager(db)
            
            # Get the current company profile
            profiles = profile_manager.get_all_company_profiles()
            if not profiles:
                raise HTTPException(status_code=400, detail="No company profile found. Please save your company profile first.")
            
            company_profile_id = profiles[0]["id"]
            
            # Check if lead already exists
            check_result = await check_lead_saved(
                payload.lead.get("company_name", ""),
                payload.lead.get("website_url")
            )
            
            if check_result["is_saved"]:
                raise HTTPException(status_code=409, detail="Lead already saved")
            
            # Save the lead
            lead_id = lead_manager.add_lead(
                payload.lead,
                discovered_by_profile_id=company_profile_id,
                discovered_sectors=payload.discovered_sectors
            )
            
            # Get the saved lead
            saved_lead = lead_manager.get_lead_by_id(lead_id)
            if not saved_lead:
                raise HTTPException(status_code=500, detail="Failed to retrieve saved lead")
            
            return LeadResponseItem(
                id=saved_lead["id"],
                company_name=saved_lead["company_name"],
                website_url=saved_lead.get("website_url"),
                address=saved_lead.get("address"),
                contact_email=saved_lead.get("contact_email"),
                phone_number=saved_lead.get("phone_number"),
                description=saved_lead.get("description"),
                automation_proposal=saved_lead.get("automation_proposal"),
                discovered_at=saved_lead["discovered_at"],
                discovered_by_profile_id=saved_lead.get("discovered_by_profile_id"),
                discovered_sectors=saved_lead.get("discovered_sectors"),
                status=saved_lead["status"],
                priority=saved_lead["priority"],
                notes=saved_lead.get("notes"),
                company_type=saved_lead.get("company_type"),
                sector=saved_lead.get("sector"),
                location=saved_lead.get("location"),
                pain_points=saved_lead.get("pain_points"),
                proposed_solution=saved_lead.get("proposed_solution"),
                confidence_score=saved_lead.get("confidence_score"),
                created_at=saved_lead["created_at"],
                updated_at=saved_lead["updated_at"]
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/leads/{lead_id}")
async def delete_lead(lead_id: int):
    """Delete a lead from the database."""
    try:
        with DatabaseManager() as db:
            lead_manager = LeadManager(db)
            
            # Check if lead exists
            lead = lead_manager.get_lead_by_id(lead_id)
            if not lead:
                raise HTTPException(status_code=404, detail="Lead not found")
            
            # Delete the lead
            success = lead_manager.delete_lead(lead_id)
            if not success:
                raise HTTPException(status_code=500, detail="Failed to delete lead")
            
            return {"message": "Lead deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/leads/{lead_id}", response_model=LeadResponseItem)
async def update_lead(lead_id: int, payload: UpdateLeadRequest):
    """Update a lead's status, priority, and notes."""
    try:
        with DatabaseManager() as db:
            lead_manager = LeadManager(db)
            
            # Check if lead exists
            lead = lead_manager.get_lead_by_id(lead_id)
            if not lead:
                raise HTTPException(status_code=404, detail="Lead not found")
            
            # Update the lead
            success = lead_manager.update_lead_fields(
                lead_id,
                status=payload.status,
                priority=payload.priority,
                notes=payload.notes
            )
            
            if not success:
                raise HTTPException(status_code=500, detail="Failed to update lead")
            
            # Get the updated lead
            updated_lead = lead_manager.get_lead_by_id(lead_id)
            if not updated_lead:
                raise HTTPException(status_code=500, detail="Failed to retrieve updated lead")
            
            return LeadResponseItem(
                id=updated_lead["id"],
                company_name=updated_lead["company_name"],
                website_url=updated_lead.get("website_url"),
                address=updated_lead.get("address"),
                contact_email=updated_lead.get("contact_email"),
                phone_number=updated_lead.get("phone_number"),
                description=updated_lead.get("description"),
                automation_proposal=updated_lead.get("automation_proposal"),
                discovered_at=updated_lead["discovered_at"],
                discovered_by_profile_id=updated_lead.get("discovered_by_profile_id"),
                discovered_sectors=updated_lead.get("discovered_sectors"),
                status=updated_lead["status"],
                priority=updated_lead["priority"],
                notes=updated_lead.get("notes"),
                company_type=updated_lead.get("company_type"),
                sector=updated_lead.get("sector"),
                location=updated_lead.get("location"),
                pain_points=updated_lead.get("pain_points"),
                proposed_solution=updated_lead.get("proposed_solution"),
                confidence_score=updated_lead.get("confidence_score"),
                created_at=updated_lead["created_at"],
                updated_at=updated_lead["updated_at"]
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class DiscoverLeadsRequest(BaseModel):
    sectors: List[str]
    profile: CompanyProfile
    max_queries: int = 2  # Default to 2 queries per sector
    sector_precision: str = "medium"  # Default to medium precision


class DiscoverLeadsResponse(BaseModel):
    companies: List[dict]
    queries_used: List[dict]


class Settings(BaseModel):
    sector_count: int = 1
    sector_precision: str = "medium"
    max_queries: int = 2


class SettingsResponse(BaseModel):
    id: int
    profile_id: int
    sector_count: int
    sector_precision: str
    max_queries: int
    created_at: str
    updated_at: str


@app.post("/leads/discover", response_model=DiscoverLeadsResponse)
async def discover_leads(payload: DiscoverLeadsRequest):
    try:
        # Build RecomendedSectorList from provided sector names
        items = [
            RecomendedSectorItem(name=name, justification="Selected by user", order=i + 1)
            for i, name in enumerate(payload.sectors)
        ]
        sector_list = RecomendedSectorList(recomended_sectors=items)

        # Run lead discovery to get search queries
        print("Starting lead discovery...")
        discovery_output = await lead_discovery_agent(sector_list, payload.profile.model_dump(), payload.max_queries)

        # Run lead scraping agent to get structured leads
        print("Starting lead scraping...")
        from ..agents.leadsense import run_lead_scraping_agent, tool_map
        scraping_results = await run_lead_scraping_agent(discovery_output, tool_map, payload.profile.model_dump())
        
        # Convert to frontend-compatible format
        companies = []
        for lead in scraping_results.leads:
            company_data = {
                "company_name": lead.company_name,
                "website_url": lead.website_url,
                "address": "",  # Not provided by scraping agent
                "contact_email": "",  # Not provided by scraping agent
                "phone_number": "",  # Not provided by scraping agent
                "description": lead.description,
                "automation_proposal": lead.lead_reasoning,  # Use lead reasoning as automation proposal
                "linkedin_info": lead.linkedin_info,
                "company_type": lead.company_type,
                "sector": lead.sector,
                "location": lead.location,
                "pain_points": lead.pain_points,
                "proposed_solution": lead.proposed_solution,
                "confidence_score": lead.confidence_score
            }
            companies.append(company_data)
        
        # Prepare queries information for display
        queries_used = []
        for search_item in discovery_output.searches:
            for query in search_item.queries:
                queries_used.append({
                    "sector": search_item.sector,
                    "language": query.language,
                    "query": query.query,
                    "order": query.order
                })
        
        print(f"Found {len(companies)} companies through lead scraping")
        return DiscoverLeadsResponse(
            companies=companies,
            queries_used=queries_used
        )
        
    except Exception as e:
        print(f"Error in discover_leads: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


class GenerateProposalsRequest(BaseModel):
    lead: CompanyLead
    company_profile: CompanyProfile

@app.post("/leads/generate-proposals")
async def generate_lead_proposals(payload: GenerateProposalsRequest):
    """Generate both email and LinkedIn proposals for a lead."""
    try:
        print("Starting proposal generation...")
        
        # Generate both proposals concurrently using company profile from request
        email_task = generate_email_proposal(payload.lead, payload.company_profile.model_dump())
        linkedin_task = generate_linkedin_message(payload.lead, payload.company_profile.model_dump())
        
        # Wait for both tasks to complete
        email_versions, linkedin_message = await asyncio.gather(email_task, linkedin_task)
        
        return {
            "automation_email": {
                "formal": email_versions.formal,
                "informal": email_versions.informal,
                "semi_formal": email_versions.semi_formal
            },
            "linkedin_message": {
                "formal": linkedin_message.formal,
                "informal": linkedin_message.informal,
                "semi_formal": linkedin_message.semi_formal
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/saved-leads/{lead_id}/generate-proposals")
async def generate_saved_lead_proposals(lead_id: int):
    """Generate both email and LinkedIn proposals for a saved lead."""
    try:
        print(f"Starting proposal generation for saved lead {lead_id}...")
        
        with DatabaseManager() as db:
            lead_manager = LeadManager(db)
            profile_manager = CompanyProfileManager(db)
            
            # Get the lead
            lead = lead_manager.get_lead_by_id(lead_id)
            if not lead:
                raise HTTPException(status_code=404, detail="Lead not found")
            
            # Get the company profile
            profiles = profile_manager.get_all_company_profiles()
            if not profiles:
                raise HTTPException(status_code=400, detail="No company profile found. Please save your company profile first.")
            
            company_profile = profiles[0]
            
            # Create CompanyLead object for the proposal generation
            company_lead = CompanyLead(
                company_name=lead["company_name"],
                website_url=lead.get("website_url", ""),
                description=lead.get("description", ""),
                linkedin_info=None,  # We don't store LinkedIn info in saved leads yet
                company_type=lead.get("company_type", ""),
                sector=lead.get("sector", ""),
                location=lead.get("location", ""),
                pain_points=lead.get("pain_points", []),
                proposed_solution=lead.get("proposed_solution", ""),
                lead_reasoning=lead.get("automation_proposal", ""),
                confidence_score=lead.get("confidence_score", 0.8)
            )
            
            # Generate both proposals concurrently
            email_task = generate_email_proposal(company_lead, company_profile)
            linkedin_task = generate_linkedin_message(company_lead, company_profile)
            
            # Wait for both tasks to complete
            email_versions, linkedin_message = await asyncio.gather(email_task, linkedin_task)
            
            # Convert to dictionaries for storage
            automation_email = {
                "formal": email_versions.formal,
                "informal": email_versions.informal,
                "semi_formal": email_versions.semi_formal
            }
            
            linkedin_message_dict = {
                "formal": linkedin_message.formal,
                "informal": linkedin_message.informal,
                "semi_formal": linkedin_message.semi_formal
            }
            
            # Update the lead with the generated proposals
            success = lead_manager.update_lead_proposals(
                lead_id, 
                automation_email=automation_email, 
                linkedin_message=linkedin_message_dict
            )
            
            if not success:
                raise HTTPException(status_code=500, detail="Failed to save proposals to database")
            
            # Get the updated lead to return the new timestamp
            updated_lead = lead_manager.get_lead_by_id(lead_id)
            if not updated_lead:
                raise HTTPException(status_code=500, detail="Failed to retrieve updated lead")
            
            return {
                "automation_email": automation_email,
                "linkedin_message": linkedin_message_dict,
                "updated_at": updated_lead["updated_at"]
            }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/settings", response_model=SettingsResponse)
async def get_settings():
    """Get settings for the current company profile."""
    try:
        with DatabaseManager() as db:
            settings_manager = SettingsManager(db)
            profile_manager = CompanyProfileManager(db)
            
            # Get the current company profile
            profiles = profile_manager.get_all_company_profiles()
            if not profiles:
                raise HTTPException(status_code=400, detail="No company profile found. Please save your company profile first.")
            
            profile_id = profiles[0]["id"]
            
            # Get or create settings for this profile
            settings = settings_manager.get_or_create_settings(profile_id)
            
            return SettingsResponse(
                id=settings["id"],
                profile_id=settings["profile_id"],
                sector_count=settings["sector_count"],
                sector_precision=settings["sector_precision"],
                max_queries=settings["max_queries"],
                created_at=settings["created_at"],
                updated_at=settings["updated_at"]
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/settings", response_model=SettingsResponse)
async def update_settings(settings: Settings):
    """Update settings for the current company profile."""
    try:
        with DatabaseManager() as db:
            settings_manager = SettingsManager(db)
            profile_manager = CompanyProfileManager(db)
            
            # Get the current company profile
            profiles = profile_manager.get_all_company_profiles()
            if not profiles:
                raise HTTPException(status_code=400, detail="No company profile found. Please save your company profile first.")
            
            profile_id = profiles[0]["id"]
            
            # Update settings
            success = settings_manager.update_settings(
                profile_id=profile_id,
                sector_count=settings.sector_count,
                sector_precision=settings.sector_precision,
                max_queries=settings.max_queries
            )
            
            if not success:
                raise HTTPException(status_code=500, detail="Failed to update settings")
            
            # Get the updated settings
            updated_settings = settings_manager.get_settings_by_profile_id(profile_id)
            if not updated_settings:
                raise HTTPException(status_code=500, detail="Failed to retrieve updated settings")
            
            return SettingsResponse(
                id=updated_settings["id"],
                profile_id=updated_settings["profile_id"],
                sector_count=updated_settings["sector_count"],
                sector_precision=updated_settings["sector_precision"],
                max_queries=updated_settings["max_queries"],
                created_at=updated_settings["created_at"],
                updated_at=updated_settings["updated_at"]
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

