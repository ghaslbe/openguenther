"""
WordPress MCP Tool

Beitraege, Seiten, Kategorien und Tags ueber die WordPress REST API verwalten.

Einstellungen (Einstellungen -> MCP Tools -> wordpress):
  - site_url  : WordPress-URL (z.B. https://meineblog.de)
  - username  : WordPress-Benutzername
  - app_password : Anwendungspasswort (WordPress → Profil → Anwendungspasswoerter)
"""

import requests
from requests.auth import HTTPBasicAuth

from config import get_tool_settings
from services.tool_context import get_emit_log

SETTINGS_INFO = """**WordPress**

Lese und verwalte Beitraege, Seiten, Kategorien und Tags ueber die WordPress REST API.

**Anwendungspasswort erstellen:**
1. WordPress-Admin oeffnen → oben rechts auf deinen Namen klicken → Profil
2. Ganz unten: "Anwendungspasswoerter" → Namen eingeben (z.B. "Guenther") → "Anwendungspasswort hinzufuegen"
3. Das generierte Passwort kopieren (wird nur einmal angezeigt!)

**Voraussetzung:** WordPress 5.6+ und Permalinks muessen aktiviert sein (nicht "Einfach")."""

SETTINGS_SCHEMA = [
    {
        "key": "site_url",
        "label": "WordPress URL",
        "type": "text",
        "placeholder": "https://meineblog.de",
        "description": "URL deiner WordPress-Seite (ohne abschliessenden Slash)",
    },
    {
        "key": "username",
        "label": "Benutzername",
        "type": "text",
        "placeholder": "admin",
        "description": "WordPress-Benutzername",
    },
    {
        "key": "app_password",
        "label": "Anwendungspasswort",
        "type": "password",
        "placeholder": "xxxx xxxx xxxx xxxx xxxx xxxx",
        "description": "Anwendungspasswort aus WordPress → Profil → Anwendungspasswoerter (Leerzeichen sind OK)",
    },
]

TOOL_DEFINITION = {
    "name": "wordpress",
    "description": (
        "WordPress: Beitraege und Seiten lesen, erstellen, bearbeiten und loeschen. "
        "Aktionen: get_posts (Beitraege abrufen) | "
        "get_post (einzelnen Beitrag lesen) | "
        "create_post (neuen Beitrag schreiben) | "
        "update_post (Beitrag bearbeiten) | "
        "delete_post (Beitrag loeschen) | "
        "get_pages (Seiten abrufen) | "
        "get_categories (Kategorien auflisten) | "
        "get_tags (Tags auflisten) | "
        "create_category (neue Kategorie anlegen)"
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": [
                    "get_posts",
                    "get_post",
                    "create_post",
                    "update_post",
                    "delete_post",
                    "get_pages",
                    "get_categories",
                    "get_tags",
                    "create_category",
                ],
                "description": (
                    "Aktion: "
                    "get_posts (Beitraege abrufen, filterbar nach Status/Kategorie/Suche) | "
                    "get_post (einzelnen Beitrag per post_id lesen inkl. Inhalt) | "
                    "create_post (neuer Beitrag mit title + content, optional status/categories/tags) | "
                    "update_post (Beitrag aendern per post_id) | "
                    "delete_post (Beitrag in Papierkorb per post_id) | "
                    "get_pages (Seiten abrufen) | "
                    "get_categories (alle Kategorien auflisten) | "
                    "get_tags (alle Tags auflisten) | "
                    "create_category (neue Kategorie per name anlegen)"
                ),
            },
            "post_id": {
                "type": "integer",
                "description": "WordPress Beitrags-ID fuer get_post, update_post, delete_post",
            },
            "title": {
                "type": "string",
                "description": "Titel des Beitrags oder der Seite",
            },
            "content": {
                "type": "string",
                "description": "Inhalt des Beitrags (HTML oder plain text, WordPress konvertiert automatisch)",
            },
            "excerpt": {
                "type": "string",
                "description": "Kurzfassung/Teaser des Beitrags (optional)",
            },
            "status": {
                "type": "string",
                "enum": ["publish", "draft", "pending", "private"],
                "description": "Beitragsstatus: publish (sofort veroeffentlichen), draft (Entwurf), pending (zur Pruefung), private",
            },
            "categories": {
                "type": "array",
                "items": {"type": "integer"},
                "description": "Liste von Kategorie-IDs fuer den Beitrag (IDs aus get_categories)",
            },
            "tags": {
                "type": "array",
                "items": {"type": "integer"},
                "description": "Liste von Tag-IDs fuer den Beitrag (IDs aus get_tags)",
            },
            "search": {
                "type": "string",
                "description": "Suchbegriff fuer get_posts",
            },
            "filter_status": {
                "type": "string",
                "description": "Status-Filter fuer get_posts: 'publish', 'draft', 'any' (Standard: publish)",
            },
            "filter_category": {
                "type": "integer",
                "description": "Kategorie-ID zum Filtern bei get_posts",
            },
            "name": {
                "type": "string",
                "description": "Name fuer create_category",
            },
            "limit": {
                "type": "integer",
                "description": "Maximale Anzahl Ergebnisse fuer get_posts / get_pages (Standard: 10)",
            },
        },
        "required": ["action"],
    },
}


def _cfg():
    return get_tool_settings("wordpress")


def _auth(cfg):
    username = cfg.get("username", "").strip()
    password = cfg.get("app_password", "").replace(" ", "")
    return HTTPBasicAuth(username, password)


def _base(cfg):
    url = cfg.get("site_url", "").strip().rstrip("/")
    return f"{url}/wp-json/wp/v2"


def _fmt_post(p):
    return {
        "id": p.get("id"),
        "title": p.get("title", {}).get("rendered", ""),
        "status": p.get("status"),
        "date": p.get("date", "")[:10],
        "link": p.get("link", ""),
        "categories": p.get("categories", []),
        "tags": p.get("tags", []),
        "excerpt": p.get("excerpt", {}).get("rendered", "").strip(),
    }


def handler(
    action,
    post_id=None,
    title=None,
    content=None,
    excerpt=None,
    status="draft",
    categories=None,
    tags=None,
    search=None,
    filter_status="publish",
    filter_category=None,
    name=None,
    limit=10,
):
    emit_log = get_emit_log()

    def log(msg):
        if emit_log:
            emit_log({"type": "text", "message": f"[WordPress] {msg}"})

    def header(msg):
        if emit_log:
            emit_log({"type": "header", "message": msg})

    cfg = _cfg()
    if not cfg.get("site_url") or not cfg.get("username") or not cfg.get("app_password"):
        return {
            "error": (
                "WordPress nicht konfiguriert. "
                "Bitte in Einstellungen -> MCP Tools -> wordpress "
                "Site-URL, Benutzername und Anwendungspasswort eintragen."
            )
        }

    auth = _auth(cfg)
    base = _base(cfg)
    cap = min(int(limit or 10), 100)

    try:

        # ── get_posts ──────────────────────────────────────────────────────
        if action == "get_posts":
            header("WORDPRESS GET POSTS")
            params = {"per_page": cap, "status": filter_status or "publish"}
            if search:
                params["search"] = search
            if filter_category:
                params["categories"] = filter_category
            r = requests.get(f"{base}/posts", auth=auth, params=params, timeout=15)
            r.raise_for_status()
            posts = r.json()
            log(f"{len(posts)} Beitrag/Beitraege")
            return {
                "count": len(posts),
                "posts": [_fmt_post(p) for p in posts],
            }

        # ── get_post ───────────────────────────────────────────────────────
        elif action == "get_post":
            if not post_id:
                return {"error": "post_id erforderlich fuer get_post"}
            header(f"WORDPRESS GET POST: {post_id}")
            r = requests.get(f"{base}/posts/{post_id}", auth=auth, timeout=15)
            r.raise_for_status()
            p = r.json()
            result = _fmt_post(p)
            result["content"] = p.get("content", {}).get("rendered", "")
            log(f"Beitrag: {result['title']}")
            return result

        # ── create_post ────────────────────────────────────────────────────
        elif action == "create_post":
            if not title:
                return {"error": "title erforderlich fuer create_post"}
            if not content:
                return {"error": "content erforderlich fuer create_post"}
            header(f"WORDPRESS CREATE: {title[:60]}")
            payload = {
                "title": title,
                "content": content,
                "status": status or "draft",
            }
            if excerpt:
                payload["excerpt"] = excerpt
            if categories:
                payload["categories"] = categories
            if tags:
                payload["tags"] = tags
            r = requests.post(f"{base}/posts", auth=auth, json=payload, timeout=15)
            r.raise_for_status()
            p = r.json()
            log(f"Beitrag erstellt: ID {p.get('id')} ({p.get('status')})")
            return {
                "success": True,
                "id": p.get("id"),
                "title": p.get("title", {}).get("rendered", title),
                "status": p.get("status"),
                "link": p.get("link", ""),
            }

        # ── update_post ────────────────────────────────────────────────────
        elif action == "update_post":
            if not post_id:
                return {"error": "post_id erforderlich fuer update_post"}
            header(f"WORDPRESS UPDATE: {post_id}")
            payload = {}
            if title:
                payload["title"] = title
            if content:
                payload["content"] = content
            if excerpt is not None:
                payload["excerpt"] = excerpt
            if status:
                payload["status"] = status
            if categories is not None:
                payload["categories"] = categories
            if tags is not None:
                payload["tags"] = tags
            if not payload:
                return {"error": "Mindestens ein Feld angeben (title, content, status, ...)"}
            r = requests.post(f"{base}/posts/{post_id}", auth=auth, json=payload, timeout=15)
            r.raise_for_status()
            p = r.json()
            log(f"Beitrag aktualisiert: {p.get('title', {}).get('rendered', '')}")
            return {
                "success": True,
                "id": p.get("id"),
                "title": p.get("title", {}).get("rendered", ""),
                "status": p.get("status"),
                "link": p.get("link", ""),
            }

        # ── delete_post ────────────────────────────────────────────────────
        elif action == "delete_post":
            if not post_id:
                return {"error": "post_id erforderlich fuer delete_post"}
            header(f"WORDPRESS DELETE: {post_id}")
            r = requests.delete(f"{base}/posts/{post_id}", auth=auth, timeout=15)
            r.raise_for_status()
            p = r.json()
            log(f"Beitrag in Papierkorb: {post_id}")
            return {
                "success": True,
                "id": post_id,
                "status": p.get("status"),
            }

        # ── get_pages ──────────────────────────────────────────────────────
        elif action == "get_pages":
            header("WORDPRESS GET PAGES")
            params = {"per_page": cap, "status": "publish,draft,private"}
            if search:
                params["search"] = search
            r = requests.get(f"{base}/pages", auth=auth, params=params, timeout=15)
            r.raise_for_status()
            pages = r.json()
            log(f"{len(pages)} Seite(n)")
            return {
                "count": len(pages),
                "pages": [
                    {
                        "id": p.get("id"),
                        "title": p.get("title", {}).get("rendered", ""),
                        "status": p.get("status"),
                        "link": p.get("link", ""),
                        "date": p.get("date", "")[:10],
                    }
                    for p in pages
                ],
            }

        # ── get_categories ─────────────────────────────────────────────────
        elif action == "get_categories":
            header("WORDPRESS CATEGORIES")
            r = requests.get(f"{base}/categories", auth=auth, params={"per_page": 100}, timeout=15)
            r.raise_for_status()
            cats = r.json()
            log(f"{len(cats)} Kategorie(n)")
            return {
                "count": len(cats),
                "categories": [
                    {"id": c.get("id"), "name": c.get("name"), "count": c.get("count", 0)}
                    for c in cats
                ],
            }

        # ── get_tags ───────────────────────────────────────────────────────
        elif action == "get_tags":
            header("WORDPRESS TAGS")
            r = requests.get(f"{base}/tags", auth=auth, params={"per_page": 100}, timeout=15)
            r.raise_for_status()
            tags_list = r.json()
            log(f"{len(tags_list)} Tag(s)")
            return {
                "count": len(tags_list),
                "tags": [
                    {"id": t.get("id"), "name": t.get("name"), "count": t.get("count", 0)}
                    for t in tags_list
                ],
            }

        # ── create_category ────────────────────────────────────────────────
        elif action == "create_category":
            if not name:
                return {"error": "name erforderlich fuer create_category"}
            header(f"WORDPRESS CREATE CATEGORY: {name}")
            r = requests.post(f"{base}/categories", auth=auth, json={"name": name}, timeout=15)
            r.raise_for_status()
            c = r.json()
            log(f"Kategorie erstellt: ID {c.get('id')}")
            return {"success": True, "id": c.get("id"), "name": c.get("name")}

        else:
            return {"error": f"Unbekannte Aktion: '{action}'."}

    except requests.HTTPError as e:
        try:
            detail = e.response.json()
        except Exception:
            detail = e.response.text[:300]
        log(f"HTTP {e.response.status_code}: {detail}")
        return {"error": f"WordPress API Fehler ({e.response.status_code}): {detail}"}
    except Exception as e:
        log(f"Fehler: {e}")
        return {"error": str(e)}
