import json
import re
import base64
from datetime import datetime
from services.openrouter import call_openrouter, SYSTEM_PROMPT
from services.tool_context import set_emit_log
from mcp.registry import registry
from config import get_tool_settings

TOOL_ROUTER_PROMPT = """Du bist ein Tool-Router. Deine Aufgabe ist es, aus einer Liste verfuegbarer Tools diejenigen auszuwaehlen, die fuer die Benutzeranfrage relevant sind.

Antworte NUR mit einem JSON-Array der Tool-Namen, die benoetigt werden.
Wenn keine Tools benoetigt werden, antworte mit [].
Keine Erklaerungen, nur das JSON-Array.

Beispiel-Antwort: ["get_current_time", "text_to_image"]"""


def _ts():
    return datetime.now().strftime("%H:%M:%S")


def _select_tools(all_tools, chat_messages, api_key, model, emit_log, base_url=None, timeout=120):
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

    # Get the last user message (handle vision content arrays)
    last_user_msg = ""
    for msg in reversed(chat_messages):
        if msg.get("role") == "user":
            content = msg.get("content", "")
            if isinstance(content, list):
                last_user_msg = " ".join(
                    part.get("text", "") for part in content
                    if part.get("type") == "text"
                )
            else:
                last_user_msg = content
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
        response = call_openrouter(router_messages, None, api_key, model, temperature=0.1, base_url=base_url, timeout=timeout)
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


def _pick_provider_and_model_for_tools(selected_tools, settings):
    """
    Check if all selected tools agree on a provider+model override.
    Returns (provider_cfg, model).
    If tools disagree or have no override, falls back to the default provider+model.
    """
    default_provider_id = settings.get('default_provider', 'openrouter')
    providers = settings.get('providers', {})
    default_provider_cfg = providers.get(default_provider_id, {})
    default_model = settings.get('model', 'openai/gpt-4o-mini')

    provider_ids = set()
    models = set()

    for t in selected_tools:
        name = t.get("function", {}).get("name", "")
        if name:
            ts = get_tool_settings(name)
            p = (ts.get("provider") or "").strip()
            m = (ts.get("model") or "").strip()
            if p:
                provider_ids.add(p)
            if m:
                models.add(m)

    override_provider_cfg = None
    if len(provider_ids) == 1:
        pid = provider_ids.pop()
        override_provider_cfg = providers.get(pid, default_provider_cfg)

    override_model = models.pop() if len(models) == 1 else default_model
    return override_provider_cfg or default_provider_cfg, override_model


def run_agent(chat_messages, settings, emit_log, system_prompt=None):
    """
    Run the agent loop: send messages to LLM, handle tool calls, iterate.
    Logs ALL communication to Guenther terminal.
    Returns the final assistant response.
    """
    # Resolve provider
    provider_id = settings.get('default_provider', 'openrouter')
    providers = settings.get('providers', {})
    provider_cfg = providers.get(provider_id, {})

    # Backward compat: fall back to legacy openrouter_api_key
    api_key = provider_cfg.get('api_key', '') or settings.get('openrouter_api_key', '')
    base_url = provider_cfg.get('base_url', 'https://openrouter.ai/api/v1')

    model = settings.get('model', 'openai/gpt-4o-mini')
    temperature = float(settings.get('temperature', 0.5))
    llm_timeout = int(settings.get('llm_timeout', 120))

    if not api_key and provider_id == 'openrouter':
        return "Fehler: Kein OpenRouter API-Key konfiguriert. Bitte in den Einstellungen hinterlegen."

    # Build messages — strip embedded base64 media from history (spart Tokens, war nie nützlich fürs LLM)
    active_prompt = system_prompt if system_prompt else SYSTEM_PROMPT
    messages = [{"role": "system", "content": active_prompt}]
    for msg in chat_messages:
        if msg.get("role") == "assistant" and isinstance(msg.get("content"), str):
            cleaned = re.sub(r'!\[[^\]]*\]\(data:[^)]{20,}\)', '', msg["content"]).strip()
            messages.append({**msg, "content": cleaned})
        else:
            messages.append(msg)

    all_tools = registry.get_openai_tools()

    # ── Log: Start ──
    emit_log({"type": "header", "message": "GUENTHER AGENT GESTARTET"})
    emit_log({"type": "text", "message": f"[{_ts()}] Modell: {model} | Temperatur: {temperature}"})

    # ── Log: System Prompt ──
    emit_log({"type": "header", "message": "SYSTEM PROMPT"})
    emit_log({"type": "text", "message": active_prompt})

    # ── Log: Alle Tool Definitions ──
    emit_log({"type": "header", "message": f"ALLE TOOLS ({len(all_tools)})"})
    emit_log({"type": "json", "label": "all_tools", "data": all_tools})

    emit_log({"type": "text", "message": f"[{_ts()}] LLM Timeout: {llm_timeout}s"})

    # ── Tool Router: Pre-filter ──
    tools = _select_tools(all_tools, chat_messages, api_key, model, emit_log, base_url=base_url, timeout=llm_timeout)

    # ── Provider+Model override: use tool-specific overrides if all tools agree ──
    effective_provider_cfg, effective_model = _pick_provider_and_model_for_tools(tools, settings)
    if effective_model != model or effective_provider_cfg.get('base_url', base_url) != base_url:
        emit_log({"type": "text", "message": f"[{_ts()}] Override aktiv: Provider={effective_provider_cfg.get('name', provider_id)} Modell={effective_model}"})
        model = effective_model
        api_key = effective_provider_cfg.get('api_key', '') or api_key
        base_url = effective_provider_cfg.get('base_url', base_url)

    # ── Log: Gefilterte Tools ──
    emit_log({"type": "header", "message": f"AKTIVE TOOLS FUER DIESEN REQUEST ({len(tools)})"})
    emit_log({"type": "json", "label": "filtered_tools", "data": tools})

    # ── Log: Chat-Nachrichten ──
    emit_log({"type": "header", "message": f"CHAT NACHRICHTEN ({len(chat_messages)} Nachrichten)"})
    for msg in chat_messages:
        role = msg.get('role', '?')
        content = msg.get('content', '')
        if isinstance(content, list):
            text_parts = [p.get('text', '') for p in content if p.get('type') == 'text']
            has_image = any(p.get('type') == 'image_url' for p in content)
            display = " ".join(text_parts)
            if has_image:
                display += " [+Bild]"
        else:
            display = content
        emit_log({"type": "text", "message": f"[{role}] {display}"})

    # Make emit_log available to tool handlers (e.g. generate_image)
    set_emit_log(emit_log)

    collected_images = []
    collected_audio = []
    collected_html = []
    collected_pptx = []
    max_iterations = 10
    iteration = 0

    while iteration < max_iterations:
        iteration += 1
        emit_log({"type": "header", "message": f"ITERATION {iteration}"})
        provider_display = provider_cfg.get('name') or provider_id
        emit_log({"type": "text", "message": f"[{_ts()}] Sende Anfrage an {provider_display}..."})

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
        emit_log({"type": "text", "message": f"POST {base_url.rstrip('/')}/chat/completions"})
        emit_log({"type": "json", "label": "payload", "data": request_payload})

        try:
            response = call_openrouter(messages, tools if tools else None, api_key, model, temperature, base_url=base_url, timeout=llm_timeout, provider_name=provider_display)
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

                        # Check for HTML report
                        if isinstance(result, dict) and 'html_content' in result:
                            collected_html.append({
                                'html_content': result['html_content'],
                                'pdf_html': result.get('pdf_html', ''),
                            })
                            simplified = {k: v for k, v in result.items()
                                          if k not in ('html_content', 'pdf_html')}
                            simplified['html_report'] = 'SEO-Report wird im Chat angezeigt.'
                            result_str = json.dumps(simplified, ensure_ascii=False)
                            emit_log({"type": "header", "message": f"TOOL RESULT: {tool_name}"})
                            emit_log({"type": "json", "label": "result", "data": simplified})

                        # Check for image data
                        elif isinstance(result, dict) and 'image_base64' in result:
                            collected_images.append(result)
                            # Alle Felder außer image_base64/mime_type an LLM schicken,
                            # damit es die Daten (z.B. Flugzeug-Liste) noch sieht.
                            # Bei reinen Bild-Tools (kein anderer Inhalt) bleibt nur die Erfolgsmeldung.
                            data_fields = {k: v for k, v in result.items()
                                           if k not in ('image_base64', 'mime_type')}
                            if data_fields:
                                data_fields['bild'] = "Karte wurde erstellt und wird im Chat angezeigt."
                                result_str = json.dumps(data_fields, ensure_ascii=False)
                                emit_log({"type": "header", "message": f"TOOL RESULT: {tool_name}"})
                                emit_log({"type": "json", "label": "result", "data": data_fields})
                            else:
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
                        elif isinstance(result, dict) and 'pptx_base64' in result:
                            collected_pptx.append(result)
                            simplified = {
                                "success": True,
                                "title": result.get("title", ""),
                                "slides": result.get("slides", 0),
                                "filename": result.get("filename", "presentation.pptx"),
                                "message": "Präsentation wurde erstellt und steht zum Download bereit.",
                            }
                            result_str = json.dumps(simplified, ensure_ascii=False)
                            emit_log({"type": "header", "message": f"TOOL RESULT: {tool_name}"})
                            emit_log({"type": "json", "label": "result", "data": simplified})
                            emit_log({"type": "text", "message": f"[{_ts()}] (PPTX: {len(result['pptx_base64'])} Bytes Base64)"})

                        elif isinstance(result, dict) and 'audio_base64' in result:
                            collected_audio.append(result)
                            simplified = {
                                "success": True,
                                "message": "Audio wurde erfolgreich erstellt",
                            }
                            result_str = json.dumps(simplified, ensure_ascii=False)

                            emit_log({"type": "header", "message": f"TOOL RESULT: {tool_name}"})
                            emit_log({"type": "json", "label": "result", "data": simplified})
                            emit_log({"type": "text", "message": f"[{_ts()}] (Audio-Daten: {len(result['audio_base64'])} Bytes Base64)"})
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

            # Append collected HTML reports
            for report in collected_html:
                content += f"\n\n[HTML_REPORT](data:text/html;base64,{report['html_content']})"
                if report.get('pdf_html'):
                    pdf_b64 = base64.b64encode(report['pdf_html'].encode('utf-8')).decode()
                    content += f"\n\n[PDF_REPORT](data:text/html;base64,{pdf_b64})"

            # Append collected PPTX downloads
            for pptx in collected_pptx:
                filename = pptx.get('filename', 'presentation.pptx')
                b64 = pptx.get('pptx_base64', '')
                content += f"\n\n[PPTX_DOWNLOAD]({filename}::{b64})"

            # Append collected images
            for img in collected_images:
                mime = img.get('mime_type', 'image/png')
                b64 = img.get('image_base64', '')
                content += f"\n\n![Generiertes Bild](data:{mime};base64,{b64})"

            # Append collected audio
            for audio in collected_audio:
                mime = audio.get('mime_type', 'audio/mpeg')
                b64 = audio.get('audio_base64', '')
                content += f"\n\n![audio](data:{mime};base64,{b64})"

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
            if 'content' in m:
                if isinstance(m['content'], str) and len(m['content']) > 500:
                    m['content'] = m['content'][:500] + f"... ({len(msg['content'])} chars)"
                elif isinstance(m['content'], list):
                    # Vision content: truncate image_url parts for logging
                    parts = []
                    for part in m['content']:
                        if part.get('type') == 'image_url':
                            parts.append({'type': 'image_url', 'image_url': {'url': '[base64 gekuerzt]'}})
                        else:
                            parts.append(part)
                    m['content'] = parts
            sanitized.append(m)
        else:
            sanitized.append(msg)
    return sanitized
