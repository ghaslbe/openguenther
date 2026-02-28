import requests

TOOL_DEFINITION = {
    "name": "fetch_url",
    "description": (
        "Ruft eine URL ab und gibt den Inhalt zurück. "
        "Unterstützt GET und POST. Bei JSON-Antworten wird das geparste Objekt zurückgegeben, "
        "bei HTML/Text der Rohtext (auf max_chars gekürzt). "
        "Nützlich um APIs abzufragen, Webseiten-Inhalte zu lesen oder HTTP-Endpunkte zu testen."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "Die abzurufende URL, z.B. 'https://api.example.com/data'"
            },
            "method": {
                "type": "string",
                "description": "HTTP-Methode: 'GET' (Standard) oder 'POST'",
                "enum": ["GET", "POST"]
            },
            "headers": {
                "type": "object",
                "description": "Optionale HTTP-Header als Key-Value-Objekt, z.B. {\"Authorization\": \"Bearer token\"}"
            },
            "body": {
                "type": "string",
                "description": "Request-Body für POST-Anfragen (als String)"
            },
            "max_chars": {
                "type": "integer",
                "description": "Maximale Zeichenanzahl der Antwort (Standard: 5000)"
            }
        },
        "required": ["url"]
    }
}


def handler(url, method="GET", headers=None, body=None, max_chars=5000):
    req_headers = {
        "User-Agent": "OPENguenther/1.0 (+https://openguenther.de)",
        "Accept": "application/json, text/html, */*",
    }
    if headers:
        req_headers.update(headers)

    try:
        if method.upper() == "POST":
            resp = requests.post(url, data=body, headers=req_headers, timeout=15)
        else:
            resp = requests.get(url, headers=req_headers, timeout=15)
    except requests.exceptions.Timeout:
        return {"success": False, "error": "Timeout — Server hat nicht innerhalb von 15s geantwortet"}
    except requests.exceptions.ConnectionError as e:
        return {"success": False, "error": f"Verbindungsfehler: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

    content_type = resp.headers.get("Content-Type", "")
    result = {
        "success": True,
        "status_code": resp.status_code,
        "content_type": content_type,
        "url": resp.url,
    }

    if "application/json" in content_type:
        try:
            result["body"] = resp.json()
        except Exception:
            result["body"] = resp.text[:max_chars]
    else:
        text = resp.text
        if len(text) > max_chars:
            result["body"] = text[:max_chars]
            result["truncated"] = True
            result["total_chars"] = len(text)
        else:
            result["body"] = text

    return result
