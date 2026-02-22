import React, { useState, useEffect } from 'react';
import { fetchProviders } from '../services/api';
import SettingsGeneral from './settings/SettingsGeneral';
import SettingsProviders from './settings/SettingsProviders';
import SettingsTools from './settings/SettingsTools';
import SettingsMcp from './settings/SettingsMcp';
import SettingsTelegram from './settings/SettingsTelegram';
import SettingsHilfe from './settings/SettingsHilfe';

const NAV_ITEMS = [
  { id: 'general',   label: 'Allgemein' },
  { id: 'providers', label: 'Provider' },
  { id: 'tools',     label: 'MCP Tools' },
  { id: 'mcp',       label: 'MCP Server' },
  { id: 'telegram',  label: 'Telegram' },
  { id: 'hilfe',     label: 'Hilfe' },
  { id: 'info',      label: 'Info' },
];

const SECTION_TITLES = {
  general:   'Allgemein',
  providers: 'LLM Provider',
  tools:     'Enthaltene MCP Tools',
  mcp:       'Externe MCP Server',
  telegram:  'Telegram Gateway',
  hilfe:     'Hilfe',
  info:      'Info',
};

export default function Settings({ onClose }) {
  const [activeSection, setActiveSection] = useState('general');
  const [providers, setProviders] = useState({});

  useEffect(() => {
    loadProviders();
  }, []);

  async function loadProviders() {
    const data = await fetchProviders();
    setProviders(data);
  }

  function renderSection() {
    switch (activeSection) {
      case 'general':
        return <SettingsGeneral providers={providers} />;
      case 'providers':
        return <SettingsProviders providers={providers} onProvidersChange={loadProviders} />;
      case 'tools':
        return <SettingsTools providers={providers} />;
      case 'mcp':
        return <SettingsMcp />;
      case 'telegram':
        return <SettingsTelegram />;
      case 'hilfe':
        return <SettingsHilfe />;
      case 'info':
        return (
          <div style={{ color: 'var(--text-secondary)', fontSize: '14px', lineHeight: '1.8', maxWidth: '620px' }}>
            <p style={{ fontSize: '22px', fontWeight: '700', color: 'var(--text-primary)', marginBottom: '4px' }}>
              <span style={{ color: 'var(--accent)' }}>OPEN</span>
              <span style={{ color: 'var(--guenther-text)', fontFamily: 'monospace' }}>guenther</span>
            </p>
            <p style={{ marginBottom: '20px' }}>Version <code style={{ color: 'var(--accent)' }}>v{__APP_VERSION__}</code></p>

            <p style={{ marginBottom: '16px' }}>Open-Source KI-Agent mit MCP-Tool-Unterstützung, selbst gehostet via Docker.</p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '28px' }}>
              <a href="https://github.com/ghaslbe/openguenther" target="_blank" rel="noopener noreferrer"
                style={{ color: 'var(--accent)', textDecoration: 'none', fontWeight: '600' }}>
                github.com/ghaslbe/openguenther
              </a>
              <a href="https://www.linkedin.com/in/guentherhaslbeck/" target="_blank" rel="noopener noreferrer"
                style={{ color: 'var(--accent)', textDecoration: 'none', fontWeight: '600' }}>
                linkedin.com/in/guentherhaslbeck
              </a>
            </div>

            <div style={{
              background: 'rgba(239, 83, 80, 0.08)',
              border: '1px solid rgba(239, 83, 80, 0.3)',
              borderRadius: '6px',
              padding: '14px 16px',
              fontSize: '13px',
              lineHeight: '1.7',
            }}>
              <p style={{ fontWeight: '700', color: '#ef5350', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                ⚠ Haftungsausschluss
              </p>
              <p style={{ marginBottom: '8px' }}>
                Diese Software wird ohne jegliche Gewährleistung bereitgestellt. Die Nutzung geschieht vollständig auf eigenes Risiko.
              </p>
              <p style={{ marginBottom: '8px' }}>
                Der Autor übernimmt <strong style={{ color: 'var(--text-primary)' }}>keinerlei Haftung</strong> — weder für direkte noch indirekte Schäden, Datenverlust, Sicherheitsvorfälle, Kosten durch API-Nutzung bei Drittanbietern (OpenRouter, OpenAI etc.), Schäden durch KI-generierte Inhalte oder fehlerhafte Tool-Ausführungen.
              </p>
              <p style={{ margin: 0, opacity: 0.8 }}>
                API-Keys mit Ausgabelimit versehen. Keine sensiblen Daten in Chats eingeben. Software nicht ohne Authentifizierung öffentlich zugänglich machen.
              </p>
            </div>
          </div>
        );
      default:
        return null;
    }
  }

  return (
    <div className="settings-panel">
      <nav className="settings-nav">
        <div className="settings-nav-header">
          <h2>Einstellungen</h2>
          <button className="btn-close" onClick={onClose} title="Schließen">✕</button>
        </div>
        {NAV_ITEMS.map(item => (
          <button
            key={item.id}
            className={`settings-nav-item ${activeSection === item.id ? 'active' : ''}`}
            onClick={() => setActiveSection(item.id)}
          >
            {item.label}
          </button>
        ))}
      </nav>

      <div className="settings-content">
        <div className="settings-content-header">
          <h3>{SECTION_TITLES[activeSection]}</h3>
        </div>
        {renderSection()}
      </div>
    </div>
  );
}
