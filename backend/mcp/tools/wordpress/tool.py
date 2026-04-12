"""
WordPress MCP Tool

Beitraege erstellen/lesen/bearbeiten/loeschen, Medien hochladen und auflisten.
Auth: WordPress Application Passwords (Benutzer + App-Passwort).

Markdown-Workflow:
  - Inhalt SENDEN:  Markdown direkt übermitteln — WordPress-Plugin konvertiert zu HTML.
  - Inhalt LESEN:   HTML aus WordPress wird automatisch zu Markdown umgewandelt.
"""

import os
import mimetypes
import requests
from requests.auth import HTTPBasicAuth

from config import get_tool_settings
from services.tool_context import get_emit_log

# html2text: HTML → Markdown (wird lazy importiert damit Ladefehler sichtbar sind)
try:
    import html2text as _html2text
    _H2T = _html2text.HTML2Text()
    _H2T.ignore_links = False
    _H2T.ignore_images = False
    _H2T.body_width = 0          # kein Zeilenumbruch
    _H2T.unicode_snob = True
    def _html_to_md(html: str) -> str:
        return _H2T.handle(html or '').strip()
except ImportError:
    def _html_to_md(html: str) -> str:
        # Fallback: einfaches Tag-Stripping
        import re
        return re.sub(r'<[^>]+>', '', html or '').strip()


SETTINGS_INFO = """**WordPress**

Lese und verwalte Beitraege und Medien über die WordPress REST API.

**Markdown-Workflow:**
- Inhalte werden als **Markdown** gesendet — das WordPress-Plugin konvertiert zu HTML.
- Empfangene Inhalte werden von HTML → Markdown umgewandelt.

**Anwendungspasswort erstellen:**
1. WordPress-Admin → oben rechts Name klicken → Profil
2. Ganz unten: "Anwendungspasswörter" → Namen eingeben (z.B. "Guenther") → Hinzufügen
3. Generiertes Passwort kopieren (wird nur einmal angezeigt!)

**Voraussetzung:** WordPress 5.6+ · Permalinks aktiviert (nicht "Einfach") · Markdown-Plugin aktiv"""

SETTINGS_SCHEMA = [
    {
        "key": "site_url",
        "label": "WordPress URL",
        "type": "text",
        "placeholder": "https://meineblog.de",
        "description": "URL der WordPress-Installation (ohne abschließenden Slash)",
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
        "description": "Anwendungspasswort aus WordPress → Profil → Anwendungspasswörter (Leerzeichen sind OK)",
    },
]

TOOL_DEFINITION = {
    "name": "wordpress",
    "description": (
        "WordPress: Beitraege und Medien verwalten. "
        "Inhalt wird als Markdown gesendet (Plugin konvertiert zu HTML); "
        "empfangene HTML-Inhalte werden automatisch nach Markdown umgewandelt. "
        "Aktionen: get_posts · get_post · create_post · update_post · delete_post · "
        "get_pages · get_categories · get_tags · create_category · "
        "upload_media · list_media"
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": [
                    "get_posts", "get_post",
                    "create_post", "update_post", "delete_post",
                    "get_pages",
                    "get_categories", "get_tags", "create_category",
                    "upload_media", "list_media",
                ],
                "description": (
                    "Aktion:\n"
                    "  get_posts        — Beiträge auflisten (filter_status, search, filter_category, limit)\n"
                    "  get_post         — Einzelnen Beitrag lesen inkl. Markdown-Inhalt (post_id)\n"
                    "  create_post      — Neuen Beitrag erstellen (title, content als Markdown, status, categories, tags, featured_media_id)\n"
                    "  update_post      — Beitrag aktualisieren (post_id + beliebige Felder)\n"
                    "  delete_post      — Beitrag in Papierkorb (post_id)\n"
                    "  get_pages        — Seiten auflisten\n"
                    "  get_categories   — Alle Kategorien auflisten\n"
                    "  get_tags         — Alle Tags auflisten\n"
                    "  create_category  — Neue Kategorie anlegen (name)\n"
                    "  upload_media     — Datei in Mediathek hochladen (file_path)\n"
                    "  list_media       — Mediathek auflisten"
                ),
            },
            # ── Beitrags-Felder ──────────────────────────────────────────────
            "post_id": {
                "type": "integer",
                "description": "Beitrags-ID (für get_post, update_post, delete_post)",
            },
            "title": {
                "type": "string",
                "description": "Titel des Beitrags",
            },
            "content": {
                "type": "string",
                "description": "Inhalt als Markdown — WordPress-Plugin konvertiert zu HTML",
            },
            "excerpt": {
                "type": "string",
                "description": "Teaser/Auszug (optional, auch Markdown)",
            },
            "status": {
                "type": "string",
                "enum": ["publish", "draft", "pending", "private"],
                "description": "Status: publish (sofort), draft (Entwurf), pending, private",
            },
            "categories": {
                "type": "array",
                "items": {"type": "integer"},
                "description": "Kategorie-IDs (aus get_categories)",
            },
            "tags": {
                "type": "array",
                "items": {"type": "integer"},
                "description": "Tag-IDs (aus get_tags)",
            },
            "featured_media_id": {
                "type": "integer",
                "description": "Medien-ID des Vorschaubilds (aus upload_media oder list_media)",
            },
            # ── Filter/Pagination ────────────────────────────────────────────
            "search": {
                "type": "string",
                "description": "Suchbegriff",
            },
            "filter_status": {
                "type": "string",
                "description": "Status-Filter für get_posts: publish, draft, any (Standard: publish)",
            },
            "filter_category": {
                "type": "integer",
                "description": "Kategorie-ID-Filter für get_posts",
            },
            "limit": {
                "type": "integer",
                "description": "Maximale Anzahl Ergebnisse (Standard: 10, max: 100)",
            },
            "page": {
                "type": "integer",
                "description": "Seitennummer für Pagination (Standard: 1)",
            },
            # ── Medien-Felder ────────────────────────────────────────────────
            "file_path": {
                "type": "string",
                "description": "Absoluter Pfad zur Datei auf dem Server (z.B. /app/data/uploads/bild.jpg)",
            },
            "media_title": {
                "type": "string",
                "description": "Titel der Mediendatei (optional, für upload_media)",
            },
            "alt_text": {
                "type": "string",
                "description": "Alt-Text für Bilder (optional, für upload_media)",
            },
            "caption": {
                "type": "string",
                "description": "Bildunterschrift (optional, für upload_media)",
            },
            "media_type": {
                "type": "string",
                "description": "Typ-Filter für list_media: image, video, audio, application",
            },
            # ── Sonstiges ────────────────────────────────────────────────────
            "name": {
                "type": "string",
                "description": "Name für create_category",
            },
        },
        "required": ["action"],
    },
}


# ── Hilfsfunktionen ──────────────────────────────────────────────────────────

def _cfg():
    return get_tool_settings("wordpress")


def _auth(cfg):
    username = cfg.get("username", "").strip()
    password = cfg.get("app_password", "").replace(" ", "")
    return HTTPBasicAuth(username, password)


def _base(cfg):
    url = cfg.get("site_url", "").strip().rstrip("/")
    return f"{url}/wp-json/wp/v2"


def _fmt_post(p, include_content=False):
    result = {
        "id": p.get("id"),
        "title": p.get("title", {}).get("rendered", ""),
        "status": p.get("status"),
        "date": p.get("date", "")[:10],
        "link": p.get("link", ""),
        "categories": p.get("categories", []),
        "tags": p.get("tags", []),
        "featured_media": p.get("featured_media"),
        "excerpt": _html_to_md(p.get("excerpt", {}).get("rendered", "")),
    }
    if include_content:
        result["content"] = _html_to_md(p.get("content", {}).get("rendered", ""))
    return result


def _fmt_media(m):
    return {
        "id": m.get("id"),
        "title": m.get("title", {}).get("rendered", ""),
        "media_type": m.get("media_type", ""),
        "mime_type": m.get("mime_type", ""),
        "source_url": m.get("source_url", ""),
        "date": m.get("date", "")[:10],
        "alt_text": m.get("alt_text", ""),
    }


# ── Haupt-Handler ────────────────────────────────────────────────────────────

def handler(
    action,
    post_id=None,
    title=None,
    content=None,
    excerpt=None,
    status="draft",
    categories=None,
    tags=None,
    featured_media_id=None,
    search=None,
    filter_status="publish",
    filter_category=None,
    name=None,
    limit=10,
    page=1,
    # Medien
    file_path=None,
    media_title=None,
    alt_text=None,
    caption=None,
    media_type=None,
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
                "Bitte in Einstellungen → MCP Tools → wordpress "
                "URL, Benutzername und Anwendungspasswort eintragen."
            )
        }

    auth = _auth(cfg)
    base = _base(cfg)
    cap = min(int(limit or 10), 100)

    try:

        # ── get_posts ──────────────────────────────────────────────────────
        if action == "get_posts":
            header("WORDPRESS GET POSTS")
            params = {"per_page": cap, "page": int(page or 1), "status": filter_status or "publish"}
            if search:
                params["search"] = search
            if filter_category:
                params["categories"] = filter_category
            r = requests.get(f"{base}/posts", auth=auth, params=params, timeout=15)
            r.raise_for_status()
            posts = r.json()
            total = r.headers.get("X-WP-Total", "?")
            log(f"{len(posts)} Beitrag/Beiträge (gesamt: {total})")
            return {"total": total, "count": len(posts), "posts": [_fmt_post(p) for p in posts]}

        # ── get_post ───────────────────────────────────────────────────────
        elif action == "get_post":
            if not post_id:
                return {"error": "post_id erforderlich"}
            header(f"WORDPRESS GET POST: {post_id}")
            r = requests.get(f"{base}/posts/{post_id}", auth=auth, timeout=15)
            r.raise_for_status()
            p = r.json()
            result = _fmt_post(p, include_content=True)
            log(f"Beitrag: {result['title']}")
            return result

        # ── create_post ────────────────────────────────────────────────────
        elif action == "create_post":
            if not title:
                return {"error": "title ist ein Pflichtfeld"}
            if not content:
                return {"error": "content ist ein Pflichtfeld"}
            header(f"WORDPRESS CREATE: {title[:60]}")
            payload = {"title": title, "content": content, "status": status or "draft"}
            if excerpt:
                payload["excerpt"] = excerpt
            if categories:
                payload["categories"] = categories
            if tags:
                payload["tags"] = tags
            if featured_media_id:
                payload["featured_media"] = featured_media_id
            r = requests.post(f"{base}/posts", auth=auth, json=payload, timeout=20)
            r.raise_for_status()
            p = r.json()
            log(f"Erstellt: ID {p.get('id')} | Status: {p.get('status')} | {p.get('link', '')}")
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
                return {"error": "post_id ist ein Pflichtfeld"}
            header(f"WORDPRESS UPDATE: {post_id}")
            payload = {}
            if title is not None:
                payload["title"] = title
            if content is not None:
                payload["content"] = content
            if excerpt is not None:
                payload["excerpt"] = excerpt
            if status:
                payload["status"] = status
            if categories is not None:
                payload["categories"] = categories
            if tags is not None:
                payload["tags"] = tags
            if featured_media_id is not None:
                payload["featured_media"] = featured_media_id
            if not payload:
                return {"error": "Mindestens ein Feld angeben (title, content, status, …)"}
            r = requests.post(f"{base}/posts/{post_id}", auth=auth, json=payload, timeout=20)
            r.raise_for_status()
            p = r.json()
            log(f"Aktualisiert: {p.get('title', {}).get('rendered', '')} | {p.get('status')}")
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
                return {"error": "post_id ist ein Pflichtfeld"}
            header(f"WORDPRESS DELETE: {post_id}")
            r = requests.delete(f"{base}/posts/{post_id}", auth=auth, timeout=15)
            r.raise_for_status()
            p = r.json()
            log(f"In Papierkorb: ID {post_id}")
            return {"success": True, "id": post_id, "status": p.get("status")}

        # ── get_pages ──────────────────────────────────────────────────────
        elif action == "get_pages":
            header("WORDPRESS GET PAGES")
            params = {"per_page": cap, "page": int(page or 1), "status": "publish,draft,private"}
            if search:
                params["search"] = search
            r = requests.get(f"{base}/pages", auth=auth, params=params, timeout=15)
            r.raise_for_status()
            pages = r.json()
            total = r.headers.get("X-WP-Total", "?")
            log(f"{len(pages)} Seite(n) (gesamt: {total})")
            return {
                "total": total,
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
                "categories": [{"id": c.get("id"), "name": c.get("name"), "count": c.get("count", 0)} for c in cats],
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
                "tags": [{"id": t.get("id"), "name": t.get("name"), "count": t.get("count", 0)} for t in tags_list],
            }

        # ── create_category ────────────────────────────────────────────────
        elif action == "create_category":
            if not name:
                return {"error": "name ist ein Pflichtfeld"}
            header(f"WORDPRESS CREATE CATEGORY: {name}")
            r = requests.post(f"{base}/categories", auth=auth, json={"name": name}, timeout=15)
            r.raise_for_status()
            c = r.json()
            log(f"Kategorie erstellt: ID {c.get('id')}")
            return {"success": True, "id": c.get("id"), "name": c.get("name")}

        # ── upload_media ───────────────────────────────────────────────────
        elif action == "upload_media":
            if not file_path:
                return {"error": "file_path ist ein Pflichtfeld"}
            if not os.path.isfile(file_path):
                return {"error": f"Datei nicht gefunden: {file_path}"}

            filename = os.path.basename(file_path)
            mime = mimetypes.guess_type(filename)[0] or "application/octet-stream"
            header(f"WORDPRESS UPLOAD MEDIA: {filename}")
            log(f"Dateityp: {mime} | Größe: {os.path.getsize(file_path):,} Bytes")

            with open(file_path, "rb") as f:
                data = f.read()

            upload_headers = {
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Type": mime,
            }
            r = requests.post(
                f"{base}/media",
                data=data,
                headers=upload_headers,
                auth=auth,
                timeout=60,
            )
            r.raise_for_status()
            m = r.json()
            media_id = m["id"]

            # Optionale Meta-Felder nachträglich setzen
            meta = {}
            if media_title:
                meta["title"] = media_title
            if alt_text:
                meta["alt_text"] = alt_text
            if caption:
                meta["caption"] = caption
            if meta:
                requests.post(f"{base}/media/{media_id}", json=meta, auth=auth, timeout=15)

            log(f"Hochgeladen: ID {media_id} | {m.get('source_url', '')}")
            return {
                "success": True,
                "id": media_id,
                "url": m.get("source_url", ""),
                "mime_type": mime,
                "filename": filename,
            }

        # ── list_media ─────────────────────────────────────────────────────
        elif action == "list_media":
            header("WORDPRESS LIST MEDIA")
            params = {"per_page": cap, "page": int(page or 1)}
            if search:
                params["search"] = search
            if media_type:
                params["media_type"] = media_type
            r = requests.get(f"{base}/media", auth=auth, params=params, timeout=15)
            r.raise_for_status()
            items = r.json()
            total = r.headers.get("X-WP-Total", "?")
            log(f"{len(items)} Medien (gesamt: {total})")
            return {
                "total": total,
                "count": len(items),
                "media": [_fmt_media(m) for m in items],
            }

        else:
            return {"error": f"Unbekannte Aktion: '{action}'."}

    except requests.HTTPError as e:
        try:
            detail = e.response.json()
            msg = detail.get("message") or detail.get("code") or str(detail)
        except Exception:
            msg = e.response.text[:400]
        log(f"HTTP {e.response.status_code}: {msg}")
        return {"error": f"WordPress API Fehler ({e.response.status_code}): {msg}"}
    except Exception as e:
        log(f"Fehler: {e}")
        return {"error": str(e)}
