import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { fetchProviders } from '../services/api';
import SettingsGeneral from './settings/SettingsGeneral';
import SettingsProviders from './settings/SettingsProviders';
import SettingsTools from './settings/SettingsTools';
import SettingsMcp from './settings/SettingsMcp';
import SettingsTelegram from './settings/SettingsTelegram';
import SettingsHilfe from './settings/SettingsHilfe';
import SettingsAgents from './settings/SettingsAgents';
import SettingsAutoprompts from './settings/SettingsAutoprompts';

export default function Settings({ onClose, onAgentsChange }) {
  const { t } = useTranslation();
  const [activeSection, setActiveSection] = useState('general');
  const [providers, setProviders] = useState({});

  useEffect(() => {
    loadProviders();
  }, []);

  async function loadProviders() {
    const data = await fetchProviders();
    setProviders(data);
  }

  const NAV_ITEMS = [
    { id: 'general',      label: t('settings.nav.general') },
    { id: 'agents',       label: t('settings.nav.agents') },
    { id: 'autoprompts',  label: t('settings.nav.autoprompts') },
    { id: 'providers',    label: t('settings.nav.providers') },
    { id: 'tools',        label: t('settings.nav.tools') },
    { id: 'mcp',          label: t('settings.nav.mcp') },
    { id: 'telegram',     label: t('settings.nav.telegram') },
    { id: 'hilfe',        label: t('settings.nav.hilfe') },
    { id: 'info',         label: t('settings.nav.info') },
  ];

  function renderSection() {
    switch (activeSection) {
      case 'agents':
        return <SettingsAgents onAgentsChange={onAgentsChange} />;
      case 'autoprompts':
        return <SettingsAutoprompts />;
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

            <p style={{ marginBottom: '16px' }}>{t('settings.info.description')}</p>

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
                ⚠ {t('settings.info.disclaimer')}
              </p>
              <p style={{ marginBottom: '8px' }}>
                {t('settings.info.disclaimerText1')}
              </p>
              <p style={{ marginBottom: '8px' }}>
                {t('settings.info.disclaimerText2')}
              </p>
              <p style={{ margin: 0, opacity: 0.8 }}>
                {t('settings.info.disclaimerText3')}
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
          <h2>{t('settings.title')}</h2>
          <button className="btn-close" onClick={onClose} title={t('settings.close')}>✕</button>
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
          <h3>{t(`settings.sections.${activeSection}`)}</h3>
        </div>
        {renderSection()}
      </div>
    </div>
  );
}
