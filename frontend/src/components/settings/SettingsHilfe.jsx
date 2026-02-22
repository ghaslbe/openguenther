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

      <Section title="Telegram Gateway">
        <P>Guenther lässt sich als Telegram-Bot betreiben. Nachrichten, Bilder und Sprachnachrichten werden direkt an den Agent weitergeleitet.</P>
        <ul style={{ paddingLeft: '18px' }}>
          <Li>Bot-Token von <a href="https://t.me/BotFather" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--accent)' }}>@BotFather</a> erstellen</Li>
          <Li>Telegram-Usernames in die Whitelist eintragen (ohne @)</Li>
          <Li><Code>/new Mein Chat</Code> startet eine neue Chat-Session im Bot</Li>
          <Li>Bilder (QR-Codes, generierte Bilder) werden als echte Fotos gesendet</Li>
        </ul>
      </Section>

    </div>
  );
}
