import requests
from services.tool_context import get_emit_log

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

TOOL_DEFINITION = {
    "name": "geocode_location",
    "description": (
        "Gibt die Geokoordinaten (Breitengrad, Längengrad) für eine Postleitzahl, "
        "einen Ortsnamen oder eine Adresse zurück. Nutzt OpenStreetMap Nominatim — "
        "kostenlos, kein API-Key nötig. "
        "Beispiele: '80331' (München PLZ), 'Berlin Mitte', '10115 Berlin', "
        "'Eiffelturm Paris', '221B Baker Street London'."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": (
                    "Postleitzahl, Ortsname oder Adresse. "
                    "Für PLZ-Suche besser mit Länderkürzel ergänzen, z.B. '80331, Deutschland'. "
                    "Funktioniert weltweit."
                )
            },
            "country": {
                "type": "string",
                "description": "Optionales Länderkürzel zur Eingrenzung, z.B. 'DE', 'AT', 'CH', 'US'"
            }
        },
        "required": ["query"]
    }
}


def geocode_location(query: str, country: str = None) -> dict:
    emit_log = get_emit_log()

    def log(msg):
        if emit_log:
            emit_log({"type": "text", "message": msg})

    log(f"Geocoding: {query}")

    params = {
        "q": query,
        "format": "json",
        "addressdetails": 1,
        "limit": 5,
        "accept-language": "de"
    }
    if country:
        params["countrycodes"] = country.lower()

    headers = {
        "User-Agent": "OpenGuenther/1.0 (MCP geocode tool)"
    }

    try:
        resp = requests.get(NOMINATIM_URL, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        results = resp.json()
    except Exception as e:
        return {"error": f"Nominatim-Fehler: {e}"}

    if not results:
        return {"error": f"Keine Ergebnisse für '{query}' gefunden."}

    output = []
    for r in results:
        addr = r.get("address", {})
        entry = {
            "name": r.get("display_name", ""),
            "latitude": float(r["lat"]),
            "longitude": float(r["lon"]),
            "typ": r.get("type", ""),
        }
        # Kompaktere Adressfelder
        for field in ["postcode", "city", "town", "village", "county", "state", "country"]:
            val = addr.get(field)
            if val:
                entry[field] = val

        output.append(entry)

    best = output[0]
    log(f"Gefunden: {best['name'][:60]} → {best['latitude']}, {best['longitude']}")

    return {
        "query": query,
        "ergebnis": best,
        "weitere_treffer": output[1:] if len(output) > 1 else []
    }
