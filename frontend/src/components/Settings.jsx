import React, { useState, useEffect } from 'react';
import { fetchProviders } from '../services/api';
import SettingsGeneral from './settings/SettingsGeneral';
import SettingsProviders from './settings/SettingsProviders';
import SettingsTools from './settings/SettingsTools';
import SettingsMcp from './settings/SettingsMcp';
import SettingsTelegram from './settings/SettingsTelegram';

const NAV_ITEMS = [
  { id: 'general',   label: 'Allgemein' },
  { id: 'providers', label: 'Provider' },
  { id: 'tools',     label: 'Tools' },
  { id: 'mcp',       label: 'MCP Server' },
  { id: 'telegram',  label: 'Telegram' },
  { id: 'hilfe',     label: 'Hilfe' },
  { id: 'info',      label: 'Info' },
];

const SECTION_TITLES = {
  general:   'Allgemein',
  providers: 'LLM Provider',
  tools:     'Tool-Einstellungen',
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
        return (
          <div style={{ color: 'var(--text-secondary)', fontSize: '15px', lineHeight: '1.7' }}>
            <p>Frag einfach <strong style={{ color: 'var(--accent)', fontFamily: 'monospace' }}>Guenther</strong> direkt im Chat was er kann!</p>
            <p style={{ marginTop: '12px' }}>Zum Beispiel:</p>
            <ul style={{ marginTop: '8px', paddingLeft: '20px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <li><em>„Was kannst du alles?"</em></li>
              <li><em>„Welche Tools hast du?"</em></li>
              <li><em>„Hilf mir mit ..."</em></li>
            </ul>
          </div>
        );
      case 'info':
        return (
          <div style={{ color: 'var(--text-secondary)', fontSize: '14px', lineHeight: '1.8' }}>
            <p style={{ fontSize: '22px', fontWeight: '700', color: 'var(--text-primary)', marginBottom: '4px' }}>
              <span style={{ color: 'var(--accent)' }}>OPEN</span>
              <span style={{ color: 'var(--guenther-text)', fontFamily: 'monospace' }}>guenther</span>
            </p>
            <p style={{ marginBottom: '16px' }}>Version <code style={{ color: 'var(--accent)' }}>v{__APP_VERSION__}</code></p>
            <p>Open-Source KI-Agent mit MCP-Tool-Unterstützung, selbst gehostet via Docker.</p>
            <p style={{ marginTop: '16px' }}>
              <a
                href="https://github.com/ghaslbe/openguenther"
                target="_blank"
                rel="noopener noreferrer"
                style={{ color: 'var(--accent)', textDecoration: 'none', fontWeight: '600' }}
              >
                github.com/ghaslbe/openguenther
              </a>
            </p>
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
