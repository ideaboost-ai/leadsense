import aiohttp

async def fetch_html_content(url: str) -> str:
    """
    Fetch raw HTML content from a URL using direct HTTP request
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
    }
    
    timeout_config = aiohttp.ClientTimeout(total=15)
    
    async with aiohttp.ClientSession(headers=headers, timeout=timeout_config) as session:
        async with session.get(url) as response:
            response.raise_for_status()  # Will raise exception for HTTP errors
            html_content = await response.text()
            return html_content