import requests
from config import get_tool_settings

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

TOOL_DEFINITION = {
    "name": "get_weather",
    "description": (
        "Aktuelles Wetter und Vorhersage für einen beliebigen Ort weltweit. "
        "Liefert Temperatur, Niederschlag, Wind, Luftfeuchtigkeit und mehr. "
        "Kostenlos, kein API-Key nötig (Open-Meteo)."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "Stadtname oder Ort, z.B. 'Berlin', 'New York', 'Wien'"
            },
            "days": {
                "type": "integer",
                "description": "Anzahl Vorhersage-Tage (1–7, Standard: 1 = nur heute)"
            }
        },
        "required": ["location"]
    }
}

WMO_CODES = {
    0: "Klar",
    1: "Überwiegend klar", 2: "Teilweise bewölkt", 3: "Bedeckt",
    45: "Nebel", 48: "Reifnebel",
    51: "Leichter Nieselregen", 53: "Nieselregen", 55: "Starker Nieselregen",
    61: "Leichter Regen", 63: "Regen", 65: "Starker Regen",
    71: "Leichter Schneefall", 73: "Schneefall", 75: "Starker Schneefall",
    77: "Schneegriesel",
    80: "Leichte Regenschauer", 81: "Regenschauer", 82: "Starke Regenschauer",
    85: "Schneeschauer", 86: "Starke Schneeschauer",
    95: "Gewitter", 96: "Gewitter mit Hagel", 99: "Gewitter mit starkem Hagel",
}


def get_weather(location, days=1):
    days = max(1, min(7, int(days)))
    timeout = int(get_tool_settings('get_weather').get('timeout') or 10)

    # Step 1: Geocoding
    try:
        geo = requests.get(
            GEOCODING_URL,
            params={"name": location, "count": 1, "language": "de", "format": "json"},
            timeout=timeout
        ).json()
    except Exception as e:
        return {"error": f"Geocoding-Fehler: {e}"}

    results = geo.get("results")
    if not results:
        return {"error": f"Ort '{location}' nicht gefunden."}

    place = results[0]
    lat = place["latitude"]
    lon = place["longitude"]
    city = place.get("name", location)
    country = place.get("country", "")

    # Step 2: Weather
    try:
        weather = requests.get(
            WEATHER_URL,
            timeout=timeout,
            params={
                "latitude": lat,
                "longitude": lon,
                "current": [
                    "temperature_2m", "relative_humidity_2m", "apparent_temperature",
                    "weather_code", "wind_speed_10m", "wind_direction_10m",
                    "precipitation", "cloud_cover"
                ],
                "daily": [
                    "weather_code", "temperature_2m_max", "temperature_2m_min",
                    "precipitation_sum", "wind_speed_10m_max"
                ],
                "timezone": "auto",
                "forecast_days": days,
                "wind_speed_unit": "kmh",
            },
        ).json()
    except Exception as e:
        return {"error": f"Wetter-API-Fehler: {e}"}

    current = weather.get("current", {})
    daily = weather.get("daily", {})

    result = {
        "ort": f"{city}, {country}".strip(", "),
        "aktuell": {
            "temperatur": f"{current.get('temperature_2m')}°C",
            "gefühlt_wie": f"{current.get('apparent_temperature')}°C",
            "beschreibung": WMO_CODES.get(current.get("weather_code", -1), "Unbekannt"),
            "luftfeuchtigkeit": f"{current.get('relative_humidity_2m')}%",
            "wind": f"{current.get('wind_speed_10m')} km/h",
            "bedeckungsgrad": f"{current.get('cloud_cover')}%",
            "niederschlag": f"{current.get('precipitation')} mm",
        }
    }

    if days > 1 and daily.get("time"):
        vorhersage = []
        for i, date in enumerate(daily["time"]):
            vorhersage.append({
                "datum": date,
                "beschreibung": WMO_CODES.get(daily["weather_code"][i], "Unbekannt"),
                "max": f"{daily['temperature_2m_max'][i]}°C",
                "min": f"{daily['temperature_2m_min'][i]}°C",
                "niederschlag": f"{daily['precipitation_sum'][i]} mm",
                "max_wind": f"{daily['wind_speed_10m_max'][i]} km/h",
            })
        result["vorhersage"] = vorhersage

    return result
