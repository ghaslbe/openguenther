"""
Pinecone Vector Database MCP Tool

Ermöglicht Indizes verwalten, Vektoren (oder Texte mit Auto-Embedding)
einfügen und semantisch suchen.

Einstellungen (Einstellungen → MCP Tools → pinecone):
  - api_key         : Pinecone API Key (app.pinecone.io → API Keys)
  - embedding_model : z.B. openai/text-embedding-3-small
  Außerdem: Provider-Override und Modell-Override für das Embedding.
"""

import requests

from config import get_tool_settings, get_settings
from services.tool_context import get_emit_log

PINECONE_CONTROL_BASE = "https://api.pinecone.io"
PINECONE_API_VERSION = "2024-10"

AGENT_OVERRIDABLE = True

SETTINGS_SCHEMA = [
    {
        "key": "api_key",
        "label": "Pinecone API Key",
        "type": "password",
        "placeholder": "pcsk_...",
        "description": "API Key aus dem Pinecone Dashboard (app.pinecone.io → API Keys)",
    },
    {
        "key": "embedding_model",
        "label": "Embedding-Modell",
        "type": "text",
        "placeholder": "openai/text-embedding-3-small",
        "description": (
            "OpenRouter-kompatibles Embedding-Modell für Text→Vektor-Konvertierung. "
            "Die Dimension muss mit dem Index übereinstimmen: "
            "text-embedding-3-small = 1536, text-embedding-3-large = 3072, "
            "text-embedding-ada-002 = 1536."
        ),
    },
]

TOOL_DEFINITION = {
    "name": "pinecone",
    "description": (
        "Pinecone Vector-Datenbank: Indizes verwalten, Vektoren und Texte einspeichern "
        "(Text wird automatisch embedded) und semantisch suchen. "
        "Aktionen: list_indexes · create_index · describe_index · delete_index · "
        "upsert · query · delete_vectors"
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": [
                    "list_indexes",
                    "create_index",
                    "describe_index",
                    "delete_index",
                    "upsert",
                    "query",
                    "delete_vectors",
                ],
                "description": (
                    "Aktion: "
                    "list_indexes (alle Indizes anzeigen) | "
                    "create_index (neuen Index anlegen) | "
                    "describe_index (Details + Statistiken) | "
                    "delete_index (Index löschen) | "
                    "upsert (Vektoren/Texte einfügen) | "
                    "query (semantisch suchen) | "
                    "delete_vectors (Vektoren löschen)"
                ),
            },
            "index_name": {
                "type": "string",
                "description": "Name des Index (erforderlich für alle Aktionen außer list_indexes)",
            },
            "dimension": {
                "type": "integer",
                "description": (
                    "Vektor-Dimension beim Erstellen. "
                    "Muss zum Embedding-Modell passen: "
                    "text-embedding-3-small → 1536, "
                    "text-embedding-3-large → 3072"
                ),
            },
            "metric": {
                "type": "string",
                "enum": ["cosine", "euclidean", "dotproduct"],
                "description": "Ähnlichkeitsmaß (Standard: cosine). Für Embedding-Modelle empfohlen: cosine.",
            },
            "cloud": {
                "type": "string",
                "description": "Cloud-Anbieter für Serverless-Index: aws (Standard), gcp, azure",
            },
            "region": {
                "type": "string",
                "description": "Region für Serverless-Index (Standard: us-east-1)",
            },
            "vectors": {
                "type": "array",
                "description": (
                    "Vektoren für 'upsert': Liste von Objekten mit "
                    "'id' (string, Pflicht) + "
                    "entweder 'text' (string → wird auto-embedded) "
                    "oder 'values' (float-Array). "
                    "Optional: 'metadata' (Objekt mit beliebigen Key-Value-Paaren). "
                    "Wenn 'text' übergeben wird, wird er als metadata.text gespeichert."
                ),
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "text": {"type": "string"},
                        "values": {"type": "array", "items": {"type": "number"}},
                        "metadata": {"type": "object"},
                    },
                    "required": ["id"],
                },
            },
            "query": {
                "type": "string",
                "description": "Suchanfrage als Text (wird auto-embedded) für Aktion 'query'",
            },
            "query_vector": {
                "type": "array",
                "items": {"type": "number"},
                "description": "Suchvektor als Float-Array (alternativ zu 'query' für direkte Vektor-Suche)",
            },
            "top_k": {
                "type": "integer",
                "description": "Anzahl Ergebnisse für 'query' (Standard: 5, max: 10000)",
            },
            "namespace": {
                "type": "string",
                "description": "Namespace im Index (optional, Standard: leer = default namespace)",
            },
            "include_metadata": {
                "type": "boolean",
                "description": "Metadaten in Ergebnissen einschließen (Standard: true)",
            },
            "filter": {
                "type": "object",
                "description": (
                    "Metadaten-Filter für 'query' im Pinecone-Format. "
                    "Beispiel: {\"genre\": {\"$eq\": \"comedy\"}} oder "
                    "{\"year\": {\"$gte\": 2020}}"
                ),
            },
            "ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Vektor-IDs für 'delete_vectors'",
            },
            "delete_all": {
                "type": "boolean",
                "description": "Alle Vektoren im (optionalen) Namespace löschen",
            },
        },
        "required": ["action"],
    },
}


# ── Internal helpers ──────────────────────────────────────────────────────────

def _cfg():
    return get_tool_settings("pinecone")


def _headers(api_key):
    return {
        "Api-Key": api_key,
        "Content-Type": "application/json",
        "X-Pinecone-Api-Version": PINECONE_API_VERSION,
    }


def _control(api_key, method, path, **kwargs):
    url = f"{PINECONE_CONTROL_BASE}{path}"
    resp = requests.request(method, url, headers=_headers(api_key), timeout=30, **kwargs)
    resp.raise_for_status()
    return resp.json() if resp.text.strip() else {}


def _get_host(api_key, index_name):
    info = _control(api_key, "GET", f"/indexes/{index_name}")
    host = info.get("host", "")
    if not host:
        raise ValueError(f"Index '{index_name}' nicht gefunden oder noch nicht bereit.")
    return host


def _data(api_key, index_name, method, path, **kwargs):
    host = _get_host(api_key, index_name)
    url = f"https://{host}{path}"
    resp = requests.request(method, url, headers=_headers(api_key), timeout=60, **kwargs)
    resp.raise_for_status()
    return resp.json() if resp.text.strip() else {}


def _embed(texts, cfg):
    """Embed a list of texts using the configured provider + model."""
    # model can come from provider-override (cfg['model']) or tool-specific setting
    model = (cfg.get("model") or cfg.get("embedding_model") or "").strip()
    if not model:
        raise ValueError(
            "Kein Embedding-Modell konfiguriert. "
            "Bitte in Einstellungen → MCP Tools → pinecone das Feld "
            "'Embedding-Modell' ausfüllen (z.B. openai/text-embedding-3-small)."
        )

    settings = get_settings()
    provider_id = (cfg.get("provider") or settings.get("default_provider", "openrouter")).strip()
    provider = settings.get("providers", {}).get(provider_id, {})
    base_url = provider.get("base_url", "https://openrouter.ai/api/v1").rstrip("/")
    llm_api_key = provider.get("api_key", "")

    resp = requests.post(
        f"{base_url}/embeddings",
        headers={
            "Authorization": f"Bearer {llm_api_key}",
            "Content-Type": "application/json",
        },
        json={"model": model, "input": texts},
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    # Sort by index to preserve order
    return [item["embedding"] for item in sorted(data["data"], key=lambda x: x["index"])]


# ── Main handler ──────────────────────────────────────────────────────────────

def handler(
    action,
    index_name=None,
    dimension=None,
    metric="cosine",
    cloud="aws",
    region="us-east-1",
    vectors=None,
    query=None,
    query_vector=None,
    top_k=5,
    namespace="",
    include_metadata=True,
    filter=None,
    ids=None,
    delete_all=False,
):
    emit_log = get_emit_log()

    def log(msg):
        if emit_log:
            emit_log({"type": "text", "message": f"[Pinecone] {msg}"})

    cfg = _cfg()
    api_key = cfg.get("api_key", "").strip()
    if not api_key:
        return {
            "error": (
                "Kein Pinecone API Key konfiguriert. "
                "Bitte in Einstellungen → MCP Tools → pinecone eintragen."
            )
        }

    try:

        # ── list_indexes ───────────────────────────────────────────────────
        if action == "list_indexes":
            log("Lade Index-Liste...")
            result = _control(api_key, "GET", "/indexes")
            indexes = result.get("indexes", [])
            log(f"{len(indexes)} Index(e) gefunden")
            return {
                "count": len(indexes),
                "indexes": [
                    {
                        "name": idx["name"],
                        "dimension": idx.get("dimension"),
                        "metric": idx.get("metric"),
                        "status": idx.get("status", {}).get("state"),
                        "host": idx.get("host"),
                        "spec": idx.get("spec", {}),
                    }
                    for idx in indexes
                ],
            }

        # ── create_index ───────────────────────────────────────────────────
        elif action == "create_index":
            if not index_name:
                return {"error": "index_name erforderlich"}
            if not dimension:
                return {"error": "dimension erforderlich (z.B. 1536 für text-embedding-3-small)"}
            log(f"Erstelle Index '{index_name}' (dim={dimension}, metric={metric}, {cloud}/{region})...")
            result = _control(api_key, "POST", "/indexes", json={
                "name": index_name,
                "dimension": int(dimension),
                "metric": metric,
                "spec": {
                    "serverless": {
                        "cloud": cloud,
                        "region": region,
                    }
                },
            })
            state = result.get("status", {}).get("state", "?")
            log(f"Index erstellt — Status: {state}")
            return {
                "name": result.get("name"),
                "dimension": result.get("dimension"),
                "metric": result.get("metric"),
                "host": result.get("host"),
                "status": state,
                "message": (
                    "Index wurde angelegt. Status 'Initializing' ist normal — "
                    "dauert ca. 30–60 Sekunden bis er bereit ist."
                ),
            }

        # ── describe_index ─────────────────────────────────────────────────
        elif action == "describe_index":
            if not index_name:
                return {"error": "index_name erforderlich"}
            log(f"Lade Details für Index '{index_name}'...")
            info = _control(api_key, "GET", f"/indexes/{index_name}")
            try:
                stats = _data(api_key, index_name, "GET", "/describe_index_stats")
            except Exception as e:
                stats = {}
                log(f"Stats nicht verfügbar: {e}")
            return {
                "name": info.get("name"),
                "dimension": info.get("dimension"),
                "metric": info.get("metric"),
                "host": info.get("host"),
                "status": info.get("status", {}).get("state"),
                "total_vector_count": stats.get("totalVectorCount", 0),
                "index_fullness": stats.get("indexFullness", 0),
                "namespaces": stats.get("namespaces", {}),
            }

        # ── delete_index ───────────────────────────────────────────────────
        elif action == "delete_index":
            if not index_name:
                return {"error": "index_name erforderlich"}
            log(f"Lösche Index '{index_name}'...")
            _control(api_key, "DELETE", f"/indexes/{index_name}")
            log("Index gelöscht")
            return {"success": True, "deleted_index": index_name}

        # ── upsert ────────────────────────────────────────────────────────
        elif action == "upsert":
            if not index_name:
                return {"error": "index_name erforderlich"}
            if not vectors:
                return {"error": "vectors erforderlich (Liste von {id, text|values, metadata?})"}

            vectors = list(vectors)  # make mutable copy

            # Auto-embed text entries
            text_indices = [
                i for i, v in enumerate(vectors)
                if "text" in v and "values" not in v
            ]
            if text_indices:
                texts = [vectors[i]["text"] for i in text_indices]
                log(f"Embedde {len(texts)} Text(e) mit '{cfg.get('model') or cfg.get('embedding_model', '?')}'...")
                embeddings = _embed(texts, cfg)
                for idx, emb in zip(text_indices, embeddings):
                    v = vectors[idx]
                    vectors[idx] = {
                        "id": v["id"],
                        "values": emb,
                        "metadata": {**v.get("metadata", {}), "text": v["text"]},
                    }

            payload_vectors = []
            for v in vectors:
                if "values" not in v:
                    return {"error": f"Vektor '{v.get('id')}' hat weder 'text' noch 'values'"}
                vec = {"id": v["id"], "values": v["values"]}
                if v.get("metadata"):
                    vec["metadata"] = v["metadata"]
                payload_vectors.append(vec)

            log(f"Upsert {len(payload_vectors)} Vektor(en) in '{index_name}' (namespace='{namespace}')...")
            result = _data(api_key, index_name, "POST", "/vectors/upsert", json={
                "vectors": payload_vectors,
                "namespace": namespace or "",
            })
            count = result.get("upsertedCount", len(payload_vectors))
            log(f"{count} Vektor(en) gespeichert")
            return {
                "upsertedCount": count,
                "index": index_name,
                "namespace": namespace or "(default)",
            }

        # ── query ─────────────────────────────────────────────────────────
        elif action == "query":
            if not index_name:
                return {"error": "index_name erforderlich"}
            if not query and not query_vector:
                return {"error": "Entweder 'query' (Text) oder 'query_vector' (Float-Array) angeben"}

            if query:
                log(f"Embedde Suchanfrage: '{query[:80]}'...")
                [vector] = _embed([query], cfg)
            else:
                vector = query_vector
                log("Direkte Vektor-Suche...")

            log(f"Suche in '{index_name}' (top_k={top_k})...")
            payload = {
                "vector": vector,
                "topK": int(top_k),
                "includeMetadata": include_metadata,
                "namespace": namespace or "",
            }
            if filter:
                payload["filter"] = filter

            result = _data(api_key, index_name, "POST", "/query", json=payload)
            matches = result.get("matches", [])
            log(f"{len(matches)} Treffer gefunden")
            return {
                "query": query if query else "[vector]",
                "index": index_name,
                "namespace": namespace or "(default)",
                "count": len(matches),
                "matches": [
                    {
                        "id": m["id"],
                        "score": round(m.get("score", 0), 6),
                        "metadata": m.get("metadata", {}),
                    }
                    for m in matches
                ],
            }

        # ── delete_vectors ────────────────────────────────────────────────
        elif action == "delete_vectors":
            if not index_name:
                return {"error": "index_name erforderlich"}
            if not delete_all and not ids:
                return {"error": "Entweder 'ids' (Liste von IDs) oder 'delete_all: true' angeben"}

            payload = {"namespace": namespace or ""}
            if delete_all:
                payload["deleteAll"] = True
                log(f"Lösche ALLE Vektoren in '{index_name}' (namespace='{namespace}')...")
            else:
                payload["ids"] = ids
                log(f"Lösche {len(ids)} Vektor(en) aus '{index_name}'...")

            _data(api_key, index_name, "POST", "/vectors/delete", json=payload)
            log("Gelöscht")
            return {
                "success": True,
                "index": index_name,
                "namespace": namespace or "(default)",
                "deleted": "all" if delete_all else ids,
            }

        else:
            return {
                "error": (
                    f"Unbekannte Aktion: '{action}'. "
                    "Gültige Aktionen: list_indexes, create_index, describe_index, "
                    "delete_index, upsert, query, delete_vectors"
                )
            }

    except requests.HTTPError as e:
        try:
            detail = e.response.json()
        except Exception:
            detail = e.response.text[:500]
        log(f"HTTP {e.response.status_code}: {detail}")
        return {"error": f"Pinecone API Fehler ({e.response.status_code}): {detail}"}
    except Exception as e:
        log(f"Fehler: {e}")
        return {"error": str(e)}
