import requests
import urllib.parse

WIKI_API = "https://{lang}.wikipedia.org/w/api.php"
WIKI_URL = "https://{lang}.wikipedia.org/wiki/{title}"

TOOL_DEFINITION = {
    "name": "wikipedia_search",
    "description": (
        "Sucht auf Wikipedia nach einem Thema und liefert die Zusammenfassung des besten Treffers. "
        "Ideal für Allgemeinwissen, Definitionen, historische Ereignisse, Personen, Orte, "
        "wissenschaftliche Konzepte und aktuelle Themen. "
        "Nutze dieses Tool wenn jemand etwas Faktisches wissen möchte. "
        "Unterstützt Deutsch (de) und Englisch (en) sowie andere Wikipedia-Sprachen."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Suchbegriff oder Thema, z.B. 'Schwarzes Loch', 'Albert Einstein', 'Python Programmiersprache'"
            },
            "language": {
                "type": "string",
                "description": "Wikipedia-Sprache: 'de' (Deutsch, Standard), 'en' (Englisch), 'fr', 'es', etc.",
                "default": "de"
            },
            "results": {
                "type": "integer",
                "description": "Anzahl der Suchergebnisse die zurückgegeben werden sollen (1–5, Standard: 1 = nur bester Treffer)"
            }
        },
        "required": ["query"]
    }
}


def wikipedia_search(query, language="de", results=1):
    lang = (language or "de").strip().lower()
    num_results = max(1, min(5, int(results) if results else 1))
    api_url = WIKI_API.format(lang=lang)

    # Step 1: Search
    try:
        search_resp = requests.get(
            api_url,
            params={
                "action": "query",
                "list": "search",
                "srsearch": query,
                "srlimit": num_results,
                "format": "json",
                "utf8": 1,
            },
            headers={"User-Agent": "OpenGuenther/1.0 (MCP Wikipedia Tool)"},
            timeout=10
        ).json()
    except Exception as e:
        return {"error": f"Wikipedia-Suche fehlgeschlagen: {e}"}

    search_hits = search_resp.get("query", {}).get("search", [])
    if not search_hits:
        # Try English as fallback if German returned nothing
        if lang != "en":
            return wikipedia_search(query, language="en", results=num_results)
        return {"error": f"Keine Wikipedia-Artikel für '{query}' gefunden."}

    # Step 2: Fetch extracts for top hit(s)
    titles = [hit["title"] for hit in search_hits[:num_results]]

    try:
        extract_resp = requests.get(
            api_url,
            params={
                "action": "query",
                "prop": "extracts",
                "exintro": True,
                "explaintext": True,
                "titles": "|".join(titles),
                "format": "json",
                "utf8": 1,
                "redirects": 1,
            },
            headers={"User-Agent": "OpenGuenther/1.0 (MCP Wikipedia Tool)"},
            timeout=10
        ).json()
    except Exception as e:
        return {"error": f"Wikipedia-Artikelabruf fehlgeschlagen: {e}"}

    pages = extract_resp.get("query", {}).get("pages", {})

    # Build result list (pages dict uses page IDs as keys)
    articles = []
    for page in pages.values():
        if page.get("ns", 0) != 0:
            continue
        title = page.get("title", "")
        extract = (page.get("extract") or "").strip()

        # Trim very long extracts — LLM should summarize, not process 50k chars
        max_chars = 4000
        truncated = False
        if len(extract) > max_chars:
            extract = extract[:max_chars].rsplit(" ", 1)[0] + "…"
            truncated = True

        if not extract:
            continue

        article_url = WIKI_URL.format(
            lang=lang,
            title=urllib.parse.quote(title.replace(" ", "_"))
        )

        articles.append({
            "titel": title,
            "sprache": lang,
            "zusammenfassung": extract,
            "gekuerzt": truncated,
            "url": article_url,
        })

    if not articles:
        return {"error": f"Keine verwertbaren Inhalte für '{query}' gefunden."}

    if num_results == 1:
        return articles[0]

    return {
        "query": query,
        "treffer": len(articles),
        "artikel": articles,
    }
