import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';

export default function FirstRunOverlay({ onClose }) {
  const { i18n } = useTranslation();
  const [lang, setLang] = useState(i18n.language || 'de');

  function selectLang(l) {
    setLang(l);
    i18n.changeLanguage(l);
    localStorage.setItem('language', l);
  }

  function handleContinue() {
    onClose();
  }

  return (
    <div style={{
      position: 'fixed', inset: 0,
      background: 'rgba(0,0,0,0.75)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      zIndex: 9999,
    }}>
      <div style={{
        background: 'var(--bg-sidebar)',
        border: '1px solid var(--border)',
        borderRadius: '10px',
        padding: '36px 40px',
        maxWidth: '520px',
        width: '90%',
        boxShadow: '0 12px 48px rgba(0,0,0,0.5)',
      }}>
        {/* Logo */}
        <p style={{ fontSize: '26px', fontWeight: '700', marginBottom: '4px' }}>
          <span style={{ color: 'var(--accent)' }}>OPEN</span>
          <span style={{ color: 'var(--guenther-text)', fontFamily: 'monospace' }}>guenther</span>
        </p>

        {/* Subtitle — always bilingual */}
        <p style={{ fontSize: '14px', color: 'var(--text-secondary)', marginBottom: '24px' }}>
          Wähle deine Sprache / Choose your language
        </p>

        {/* Language selector */}
        <div style={{ display: 'flex', gap: '10px', marginBottom: '32px' }}>
          <button
            onClick={() => selectLang('de')}
            style={{
              flex: 1, padding: '10px',
              borderRadius: '6px',
              border: lang === 'de' ? '2px solid var(--accent)' : '2px solid var(--border)',
              background: lang === 'de' ? 'rgba(var(--accent-rgb, 100,181,246), 0.12)' : 'var(--bg-input)',
              color: 'var(--text-primary)',
              fontWeight: lang === 'de' ? '700' : '400',
              cursor: 'pointer', fontSize: '15px',
            }}
          >
            🇩🇪 Deutsch
          </button>
          <button
            onClick={() => selectLang('en')}
            style={{
              flex: 1, padding: '10px',
              borderRadius: '6px',
              border: lang === 'en' ? '2px solid var(--accent)' : '2px solid var(--border)',
              background: lang === 'en' ? 'rgba(var(--accent-rgb, 100,181,246), 0.12)' : 'var(--bg-input)',
              color: 'var(--text-primary)',
              fontWeight: lang === 'en' ? '700' : '400',
              cursor: 'pointer', fontSize: '15px',
            }}
          >
            🇬🇧 English
          </button>
        </div>

        {/* Requirement — always bilingual */}
        <div style={{
          background: 'rgba(100,181,246,0.07)',
          border: '1px solid rgba(100,181,246,0.25)',
          borderRadius: '8px',
          padding: '16px 18px',
          marginBottom: '28px',
          fontSize: '13px',
          lineHeight: '1.7',
        }}>
          <p style={{ fontWeight: '700', color: 'var(--text-primary)', marginBottom: '10px' }}>
            ⚠ Voraussetzung / Requirement
          </p>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '4px' }}>
            Du benötigst einen der folgenden Zugänge / You need one of the following:
          </p>
          <ul style={{ margin: '8px 0 0 0', paddingLeft: '18px', color: 'var(--text-secondary)' }}>
            <li>
              <strong style={{ color: 'var(--accent)' }}>OpenRouter</strong>
              {' '}API Key (empfohlen / recommended) —{' '}
              <a
                href="https://openrouter.ai/settings/keys"
                target="_blank"
                rel="noopener noreferrer"
                style={{ color: 'var(--accent)', textDecoration: 'underline' }}
              >
                openrouter.ai
              </a>
            </li>
            <li>
              <strong style={{ color: 'var(--text-primary)' }}>Ollama</strong>
              {' '}— lokal / locally
            </li>
            <li>
              <strong style={{ color: 'var(--text-primary)' }}>LM Studio</strong>
              {' '}— lokal / locally
            </li>
          </ul>
          <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '10px', opacity: 0.75 }}>
            Einstellungen → LLM Provider / Settings → LLM Providers
          </p>
        </div>

        <button
          onClick={handleContinue}
          style={{
            width: '100%', padding: '12px',
            background: 'var(--accent)',
            color: '#000',
            border: 'none', borderRadius: '6px',
            fontWeight: '700', fontSize: '15px',
            cursor: 'pointer',
          }}
        >
          {lang === 'de' ? 'Weiter' : 'Continue'} →
        </button>
      </div>
    </div>
  );
}
