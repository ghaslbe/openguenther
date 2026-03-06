"""
Pipedrive MCP Tool

Kontakte (Persons), Deals, Organisationen und Aktivitaeten in Pipedrive verwalten.

Einstellungen (Einstellungen -> MCP Tools -> pipedrive):
  - api_token  : Pipedrive API Token
  - subdomain  : Pipedrive Subdomain (z.B. 'meinefirma' fuer meinefirma.pipedrive.com)
"""

import requests

from config import get_tool_settings
from services.tool_context import get_emit_log

SETTINGS_INFO = """**Pipedrive**

Verwalte Deals, Kontakte und Aktivitaeten in Pipedrive.

**API Token:** In Pipedrive unter Einstellungen → Persoenliche Einstellungen → API → API Token kopieren.

**Subdomain:** Der erste Teil deiner Pipedrive-URL, z.B. bei `meinefirma.pipedrive.com` ist es `meinefirma`."""

SETTINGS_SCHEMA = [
    {
        "key": "api_token",
        "label": "Pipedrive API Token",
        "type": "password",
        "placeholder": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "description": "API Token aus Pipedrive → Einstellungen → Persoenliche Einstellungen → API",
    },
    {
        "key": "subdomain",
        "label": "Subdomain",
        "type": "text",
        "placeholder": "meinefirma",
        "description": "Deine Pipedrive-Subdomain (erster Teil von meinefirma.pipedrive.com)",
    },
]

TOOL_DEFINITION = {
    "name": "pipedrive",
    "description": (
        "Pipedrive CRM: Deals, Kontakte, Organisationen und Aktivitaeten verwalten. "
        "Aktionen: get_deals (Deals abrufen) | "
        "create_deal (neuen Deal anlegen) | "
        "update_deal (Deal aktualisieren) | "
        "get_persons (Kontakte abrufen) | "
        "create_person (neuen Kontakt anlegen) | "
        "get_organizations (Organisationen abrufen) | "
        "create_organization (neue Organisation anlegen) | "
        "get_pipelines (Pipelines auflisten) | "
        "add_activity (Aktivitaet zu Deal oder Kontakt hinzufuegen)"
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": [
                    "get_deals",
                    "create_deal",
                    "update_deal",
                    "get_persons",
                    "create_person",
                    "get_organizations",
                    "create_organization",
                    "get_pipelines",
                    "add_activity",
                ],
                "description": (
                    "Aktion: "
                    "get_deals (alle oder gefilterte Deals) | "
                    "create_deal (neuer Deal mit title + optional person_id, org_id, value, pipeline_id) | "
                    "update_deal (Deal aktualisieren per deal_id) | "
                    "get_persons (Kontakte suchen oder auflisten) | "
                    "create_person (neuer Kontakt mit name + optional email, phone, org_id) | "
                    "get_organizations (Organisationen auflisten) | "
                    "create_organization (neue Organisation mit name) | "
                    "get_pipelines (alle Pipelines und Stages auflisten) | "
                    "add_activity (Aktivitaet zu Deal/Person per deal_id oder person_id)"
                ),
            },
            "deal_id": {
                "type": "integer",
                "description": "Pipedrive Deal-ID",
            },
            "person_id": {
                "type": "integer",
                "description": "Pipedrive Person-ID",
            },
            "org_id": {
                "type": "integer",
                "description": "Pipedrive Organisations-ID",
            },
            "pipeline_id": {
                "type": "integer",
                "description": "Pipeline-ID fuer create_deal oder Filter",
            },
            "stage_id": {
                "type": "integer",
                "description": "Stage-ID fuer create_deal oder update_deal",
            },
            "title": {
                "type": "string",
                "description": "Titel des Deals fuer create_deal oder update_deal",
            },
            "value": {
                "type": "number",
                "description": "Deal-Wert in der konfigurierten Waehrung",
            },
            "currency": {
                "type": "string",
                "description": "Waehrung des Deals, z.B. 'EUR', 'USD' (Standard: EUR)",
            },
            "status": {
                "type": "string",
                "description": "Deal-Status: 'open', 'won', 'lost' fuer update_deal",
            },
            "name": {
                "type": "string",
                "description": "Name der Person oder Organisation",
            },
            "email": {
                "type": "string",
                "description": "E-Mail der Person",
            },
            "phone": {
                "type": "string",
                "description": "Telefonnummer der Person",
            },
            "activity_type": {
                "type": "string",
                "description": "Typ der Aktivitaet: 'call', 'meeting', 'email', 'task', 'deadline' (Standard: 'task')",
            },
            "activity_subject": {
                "type": "string",
                "description": "Betreff der Aktivitaet",
            },
            "due_date": {
                "type": "string",
                "description": "Faelligkeitsdatum der Aktivitaet im Format YYYY-MM-DD",
            },
            "query": {
                "type": "string",
                "description": "Suchbegriff fuer get_persons oder get_deals",
            },
            "limit": {
                "type": "integer",
                "description": "Maximale Anzahl Ergebnisse (Standard: 20)",
            },
        },
        "required": ["action"],
    },
}


def _cfg():
    return get_tool_settings("pipedrive")


def _base_url(cfg):
    subdomain = cfg.get("subdomain", "").strip()
    if subdomain:
        return f"https://{subdomain}.pipedrive.com/api/v1"
    return "https://api.pipedrive.com/v1"


def _get(cfg, path, **params):
    token = cfg.get("api_token", "").strip()
    url = f"{_base_url(cfg)}{path}"
    r = requests.get(url, params={"api_token": token, **params}, timeout=15)
    r.raise_for_status()
    data = r.json()
    if not data.get("success"):
        raise ValueError(data.get("error", "Pipedrive Fehler"))
    return data.get("data") or []


def _post(cfg, path, payload):
    token = cfg.get("api_token", "").strip()
    url = f"{_base_url(cfg)}{path}"
    r = requests.post(url, params={"api_token": token}, json=payload, timeout=15)
    r.raise_for_status()
    data = r.json()
    if not data.get("success"):
        raise ValueError(data.get("error", "Pipedrive Fehler"))
    return data.get("data", {})


def _put(cfg, path, payload):
    token = cfg.get("api_token", "").strip()
    url = f"{_base_url(cfg)}{path}"
    r = requests.put(url, params={"api_token": token}, json=payload, timeout=15)
    r.raise_for_status()
    data = r.json()
    if not data.get("success"):
        raise ValueError(data.get("error", "Pipedrive Fehler"))
    return data.get("data", {})


def _fmt_deal(d):
    return {
        "id": d.get("id"),
        "title": d.get("title"),
        "value": d.get("value"),
        "currency": d.get("currency"),
        "status": d.get("status"),
        "stage": d.get("stage_id"),
        "pipeline": d.get("pipeline_id"),
        "person": d.get("person_id", {}).get("name") if isinstance(d.get("person_id"), dict) else d.get("person_id"),
        "org": d.get("org_id", {}).get("name") if isinstance(d.get("org_id"), dict) else d.get("org_id"),
        "add_time": d.get("add_time"),
        "close_time": d.get("close_time"),
    }


def _fmt_person(p):
    emails = p.get("email", [])
    phones = p.get("phone", [])
    return {
        "id": p.get("id"),
        "name": p.get("name"),
        "email": emails[0].get("value") if emails else None,
        "phone": phones[0].get("value") if phones else None,
        "org": p.get("org_id", {}).get("name") if isinstance(p.get("org_id"), dict) else None,
    }


def handler(
    action,
    deal_id=None,
    person_id=None,
    org_id=None,
    pipeline_id=None,
    stage_id=None,
    title=None,
    value=None,
    currency="EUR",
    status=None,
    name=None,
    email=None,
    phone=None,
    activity_type="task",
    activity_subject=None,
    due_date=None,
    query=None,
    limit=20,
):
    emit_log = get_emit_log()

    def log(msg):
        if emit_log:
            emit_log({"type": "text", "message": f"[Pipedrive] {msg}"})

    def header(msg):
        if emit_log:
            emit_log({"type": "header", "message": msg})

    cfg = _cfg()
    if not cfg.get("api_token"):
        return {"error": "Kein Pipedrive API Token konfiguriert. Bitte in Einstellungen -> MCP Tools -> pipedrive eintragen."}

    cap = min(int(limit or 20), 100)

    try:

        # ── get_pipelines ──────────────────────────────────────────────────
        if action == "get_pipelines":
            header("PIPEDRIVE PIPELINES")
            pipelines = _get(cfg, "/pipelines")
            result = []
            for p in (pipelines if isinstance(pipelines, list) else []):
                stages = _get(cfg, f"/stages", pipeline_id=p["id"])
                result.append({
                    "id": p["id"],
                    "name": p["name"],
                    "stages": [{"id": s["id"], "name": s["name"]} for s in (stages if isinstance(stages, list) else [])],
                })
            log(f"{len(result)} Pipeline(s)")
            return {"count": len(result), "pipelines": result}

        # ── get_deals ──────────────────────────────────────────────────────
        elif action == "get_deals":
            header("PIPEDRIVE DEALS")
            params = {"limit": cap, "status": status or "open"}
            if pipeline_id:
                params["pipeline_id"] = pipeline_id
            deals = _get(cfg, "/deals", **params)
            deals = deals if isinstance(deals, list) else []
            if query:
                q = query.lower()
                deals = [d for d in deals if q in (d.get("title") or "").lower()]
            log(f"{len(deals)} Deal(s)")
            return {"count": len(deals), "deals": [_fmt_deal(d) for d in deals]}

        # ── create_deal ────────────────────────────────────────────────────
        elif action == "create_deal":
            if not title:
                return {"error": "title erforderlich fuer create_deal"}
            header(f"PIPEDRIVE CREATE DEAL: {title}")
            payload = {"title": title, "currency": currency or "EUR"}
            if value is not None:
                payload["value"] = value
            if person_id:
                payload["person_id"] = person_id
            if org_id:
                payload["org_id"] = org_id
            if pipeline_id:
                payload["pipeline_id"] = pipeline_id
            if stage_id:
                payload["stage_id"] = stage_id
            deal = _post(cfg, "/deals", payload)
            log(f"Deal erstellt: {deal.get('id')}")
            return {"success": True, "id": deal.get("id"), "title": title}

        # ── update_deal ────────────────────────────────────────────────────
        elif action == "update_deal":
            if not deal_id:
                return {"error": "deal_id erforderlich fuer update_deal"}
            header(f"PIPEDRIVE UPDATE DEAL: {deal_id}")
            payload = {}
            if title:
                payload["title"] = title
            if value is not None:
                payload["value"] = value
            if status:
                payload["status"] = status
            if stage_id:
                payload["stage_id"] = stage_id
            if not payload:
                return {"error": "Mindestens ein Feld angeben (title, value, status, stage_id)"}
            deal = _put(cfg, f"/deals/{deal_id}", payload)
            log(f"Deal aktualisiert: {deal.get('title')}")
            return {"success": True, "id": deal_id}

        # ── get_persons ────────────────────────────────────────────────────
        elif action == "get_persons":
            header("PIPEDRIVE PERSONS")
            if query:
                data = _get(cfg, "/persons/search", term=query, limit=cap)
                persons = [item.get("item", {}) for item in (data.get("items", []) if isinstance(data, dict) else [])]
            else:
                persons = _get(cfg, "/persons", limit=cap)
                persons = persons if isinstance(persons, list) else []
            log(f"{len(persons)} Person(en)")
            return {"count": len(persons), "persons": [_fmt_person(p) for p in persons]}

        # ── create_person ──────────────────────────────────────────────────
        elif action == "create_person":
            if not name:
                return {"error": "name erforderlich fuer create_person"}
            header(f"PIPEDRIVE CREATE PERSON: {name}")
            payload = {"name": name}
            if email:
                payload["email"] = [{"value": email, "primary": True}]
            if phone:
                payload["phone"] = [{"value": phone, "primary": True}]
            if org_id:
                payload["org_id"] = org_id
            person = _post(cfg, "/persons", payload)
            log(f"Person erstellt: {person.get('id')}")
            return {"success": True, "id": person.get("id"), "name": name}

        # ── get_organizations ──────────────────────────────────────────────
        elif action == "get_organizations":
            header("PIPEDRIVE ORGANIZATIONS")
            orgs = _get(cfg, "/organizations", limit=cap)
            orgs = orgs if isinstance(orgs, list) else []
            log(f"{len(orgs)} Organisation(en)")
            return {
                "count": len(orgs),
                "organizations": [
                    {"id": o.get("id"), "name": o.get("name"), "address": o.get("address")}
                    for o in orgs
                ],
            }

        # ── create_organization ────────────────────────────────────────────
        elif action == "create_organization":
            if not name:
                return {"error": "name erforderlich fuer create_organization"}
            header(f"PIPEDRIVE CREATE ORG: {name}")
            org = _post(cfg, "/organizations", {"name": name})
            log(f"Organisation erstellt: {org.get('id')}")
            return {"success": True, "id": org.get("id"), "name": name}

        # ── add_activity ───────────────────────────────────────────────────
        elif action == "add_activity":
            if not activity_subject:
                return {"error": "activity_subject erforderlich fuer add_activity"}
            header(f"PIPEDRIVE ADD ACTIVITY: {activity_subject}")
            payload = {
                "subject": activity_subject,
                "type": activity_type or "task",
            }
            if deal_id:
                payload["deal_id"] = deal_id
            if person_id:
                payload["person_id"] = person_id
            if due_date:
                payload["due_date"] = due_date
            activity = _post(cfg, "/activities", payload)
            log(f"Aktivitaet erstellt: {activity.get('id')}")
            return {"success": True, "id": activity.get("id"), "subject": activity_subject}

        else:
            return {"error": f"Unbekannte Aktion: '{action}'."}

    except requests.HTTPError as e:
        try:
            detail = e.response.json()
        except Exception:
            detail = e.response.text[:300]
        log(f"HTTP {e.response.status_code}: {detail}")
        return {"error": f"Pipedrive API Fehler ({e.response.status_code}): {detail}"}
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        log(f"Fehler: {e}")
        return {"error": str(e)}
