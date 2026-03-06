"""
Todoist MCP Tool

Aufgaben, Projekte und Kommentare in Todoist verwalten.

Einstellungen (Einstellungen -> MCP Tools -> todoist):
  - api_token : Todoist API Token (todoist.com/app/settings/integrations/developer)
"""

import requests

from config import get_tool_settings
from services.tool_context import get_emit_log

TODOIST_BASE = "https://api.todoist.com/rest/v2"

SETTINGS_INFO = """**Todoist**

Verwalte Aufgaben und Projekte in Todoist.

**API Token:** In Todoist unter Einstellungen → Integrationen → Entwickler → API Token kopieren.

> ⚠️ **Achtung:** Dieses Tool kann Daten schreiben, bearbeiten oder loeschen. Fehlerhafte Eingaben koennen zu **Datenverlust oder ungewollten Aktionen** fuehren. Bitte mit Bedacht einsetzen."""

SETTINGS_SCHEMA = [
    {
        "key": "api_token",
        "label": "Todoist API Token",
        "type": "password",
        "placeholder": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "description": "API Token aus Todoist → Einstellungen → Integrationen → Entwickler",
    },
]

TOOL_DEFINITION = {
    "name": "todoist",
    "description": (
        "Todoist: Aufgaben und Projekte verwalten. "
        "Aktionen: get_tasks (Aufgaben abrufen) | "
        "get_projects (Projekte auflisten) | "
        "create_task (neue Aufgabe erstellen) | "
        "update_task (Aufgabe bearbeiten) | "
        "complete_task (Aufgabe als erledigt markieren) | "
        "delete_task (Aufgabe loeschen) | "
        "add_comment (Kommentar zu Aufgabe hinzufuegen)"
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": [
                    "get_tasks",
                    "get_projects",
                    "create_task",
                    "update_task",
                    "complete_task",
                    "delete_task",
                    "add_comment",
                ],
                "description": (
                    "Aktion: "
                    "get_tasks (alle oder gefilterte Aufgaben) | "
                    "get_projects (alle Projekte) | "
                    "create_task (neue Aufgabe, benoetigt content) | "
                    "update_task (Aufgabe aendern per task_id) | "
                    "complete_task (als erledigt markieren per task_id) | "
                    "delete_task (loeschen per task_id) | "
                    "add_comment (Kommentar zu Aufgabe per task_id + comment)"
                ),
            },
            "task_id": {
                "type": "string",
                "description": "Todoist Aufgaben-ID (aus get_tasks)",
            },
            "project_id": {
                "type": "string",
                "description": "Projekt-ID zum Filtern bei get_tasks oder fuer create_task",
            },
            "content": {
                "type": "string",
                "description": "Aufgabentext fuer create_task oder update_task",
            },
            "description": {
                "type": "string",
                "description": "Beschreibung der Aufgabe (optional)",
            },
            "due_string": {
                "type": "string",
                "description": "Faelligkeitsdatum als Text, z.B. 'morgen', 'naechsten Montag', '2025-04-01', 'jeden Montag'",
            },
            "priority": {
                "type": "integer",
                "description": "Prioritaet: 1 (normal), 2 (mittel), 3 (hoch), 4 (dringend)",
            },
            "label": {
                "type": "string",
                "description": "Label-Name fuer die Aufgabe (optional)",
            },
            "filter": {
                "type": "string",
                "description": "Todoist-Filter fuer get_tasks, z.B. 'heute', 'ueberfallig', 'p1', '@arbeit'",
            },
            "comment": {
                "type": "string",
                "description": "Kommentartext fuer add_comment",
            },
        },
        "required": ["action"],
    },
}


def _cfg():
    return get_tool_settings("todoist")


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


def handler(
    action,
    task_id=None,
    project_id=None,
    content=None,
    description=None,
    due_string=None,
    priority=None,
    label=None,
    filter=None,
    comment=None,
):
    emit_log = get_emit_log()

    def log(msg):
        if emit_log:
            emit_log({"type": "text", "message": f"[Todoist] {msg}"})

    def header(msg):
        if emit_log:
            emit_log({"type": "header", "message": msg})

    cfg = _cfg()
    token = cfg.get("api_token", "").strip()
    if not token:
        return {"error": "Kein Todoist API Token konfiguriert. Bitte in Einstellungen -> MCP Tools -> todoist eintragen."}

    hdrs = _headers(token)

    try:

        # ── get_projects ───────────────────────────────────────────────────
        if action == "get_projects":
            header("TODOIST PROJECTS")
            r = requests.get(f"{TODOIST_BASE}/projects", headers=hdrs, timeout=15)
            r.raise_for_status()
            projects = r.json()
            log(f"{len(projects)} Projekt(e)")
            return {
                "count": len(projects),
                "projects": [{"id": p["id"], "name": p["name"], "color": p.get("color")} for p in projects],
            }

        # ── get_tasks ──────────────────────────────────────────────────────
        elif action == "get_tasks":
            header("TODOIST TASKS")
            params = {}
            if project_id:
                params["project_id"] = project_id
            if filter:
                params["filter"] = filter
            r = requests.get(f"{TODOIST_BASE}/tasks", headers=hdrs, params=params, timeout=15)
            r.raise_for_status()
            tasks = r.json()
            log(f"{len(tasks)} Aufgabe(n)")
            return {
                "count": len(tasks),
                "tasks": [
                    {
                        "id": t["id"],
                        "content": t["content"],
                        "description": t.get("description", ""),
                        "priority": t.get("priority", 1),
                        "due": t.get("due", {}).get("string") if t.get("due") else None,
                        "labels": t.get("labels", []),
                        "project_id": t.get("project_id"),
                        "url": t.get("url", ""),
                    }
                    for t in tasks
                ],
            }

        # ── create_task ────────────────────────────────────────────────────
        elif action == "create_task":
            if not content:
                return {"error": "content erforderlich fuer create_task"}
            header(f"TODOIST CREATE: {content[:60]}")
            payload = {"content": content}
            if description:
                payload["description"] = description
            if project_id:
                payload["project_id"] = project_id
            if due_string:
                payload["due_string"] = due_string
            if priority:
                payload["priority"] = int(priority)
            if label:
                payload["labels"] = [label]
            r = requests.post(f"{TODOIST_BASE}/tasks", headers=hdrs, json=payload, timeout=15)
            r.raise_for_status()
            task = r.json()
            log(f"Aufgabe erstellt: {task['id']}")
            return {
                "success": True,
                "id": task["id"],
                "content": task["content"],
                "url": task.get("url", ""),
            }

        # ── update_task ────────────────────────────────────────────────────
        elif action == "update_task":
            if not task_id:
                return {"error": "task_id erforderlich fuer update_task"}
            header(f"TODOIST UPDATE: {task_id}")
            payload = {}
            if content:
                payload["content"] = content
            if description is not None:
                payload["description"] = description
            if due_string:
                payload["due_string"] = due_string
            if priority:
                payload["priority"] = int(priority)
            if label:
                payload["labels"] = [label]
            if not payload:
                return {"error": "Mindestens ein Feld angeben (content, description, due_string, priority, label)"}
            r = requests.post(f"{TODOIST_BASE}/tasks/{task_id}", headers=hdrs, json=payload, timeout=15)
            r.raise_for_status()
            task = r.json()
            log(f"Aufgabe aktualisiert: {task.get('content')}")
            return {"success": True, "id": task["id"], "content": task["content"]}

        # ── complete_task ──────────────────────────────────────────────────
        elif action == "complete_task":
            if not task_id:
                return {"error": "task_id erforderlich fuer complete_task"}
            header(f"TODOIST COMPLETE: {task_id}")
            r = requests.post(f"{TODOIST_BASE}/tasks/{task_id}/close", headers=hdrs, timeout=15)
            r.raise_for_status()
            log("Aufgabe als erledigt markiert")
            return {"success": True, "task_id": task_id, "completed": True}

        # ── delete_task ────────────────────────────────────────────────────
        elif action == "delete_task":
            if not task_id:
                return {"error": "task_id erforderlich fuer delete_task"}
            header(f"TODOIST DELETE: {task_id}")
            r = requests.delete(f"{TODOIST_BASE}/tasks/{task_id}", headers=hdrs, timeout=15)
            r.raise_for_status()
            log("Aufgabe geloescht")
            return {"success": True, "task_id": task_id, "deleted": True}

        # ── add_comment ────────────────────────────────────────────────────
        elif action == "add_comment":
            if not task_id:
                return {"error": "task_id erforderlich fuer add_comment"}
            if not comment:
                return {"error": "comment erforderlich fuer add_comment"}
            header(f"TODOIST COMMENT: {task_id}")
            r = requests.post(
                f"{TODOIST_BASE}/comments",
                headers=hdrs,
                json={"task_id": task_id, "content": comment},
                timeout=15,
            )
            r.raise_for_status()
            c = r.json()
            log("Kommentar hinzugefuegt")
            return {"success": True, "comment_id": c["id"], "task_id": task_id}

        else:
            return {"error": f"Unbekannte Aktion: '{action}'."}

    except requests.HTTPError as e:
        try:
            detail = e.response.json()
        except Exception:
            detail = e.response.text[:300]
        log(f"HTTP {e.response.status_code}: {detail}")
        return {"error": f"Todoist API Fehler ({e.response.status_code}): {detail}"}
    except Exception as e:
        log(f"Fehler: {e}")
        return {"error": str(e)}
