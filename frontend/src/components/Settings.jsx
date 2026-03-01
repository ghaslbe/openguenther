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
import SettingsWebhooks from './settings/SettingsWebhooks';

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
    { id: 'webhooks',     label: t('settings.nav.webhooks') },
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
      case 'webhooks':
        return <SettingsWebhooks />;
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

            <p style={{ marginBottom: '4px', fontSize: '13px', color: 'var(--text-secondary)' }}>
              Open-Source KI-Agent mit MCP-Tool-Unterstützung, selbst gehostet via Docker. ·{' '}
              Open-source AI agent with MCP tool support, self-hosted via Docker.
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginBottom: '24px', marginTop: '12px' }}>
              <a href="https://github.com/ghaslbe/openguenther" target="_blank" rel="noopener noreferrer"
                style={{ color: 'var(--accent)', textDecoration: 'none', fontWeight: '600', fontSize: '13px' }}>
                github.com/ghaslbe/openguenther
              </a>
              <a href="https://www.linkedin.com/in/guentherhaslbeck/" target="_blank" rel="noopener noreferrer"
                style={{ color: 'var(--accent)', textDecoration: 'none', fontWeight: '600', fontSize: '13px' }}>
                linkedin.com/in/guentherhaslbeck
              </a>
            </div>

            {/* Disclaimer — immer zweisprachig / always bilingual */}
            <div style={{
              background: 'rgba(239, 83, 80, 0.07)',
              border: '1px solid rgba(239, 83, 80, 0.3)',
              borderRadius: '8px',
              overflow: 'hidden',
            }}>
              {/* DE */}
              <div style={{ padding: '16px 18px 14px', borderBottom: '1px solid rgba(239, 83, 80, 0.2)' }}>
                <p style={{ fontWeight: '700', color: '#ef5350', marginBottom: '10px', fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.8px' }}>
                  🇩🇪 &nbsp;⚠ Haftungsausschluss
                </p>
                <p style={{ fontWeight: '700', color: 'var(--text-primary)', marginBottom: '8px', fontSize: '13px' }}>
                  DIE NUTZUNG DIESER SOFTWARE GESCHIEHT VOLLSTÄNDIG AUF EIGENES RISIKO. DIE ALLEINIGE VERANTWORTUNG FÜR DIE NUTZUNG LIEGT BEIM NUTZER.
                </p>
                <p style={{ fontSize: '13px', marginBottom: '8px' }}>
                  Diese Software wird <strong style={{ color: 'var(--text-primary)' }}>„wie besehen"</strong> (as-is) ohne jegliche ausdrückliche oder stillschweigende Gewährleistung bereitgestellt. Der Autor übernimmt <strong style={{ color: 'var(--text-primary)' }}>keinerlei Haftung</strong> für direkte, indirekte, zufällige, besondere oder Folgeschäden, die aus der Nutzung oder Nichtnutzung dieser Software entstehen – gleichgültig, ob diese auf Vertrag, unerlaubter Handlung oder einem anderen Rechtsgrund beruhen.
                </p>
                <p style={{ fontSize: '13px', marginBottom: '8px' }}>
                  <strong style={{ color: 'var(--text-primary)' }}>Die gesamte Verantwortung für den Betrieb, die Konfiguration und die Nutzung dieser Software – einschließlich aller daraus resultierenden Handlungen und Konsequenzen – liegt ausschließlich beim Nutzer.</strong>
                </p>
                <p style={{ fontSize: '13px', marginBottom: '6px' }}>Dies umfasst insbesondere, aber nicht ausschließlich:</p>
                <ul style={{ fontSize: '13px', paddingLeft: '20px', marginBottom: '10px', lineHeight: '1.8' }}>
                  <li>Schäden durch KI-generierte Inhalte</li>
                  <li>Kosten durch API-Nutzung bei Drittanbietern (OpenRouter, OpenAI, etc.)</li>
                  <li>Datenverlust oder Sicherheitsvorfälle</li>
                  <li>Schäden durch fehlerhafte Tool-Ausführungen</li>
                  <li>Rechtliche Konsequenzen aus der Nutzung oder den durch die Software ausgeführten Aktionen</li>
                </ul>
                <p style={{ fontSize: '13px', marginBottom: '6px' }}><strong style={{ color: 'var(--text-primary)' }}>Der Autor empfiehlt ausdrücklich:</strong></p>
                <ul style={{ fontSize: '13px', paddingLeft: '20px', marginBottom: '10px', lineHeight: '1.8' }}>
                  <li>API-Keys mit minimalen Berechtigungen und Ausgabelimits zu versehen</li>
                  <li>Die Software nicht ohne Authentifizierung öffentlich zugänglich zu machen</li>
                  <li>Keine sensiblen Daten in Chats einzugeben</li>
                </ul>
                <p style={{ fontSize: '12px', opacity: 0.75, lineHeight: '1.7', margin: 0 }}>
                  <strong style={{ color: 'var(--text-primary)' }}>Hinweis zur Softwarequalität:</strong> Diese Software befindet sich in aktiver Entwicklung und wird ohne Anspruch auf Fehlerfreiheit, Vollständigkeit oder Sicherheit veröffentlicht. Es ist davon auszugehen, dass die Software — wie jede Software vergleichbarer Komplexität — Fehler, Unzulänglichkeiten und mit hoher Wahrscheinlichkeit auch Sicherheitslücken enthält, die zum Zeitpunkt der Veröffentlichung weder bekannt noch behoben sind. Der Betreiber trägt die alleinige Verantwortung dafür, die damit verbundenen Risiken zu bewerten und geeignete Schutzmaßnahmen zu ergreifen.
                </p>
              </div>

              {/* EN */}
              <div style={{ padding: '16px 18px 14px' }}>
                <p style={{ fontWeight: '700', color: '#ef5350', marginBottom: '10px', fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.8px' }}>
                  🇬🇧 &nbsp;⚠ Disclaimer
                </p>
                <p style={{ fontWeight: '700', color: 'var(--text-primary)', marginBottom: '8px', fontSize: '13px' }}>
                  USE OF THIS SOFTWARE IS ENTIRELY AT YOUR OWN RISK. SOLE RESPONSIBILITY FOR USE RESTS WITH THE USER.
                </p>
                <p style={{ fontSize: '13px', marginBottom: '8px' }}>
                  This software is provided <strong style={{ color: 'var(--text-primary)' }}>"as is"</strong> without any express or implied warranty of any kind. The author accepts <strong style={{ color: 'var(--text-primary)' }}>no liability</strong> for any direct, indirect, incidental, special or consequential damages arising from the use or inability to use this software — regardless of whether based on contract, tort or any other legal basis.
                </p>
                <p style={{ fontSize: '13px', marginBottom: '8px' }}>
                  <strong style={{ color: 'var(--text-primary)' }}>Full responsibility for operating, configuring and using this software — including all resulting actions and consequences — rests solely with the user.</strong>
                </p>
                <p style={{ fontSize: '13px', marginBottom: '6px' }}>This includes but is not limited to:</p>
                <ul style={{ fontSize: '13px', paddingLeft: '20px', marginBottom: '10px', lineHeight: '1.8' }}>
                  <li>Damages caused by AI-generated content</li>
                  <li>Costs incurred through third-party API usage (OpenRouter, OpenAI, etc.)</li>
                  <li>Data loss or security incidents</li>
                  <li>Damages caused by faulty tool executions</li>
                  <li>Legal consequences arising from use or actions carried out by the software</li>
                </ul>
                <p style={{ fontSize: '13px', marginBottom: '6px' }}><strong style={{ color: 'var(--text-primary)' }}>The author strongly recommends:</strong></p>
                <ul style={{ fontSize: '13px', paddingLeft: '20px', marginBottom: '10px', lineHeight: '1.8' }}>
                  <li>Setting spending limits on API keys</li>
                  <li>Not exposing the software publicly without authentication</li>
                  <li>Not entering sensitive data in chats</li>
                </ul>
                <p style={{ fontSize: '12px', opacity: 0.75, lineHeight: '1.7', margin: 0 }}>
                  <strong style={{ color: 'var(--text-primary)' }}>Notice on software quality:</strong> This software is under active development and is released without any claim of correctness, completeness or security. It should be assumed that the software — like any software of comparable complexity — contains bugs, deficiencies and, in all likelihood, security vulnerabilities that are neither known nor remediated at the time of release. The operator bears sole responsibility for assessing the associated risks and implementing appropriate protective measures.
                </p>
              </div>
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
