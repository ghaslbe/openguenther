import json
from datetime import datetime
from services.openrouter import call_openrouter, SYSTEM_PROMPT
from mcp.registry import registry

TOOL_ROUTER_PROMPT = """Du bist ein Tool-Router. Deine Aufgabe ist es, aus einer Liste verfuegbarer Tools diejenigen auszuwaehlen, die fuer die Benutzeranfrage relevant sind.

Antworte NUR mit einem JSON-Array der Tool-Namen, die benoetigt werden.
Wenn keine Tools benoetigt werden, antworte mit [].
Keine Erklaerungen, nur das JSON-Array.

Beispiel-Antwort: ["get_current_time", "text_to_image"]"""


def _ts():
    return datetime.now().strftime("%H:%M:%S")


def _select_tools(all_tools, chat_messages, api_key, model, emit_log):
    """
    Pre-filter: Ask LLM which tools are relevant for this request.
    Uses only tool names + descriptions (no full schemas) to save tokens.
    """
    if len(all_tools) <= 3:
        emit_log({"type": "text", "message": f"[{_ts()}] Tool-Router: Nur {len(all_tools)} Tools vorhanden, ueberspringe Filterung."})
        return all_tools

    tool_summary = []
    for t in all_tools:
        func = t.get("function", {})
        tool_summary.append({
            "name": func.get("name", ""),
            "description": func.get("description", "")
        })

    # Get the last user message
    last_user_msg = ""
    for msg in reversed(chat_messages):
        if msg.get("role") == "user":
            last_user_msg = msg.get("content", "")
            break

    router_messages = [
        {"role": "system", "content": TOOL_ROUTER_PROMPT},
        {"role": "user", "content": f"Verfuegbare Tools:\n{json.dumps(tool_summary, ensure_ascii=False, indent=2)}\n\nBenutzeranfrage: {last_user_msg}"}
    ]

    emit_log({"type": "header", "message": "TOOL-ROUTER (Pre-Filter)"})
    emit_log({"type": "json", "label": "router_request", "data": {
        "tools_available": [t["name"] for t in tool_summary],
        "user_query": last_user_msg
    }})

    try:
        response = call_openrouter(router_messages, None, api_key, model)
        content = response.get("choices", [{}])[0].get("message", {}).get("content", "[]")

        emit_log({"type": "json", "label": "router_response_raw", "data": response})

        # Parse the tool names from response
        # Handle cases where LLM wraps in markdown code block
        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

        selected_names = json.loads(content)

        if not isinstance(selected_names, list):
            raise ValueError("Response is not a list")

        # Filter tools
        selected = [t for t in all_tools if t.get("function", {}).get("name") in selected_names]

        emit_log({"type": "header", "message": "TOOL-ROUTER ERGEBNIS"})
        emit_log({"type": "json", "label": "selected_tools", "data": selected_names})
        emit_log({"type": "text", "message": f"[{_ts()}] {len(selected)}/{len(all_tools)} Tools ausgewaehlt"})

        # If router selected nothing but we have tools, fall back to all
        if not selected and all_tools:
            emit_log({"type": "text", "message": f"[{_ts()}] Keine Tools ausgewaehlt, verwende alle."})
            return all_tools

        return selected

    except Exception as e:
        emit_log({"type": "text", "message": f"[{_ts()}] Tool-Router Fehler: {str(e)} - verwende alle Tools"})
        return all_tools


def run_agent(chat_messages, settings, emit_log):
    """
    Run the agent loop: send messages to LLM, handle tool calls, iterate.
    Logs ALL communication to Guenther terminal.
    Returns the final assistant response.
    """
    api_key = settings.get('openrouter_api_key', '')
    model = settings.get('model', 'openai/gpt-4o-mini')

    if not api_key:
        return "Fehler: Kein OpenRouter API-Key konfiguriert. Bitte in den Einstellungen hinterlegen."

    # Build messages
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(chat_messages)

    all_tools = registry.get_openai_tools()

    # ── Log: Start ──
    emit_log({"type": "header", "message": "GUENTHER AGENT GESTARTET"})
    emit_log({"type": "text", "message": f"[{_ts()}] Modell: {model}"})

    # ── Log: System Prompt ──
    emit_log({"type": "header", "message": "SYSTEM PROMPT"})
    emit_log({"type": "text", "message": SYSTEM_PROMPT})

    # ── Log: Alle Tool Definitions ──
    emit_log({"type": "header", "message": f"ALLE TOOLS ({len(all_tools)})"})
    emit_log({"type": "json", "label": "all_tools", "data": all_tools})

    # ── Tool Router: Pre-filter ──
    tools = _select_tools(all_tools, chat_messages, api_key, model, emit_log)

    # ── Log: Gefilterte Tools ──
    emit_log({"type": "header", "message": f"AKTIVE TOOLS FUER DIESEN REQUEST ({len(tools)})"})
    emit_log({"type": "json", "label": "filtered_tools", "data": tools})

    # ── Log: Chat-Nachrichten ──
    emit_log({"type": "header", "message": f"CHAT NACHRICHTEN ({len(chat_messages)} Nachrichten)"})
    for msg in chat_messages:
        role = msg.get('role', '?')
        content = msg.get('content', '')
        emit_log({"type": "text", "message": f"[{role}] {content}"})

    collected_images = []
    max_iterations = 10
    iteration = 0

    while iteration < max_iterations:
        iteration += 1
        emit_log({"type": "header", "message": f"ITERATION {iteration}"})
        emit_log({"type": "text", "message": f"[{_ts()}] Sende Anfrage an OpenRouter..."})

        # ── Log: Full API Request ──
        # Build the payload like openrouter.py does
        request_payload = {
            "model": model,
            "messages": _sanitize_messages(messages),
        }
        if tools:
            request_payload["tools"] = tools
            request_payload["tool_choice"] = "auto"

        emit_log({"type": "header", "message": "API REQUEST"})
        emit_log({"type": "text", "message": f"POST https://openrouter.ai/api/v1/chat/completions"})
        emit_log({"type": "json", "label": "payload", "data": request_payload})

        try:
            response = call_openrouter(messages, tools if tools else None, api_key, model)
        except Exception as e:
            error_msg = f"Fehler bei LLM-Anfrage: {str(e)}"
            emit_log({"type": "text", "message": f"[{_ts()}] FEHLER: {error_msg}"})
            return error_msg

        # ── Log: Full API Response ──
        emit_log({"type": "header", "message": "API RESPONSE"})
        emit_log({"type": "json", "label": "response", "data": response})

        choice = response.get('choices', [{}])[0]
        message = choice.get('message', {})
        usage = response.get('usage', {})

        if usage:
            emit_log({"type": "text", "message": f"[{_ts()}] Tokens: prompt={usage.get('prompt_tokens', '?')} completion={usage.get('completion_tokens', '?')} total={usage.get('total_tokens', '?')}"})

        tool_calls = message.get('tool_calls', [])

        if tool_calls:
            emit_log({"type": "text", "message": f"[{_ts()}] LLM moechte {len(tool_calls)} Tool(s) aufrufen"})

            if message.get('content'):
                emit_log({"type": "header", "message": "LLM PLAN"})
                emit_log({"type": "text", "message": message['content']})

            messages.append(message)

            for tc in tool_calls:
                func = tc.get('function', {})
                tool_name = func.get('name', '')
                try:
                    tool_args = json.loads(func.get('arguments', '{}'))
                except json.JSONDecodeError:
                    tool_args = {}

                emit_log({"type": "header", "message": f"TOOL CALL: {tool_name}"})
                emit_log({"type": "json", "label": "arguments", "data": tool_args})

                tool = registry.get_tool(tool_name)
                if tool and tool.handler:
                    try:
                        emit_log({"type": "text", "message": f"[{_ts()}] Fuehre aus..."})
                        result = tool.handler(**tool_args)

                        # Check for image data
                        if isinstance(result, dict) and 'image_base64' in result:
                            collected_images.append(result)
                            simplified = {
                                "success": True,
                                "message": "Bild wurde erfolgreich erstellt",
                                "width": result.get("width"),
                                "height": result.get("height")
                            }
                            result_str = json.dumps(simplified, ensure_ascii=False)

                            emit_log({"type": "header", "message": f"TOOL RESULT: {tool_name}"})
                            emit_log({"type": "json", "label": "result", "data": simplified})
                            emit_log({"type": "text", "message": f"[{_ts()}] (Bild-Daten: {len(result['image_base64'])} Bytes Base64)"})
                        else:
                            result_str = json.dumps(result, ensure_ascii=False)
                            emit_log({"type": "header", "message": f"TOOL RESULT: {tool_name}"})
                            emit_log({"type": "json", "label": "result", "data": result})

                    except Exception as e:
                        result_str = json.dumps({"error": str(e)}, ensure_ascii=False)
                        emit_log({"type": "text", "message": f"[{_ts()}] FEHLER: {str(e)}"})
                else:
                    result_str = json.dumps(
                        {"error": f"Tool '{tool_name}' nicht gefunden"},
                        ensure_ascii=False
                    )
                    emit_log({"type": "text", "message": f"[{_ts()}] Tool nicht gefunden: {tool_name}"})

                # ── Log: Message sent back to LLM ──
                tool_msg = {
                    "role": "tool",
                    "tool_call_id": tc.get('id', ''),
                    "content": result_str
                }
                messages.append(tool_msg)
                emit_log({"type": "header", "message": "TOOL RESPONSE -> LLM"})
                emit_log({"type": "json", "label": "tool_message", "data": tool_msg})
        else:
            # Final response
            content = message.get('content', '')

            emit_log({"type": "header", "message": "FINALE ANTWORT"})
            emit_log({"type": "text", "message": content})

            # Append collected images
            for img in collected_images:
                mime = img.get('mime_type', 'image/png')
                b64 = img.get('image_base64', '')
                content += f"\n\n![Generiertes Bild](data:{mime};base64,{b64})"

            emit_log({"type": "header", "message": "GUENTHER AGENT BEENDET"})
            return content

    emit_log({"type": "text", "message": f"[{_ts()}] WARNUNG: Maximale Iterationen erreicht!"})
    return "Maximale Iterationen erreicht. Bitte versuche es erneut."


def _sanitize_messages(messages):
    """Create a safe copy of messages for logging (truncate long content)."""
    sanitized = []
    for msg in messages:
        if isinstance(msg, dict):
            m = dict(msg)
            if 'content' in m and isinstance(m['content'], str) and len(m['content']) > 500:
                m['content'] = m['content'][:500] + f"... ({len(msg['content'])} chars)"
            sanitized.append(m)
        else:
            sanitized.append(msg)
    return sanitized
