import re
import base64
import requests
from html.parser import HTMLParser


# ── HTML Parser ──────────────────────────────────────────────────────────────

class _SEOParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ''
        self._in_title = False
        self.meta = {}          # name/property -> content
        self.headings = []      # list of (level, text)
        self._in_heading = None
        self._heading_buf = ''
        self.images = []        # list of {'src', 'alt'}
        self.links = []         # list of {'href', 'rel'}
        self.lang = ''
        self.canonical = ''
        self.json_ld = []
        self._in_json_ld = False
        self._json_ld_buf = ''

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'html':
            self.lang = attrs.get('lang', '')
        elif tag == 'title':
            self._in_title = True
        elif tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            self._in_heading = tag
            self._heading_buf = ''
        elif tag == 'meta':
            name = (attrs.get('name') or attrs.get('property') or '').lower()
            content = attrs.get('content', '')
            if name:
                self.meta[name] = content
        elif tag == 'link':
            rel = attrs.get('rel', '')
            if 'canonical' in rel:
                self.canonical = attrs.get('href', '')
        elif tag == 'img':
            self.images.append({'src': attrs.get('src', ''), 'alt': attrs.get('alt')})
        elif tag == 'a':
            self.links.append({'href': attrs.get('href', ''), 'rel': attrs.get('rel', '')})
        elif tag == 'script' and attrs.get('type') == 'application/ld+json':
            self._in_json_ld = True
            self._json_ld_buf = ''

    def handle_endtag(self, tag):
        if tag == 'title':
            self._in_title = False
        elif tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            if self._in_heading == tag:
                self.headings.append((int(tag[1]), self._heading_buf.strip()))
                self._in_heading = None
        elif tag == 'script' and self._in_json_ld:
            self.json_ld.append(self._json_ld_buf.strip())
            self._in_json_ld = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        if self._in_heading:
            self._heading_buf += data
        if self._in_json_ld:
            self._json_ld_buf += data


# ── Analysis ──────────────────────────────────────────────────────────────────

def _analyze(html):
    parser = _SEOParser()
    try:
        parser.feed(html)
    except Exception:
        pass

    checks = []
    score = 0
    max_score = 0

    def add(label, status, value, tip):
        # status: 'ok' | 'warn' | 'err'
        nonlocal score, max_score
        max_score += 2
        if status == 'ok':
            score += 2
        elif status == 'warn':
            score += 1
        checks.append({'label': label, 'status': status, 'value': value, 'tip': tip})

    # Title
    title = parser.title.strip()
    tlen = len(title)
    if not title:
        add('Title-Tag', 'err', '(fehlt)', 'Jede Seite braucht einen eindeutigen <title>-Tag.')
    elif tlen < 30:
        add('Title-Tag', 'warn', f'"{title}" ({tlen} Zeichen)', f'Zu kurz — ideal sind 50–60 Zeichen. Aktuell: {tlen}.')
    elif tlen > 60:
        add('Title-Tag', 'warn', f'"{title}" ({tlen} Zeichen)', f'Zu lang — wird in Suchergebnissen abgeschnitten. Ideal: 50–60 Zeichen.')
    else:
        add('Title-Tag', 'ok', f'"{title}" ({tlen} Zeichen)', f'Länge optimal ({tlen} Zeichen).')

    # Meta Description
    desc = parser.meta.get('description', '')
    dlen = len(desc)
    if not desc:
        add('Meta Description', 'err', '(fehlt)', 'Meta-Description fehlt — wichtig für CTR in Suchergebnissen.')
    elif dlen < 70:
        add('Meta Description', 'warn', f'{dlen} Zeichen', f'Zu kurz — ideal sind 150–160 Zeichen. Aktuell: {dlen}.')
    elif dlen > 160:
        add('Meta Description', 'warn', f'{dlen} Zeichen', f'Zu lang — wird abgeschnitten. Ideal: 150–160 Zeichen.')
    else:
        add('Meta Description', 'ok', f'{dlen} Zeichen', 'Länge optimal.')

    # H1
    h1s = [h for h in parser.headings if h[0] == 1]
    if len(h1s) == 0:
        add('H1-Überschrift', 'err', '(fehlt)', 'Genau eine H1 pro Seite — wichtigstes Keyword-Signal.')
    elif len(h1s) > 1:
        add('H1-Überschrift', 'warn', f'{len(h1s)}× vorhanden', f'Nur eine H1 verwenden. Gefunden: {", ".join(h[1][:40] for h in h1s)}')
    else:
        add('H1-Überschrift', 'ok', f'"{h1s[0][1][:60]}"', 'Genau eine H1 vorhanden.')

    # Heading-Hierarchie
    levels = [h[0] for h in parser.headings]
    if levels:
        jumps = [levels[i+1] - levels[i] for i in range(len(levels)-1) if levels[i+1] - levels[i] > 1]
        if jumps:
            add('Heading-Hierarchie', 'warn', f'H{levels}-Sprünge erkannt', 'Keine Ebenen überspringen (z.B. H1 → H3 ohne H2).')
        else:
            add('Heading-Hierarchie', 'ok', f'{len(levels)} Überschriften', 'Hierarchie korrekt.')
    else:
        add('Heading-Hierarchie', 'warn', '(keine Überschriften)', 'Überschriften helfen Nutzern und Suchmaschinen.')

    # Bilder ohne Alt
    imgs = parser.images
    no_alt = [i for i in imgs if i['alt'] is None or i['alt'].strip() == '']
    if imgs:
        if no_alt:
            add('Bild-Alt-Texte', 'warn' if len(no_alt) < len(imgs) else 'err',
                f'{len(no_alt)} von {len(imgs)} ohne Alt',
                f'Alt-Attribute für alle Bilder setzen: {", ".join(i["src"][:30] for i in no_alt[:3])}')
        else:
            add('Bild-Alt-Texte', 'ok', f'Alle {len(imgs)} Bilder haben Alt-Text', 'Super — alle Bilder haben Alt-Attribute.')
    else:
        add('Bild-Alt-Texte', 'ok', '(keine Bilder)', 'Keine Bilder gefunden.')

    # Canonical
    if parser.canonical:
        add('Canonical-Tag', 'ok', parser.canonical[:60], 'Canonical-URL gesetzt.')
    else:
        add('Canonical-Tag', 'warn', '(fehlt)', '<link rel="canonical"> verhindert Duplicate-Content-Probleme.')

    # Lang
    if parser.lang:
        add('HTML lang-Attribut', 'ok', parser.lang, 'Sprache korrekt deklariert.')
    else:
        add('HTML lang-Attribut', 'warn', '(fehlt)', '<html lang="de"> für Barrierefreiheit und SEO setzen.')

    # Open Graph
    og_title = parser.meta.get('og:title', '')
    og_desc = parser.meta.get('og:description', '')
    og_image = parser.meta.get('og:image', '')
    og_ok = sum([bool(og_title), bool(og_desc), bool(og_image)])
    if og_ok == 3:
        add('Open Graph Tags', 'ok', 'og:title, og:description, og:image', 'Alle wichtigen OG-Tags vorhanden.')
    elif og_ok > 0:
        missing = [t for t, v in [('og:title', og_title), ('og:description', og_desc), ('og:image', og_image)] if not v]
        add('Open Graph Tags', 'warn', f'{og_ok}/3 vorhanden', f'Fehlend: {", ".join(missing)}')
    else:
        add('Open Graph Tags', 'err', '(fehlen)', 'OG-Tags für Social-Media-Vorschau hinzufügen.')

    # Twitter Card
    tw_card = parser.meta.get('twitter:card', '')
    if tw_card:
        add('Twitter Card', 'ok', tw_card, 'Twitter Card deklariert.')
    else:
        add('Twitter Card', 'warn', '(fehlt)', '<meta name="twitter:card"> für bessere Twitter-Vorschau.')

    # Viewport
    viewport = parser.meta.get('viewport', '')
    if 'width=device-width' in viewport:
        add('Viewport (Mobile)', 'ok', viewport[:60], 'Mobile-optimiert.')
    else:
        add('Viewport (Mobile)', 'err', '(fehlt)', '<meta name="viewport" content="width=device-width, initial-scale=1"> hinzufügen.')

    # Robots
    robots = parser.meta.get('robots', '').lower()
    if 'noindex' in robots:
        add('Robots-Meta', 'err', robots, '⚠ Seite ist mit "noindex" für Suchmaschinen gesperrt!')
    elif robots:
        add('Robots-Meta', 'ok', robots, 'Robots-Direktive gesetzt.')
    else:
        add('Robots-Meta', 'ok', '(kein Tag = Standard)', 'Ohne robots-Tag ist die Seite indexierbar.')

    # JSON-LD
    if parser.json_ld:
        add('Strukturierte Daten (JSON-LD)', 'ok', f'{len(parser.json_ld)} Block(s)', 'Strukturierte Daten helfen bei Rich Results.')
    else:
        add('Strukturierte Daten (JSON-LD)', 'warn', '(fehlen)', 'JSON-LD für Rich Results in Suchergebnissen erwägen.')

    pct = round(score / max_score * 100) if max_score else 0
    return checks, pct, title


# ── HTML Report Generator ─────────────────────────────────────────────────────

def _render_report(checks, score, title, source_label):
    ok = sum(1 for c in checks if c['status'] == 'ok')
    warn = sum(1 for c in checks if c['status'] == 'warn')
    err = sum(1 for c in checks if c['status'] == 'err')

    color = '#4caf50' if score >= 75 else '#ff9800' if score >= 45 else '#f44336'

    rows = ''
    for c in checks:
        icon = {'ok': '✓', 'warn': '⚠', 'err': '✗'}[c['status']]
        bg = {'ok': '#1a2e1a', 'warn': '#2e260a', 'err': '#2e1010'}[c['status']]
        ic = {'ok': '#4caf50', 'warn': '#ffc107', 'err': '#f44336'}[c['status']]
        rows += f'''
        <tr style="background:{bg};">
          <td style="padding:10px 12px;white-space:nowrap;">
            <span style="color:{ic};font-weight:700;font-size:15px;">{icon}</span>
          </td>
          <td style="padding:10px 12px;color:#c8c8d8;font-weight:600;white-space:nowrap;">{c["label"]}</td>
          <td style="padding:10px 12px;color:#9090a8;font-size:13px;word-break:break-all;">{c["value"]}</td>
          <td style="padding:10px 12px;color:#a0a8c0;font-size:12px;">{c["tip"]}</td>
        </tr>'''

    return f'''<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
        background:#0e1117;color:#c8c8d8;padding:20px;font-size:14px;}}
  .card{{background:#161b27;border-radius:12px;overflow:hidden;
         border:1px solid #2a2d3e;max-width:900px;margin:0 auto;}}
  .header{{padding:20px 24px;background:#1a1f30;border-bottom:1px solid #2a2d3e;
           display:flex;align-items:center;gap:20px;flex-wrap:wrap;}}
  .score-ring{{position:relative;width:80px;height:80px;flex-shrink:0;}}
  .score-ring svg{{transform:rotate(-90deg)}}
  .score-num{{position:absolute;inset:0;display:flex;align-items:center;
              justify-content:center;font-size:22px;font-weight:800;color:{color};}}
  .header-text h1{{font-size:16px;color:#e0e0f0;margin-bottom:4px;}}
  .header-text p{{font-size:12px;color:#6070a0;}}
  .badges{{display:flex;gap:8px;margin-top:8px;flex-wrap:wrap;}}
  .badge{{padding:3px 10px;border-radius:20px;font-size:12px;font-weight:600;}}
  .b-ok{{background:rgba(76,175,80,.2);color:#4caf50;}}
  .b-warn{{background:rgba(255,193,7,.15);color:#ffc107;}}
  .b-err{{background:rgba(244,67,54,.2);color:#f44336;}}
  table{{width:100%;border-collapse:collapse;}}
  tr{{border-bottom:1px solid #1e2235;}}
  tr:last-child{{border-bottom:none;}}
  tr:hover{{background:#1c2133!important;}}
  th{{padding:10px 12px;text-align:left;font-size:11px;color:#5060a0;
      text-transform:uppercase;letter-spacing:.8px;background:#131825;}}
</style>
</head>
<body>
<div class="card">
  <div class="header">
    <div class="score-ring">
      <svg width="80" height="80" viewBox="0 0 80 80">
        <circle cx="40" cy="40" r="34" fill="none" stroke="#2a2d3e" stroke-width="8"/>
        <circle cx="40" cy="40" r="34" fill="none" stroke="{color}" stroke-width="8"
          stroke-dasharray="{round(score/100*213.6)} 213.6" stroke-linecap="round"/>
      </svg>
      <div class="score-num">{score}</div>
    </div>
    <div class="header-text">
      <h1>SEO-Analyse{": " + title[:60] if title else ""}</h1>
      <p>{source_label}</p>
      <div class="badges">
        <span class="badge b-ok">✓ {ok} OK</span>
        <span class="badge b-warn">⚠ {warn} Hinweise</span>
        <span class="badge b-err">✗ {err} Fehler</span>
      </div>
    </div>
  </div>
  <table>
    <thead>
      <tr>
        <th style="width:36px"></th>
        <th>Kriterium</th>
        <th>Wert</th>
        <th>Empfehlung</th>
      </tr>
    </thead>
    <tbody>{rows}</tbody>
  </table>
</div>
</body>
</html>'''


# ── Tool Handler ──────────────────────────────────────────────────────────────

def analyze_seo(html=None, url=None):
    source_label = ''

    if url:
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        try:
            resp = requests.get(url, timeout=12, headers={'User-Agent': 'Guenther-SEO/1.0'})
            resp.raise_for_status()
            html = resp.text
            source_label = url
        except Exception as e:
            return {'error': f'URL konnte nicht abgerufen werden: {e}'}
    elif html:
        source_label = 'HTML-Eingabe'
    else:
        return {'error': 'Bitte html oder url angeben.'}

    checks, score, title = _analyze(html)
    report_html = _render_report(checks, score, title, source_label)
    html_b64 = base64.b64encode(report_html.encode('utf-8')).decode()

    ok = sum(1 for c in checks if c['status'] == 'ok')
    warn = sum(1 for c in checks if c['status'] == 'warn')
    err = sum(1 for c in checks if c['status'] == 'err')

    return {
        'html_content': html_b64,
        'score': score,
        'ok': ok,
        'warnings': warn,
        'errors': err,
        'summary': f'SEO-Score: {score}/100 — {ok} OK, {warn} Hinweise, {err} Fehler',
    }


TOOL_DEFINITION = {
    'name': 'analyze_seo',
    'description': (
        'Analysiert eine Webseite auf SEO-Faktoren (Title, Meta Description, Headings, '
        'Bilder, Open Graph, Canonical, JSON-LD u.v.m.) und gibt einen visuellen HTML-Report aus. '
        'Aufruf entweder mit html="<html>...</html>" (direkter HTML-Code) '
        'oder mit url="https://example.com" (Seite wird automatisch abgerufen).'
    ),
    'input_schema': {
        'type': 'object',
        'properties': {
            'html': {
                'type': 'string',
                'description': 'Vollständiger HTML-Quellcode der zu analysierenden Seite.',
            },
            'url': {
                'type': 'string',
                'description': 'URL der zu analysierenden Seite — wird automatisch abgerufen.',
            },
        },
    },
}
