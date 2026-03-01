import React, { useState } from 'react';

function Group({ title }) {
  return (
    <div style={{
      marginTop: '28px',
      marginBottom: '6px',
      fontSize: '10px',
      fontWeight: 800,
      textTransform: 'uppercase',
      letterSpacing: '1.5px',
      color: 'var(--text-secondary)',
      opacity: 0.55,
    }}>
      {title}
    </div>
  );
}

function Section({ title, children, defaultOpen = false }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div style={{ marginBottom: '4px', border: '1px solid var(--border)', borderRadius: '7px', overflow: 'hidden' }}>
      <button
        onClick={() => setOpen(v => !v)}
        style={{
          width: '100%',
          textAlign: 'left',
          background: open ? 'rgba(79,195,247,0.06)' : 'var(--bg-sidebar)',
          border: 'none',
          padding: '9px 14px',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          fontSize: '13px',
          fontWeight: 600,
          color: 'var(--text-primary)',
        }}
      >
        <span style={{ color: 'var(--accent)', fontSize: '11px', minWidth: '10px' }}>{open ? '▾' : '▸'}</span>
        {title}
      </button>
      {open && (
        <div style={{ padding: '12px 16px', fontSize: '13px', color: 'var(--text-secondary)', borderTop: '1px solid var(--border)' }}>
          {children}
        </div>
      )}
    </div>
  );
}

function Code({ children }) {
  return (
    <code style={{
      background: 'var(--bg-input)',
      border: '1px solid var(--border)',
      borderRadius: '3px',
      padding: '1px 6px',
      fontFamily: 'monospace',
      fontSize: '12px',
      color: 'var(--accent)',
    }}>
      {children}
    </code>
  );
}

function Block({ children }) {
  return (
    <pre style={{
      background: 'var(--bg-input)',
      border: '1px solid var(--border)',
      borderRadius: '6px',
      padding: '10px 14px',
      fontFamily: 'monospace',
      fontSize: '12px',
      color: 'var(--text-primary)',
      overflowX: 'auto',
      margin: '8px 0',
      lineHeight: '1.6',
      whiteSpace: 'pre-wrap',
    }}>
      {children}
    </pre>
  );
}

function Hint({ children }) {
  return (
    <div style={{
      background: 'rgba(79, 195, 247, 0.08)',
      border: '1px solid rgba(79, 195, 247, 0.25)',
      borderRadius: '6px',
      padding: '8px 12px',
      fontSize: '12px',
      color: 'var(--text-secondary)',
      margin: '8px 0',
    }}>
      {children}
    </div>
  );
}

const P = ({ children }) => <p style={{ marginBottom: '8px', lineHeight: '1.7' }}>{children}</p>;
const Li = ({ children }) => <li style={{ marginBottom: '4px' }}>{children}</li>;

export default function SettingsHilfe() {
  return (
    <div style={{ fontSize: '13px', color: 'var(--text-secondary)', maxWidth: '700px' }}>

      <Section title="💬 Guenther direkt fragen" defaultOpen={true}>
        <P>Frag <strong style={{ color: 'var(--accent)', fontFamily: 'monospace' }}>Guenther</strong> direkt im Chat — er kennt alle seine Tools und erklärt gerne was er kann:</P>
        <ul style={{ paddingLeft: '18px' }}>
          <Li><em>„Was kannst du alles?"</em></Li>
          <Li><em>„Welche Tools hast du?"</em></Li>
          <Li><em>„Erkläre mir das Tool X"</em></Li>
        </ul>
      </Section>

      <Group title="Provider & Modelle" />

      <Section title="Allgemein — Provider, Modell, Temperatur">
        <P><strong style={{ color: 'var(--text-primary)' }}>Standard-Provider</strong> — welcher LLM-Provider standardmäßig verwendet wird. Muss unter <em>Provider</em> aktiviert und konfiguriert sein.</P>
        <P><strong style={{ color: 'var(--text-primary)' }}>Standard-Modell</strong> — das Modell das beim gewählten Provider läuft, z.B. <Code>openai/gpt-4o-mini</Code> für OpenRouter oder <Code>llama3.2</Code> für Ollama.</P>
        <P><strong style={{ color: 'var(--text-primary)' }}>Temperatur</strong> — wie kreativ/unvorhersehbar die Antworten sind. <Code>0.1</Code> = präzise, <Code>0.5</Code> = ausgewogen, <Code>0.8</Code> = kreativ.</P>
        <P><strong style={{ color: 'var(--text-primary)' }}>Bildgenerierungs-Modell</strong> — wird direkt beim Tool <Code>generate_image</Code> unter <em>Tools</em> konfiguriert. Empfohlen: <Code>google/gemini-2.5-flash-image-preview</Code> oder <Code>black-forest-labs/flux-1.1-pro</Code>.</P>
        <P><strong style={{ color: 'var(--text-primary)' }}>STT-Modell</strong> — für Sprachnachrichten via Telegram. Empfohlen: <Code>google/gemini-2.5-flash</Code>. Alternativ: OpenAI Whisper aktivieren.</P>
      </Section>

      <Section title="Provider — OpenRouter">
        <P>OpenRouter ist ein API-Gateway für viele LLM-Anbieter (OpenAI, Anthropic, Google, Meta, …) mit einem einzigen API-Key.</P>
        <ul style={{ paddingLeft: '18px', marginBottom: '8px' }}>
          <Li>API-Key unter <a href="https://openrouter.ai/keys" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--accent)' }}>openrouter.ai/keys</a> erstellen</Li>
          <Li>Base URL: <Code>https://openrouter.ai/api/v1</Code> (voreingestellt)</Li>
          <Li>Modelle: <a href="https://openrouter.ai/models" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--accent)' }}>openrouter.ai/models</a></Li>
        </ul>
        <Hint>💡 Ausgaben-Limit im OpenRouter-Dashboard setzen, um unerwartete Kosten zu vermeiden.</Hint>
      </Section>

      <Section title="Provider — Ollama (lokal, kostenlos)">
        <P>Ollama lässt dich LLMs lokal auf deinem Rechner ausführen — komplett offline, keine API-Kosten.</P>
        <P><strong style={{ color: 'var(--text-primary)' }}>1. Ollama installieren</strong></P>
        <Block>{'# Mac / Linux\ncurl -fsSL https://ollama.com/install.sh | sh\n\n# oder: https://ollama.com/download'}</Block>
        <P><strong style={{ color: 'var(--text-primary)' }}>2. Modell herunterladen</strong></P>
        <Block>{'ollama pull llama3.2        # ~2 GB\nollama pull mistral        # ~4 GB\nollama pull qwen2.5:7b    # ~5 GB, mehrsprachig'}</Block>
        <P><strong style={{ color: 'var(--text-primary)' }}>3. In Guenther aktivieren</strong></P>
        <ul style={{ paddingLeft: '18px', marginBottom: '8px' }}>
          <Li>Provider: Ollama einschalten, Base URL: <Code>http://localhost:11434/v1</Code></Li>
          <Li>Allgemein: Standard-Provider → <strong>Ollama</strong>, Modell exakt wie gepullt</Li>
        </ul>
        <Hint>⚠️ Im Docker-Container erreichst du deinen Host über <Code>host.docker.internal</Code> statt <Code>localhost</Code>.</Hint>
      </Section>

      <Section title="Provider — LM Studio (lokal, kostenlos)">
        <P>LM Studio ist eine Desktop-App mit grafischer Oberfläche zum Laden und Ausführen von GGUF-Modellen.</P>
        <ul style={{ paddingLeft: '18px', marginBottom: '8px' }}>
          <Li>Download: <a href="https://lmstudio.ai" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--accent)' }}>lmstudio.ai</a></Li>
          <Li>Tab <strong>„Local Server"</strong> → <strong>„Start Server"</strong></Li>
          <Li>In Guenther: Provider LM Studio einschalten, Base URL: <Code>http://localhost:1234/v1</Code></Li>
        </ul>
        <Hint>⚠️ Gleich wie bei Ollama: Im Docker <Code>host.docker.internal</Code> statt <Code>localhost</Code>.</Hint>
      </Section>

      <Group title="Tools & Erweiterungen" />

      <Section title="Tools — Provider- & Modell-Override pro Tool">
        <P>Unter <em>Tools</em> kann jedes Tool einen eigenen Provider und ein eigenes Modell verwenden — unabhängig vom Standard.</P>
        <P>Beispiel: <Code>generate_image</Code> läuft immer über OpenRouter mit einem Bildgenerierungs-Modell, während der Chat-Provider Ollama ist.</P>
        <Hint>Der Override greift nur wenn <strong>alle</strong> vom Tool-Router ausgewählten Tools auf denselben Provider/Modell zeigen.</Hint>
      </Section>

      <Section title="MCP Server — externe Tools">
        <P>Guenther unterstützt das <strong>Model Context Protocol (MCP)</strong> — externe Tool-Server die via <Code>stdio</Code> (JSON-RPC 2.0) angebunden werden.</P>
        <Block>{'Name:      GitHub MCP\nCommand:   npx\nArgumente: -y @modelcontextprotocol/server-github'}</Block>
        <P>Nach dem Hinzufügen unter <em>Tools</em> auf <strong>„MCP Tools neu laden"</strong> klicken.</P>
      </Section>

      <Section title="Custom Tools — erstellen, bearbeiten, löschen">
        <P>Guenther kann eigene MCP-Tools direkt im Chat anlegen, bearbeiten und löschen — ohne Neustart.</P>
        <P><strong style={{ color: 'var(--text-primary)' }}>Erstellen</strong></P>
        <Block>{'Erstelle ein neues Tool namens spiegelcaller.\nEs soll spiegel.de 10x aufrufen und die Antwortzeiten zurückgeben.'}</Block>
        <P><strong style={{ color: 'var(--text-primary)' }}>Bearbeiten</strong></P>
        <Block>{'Bearbeite spiegelcaller, es soll jetzt stern.de 20x aufrufen.'}</Block>
        <P><strong style={{ color: 'var(--text-primary)' }}>Löschen</strong></P>
        <Block>{'Lösche das Tool spiegelcaller.'}</Block>
        <P><strong style={{ color: 'var(--text-primary)' }}>Pflichtstruktur für tool.py</strong></P>
        <Block>{'TOOL_DEFINITION = {\n    "name": "mein_tool",\n    "description": "Was das Tool tut.",\n    "input_schema": {\n        "type": "object",\n        "properties": {\n            "param": {"type": "string", "description": "..."}\n        },\n        "required": ["param"]\n    }\n}\n\ndef handler(param):\n    return {"result": param}'}</Block>
        <Hint>Custom Tools liegen in <Code>/app/data/custom_tools/</Code> (persistentes Volume) und überleben jeden Container-Neustart. Vollständige Anleitung: <strong>CUSTOM_TOOL_GUIDE.md</strong></Hint>
      </Section>

      <Section title="Custom Tools — Dateien ausgeben (LOCAL_FILE-Muster)">
        <P>Wenn ein Custom Tool eine Datei erzeugt (z.B. WAV, XLSX, PDF), soll diese nie als Base64 ans LLM zurückgegeben werden — das würde das Token-Limit sprengen.</P>
        <P><strong style={{ color: 'var(--text-primary)' }}>Stattdessen: <Code>[LOCAL_FILE](pfad)</Code>-Marker zurückgeben</strong></P>
        <Block>{'def handler(file_path):\n    # ... Datei erzeugen und in output_path speichern ...\n    return {\n        "result": (\n            "Verarbeitung abgeschlossen.\\n\\n"\n            "Antworte dem Nutzer kurz und füge diesen Marker "\n            "EXAKT und UNVERÄNDERT in deine Antwort ein:\\n\\n"\n            "[LOCAL_FILE](" + output_path + ")"\n        )\n    }'}</Block>
        <P><strong style={{ color: 'var(--text-primary)' }}>Was passiert dann:</strong></P>
        <ul style={{ paddingLeft: '18px', marginBottom: '8px' }}>
          <Li>Das Tool gibt dem LLM eine <strong>Instruktion</strong> (kein Base64, kein Dateiinhalt)</Li>
          <Li>Das LLM schreibt eine kurze Antwort und kopiert den Marker wörtlich</Li>
          <Li>Guenthers Backend erkennt <Code>[LOCAL_FILE](...)</Code>, liest die Datei vom Server</Li>
          <Li>Die Datei wird im Chat-Ordner gespeichert und durch einen <strong>Download-Button</strong> ersetzt</Li>
        </ul>
        <Hint>💡 Dateien werden immer serverseitig gehalten — nichts geht durchs LLM. Empfohlener Speicherort für Zwischendateien: <Code>/app/data/uploads/</Code></Hint>
        <P><strong style={{ color: 'var(--text-primary)' }}>Beispiel: mp3towav Tool</strong></P>
        <Block>{'from pydub import AudioSegment\nimport os\n\ndef handler(file_path):\n    audio = AudioSegment.from_mp3(file_path)\n    wav = os.path.splitext(file_path)[0] + ".wav"\n    audio.export(wav, format="wav")\n    return {\n        "result": (\n            "Konvertierung abgeschlossen.\\n\\n"\n            "Füge diesen Marker exakt in deine Antwort ein:\\n"\n            "[LOCAL_FILE](" + wav + ")"\n        )\n    }'}</Block>
      </Section>

      <Section title="Datei-Upload im Chat">
        <P>Das 📎-Symbol neben dem Eingabefeld öffnet den Datei-Dialog.</P>
        <P><strong style={{ color: 'var(--text-primary)' }}>Textdateien</strong> — Inhalt wird als Kontext ans LLM übergeben:</P>
        <ul style={{ paddingLeft: '18px', marginBottom: '8px' }}>
          <Li>CSV, JSON, XML, TXT, YAML, LOG, TSV …</Li>
          <Li>Das LLM kann den Inhalt direkt an <Code>run_code</Code> übergeben</Li>
        </ul>
        <P><strong style={{ color: 'var(--text-primary)' }}>Binärdateien</strong> — werden serverseitig gespeichert, LLM erhält nur den Pfad:</P>
        <ul style={{ paddingLeft: '18px', marginBottom: '8px' }}>
          <Li>Audio: MP3, WAV, OGG, FLAC, M4A, AAC, Opus → 🎵</Li>
          <Li>Office: XLS, XLSX, DOC, DOCX → 📄</Li>
        </ul>
        <P>Der Pfad lautet z.B. <Code>/app/data/uploads/abc123_datei.mp3</Code> — Custom Tools können ihn direkt öffnen.</P>
        <Hint>⚠️ Binärdateien werden per REST-Upload übertragen (nicht via Socket.IO) — dadurch kein Größenlimit.</Hint>
      </Section>

      <Group title="Automatisierung & Integrationen" />

      <Section title="Autoprompts — geplante Aufgaben">
        <P>Prompts die automatisch zu bestimmten Zeiten ausgeführt werden — ähnlich wie Cron-Jobs.</P>
        <ul style={{ paddingLeft: '18px', marginBottom: '10px' }}>
          <Li><strong>Intervall</strong>: alle X Minuten</Li>
          <Li><strong>Täglich</strong>: einmal pro Tag zu einer Uhrzeit (UTC)</Li>
          <Li><strong>Wöchentlich</strong>: Wochentag + Uhrzeit (UTC)</Li>
        </ul>
        <P><strong style={{ color: 'var(--text-primary)' }}>Ausführungsmodus</strong></P>
        <P><strong>Still</strong> (Standard) — Agent läuft im Hintergrund, kein Chat-Eintrag. Ergebnis z.B. per Telegram weiterschicken:</P>
        <Block>{'Ruf den Wetterbericht für München ab und sende ihn per Telegram an 5761888867.'}</Block>
        <P><strong>„Ergebnis in Chat speichern"</strong> — Antwort landet in einem dedizierten Chat, der beim ersten Lauf angelegt und danach immer wiederverwendet wird.</P>
        <P>Der <strong>▶-Button</strong> führt den Autoprompt sofort aus — unabhängig vom Zeitplan.</P>
        <Hint>Alle Zeiten sind UTC. Die aktuelle Server-Zeit wird neben dem Zeitfeld angezeigt.</Hint>
      </Section>

      <Section title="Telegram Gateway">
        <P>Guenther als Telegram-Bot betreiben — Nachrichten, Bilder und Sprachnachrichten werden direkt an den Agent weitergeleitet.</P>
        <ul style={{ paddingLeft: '18px' }}>
          <Li>Bot-Token von <a href="https://t.me/BotFather" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--accent)' }}>@BotFather</a> erstellen</Li>
          <Li>Telegram-Usernames in die Whitelist eintragen (ohne @)</Li>
          <Li><Code>/new Mein Chat</Code> startet eine neue Chat-Session im Bot</Li>
          <Li>Bilder (QR-Codes, generierte Bilder) werden als echte Fotos gesendet</Li>
          <Li>Tool <Code>send_telegram</Code>: Guenther kann aktiv Nachrichten senden</Li>
        </ul>
      </Section>

    </div>
  );
}
