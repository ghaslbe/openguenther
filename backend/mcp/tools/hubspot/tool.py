"""
HubSpot MCP Tool

Kontakte, Firmen und Deals in HubSpot verwalten.

Einstellungen (Einstellungen -> MCP Tools -> hubspot):
  - api_key : HubSpot Private App Token
"""

import requests

from config import get_tool_settings
from services.tool_context import get_emit_log

HUBSPOT_BASE = "https://api.hubapi.com"

SETTINGS_INFO = """**HubSpot**

Verwalte Kontakte, Firmen und Deals in HubSpot.

**Private App Token:** In HubSpot unter Einstellungen → Integrationen → Private Apps → "Private App erstellen".
Berechtigungen benoetigt: `crm.objects.contacts.read/write`, `crm.objects.companies.read/write`, `crm.objects.deals.read/write`.
Token beginnt mit `pat-`."""

SETTINGS_SCHEMA = [
    {
        "key": "api_key",
        "label": "HubSpot Private App Token",
        "type": "password",
        "placeholder": "pat-eu1-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
        "description": "Private App Token aus HubSpot → Einstellungen → Integrationen → Private Apps",
    },
]

TOOL_DEFINITION = {
    "name": "hubspot",
    "description": (
        "HubSpot CRM: Kontakte, Firmen und Deals verwalten. "
        "Aktionen: search_contacts (Kontakte suchen) | "
        "get_contact (Kontakt-Details per contact_id) | "
        "create_contact (neuen Kontakt anlegen) | "
        "update_contact (Kontakt aktualisieren) | "
        "get_deals (Deals abrufen) | "
        "create_deal (neuen Deal anlegen) | "
        "get_companies (Firmen abrufen) | "
        "create_company (neue Firma anlegen)"
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": [
                    "search_contacts",
                    "get_contact",
                    "create_contact",
                    "update_contact",
                    "get_deals",
                    "create_deal",
                    "get_companies",
                    "create_company",
                ],
                "description": (
                    "Aktion: "
                    "search_contacts (nach Name/Email suchen per query) | "
                    "get_contact (Details per contact_id) | "
                    "create_contact (neuer Kontakt mit email, firstname, lastname) | "
                    "update_contact (aktualisieren per contact_id + properties) | "
                    "get_deals (offene Deals abrufen) | "
                    "create_deal (neuer Deal mit dealname, amount, pipeline) | "
                    "get_companies (Firmen abrufen) | "
                    "create_company (neue Firma mit name, domain)"
                ),
            },
            "query": {
                "type": "string",
                "description": "Suchbegriff fuer search_contacts (Name oder E-Mail)",
            },
            "contact_id": {
                "type": "string",
                "description": "HubSpot Kontakt-ID",
            },
            "email": {
                "type": "string",
                "description": "E-Mail-Adresse des Kontakts",
            },
            "firstname": {
                "type": "string",
                "description": "Vorname des Kontakts",
            },
            "lastname": {
                "type": "string",
                "description": "Nachname des Kontakts",
            },
            "phone": {
                "type": "string",
                "description": "Telefonnummer des Kontakts",
            },
            "company": {
                "type": "string",
                "description": "Firmenname des Kontakts",
            },
            "properties": {
                "type": "object",
                "description": (
                    "Beliebige HubSpot-Properties als Objekt fuer update_contact, create_deal, create_company. "
                    'Beispiel: {"lifecyclestage": "lead", "city": "Berlin"}'
                ),
            },
            "dealname": {
                "type": "string",
                "description": "Name des Deals fuer create_deal",
            },
            "amount": {
                "type": "string",
                "description": "Deal-Wert als String fuer create_deal (z.B. '5000')",
            },
            "pipeline": {
                "type": "string",
                "description": "Pipeline-ID fuer create_deal (Standard: 'default')",
            },
            "dealstage": {
                "type": "string",
                "description": "Deal-Stage fuer create_deal (z.B. 'appointmentscheduled', 'qualifiedtobuy', 'closedwon')",
            },
            "name": {
                "type": "string",
                "description": "Firmenname fuer create_company",
            },
            "domain": {
                "type": "string",
                "description": "Domain der Firma fuer create_company (z.B. 'beispiel.de')",
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
    return get_tool_settings("hubspot")


def _headers(api_key):
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def _fmt_contact(c):
    p = c.get("properties", {})
    return {
        "id": c["id"],
        "email": p.get("email"),
        "firstname": p.get("firstname"),
        "lastname": p.get("lastname"),
        "phone": p.get("phone"),
        "company": p.get("company"),
        "lifecycle": p.get("lifecyclestage"),
        "created": p.get("createdate"),
    }


def handler(
    action,
    query=None,
    contact_id=None,
    email=None,
    firstname=None,
    lastname=None,
    phone=None,
    company=None,
    properties=None,
    dealname=None,
    amount=None,
    pipeline="default",
    dealstage=None,
    name=None,
    domain=None,
    limit=20,
):
    emit_log = get_emit_log()

    def log(msg):
        if emit_log:
            emit_log({"type": "text", "message": f"[HubSpot] {msg}"})

    def header(msg):
        if emit_log:
            emit_log({"type": "header", "message": msg})

    cfg = _cfg()
    api_key = cfg.get("api_key", "").strip()
    if not api_key:
        return {"error": "Kein HubSpot Token konfiguriert. Bitte in Einstellungen -> MCP Tools -> hubspot eintragen."}

    hdrs = _headers(api_key)
    cap = min(int(limit or 20), 100)

    try:

        # ── search_contacts ────────────────────────────────────────────────
        if action == "search_contacts":
            header("HUBSPOT SEARCH CONTACTS")
            if not query:
                # Alle neuesten Kontakte
                r = requests.get(
                    f"{HUBSPOT_BASE}/crm/v3/objects/contacts",
                    headers=hdrs,
                    params={"limit": cap, "properties": "email,firstname,lastname,phone,company,lifecyclestage"},
                    timeout=15,
                )
            else:
                r = requests.post(
                    f"{HUBSPOT_BASE}/crm/v3/objects/contacts/search",
                    headers=hdrs,
                    json={
                        "query": query,
                        "limit": cap,
                        "properties": ["email", "firstname", "lastname", "phone", "company", "lifecyclestage"],
                    },
                    timeout=15,
                )
            r.raise_for_status()
            results = r.json().get("results", [])
            log(f"{len(results)} Kontakt(e)")
            return {"count": len(results), "contacts": [_fmt_contact(c) for c in results]}

        # ── get_contact ────────────────────────────────────────────────────
        elif action == "get_contact":
            if not contact_id:
                return {"error": "contact_id erforderlich fuer get_contact"}
            header(f"HUBSPOT CONTACT: {contact_id}")
            r = requests.get(
                f"{HUBSPOT_BASE}/crm/v3/objects/contacts/{contact_id}",
                headers=hdrs,
                params={"properties": "email,firstname,lastname,phone,company,lifecyclestage,city,country,jobtitle"},
                timeout=15,
            )
            r.raise_for_status()
            log("Kontakt geladen")
            return _fmt_contact(r.json())

        # ── create_contact ─────────────────────────────────────────────────
        elif action == "create_contact":
            if not email:
                return {"error": "email erforderlich fuer create_contact"}
            header(f"HUBSPOT CREATE CONTACT: {email}")
            props = {"email": email}
            if firstname:
                props["firstname"] = firstname
            if lastname:
                props["lastname"] = lastname
            if phone:
                props["phone"] = phone
            if company:
                props["company"] = company
            if properties:
                props.update(properties)
            r = requests.post(
                f"{HUBSPOT_BASE}/crm/v3/objects/contacts",
                headers=hdrs,
                json={"properties": props},
                timeout=15,
            )
            r.raise_for_status()
            c = r.json()
            log(f"Kontakt erstellt: {c['id']}")
            return {"success": True, "id": c["id"], "email": email}

        # ── update_contact ─────────────────────────────────────────────────
        elif action == "update_contact":
            if not contact_id:
                return {"error": "contact_id erforderlich fuer update_contact"}
            header(f"HUBSPOT UPDATE CONTACT: {contact_id}")
            props = {}
            if email:
                props["email"] = email
            if firstname:
                props["firstname"] = firstname
            if lastname:
                props["lastname"] = lastname
            if phone:
                props["phone"] = phone
            if company:
                props["company"] = company
            if properties:
                props.update(properties)
            if not props:
                return {"error": "Mindestens ein Feld angeben"}
            r = requests.patch(
                f"{HUBSPOT_BASE}/crm/v3/objects/contacts/{contact_id}",
                headers=hdrs,
                json={"properties": props},
                timeout=15,
            )
            r.raise_for_status()
            log("Kontakt aktualisiert")
            return {"success": True, "id": contact_id}

        # ── get_deals ──────────────────────────────────────────────────────
        elif action == "get_deals":
            header("HUBSPOT DEALS")
            r = requests.get(
                f"{HUBSPOT_BASE}/crm/v3/objects/deals",
                headers=hdrs,
                params={"limit": cap, "properties": "dealname,amount,dealstage,pipeline,closedate,hubspot_owner_id"},
                timeout=15,
            )
            r.raise_for_status()
            results = r.json().get("results", [])
            log(f"{len(results)} Deal(s)")
            return {
                "count": len(results),
                "deals": [
                    {
                        "id": d["id"],
                        "name": d["properties"].get("dealname"),
                        "amount": d["properties"].get("amount"),
                        "stage": d["properties"].get("dealstage"),
                        "pipeline": d["properties"].get("pipeline"),
                        "close_date": d["properties"].get("closedate"),
                    }
                    for d in results
                ],
            }

        # ── create_deal ────────────────────────────────────────────────────
        elif action == "create_deal":
            if not dealname:
                return {"error": "dealname erforderlich fuer create_deal"}
            header(f"HUBSPOT CREATE DEAL: {dealname}")
            props = {
                "dealname": dealname,
                "pipeline": pipeline or "default",
            }
            if amount:
                props["amount"] = str(amount)
            if dealstage:
                props["dealstage"] = dealstage
            if properties:
                props.update(properties)
            r = requests.post(
                f"{HUBSPOT_BASE}/crm/v3/objects/deals",
                headers=hdrs,
                json={"properties": props},
                timeout=15,
            )
            r.raise_for_status()
            d = r.json()
            log(f"Deal erstellt: {d['id']}")
            return {"success": True, "id": d["id"], "name": dealname}

        # ── get_companies ──────────────────────────────────────────────────
        elif action == "get_companies":
            header("HUBSPOT COMPANIES")
            r = requests.get(
                f"{HUBSPOT_BASE}/crm/v3/objects/companies",
                headers=hdrs,
                params={"limit": cap, "properties": "name,domain,city,country,phone,industry"},
                timeout=15,
            )
            r.raise_for_status()
            results = r.json().get("results", [])
            log(f"{len(results)} Firma(en)")
            return {
                "count": len(results),
                "companies": [
                    {
                        "id": c["id"],
                        "name": c["properties"].get("name"),
                        "domain": c["properties"].get("domain"),
                        "city": c["properties"].get("city"),
                        "industry": c["properties"].get("industry"),
                    }
                    for c in results
                ],
            }

        # ── create_company ─────────────────────────────────────────────────
        elif action == "create_company":
            if not name:
                return {"error": "name erforderlich fuer create_company"}
            header(f"HUBSPOT CREATE COMPANY: {name}")
            props = {"name": name}
            if domain:
                props["domain"] = domain
            if properties:
                props.update(properties)
            r = requests.post(
                f"{HUBSPOT_BASE}/crm/v3/objects/companies",
                headers=hdrs,
                json={"properties": props},
                timeout=15,
            )
            r.raise_for_status()
            c = r.json()
            log(f"Firma erstellt: {c['id']}")
            return {"success": True, "id": c["id"], "name": name}

        else:
            return {"error": f"Unbekannte Aktion: '{action}'."}

    except requests.HTTPError as e:
        try:
            detail = e.response.json()
        except Exception:
            detail = e.response.text[:300]
        log(f"HTTP {e.response.status_code}: {detail}")
        return {"error": f"HubSpot API Fehler ({e.response.status_code}): {detail}"}
    except Exception as e:
        log(f"Fehler: {e}")
        return {"error": str(e)}
