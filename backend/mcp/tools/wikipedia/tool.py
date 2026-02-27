import requests
import urllib.parse
from config import get_tool_settings

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


def _api_get(api_url, params, timeout=10):
    return requests.get(api_url, params={**params, "format": "json", "utf8": 1},
                        headers=HEADERS, timeout=timeout).json()


def _fetch_page(api_url, titles, intro_only=True, timeout=10):
    """Fetch page extract(s). Returns (pages_list, redirects_dict)."""
    params = {
        "action": "query",
        "prop": "extracts",
        "explaintext": True,
        "titles": "|".join(titles) if isinstance(titles, list) else titles,
        "redirects": 1,
    }
    if intro_only:
        params["exintro"] = True
    try:
        resp = _api_get(api_url, params, timeout=timeout)
    except Exception:
        return [], {}
    qdata = resp.get("query", {})
    redirects = {r["from"]: r["to"] for r in qdata.get("redirects", [])}
    pages = [p for p in qdata.get("pages", {}).values() if p.get("ns", 0) == 0]
    return pages, redirects


def _find_snippet(full_text, query, context=600):
    """Return a text window around the first occurrence of query in full_text."""
    pos = full_text.lower().find(query.lower())
    if pos == -1:
        return None
    start = max(0, pos - 150)
    end = min(len(full_text), pos + len(query) + context)
    snippet = full_text[start:end].strip()
    # Trim to word boundaries
    if start > 0:
        cut = snippet.find(" ")
        if 0 < cut < 40:
            snippet = "…" + snippet[cut:]
    if end < len(full_text):
        cut = snippet.rfind(" ")
        if cut > len(snippet) - 40:
            snippet = snippet[:cut] + "…"
    return snippet


def _score(page, query):
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


def _build_result(page, query, lang, redirect_from=None, snippet=None):
    title = page.get("title", "")
    intro = (page.get("extract") or "").strip()

    max_chars = 3000
    truncated = False
    if len(intro) > max_chars:
        intro = intro[:max_chars].rsplit(" ", 1)[0] + "…"
        truncated = True

    result = {
        "titel": title,
        "sprache": lang,
        "zusammenfassung": intro,
        "url": WIKI_URL.format(lang=lang,
                               title=urllib.parse.quote(title.replace(" ", "_"))),
    }
    if truncated:
        result["gekuerzt"] = True
    if redirect_from and redirect_from.lower() != title.lower():
        result["weiterleitung_von"] = redirect_from
    if snippet:
        result["erwaehnung_im_artikel"] = snippet
    return result


def wikipedia_search(query, language="de", results=1):
    lang = (language or "de").strip().lower()
    num_results = max(1, min(5, int(results) if results else 1))
    api_url = WIKI_API.format(lang=lang)
    timeout = int(get_tool_settings('wikipedia_search').get('timeout') or 10)

    # ── Step 1: Direct title lookup with redirect following ──
    pages, redirects = _fetch_page(api_url, [query], intro_only=True, timeout=timeout)
    valid = [p for p in pages if not p.get("missing") and p.get("extract")]

    if valid:
        page = valid[0]
        redirect_from = redirects.get(query)
        score = _score(page, query)

        # Query not found in intro → dig into the full article text
        snippet = None
        if score < 40:
            full_pages, _ = _fetch_page(api_url, [page.get("title", query)], intro_only=False, timeout=timeout)
            if full_pages and full_pages[0].get("extract"):
                snippet = _find_snippet(full_pages[0]["extract"], query)

        result = _build_result(page, query, lang, redirect_from, snippet)

        if redirect_from:
            if snippet:
                result["hinweis"] = (
                    f"'{query}' leitet auf '{page.get('title')}' weiter und wird "
                    f"im Artikel im Abschnitt 'erwaehnung_im_artikel' erwähnt."
                )
            elif score < 40:
                result["hinweis"] = (
                    f"'{query}' leitet auf '{page.get('title')}' weiter, "
                    f"wird aber in der Einleitung nicht erwähnt. "
                    f"Der Begriff ist wahrscheinlich ein Ortsteil oder Unterthema."
                )
            else:
                result["hinweis"] = f"'{query}' leitet auf '{page.get('title')}' weiter."
        return result

    # ── Step 2: Full-text search ──
    try:
        sr = _api_get(api_url, {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": max(num_results + 2, 5),
        }, timeout=timeout)
    except Exception as e:
        return {"error": f"Wikipedia-Suche fehlgeschlagen: {e}"}

    hits = sr.get("query", {}).get("search", [])
    if not hits:
        if lang != "en":
            return wikipedia_search(query, language="en", results=num_results)
        return {"error": f"Keine Wikipedia-Artikel für '{query}' gefunden."}

    # ── Step 3: Fetch intros, score, enrich weak matches with full-text snippet ──
    titles = [h["title"] for h in hits[:5]]
    pages, redirects = _fetch_page(api_url, titles, intro_only=True, timeout=timeout)
    valid = [p for p in pages if p.get("extract")]
    if not valid:
        if lang != "en":
            return wikipedia_search(query, language="en", results=num_results)
        return {"error": f"Keine verwertbaren Inhalte für '{query}' gefunden."}

    scored = sorted(valid, key=lambda p: -_score(p, query))

    def enrich(page):
        score = _score(page, query)
        snippet = None
        if score < 40:
            full_pages, _ = _fetch_page(api_url, [page.get("title", "")], intro_only=False, timeout=timeout)
            if full_pages and full_pages[0].get("extract"):
                snippet = _find_snippet(full_pages[0]["extract"], query)
        r = _build_result(page, query, lang, redirects.get(page.get("title")), snippet)
        if score < 40 and not snippet:
            r["hinweis"] = (
                f"Kein direkter Artikel für '{query}'. "
                f"Ähnlichster Treffer: '{page.get('title')}'"
            )
        elif score < 40 and snippet:
            r["hinweis"] = f"'{query}' wird im Artikel '{page.get('title')}' erwähnt."
        return r

    if num_results == 1:
        return enrich(scored[0])

    formatted = []
    for p in scored[:num_results]:
        r = enrich(p)
        s = _score(p, query)
        r["relevanz"] = "hoch" if s >= 80 else ("mittel" if s >= 40 else "gering")
        formatted.append(r)

    return {"query": query, "treffer": len(formatted), "artikel": formatted}
