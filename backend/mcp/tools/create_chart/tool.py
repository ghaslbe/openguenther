"""
Chart Generator MCP Tool

Erstellt Charts (Linien, Balken, Torte, Scatter, Histogramm) aus Daten
und speichert sie als PNG-Datei. Gibt einen [LOCAL_FILE]-Marker zurueck,
der im Chat als Download-Button erscheint und direkt an Telegram gesendet
werden kann.

Typischer Workflow:
  1. Daten aus DB holen (mysql / postgresql / airtable / ...)
  2. create_chart aufrufen
  3. PNG herunterladen oder via send_telegram verschicken
"""

import json
import os
import uuid

from config import DATA_DIR
from services.tool_context import get_emit_log

TOOL_DEFINITION = {
    "name": "create_chart",
    "description": (
        "Erstellt einen Chart (Diagramm) aus Daten und speichert ihn als PNG. "
        "Unterstuetzte Typen: line (Linie), bar (Balken), barh (horizontale Balken), "
        "pie (Torte), scatter (Punkte), histogram (Haeufigkeit). "
        "Gibt [LOCAL_FILE]-Marker zurueck — PNG kann heruntergeladen oder per Telegram gesendet werden."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "chart_type": {
                "type": "string",
                "enum": ["line", "bar", "barh", "pie", "scatter", "histogram"],
                "description": "Chart-Typ: line, bar, barh, pie, scatter, histogram",
            },
            "data": {
                "type": "string",
                "description": (
                    "Daten als JSON-String. Zwei Formate moeglich:\n"
                    "1. Array von Objekten: '[{\"monat\": \"Jan\", \"umsatz\": 1200}, ...]'\n"
                    "2. Einfaches Array von Zahlen: '[12, 45, 33, 67]' (fuer histogram)"
                ),
            },
            "x_key": {
                "type": "string",
                "description": "Feldname fuer die X-Achse (bei Array-von-Objekten-Format), z.B. 'monat'",
            },
            "y_key": {
                "type": "string",
                "description": (
                    "Feldname(n) fuer die Y-Achse. Einzeln: 'umsatz'. "
                    "Mehrere Serien kommagetrennt: 'umsatz,kosten' (nur fuer line und bar)"
                ),
            },
            "title": {
                "type": "string",
                "description": "Titel des Charts",
            },
            "x_label": {
                "type": "string",
                "description": "Beschriftung der X-Achse",
            },
            "y_label": {
                "type": "string",
                "description": "Beschriftung der Y-Achse",
            },
            "colors": {
                "type": "string",
                "description": "Farben kommagetrennt, z.B. '#4fc3f7,#ef5350,#66bb6a'. Standard: automatisch",
            },
            "width": {
                "type": "number",
                "description": "Breite des Charts in Zoll (Standard: 10)",
            },
            "height": {
                "type": "number",
                "description": "Hoehe des Charts in Zoll (Standard: 5)",
            },
            "style": {
                "type": "string",
                "description": "Matplotlib-Style: 'dark', 'light' (Standard: dark)",
            },
            "rotate_x_labels": {
                "type": "integer",
                "description": "X-Achsenbeschriftungen rotieren in Grad, z.B. 45 (Standard: 0)",
            },
        },
        "required": ["chart_type", "data"],
    },
}


# Farb-Paletten
DARK_PALETTE  = ["#4fc3f7", "#ef5350", "#66bb6a", "#ffa726", "#ab47bc", "#26c6da", "#ff7043", "#9ccc65"]
LIGHT_PALETTE = ["#1565c0", "#c62828", "#2e7d32", "#e65100", "#6a1b9a", "#00695c", "#bf360c", "#558b2f"]


def handler(
    chart_type,
    data,
    x_key=None,
    y_key=None,
    title=None,
    x_label=None,
    y_label=None,
    colors=None,
    width=10,
    height=5,
    style="dark",
    rotate_x_labels=0,
):
    emit_log = get_emit_log()

    def log(msg):
        if emit_log:
            emit_log({"type": "text", "message": f"[Chart] {msg}"})

    def header(msg):
        if emit_log:
            emit_log({"type": "header", "message": msg})

    try:
        import matplotlib
        matplotlib.use("Agg")  # kein Display noetig
        import matplotlib.pyplot as plt
        import matplotlib.ticker as mticker
    except ImportError:
        return {"error": "matplotlib nicht installiert. Bitte in requirements.txt eintragen und Container neu bauen."}

    header(f"CREATE CHART: {chart_type.upper()}")

    # ── Daten parsen ──────────────────────────────────────────────────────────
    try:
        raw = json.loads(data) if isinstance(data, str) else data
    except json.JSONDecodeError as e:
        return {"error": f"Ungueltige JSON-Daten: {e}"}

    if not raw:
        return {"error": "Keine Daten vorhanden (leeres Array)"}

    # ── Farben ────────────────────────────────────────────────────────────────
    use_dark = style != "light"
    default_palette = DARK_PALETTE if use_dark else LIGHT_PALETTE
    if colors:
        palette = [c.strip() for c in colors.split(",")]
    else:
        palette = default_palette

    # ── Figure + Theme ────────────────────────────────────────────────────────
    w = float(width or 10)
    h = float(height or 5)

    if use_dark:
        plt.style.use("dark_background")
        bg_color   = "#1e1e2e"
        text_color = "#cdd6f4"
        grid_color = "#313244"
    else:
        plt.rcdefaults()
        bg_color   = "#ffffff"
        text_color = "#1a1a2e"
        grid_color = "#e0e0e0"

    fig, ax = plt.subplots(figsize=(w, h), facecolor=bg_color)
    ax.set_facecolor(bg_color)
    for spine in ax.spines.values():
        spine.set_edgecolor(grid_color)
    ax.tick_params(colors=text_color)
    ax.xaxis.label.set_color(text_color)
    ax.yaxis.label.set_color(text_color)
    if title:
        ax.set_title(title, color=text_color, fontsize=14, pad=12)
    if x_label:
        ax.set_xlabel(x_label, color=text_color)
    if y_label:
        ax.set_ylabel(y_label, color=text_color)

    # ── Daten extrahieren ─────────────────────────────────────────────────────
    def extract_series(records, key):
        """Extrahiert eine Wertereihe; versucht float-Konvertierung."""
        vals = []
        for r in records:
            v = r.get(key) if isinstance(r, dict) else r
            try:
                vals.append(float(v))
            except (TypeError, ValueError):
                vals.append(v)
        return vals

    # ── Chart zeichnen ────────────────────────────────────────────────────────
    if chart_type == "histogram":
        values = [float(v) for v in (raw if not isinstance(raw[0], dict) else extract_series(raw, y_key or x_key or list(raw[0].keys())[0]))]
        ax.hist(values, color=palette[0], edgecolor=bg_color, alpha=0.85)
        ax.yaxis.grid(True, color=grid_color, linewidth=0.5)

    elif chart_type == "pie":
        if isinstance(raw[0], dict):
            label_key = x_key or list(raw[0].keys())[0]
            value_key = y_key or list(raw[0].keys())[1]
            labels_data = [str(r.get(label_key, "")) for r in raw]
            values_data = [float(r.get(value_key, 0)) for r in raw]
        else:
            labels_data = None
            values_data = [float(v) for v in raw]
        wedge_colors = (palette * ((len(values_data) // len(palette)) + 1))[:len(values_data)]
        wedge_props = {"edgecolor": bg_color, "linewidth": 1.5}
        ax.pie(
            values_data,
            labels=labels_data,
            colors=wedge_colors,
            autopct="%1.1f%%",
            wedgeprops=wedge_props,
            textprops={"color": text_color},
        )

    elif chart_type == "scatter":
        if isinstance(raw[0], dict):
            xk = x_key or list(raw[0].keys())[0]
            yk = y_key or list(raw[0].keys())[1]
            xs = extract_series(raw, xk)
            ys = extract_series(raw, yk)
        else:
            xs = list(range(len(raw)))
            ys = [float(v) for v in raw]
        ax.scatter(xs, ys, color=palette[0], alpha=0.8, edgecolors=bg_color, linewidths=0.5)
        ax.yaxis.grid(True, color=grid_color, linewidth=0.5)

    else:
        # line, bar, barh — ggf. mehrere Serien
        if isinstance(raw[0], dict):
            xk = x_key or list(raw[0].keys())[0]
            x_vals = [str(r.get(xk, "")) for r in raw]
            y_keys = [k.strip() for k in y_key.split(",")] if y_key else [k for k in raw[0].keys() if k != xk]
        else:
            x_vals = list(range(len(raw)))
            y_keys = ["value"]
            raw = [{"value": float(v)} for v in raw]

        n = len(y_keys)
        bar_width = 0.8 / n if n > 1 else 0.6
        x_pos = list(range(len(x_vals)))

        for i, yk in enumerate(y_keys):
            y_vals = extract_series(raw, yk)
            color = palette[i % len(palette)]
            offset = (i - (n - 1) / 2) * bar_width if chart_type in ("bar", "barh") and n > 1 else 0

            if chart_type == "line":
                ax.plot(x_pos, y_vals, marker="o", markersize=4, color=color, linewidth=2, label=yk if n > 1 else None)
                ax.fill_between(x_pos, y_vals, alpha=0.08, color=color)
            elif chart_type == "bar":
                positions = [p + offset for p in x_pos]
                ax.bar(positions, y_vals, width=bar_width, color=color, alpha=0.85, label=yk if n > 1 else None, edgecolor=bg_color)
            elif chart_type == "barh":
                positions = [p + offset for p in x_pos]
                ax.barh(positions, y_vals, height=bar_width, color=color, alpha=0.85, label=yk if n > 1 else None, edgecolor=bg_color)

        if chart_type in ("line", "bar"):
            ax.set_xticks(x_pos)
            ax.set_xticklabels(x_vals, rotation=int(rotate_x_labels or 0), ha="right" if rotate_x_labels else "center")
        elif chart_type == "barh":
            ax.set_yticks(x_pos)
            ax.set_yticklabels(x_vals)

        ax.yaxis.grid(True, color=grid_color, linewidth=0.5, zorder=0)
        ax.set_axisbelow(True)

        if n > 1:
            legend = ax.legend(facecolor=bg_color, edgecolor=grid_color, labelcolor=text_color)

    # ── Speichern ─────────────────────────────────────────────────────────────
    uploads_dir = os.path.join(DATA_DIR, "uploads")
    os.makedirs(uploads_dir, exist_ok=True)
    filename = f"chart_{uuid.uuid4().hex[:8]}.png"
    output_path = os.path.join(uploads_dir, filename)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=bg_color)
    plt.close(fig)

    log(f"Gespeichert: {filename}")

    return {
        "result": (
            f"Chart erfolgreich erstellt ({chart_type}, {len(raw)} Datenpunkte).\n\n"
            "Antworte dem Nutzer kurz und fuege diesen Marker "
            "EXAKT und UNVERAENDERT in deine Antwort ein:\n\n"
            f"[LOCAL_FILE]({output_path})"
        ),
        "path": output_path,
        "filename": filename,
    }
