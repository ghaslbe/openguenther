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
];

const SECTION_TITLES = {
  general:   'Allgemein',
  providers: 'LLM Provider',
  tools:     'Tool-Einstellungen',
  mcp:       'Externe MCP Server',
  telegram:  'Telegram Gateway',
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
