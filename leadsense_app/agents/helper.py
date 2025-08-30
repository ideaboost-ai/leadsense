import re

def extract_json_string(s: str) -> str:
    """Extract JSON string from a given string, handling code fences if present."""
    fenced = re.search(r"```(?:json)?(.*?)```", s, re.S)
    if fenced:
        return fenced.group(1).strip()
    return s.strip()