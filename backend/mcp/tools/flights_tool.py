import io
import math
import base64
import requests
from services.tool_context import get_emit_log

OPENSKY_URL = "https://opensky-network.org/api/states/all"

# OpenSky state vector field indices
FIELDS = [
    "icao24", "callsign", "origin_country", "time_position",
    "last_contact", "longitude", "latitude", "baro_altitude",
    "on_ground", "velocity", "true_track", "vertical_rate",
    "sensors", "geo_altitude", "squawk", "spi", "position_source"
]

TOOL_DEFINITION = {
    "name": "get_flights_nearby",
    "description": (
        "Zeigt aktuelle Flugzeuge in der Nähe von Geokoordinaten (live ADS-B Daten). "
        "Gibt Rufzeichen, Herkunftsland, Höhe, Geschwindigkeit und Kurs zurück. "
        "Kann optional eine Karte als Bild ausgeben (show_map: true). "
        "Nutzt OpenSky Network — kostenlos, kein API-Key nötig. "
        "Tipp: Erst geocode_location aufrufen, um Koordinaten einer PLZ oder Stadt zu ermitteln, "
        "dann diese Funktion mit den Koordinaten verwenden."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "latitude": {
                "type": "number",
                "description": "Breitengrad (z.B. 48.1374 für München)"
            },
            "longitude": {
                "type": "number",
                "description": "Längengrad (z.B. 11.5755 für München)"
            },
            "radius_km": {
                "type": "number",
                "description": "Suchradius in Kilometern (Standard: 100, Max: 500)"
            },
            "max_results": {
                "type": "integer",
                "description": "Maximale Anzahl zurückgegebener Flugzeuge (Standard: 20, Max: 50)"
            },
            "show_map": {
                "type": "boolean",
                "description": "Karte mit eingezeichneten Flugzeugen als Bild ausgeben (Standard: false)"
            }
        },
        "required": ["latitude", "longitude"]
    }
}


def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _render_map(center_lat: float, center_lon: float, radius_km: float, flights: list) -> str:
    """Rendert eine OSM-Karte mit Flugzeug-Markierungen. Gibt base64-PNG zurück."""
    from staticmap import StaticMap, CircleMarker

    # Zoom-Level aus Radius ableiten
    if radius_km > 400:
        zoom = 6
    elif radius_km > 200:
        zoom = 7
    elif radius_km > 100:
        zoom = 8
    elif radius_km > 50:
        zoom = 9
    elif radius_km > 20:
        zoom = 10
    else:
        zoom = 11

    m = StaticMap(900, 900, url_template="https://tile.openstreetmap.org/{z}/{x}/{y}.png")

    # Mittelpunkt (rot, größer)
    m.add_marker(CircleMarker((center_lon, center_lat), "#ff3333", 14))
    m.add_marker(CircleMarker((center_lon, center_lat), "white", 6))

    # Flugzeuge (blau, mit Richtungsindikator wenn Track bekannt)
    for f in flights:
        lat = f["koordinaten"]["lat"]
        lon = f["koordinaten"]["lon"]
        on_ground = f.get("am_boden", False)
        color = "#888888" if on_ground else "#1a88ff"
        m.add_marker(CircleMarker((lon, lat), "white", 12))
        m.add_marker(CircleMarker((lon, lat), color, 9))

    image = m.render(zoom=zoom)

    # Callsigns als Text einzeichnen (mit Pillow)
    try:
        from PIL import ImageDraw, ImageFont
        draw = ImageDraw.Draw(image)

        # Koordinaten → Pixel-Position (grobe Näherung via staticmap-Projektion)
        # staticmap zentriert das Bild auf center_lat/lon bei gegebenem Zoom
        def deg_to_tile(lat, lon, z):
            n = 2 ** z
            x = (lon + 180) / 360 * n
            y = (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n
            return x, y

        cx, cy = deg_to_tile(center_lat, center_lon, zoom)
        tile_size = 256
        img_w, img_h = image.size

        for f in flights:
            lat = f["koordinaten"]["lat"]
            lon = f["koordinaten"]["lon"]
            tx, ty = deg_to_tile(lat, lon, zoom)
            px = int((tx - cx) * tile_size + img_w / 2)
            py = int((ty - cy) * tile_size + img_h / 2)

            callsign = f.get("callsign", "")
            if callsign and callsign != "unbekannt" and 0 < px < img_w and 0 < py < img_h:
                # Weißer Hintergrund für Lesbarkeit
                draw.text((px + 8, py - 8), callsign, fill="black", stroke_width=2, stroke_fill="white")
    except Exception:
        pass  # Text-Overlay optional, kein harter Fehler

    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def get_flights_nearby(latitude: float, longitude: float,
                       radius_km: float = 100, max_results: int = 20,
                       show_map: bool = False) -> dict:
    emit_log = get_emit_log()

    def log(msg):
        if emit_log:
            emit_log({"type": "text", "message": msg})

    radius_km = min(float(radius_km), 500)
    max_results = min(int(max_results), 50)

    # Bounding box aus Radius berechnen (1° Breitengrad ≈ 111 km)
    lat_delta = radius_km / 111.0
    lon_delta = radius_km / (111.0 * abs(math.cos(math.radians(latitude))) or 0.001)

    lamin = latitude - lat_delta
    lamax = latitude + lat_delta
    lomin = longitude - lon_delta
    lomax = longitude + lon_delta

    log(f"Flüge abrufen bei {latitude:.4f}, {longitude:.4f} (Radius: {radius_km} km)")

    params = {
        "lamin": round(lamin, 4),
        "lamax": round(lamax, 4),
        "lomin": round(lomin, 4),
        "lomax": round(lomax, 4),
    }

    headers = {"User-Agent": "OpenGuenther/1.0 (MCP flights tool)"}

    try:
        resp = requests.get(OPENSKY_URL, params=params, headers=headers, timeout=15)
        if resp.status_code == 429:
            return {"error": "OpenSky Rate-Limit erreicht. Bitte kurz warten und erneut versuchen."}
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return {"error": f"OpenSky-Fehler: {e}"}

    states = data.get("states") or []
    if not states:
        return {
            "koordinaten": {"lat": latitude, "lon": longitude},
            "radius_km": radius_km,
            "anzahl": 0,
            "flugzeuge": [],
            "hinweis": "Keine Flugzeuge in diesem Bereich gefunden (oder keine aktuellen Daten)."
        }

    flights = []
    for s in states:
        sv = dict(zip(FIELDS, s))
        lat = sv.get("latitude")
        lon = sv.get("longitude")
        if lat is None or lon is None:
            continue

        dist = haversine(latitude, longitude, lat, lon)
        callsign = (sv.get("callsign") or "").strip() or "unbekannt"
        altitude = sv.get("baro_altitude")
        geo_alt = sv.get("geo_altitude")
        velocity = sv.get("velocity")
        track = sv.get("true_track")
        vrate = sv.get("vertical_rate")
        on_ground = sv.get("on_ground", False)

        entry = {
            "callsign": callsign,
            "icao24": sv.get("icao24", ""),
            "herkunftsland": sv.get("origin_country", ""),
            "entfernung_km": round(dist, 1),
            "koordinaten": {"lat": round(lat, 4), "lon": round(lon, 4)},
            "am_boden": on_ground,
        }

        if altitude is not None:
            entry["höhe_m"] = round(altitude)
            entry["höhe_ft"] = round(altitude * 3.28084)
        elif geo_alt is not None:
            entry["höhe_m"] = round(geo_alt)
            entry["höhe_ft"] = round(geo_alt * 3.28084)

        if velocity is not None:
            entry["geschwindigkeit_kmh"] = round(velocity * 3.6)

        if track is not None:
            entry["kurs_grad"] = round(track)
            directions = ["N", "NO", "O", "SO", "S", "SW", "W", "NW"]
            entry["kurs_richtung"] = directions[int((track + 22.5) / 45) % 8]

        if vrate is not None and abs(vrate) > 0.5:
            entry["vertikalrate_m_s"] = round(vrate, 1)
            entry["steigt"] = vrate > 0

        flights.append((dist, entry))

    flights.sort(key=lambda x: x[0])
    flights = [f[1] for f in flights[:max_results]]

    log(f"{len(flights)} Flugzeuge gefunden (von {len(states)} in Bounding Box)")

    result = {
        "koordinaten": {"lat": latitude, "lon": longitude},
        "radius_km": radius_km,
        "anzahl": len(flights),
        "flugzeuge": flights
    }

    if show_map and flights:
        log("Karte wird gerendert (OSM-Tiles)...")
        try:
            result["image_base64"] = _render_map(latitude, longitude, radius_km, flights)
            result["mime_type"] = "image/png"
            log("Karte fertig.")
        except Exception as e:
            result["map_fehler"] = f"Karte konnte nicht erstellt werden: {e}"
            log(f"Karten-Fehler: {e}")

    return result
