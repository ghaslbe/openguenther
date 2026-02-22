import requests
import urllib.parse

WIKI_API = "https://{lang}.wikipedia.org/w/api.php"
WIKI_URL = "https://{lang}.wikipedia.org/wiki/{title}"

HEADERS = {"User-Agent": "OpenGuenther/1.0 (MCP Wikipedia Tool)"}

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


def _fetch_extracts(api_url, titles):
    """Fetch intro extracts for one or more page titles. Returns list of page dicts."""
    try:
        resp = requests.get(
            api_url,
            params={
                "action": "query",
                "prop": "extracts",
                "exintro": True,
                "explaintext": True,
                "titles": "|".join(titles) if isinstance(titles, list) else titles,
                "format": "json",
                "utf8": 1,
                "redirects": 1,
            },
            headers=HEADERS,
            timeout=10
        ).json()
    except Exception as e:
        return [], {}

    query_data = resp.get("query", {})
    pages = query_data.get("pages", {})
    # Map "redirect from" → "redirect to"
    redirects = {r["from"]: r["to"] for r in query_data.get("redirects", [])}
    return [p for p in pages.values() if p.get("ns", 0) == 0], redirects


def _format_page(page, query, lang, redirect_from=None):
    """Format a Wikipedia page dict into the tool result format."""
    title = page.get("title", "")
    extract = (page.get("extract") or "").strip()

    max_chars = 4000
    truncated = False
    if len(extract) > max_chars:
        extract = extract[:max_chars].rsplit(" ", 1)[0] + "…"
        truncated = True

    result = {
        "titel": title,
        "sprache": lang,
        "zusammenfassung": extract,
        "url": WIKI_URL.format(
            lang=lang,
            title=urllib.parse.quote(title.replace(" ", "_"))
        ),
    }
    if truncated:
        result["gekuerzt"] = True
    if redirect_from and redirect_from.lower() != title.lower():
        result["weiterleitung_von"] = redirect_from
    return result


def _score(page, query):
    """Score how relevant a page is for the query (higher = better)."""
    title_lower = (page.get("title") or "").lower()
    extract_lower = (page.get("extract") or "").lower()
    query_lower = query.lower()

    if query_lower == title_lower:
        return 100
    if query_lower in title_lower:
        return 80
    if title_lower in query_lower:
        return 60
    if query_lower in extract_lower:
        return 40
    return 10


def wikipedia_search(query, language="de", results=1):
    lang = (language or "de").strip().lower()
    num_results = max(1, min(5, int(results) if results else 1))
    api_url = WIKI_API.format(lang=lang)

    # ── Step 1: Direct title lookup (follows redirects automatically) ──
    pages, redirects = _fetch_extracts(api_url, [query])
    valid = [p for p in pages if not p.get("missing") and p.get("extract")]
    if valid:
        page = valid[0]
        redirect_from = redirects.get(query)
        result = _format_page(page, query, lang, redirect_from)

        # If we landed on a different article via redirect, note that the
        # original term may only be mentioned somewhere in the article body.
        if redirect_from and _score(page, query) < 40:
            result["hinweis"] = (
                f"'{query}' ist eine Wikipedia-Weiterleitung zu '{page.get('title')}'. "
                f"Der Begriff kommt möglicherweise nicht in der Artikeleinleitung vor, "
                f"sondern erst im Artikeltext."
            )
        elif redirect_from:
            result["hinweis"] = f"'{query}' leitet auf '{page.get('title')}' weiter."
        return result

    # ── Step 2: Full-text search ──
    try:
        sr = requests.get(
            api_url,
            params={
                "action": "query",
                "list": "search",
                "srsearch": query,
                "srlimit": max(num_results + 2, 5),
                "format": "json",
                "utf8": 1,
            },
            headers=HEADERS,
            timeout=10
        ).json()
    except Exception as e:
        return {"error": f"Wikipedia-Suche fehlgeschlagen: {e}"}

    hits = sr.get("query", {}).get("search", [])
    if not hits:
        if lang != "en":
            return wikipedia_search(query, language="en", results=num_results)
        return {"error": f"Keine Wikipedia-Artikel für '{query}' gefunden."}

    # ── Step 3: Fetch extracts, score by relevance ──
    titles = [h["title"] for h in hits[:5]]
    pages, redirects = _fetch_extracts(api_url, titles)
    valid = [p for p in pages if p.get("extract")]

    if not valid:
        if lang != "en":
            return wikipedia_search(query, language="en", results=num_results)
        return {"error": f"Keine verwertbaren Inhalte für '{query}' gefunden."}

    scored = sorted(valid, key=lambda p: -_score(p, query))

    if num_results == 1:
        best = scored[0]
        score = _score(best, query)
        result = _format_page(best, query, lang, redirects.get(best.get("title")))

        if score < 40:
            result["hinweis"] = (
                f"Kein direkter Wikipedia-Artikel für '{query}' gefunden. "
                f"Ähnlichster Treffer: '{best.get('title')}' — der Suchbegriff kommt "
                f"möglicherweise nicht in der Einleitung vor."
            )
        elif score == 40:
            result["hinweis"] = f"'{query}' wird im Artikel '{best.get('title')}' erwähnt."

        return result

    # Multiple results
    formatted = []
    for p in scored[:num_results]:
        r = _format_page(p, query, lang, redirects.get(p.get("title")))
        score = _score(p, query)
        if score >= 80:
            r["relevanz"] = "hoch"
        elif score >= 40:
            r["relevanz"] = "mittel"
        else:
            r["relevanz"] = "gering"
        formatted.append(r)

    return {"query": query, "treffer": len(formatted), "artikel": formatted}
