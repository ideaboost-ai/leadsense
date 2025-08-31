import os
import httpx

async def scrape_website(url: str) -> str:
    headers = {
        'Authorization': f'Bearer {os.getenv("SPIDER_API_KEY")}',
        'Content-Type': 'application/json',
    }

    payload = {
        "limit": 1,
        "return_format": "markdown",
        "url": url
    }

    async with httpx.AsyncClient() as client:
        response = await client.post('https://api.spider.cloud/crawl', headers=headers, json=payload)
        response.raise_for_status()

    return response.json()

async def google_search(query: str) -> str:
    headers = {
        'X-API-KEY': os.getenv("SERPER_API_KEY"),
        'Content-Type': 'application/json',
    }

    payload = {
        "q": query
    }

    async with httpx.AsyncClient() as client:
        response = await client.post('https://google.serper.dev/search', headers=headers, json=payload)
        response.raise_for_status()
        return response.text

async def extract_company_linkedin_profile(company_name: str) -> str:
    headers = {
        "x-rapidapi-key": os.getenv("RAPID_API_KEY"),
        "x-rapidapi-host": "linkedin-data-api.p.rapidapi.com",
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(f'https://linkedin-data-api.p.rapidapi.com/get-company-details?username={company_name}', headers=headers)
        response.raise_for_status()
        return response.json()

def reflection(drafted_answer: str, reflection: str, next_step: str) -> str:
    return "Reflection completed. Next step: " + next_step

tools = [
    {
        "type": "function",
        "function": {
            "name": "scrape_website",
            "description": "Scrapes a website and returns the content in markdown format",
            "strict": True,
            "parameters": {
                "type": "object",
                "required": [
                    "url"
                ],
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL of the website to scrape"
                    }
                },
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "reflection",
            "description": "Make sure you use this reflection before finish any task, and only consider task as completed if next step is 'Provide answer'",
            "strict": True,
            "parameters": {
                "type": "object",
                "required": [
                    "drafted_answer", "reflection", "next_step"
                ],
                "properties": {
                    "drafted_answer": {
                        "type": "string",
                        "description": "draft the answer to research topic based on information found so far" 
                    },
                    "reflection": {
                        "type": "string",
                        "description": "Review the information we had so far, critique & review if our answer is right"
                    },
                    "next_step": {
                        "type": "string",
                        "description": "The next step we should take, if no further actions can be taken and you already did everything you can to do the research, then output 'Provide answer', Otherwise, instruct the next best actions"
                    }
                },
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "google_search",
            "description": "Performs a Google search and returns the results as a string",
            "strict": True,
            "parameters": {
                "type": "object",
                "required": [
                    "query"
                ],
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query string"
                    }
                },
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "extract_company_linkedin_profile",
            "description": "Extracts LinkedIn profile information from a given company name.",
            "strict": True,
            "parameters": {
                "type": "object",
                "required": [
                    "company_name"
                ],
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "Company name to extract information from, e.g. google, apple, etc."
                    }
                },
                "additionalProperties": False
            }
        }
    }
]

tool_map = {
    'scrape_website': scrape_website,
    'google_search': google_search,
    'extract_company_linkedin_profile': extract_company_linkedin_profile,
    'reflection': reflection
}