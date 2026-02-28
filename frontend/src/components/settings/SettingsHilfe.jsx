import React, { useState } from 'react';

function Section({ title, children }) {
  return (
    <div style={{ marginBottom: '28px' }}>
      <h4 style={{
        fontSize: '12px',
        fontWeight: '700',
        textTransform: 'uppercase',
        letterSpacing: '1px',
        color: 'var(--accent)',
        marginBottom: '10px',
        paddingBottom: '6px',
        borderBottom: '1px solid var(--border)',
      }}>
        {title}
      </h4>
      {children}
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
      fontSize: '13px',
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
    <div style={{ fontSize: '14px', color: 'var(--text-secondary)', maxWidth: '700px' }}>

      <Section title="Guenther fragen">
        <P>Frag <strong style={{ color: 'var(--accent)', fontFamily: 'monospace' }}>Guenther</strong> direkt im Chat — er kennt alle seine Tools und erklärt gerne was er kann:</P>
        <ul style={{ paddingLeft: '18px' }}>
          <Li><em>„Was kannst du alles?"</em></Li>
          <Li><em>„Welche Tools hast du?"</em></Li>
          <Li><em>„Erkläre mir das Tool X"</em></Li>
        </ul>
      </Section>

      <Section title="Allgemein">
        <P><strong style={{ color: 'var(--text-primary)' }}>Standard-Provider</strong> — welcher LLM-Provider standardmäßig für den Chat verwendet wird. Muss unter <em>Provider</em> aktiviert und konfiguriert sein.</P>
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
        <Hint>💡 Tipp: Ausgaben-Limit im OpenRouter-Dashboard setzen, um unerwartete Kosten zu vermeiden.</Hint>
      </Section>

      <Section title="Provider — Ollama (lokal, kostenlos)">
        <P>Ollama lässt dich LLMs lokal auf deinem Rechner ausführen — komplett offline, keine API-Kosten.</P>
        <P><strong style={{ color: 'var(--text-primary)' }}>1. Ollama installieren</strong></P>
        <Block>{'# Mac / Linux\ncurl -fsSL https://ollama.com/install.sh | sh\n\n# oder: https://ollama.com/download'}</Block>
        <P><strong style={{ color: 'var(--text-primary)' }}>2. Modell herunterladen</strong></P>
        <Block>{'ollama pull llama3.2        # ~2 GB, gut für Allgemeines\nollama pull mistral        # ~4 GB, stärker\nollama pull qwen2.5:7b    # ~5 GB, mehrsprachig'}</Block>
        <P><strong style={{ color: 'var(--text-primary)' }}>3. In Guenther aktivieren</strong></P>
        <ul style={{ paddingLeft: '18px', marginBottom: '8px' }}>
          <Li>Unter <em>Provider</em>: Ollama-Toggle einschalten</Li>
          <Li>Base URL: <Code>http://localhost:11434/v1</Code> (voreingestellt)</Li>
          <Li>API Key: leer lassen</Li>
          <Li>Unter <em>Allgemein</em>: Standard-Provider auf <strong>Ollama</strong> setzen</Li>
          <Li>Modell: exakt den Namen eingeben den du gepullt hast, z.B. <Code>llama3.2</Code></Li>
        </ul>
        <Hint>⚠️ Ollama muss auf demselben Rechner laufen wie der Guenther-Server. Im Docker-Container erreichst du deinen Host über <Code>host.docker.internal</Code> statt <Code>localhost</Code>.</Hint>
      </Section>

      <Section title="Provider — LM Studio (lokal, kostenlos)">
        <P>LM Studio ist eine Desktop-App mit grafischer Oberfläche zum Laden und Ausführen von GGUF-Modellen.</P>
        <P><strong style={{ color: 'var(--text-primary)' }}>1. LM Studio starten</strong></P>
        <ul style={{ paddingLeft: '18px', marginBottom: '8px' }}>
          <Li>Download unter <a href="https://lmstudio.ai" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--accent)' }}>lmstudio.ai</a></Li>
          <Li>Ein Modell herunterladen (z.B. Llama, Mistral, Phi)</Li>
          <Li>Im Tab <strong>„Local Server"</strong> (⇄-Icon) auf <strong>„Start Server"</strong> klicken</Li>
        </ul>
        <P><strong style={{ color: 'var(--text-primary)' }}>2. In Guenther aktivieren</strong></P>
        <ul style={{ paddingLeft: '18px', marginBottom: '8px' }}>
          <Li>Unter <em>Provider</em>: LM Studio-Toggle einschalten</Li>
          <Li>Base URL: <Code>http://localhost:1234/v1</Code> (voreingestellt)</Li>
          <Li>API Key: leer lassen</Li>
          <Li>Unter <em>Allgemein</em>: Standard-Provider auf <strong>LM Studio</strong> setzen</Li>
          <Li>Modell: den Modellnamen aus LM Studio kopieren (z.B. <Code>lmstudio-community/Meta-Llama-3.1-8B-Instruct-GGUF</Code>)</Li>
        </ul>
        <Hint>⚠️ Gleiches gilt wie bei Ollama: Im Docker erreichst du deinen Host-Rechner über <Code>host.docker.internal</Code> statt <Code>localhost</Code>.</Hint>
      </Section>

      <Section title="Tools — Provider- &amp; Modell-Override">
        <P>Unter <em>Tools</em> kann jedes Tool einen eigenen Provider und ein eigenes Modell verwenden — unabhängig vom Standard.</P>
        <P>Beispiel: <Code>generate_image</Code> läuft immer über OpenRouter mit einem Bildgenerierungs-Modell, während der Chat-Provider Ollama ist.</P>
        <Hint>Der Override greift nur wenn <strong>alle</strong> vom Tool-Router ausgewählten Tools auf denselben Provider/Modell zeigen. Bei gemischten Anfragen wird der Standard-Provider verwendet.</Hint>
      </Section>

      <Section title="MCP Server — externe Tools">
        <P>Guenther unterstützt das <strong>Model Context Protocol (MCP)</strong> — externe Tool-Server die via <Code>stdio</Code> (JSON-RPC 2.0) angebunden werden.</P>
        <P>Beispiel: einen Community-MCP-Server für GitHub hinzufügen:</P>
        <Block>{'Name:      GitHub MCP\nCommand:   npx\nArgumente: -y @modelcontextprotocol/server-github'}</Block>
        <P>Nach dem Hinzufügen unter <em>Tools</em> auf <strong>„MCP Tools neu laden"</strong> klicken. Die neuen Tools erscheinen dann in der Liste und stehen Guenther zur Verfügung.</P>
      </Section>

      <Section title="Custom Tools — erstellen, bearbeiten, löschen">
        <P>Guenther kann eigene MCP-Tools direkt im Chat anlegen, bearbeiten und löschen — ohne Neustart, ohne Dateibearbeitung.</P>

        <P><strong style={{ color: 'var(--text-primary)' }}>Tool erstellen</strong></P>
        <P>Einfach im Chat beschreiben was das Tool tun soll:</P>
        <Block>{'Erstelle ein neues Tool namens spiegelcaller.\nEs soll spiegel.de 10x aufrufen und die Antwortzeiten zurückgeben.'}</Block>
        <P>Guenther ruft intern <Code>create_mcp_tool</Code> auf, schreibt <Code>tool.py</Code> nach <Code>/app/data/custom_tools/spiegelcaller/</Code> und registriert das Tool sofort.</P>

        <P><strong style={{ color: 'var(--text-primary)' }}>Tool bearbeiten</strong></P>
        <Block>{'Bearbeite spiegelcaller, es soll jetzt stern.de 20x aufrufen\nund die Antwortzeiten als Tabelle zurückgeben.'}</Block>
        <P>Guenther ruft <Code>edit_mcp_tool</Code> auf — der alte Code wird ersetzt, das Tool sofort neu geladen.</P>

        <P><strong style={{ color: 'var(--text-primary)' }}>Tool löschen</strong></P>
        <Block>{'Lösche das Tool spiegelcaller.'}</Block>
        <P>Guenther ruft <Code>delete_mcp_tool</Code> auf — Verzeichnis wird gelöscht, Tool aus der Registry entfernt.</P>

        <Hint>Custom Tools liegen in <Code>/app/data/custom_tools/</Code> (persistentes Docker-Volume) und überleben jeden Container-Neustart.</Hint>

        <P><strong style={{ color: 'var(--text-primary)' }}>Pflichtstruktur für tool.py</strong></P>
        <Block>{'TOOL_DEFINITION = {\n    "name": "mein_tool",\n    "description": "Was das Tool tut.",\n    "input_schema": {\n        "type": "object",\n        "properties": {\n            "param": {"type": "string", "description": "..."}\n        },\n        "required": ["param"]\n    }\n}\n\ndef handler(param):\n    return {"result": param}'}</Block>

        <P><strong style={{ color: 'var(--text-primary)' }}>Manuell ablegen (alternativ)</strong></P>
        <ul style={{ paddingLeft: '18px', marginBottom: '8px' }}>
          <Li>Datei nach <Code>/app/data/custom_tools/&lt;name&gt;/tool.py</Code> legen</Li>
          <Li>Unter <em>Tools</em> auf <strong>„MCP Tools neu laden"</strong> klicken</Li>
        </ul>
        <Hint>📄 Vollständige Schnittstellenbeschreibung: <strong>CUSTOM_TOOL_GUIDE.md</strong> im Projektverzeichnis</Hint>
      </Section>

      <Section title="Autoprompts">
        <P>Unter <em>Autoprompts</em> kannst du Prompts hinterlegen, die automatisch zu bestimmten Zeiten ausgeführt werden — ähnlich wie ein Cron-Job.</P>
        <ul style={{ paddingLeft: '18px', marginBottom: '10px' }}>
          <Li><strong>Intervall</strong>: alle X Minuten, z.B. alle 60 min</Li>
          <Li><strong>Täglich</strong>: einmal pro Tag zu einer bestimmten Uhrzeit (UTC)</Li>
          <Li><strong>Wöchentlich</strong>: einmal pro Woche (Wochentag + Uhrzeit UTC)</Li>
        </ul>
        <P><strong style={{ color: 'var(--text-primary)' }}>Ausführungsmodus</strong></P>
        <P>Standard: <strong>Still</strong> — der Agent läuft im Hintergrund ohne Chat-Eintrag. Das Ergebnis kann z.B. per Telegram weitergeleitet werden:</P>
        <Block>{'Ruf den Wetterbericht für München ab und sende ihn per Telegram an 5761888867.'}</Block>
        <P>Optional: <strong>„Ergebnis in Chat speichern"</strong> aktivieren — dann landet das Ergebnis in einem dedizierten Chat der beim ersten Lauf angelegt und danach immer wiederverwendet wird.</P>
        <Hint>Alle Zeiten sind UTC. Die aktuelle Server-Zeit wird neben dem Zeitfeld angezeigt.</Hint>
        <P><strong style={{ color: 'var(--text-primary)' }}>▶ Jetzt ausführen</strong></P>
        <P>Der ▶-Button führt den Autoprompt sofort aus — unabhängig vom Zeitplan. Nach dem Lauf erscheint <span style={{ color: '#66bb6a' }}>Erfolgreich</span> oder <span style={{ color: '#ef5350' }}>Fehler</span> mit einem klickbaren Log der alle Agent-Schritte zeigt.</P>
      </Section>

      <Section title="Telegram Gateway">
        <P>Guenther lässt sich als Telegram-Bot betreiben. Nachrichten, Bilder und Sprachnachrichten werden direkt an den Agent weitergeleitet.</P>
        <ul style={{ paddingLeft: '18px' }}>
          <Li>Bot-Token von <a href="https://t.me/BotFather" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--accent)' }}>@BotFather</a> erstellen</Li>
          <Li>Telegram-Usernames in die Whitelist eintragen (ohne @)</Li>
          <Li><Code>/new Mein Chat</Code> startet eine neue Chat-Session im Bot</Li>
          <Li>Bilder (QR-Codes, generierte Bilder) werden als echte Fotos gesendet</Li>
          <Li>Tool <Code>send_telegram</Code>: Guenther kann aktiv Nachrichten senden — per <Code>@username</Code> oder numerischer Chat-ID</Li>
        </ul>
      </Section>

    </div>
  );
}
