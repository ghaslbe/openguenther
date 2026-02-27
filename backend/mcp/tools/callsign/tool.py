import csv
import io
import os
import requests
from services.tool_context import get_emit_log
from config import DATA_DIR

AIRLINES_URL = "https://raw.githubusercontent.com/jpatokal/openflights/master/data/airlines.dat"
AIRLINES_CACHE = os.path.join(DATA_DIR, "airlines.dat")
ADSBONE_URL = "https://api.adsb.one/v2/callsign/{callsign}"

TOOL_DEFINITION = {
    "name": "resolve_callsign",
    "description": (
        "Löst ein Flugzeug-Rufzeichen (Callsign) auf: Airline-Name, Land, ICAO/IATA-Code "
        "und — falls das Flugzeug gerade in der Luft ist — Live-Daten wie Position, Höhe, "
        "Geschwindigkeit und Strecke. "
        "Beispiele: 'DLH1MH' (Lufthansa), 'BAW123' (British Airways), 'DLH' (nur Airline-Info). "
        "Kein API-Key nötig (OpenFlights + adsb.one)."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "callsign": {
                "type": "string",
                "description": (
                    "ICAO-Rufzeichen, z.B. 'DLH1MH', 'BAW456', 'UAL123'. "
                    "Die ersten 2-3 Buchstaben sind der Airline-ICAO-Code."
                )
            }
        },
        "required": ["callsign"]
    }
}


def _load_airlines() -> dict:
    """Lädt die OpenFlights airlines.dat, cached in DATA_DIR. Gibt dict icao -> info zurück."""
    # Cache verwenden wenn vorhanden
    if os.path.exists(AIRLINES_CACHE):
        raw = open(AIRLINES_CACHE, encoding="utf-8", errors="replace").read()
    else:
        resp = requests.get(AIRLINES_URL, timeout=15)
        resp.raise_for_status()
        raw = resp.text
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(AIRLINES_CACHE, "w", encoding="utf-8") as f:
            f.write(raw)

    # Format: id, name, alias, iata, icao, callsign, country, active
    airlines = {}
    reader = csv.reader(io.StringIO(raw))
    for row in reader:
        if len(row) < 8:
            continue
        icao = row[4].strip()
        if icao and icao != r"\N" and icao != "ICAO":
            airlines[icao.upper()] = {
                "name": row[1].strip(),
                "alias": row[2].strip() if row[2].strip() not in ("", r"\N") else None,
                "iata": row[3].strip() if row[3].strip() not in ("", r"\N") else None,
                "icao": icao.upper(),
                "rufzeichen": row[5].strip() if row[5].strip() not in ("", r"\N") else None,
                "land": row[6].strip() if row[6].strip() not in ("", r"\N") else None,
                "aktiv": row[7].strip() == "Y",
            }
    return airlines


def _extract_airline_prefix(callsign: str) -> str | None:
    """Versucht den ICAO-Airline-Prefix aus dem Callsign zu extrahieren (2-3 Buchstaben)."""
    cs = callsign.upper().strip()
    # Typisch: 3 Buchstaben + Ziffern/Rest
    prefix3 = cs[:3] if len(cs) >= 3 else cs
    prefix2 = cs[:2] if len(cs) >= 2 else cs
    return prefix3, prefix2


def resolve_callsign(callsign: str) -> dict:
    emit_log = get_emit_log()

    def log(msg):
        if emit_log:
            emit_log({"type": "text", "message": msg})

    cs = callsign.upper().strip()
    log(f"Callsign auflösen: {cs}")

    result = {"callsign": cs}

    # 1) Airline aus OpenFlights-Datenbank
    try:
        airlines = _load_airlines()
        prefix3, prefix2 = _extract_airline_prefix(cs)

        airline_info = airlines.get(prefix3) or airlines.get(prefix2)
        if airline_info:
            result["airline"] = {k: v for k, v in airline_info.items() if v is not None}
            log(f"Airline: {airline_info['name']} ({prefix3})")
        else:
            result["airline"] = None
            result["hinweis_airline"] = f"Kein Airline-Eintrag für Prefix '{prefix3}' gefunden."
            log(f"Kein Airline-Eintrag für '{prefix3}'")
    except Exception as e:
        result["airline_fehler"] = f"Airline-Lookup fehlgeschlagen: {e}"
        log(f"Airline-Lookup Fehler: {e}")

    # 2) Live-Daten von adsb.one (nur wenn Flugzeug in der Luft)
    try:
        log(f"Live-Daten abrufen: adsb.one/{cs}")
        resp = requests.get(
            ADSBONE_URL.format(callsign=cs),
            headers={"User-Agent": "OpenGuenther/1.0"},
            timeout=10
        )

        if resp.status_code == 404:
            result["live"] = None
            result["hinweis_live"] = "Kein aktiver Flug gefunden (Flugzeug am Boden oder Callsign unbekannt)."
            log("Kein aktiver Flug")
        elif resp.status_code == 200:
            data = resp.json()
            ac_list = data.get("ac") or []

            if not ac_list:
                result["live"] = None
                result["hinweis_live"] = "Kein aktiver Flug gefunden."
                log("Keine Live-Daten")
            else:
                ac = ac_list[0]
                live = {}

                if ac.get("flight"):
                    live["flight"] = ac["flight"].strip()
                if ac.get("r"):
                    live["registration"] = ac["r"]
                if ac.get("t"):
                    live["typ"] = ac["t"]

                lat = ac.get("lat")
                lon = ac.get("lon")
                if lat is not None and lon is not None:
                    live["position"] = {"lat": round(lat, 4), "lon": round(lon, 4)}

                alt_baro = ac.get("alt_baro")
                alt_geom = ac.get("alt_geom")
                alt = alt_baro or alt_geom
                if alt and alt != "ground":
                    try:
                        alt_ft = int(alt)
                        live["höhe_ft"] = alt_ft
                        live["höhe_m"] = round(alt_ft * 0.3048)
                    except (ValueError, TypeError):
                        pass

                gs = ac.get("gs")
                if gs:
                    live["geschwindigkeit_kmh"] = round(float(gs) * 1.852)

                track = ac.get("track")
                if track is not None:
                    live["kurs_grad"] = round(float(track))
                    directions = ["N", "NO", "O", "SO", "S", "SW", "W", "NW"]
                    live["kurs_richtung"] = directions[int((float(track) + 22.5) / 45) % 8]

                baro_rate = ac.get("baro_rate")
                if baro_rate:
                    live["vertikalrate_ft_min"] = int(baro_rate)
                    live["steigt"] = int(baro_rate) > 0

                squawk = ac.get("squawk")
                if squawk:
                    live["squawk"] = squawk

                # Departure / Destination (wenn vorhanden)
                for key, label in [("dep", "abflug_iata"), ("arr", "ziel_iata"),
                                    ("from", "abflug"), ("to", "ziel")]:
                    val = ac.get(key)
                    if val:
                        live[label] = val

                result["live"] = live
                pos_str = f"{live['position']['lat']}, {live['position']['lon']}" if "position" in live else "unbekannt"
                log(f"Live: {live.get('typ', '?')} @ {pos_str}, {live.get('höhe_ft', '?')} ft")
        else:
            result["live"] = None
            result["hinweis_live"] = f"adsb.one antwortete mit Status {resp.status_code}."

    except Exception as e:
        result["live"] = None
        result["live_fehler"] = f"Live-Lookup fehlgeschlagen: {e}"
        log(f"Live-Fehler: {e}")

    return result
