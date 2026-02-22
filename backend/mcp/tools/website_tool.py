import requests
import re
from config import get_tool_settings


def fetch_website_info(url):
    """Fetch title and meta description from a website."""
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    timeout = int(get_tool_settings('fetch_website_info').get('timeout') or 10)

    try:
        response = requests.get(url, timeout=timeout, headers={
            'User-Agent': 'Guenther-Bot/1.0'
        })
        response.raise_for_status()
        html = response.text[:50000]  # Limit to first 50k chars

        title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
        title = title_match.group(1).strip() if title_match else None

        desc_match = re.search(
            r'<meta[^>]*name=["\']description["\'][^>]*content=["\'](.*?)["\']',
            html, re.IGNORECASE | re.DOTALL
        )
        if not desc_match:
            desc_match = re.search(
                r'<meta[^>]*content=["\'](.*?)["\'][^>]*name=["\']description["\']',
                html, re.IGNORECASE | re.DOTALL
            )
        description = desc_match.group(1).strip() if desc_match else None

        return {
            "url": url,
            "title": title,
            "description": description,
            "status_code": response.status_code
        }
    except requests.RequestException as e:
        return {"url": url, "error": str(e)}


TOOL_DEFINITION = {
    "name": "fetch_website_info",
    "description": "Ruft den Titel und die Beschreibung einer Website ab.",
    "input_schema": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "Die URL der Website (z.B. 'https://example.com')"
            }
        },
        "required": ["url"]
    }
}
