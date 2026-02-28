import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { fetchSettings, updateSettings, fetchProviderModels } from '../../services/api';

export default function SettingsGeneral({ providers }) {
  const { t } = useTranslation();
  const [model, setModel] = useState('openai/gpt-4o-mini');
  const [temperature, setTemperature] = useState(0.5);
  const [defaultProvider, setDefaultProvider] = useState('openrouter');
  const [sttModel, setSttModel] = useState('');
  const [ttsModel, setTtsModel] = useState('');
  const [openaiKey, setOpenaiKey] = useState('');
  const [openaiKeyMasked, setOpenaiKeyMasked] = useState('');
  const [showOpenaiKey, setShowOpenaiKey] = useState(false);
  const [useWhisper, setUseWhisper] = useState(false);
  const [llmTimeout, setLlmTimeout] = useState('120');
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [availableModels, setAvailableModels] = useState([]);
  const [loadingModels, setLoadingModels] = useState(false);
  const [modelsError, setModelsError] = useState('');

  useEffect(() => {
    loadSettings();
  }, []);

  async function loadSettings() {
    const s = await fetchSettings();
    setModel(s.model || 'openai/gpt-4o-mini');
    setTemperature(s.temperature ?? 0.5);
    setDefaultProvider(s.default_provider || 'openrouter');
    setSttModel(s.stt_model || '');
    setTtsModel(s.tts_model || '');
    setOpenaiKeyMasked(s.openai_api_key_masked || '');
    setUseWhisper(s.use_openai_whisper || false);
    setLlmTimeout(String(s.llm_timeout ?? 120));
  }

  async function handleLoadModels() {
    setLoadingModels(true);
    setModelsError('');
    setAvailableModels([]);
    const result = await fetchProviderModels(defaultProvider);
    setLoadingModels(false);
    if (result.success) {
      setAvailableModels((result.models || []).slice().sort());
      if (!result.models?.length) setModelsError(t('settings.general.noModels'));
    } else {
      setModelsError(result.error || t('settings.general.loadError'));
    }
  }

  async function handleSave() {
    setSaving(true);
    const data = {
      model, temperature, default_provider: defaultProvider,
      stt_model: sttModel, tts_model: ttsModel,
      use_openai_whisper: useWhisper,
      llm_timeout: parseInt(llmTimeout) || 120,
    };
    if (openaiKey) data.openai_api_key = openaiKey;
    await updateSettings(data);
    setMessage(t('settings.general.saved'));
    setSaving(false);
    setTimeout(() => setMessage(''), 3000);
  }

  const activeProviders = Object.entries(providers || {}).filter(([, p]) => p.enabled);

  return (
    <div>
      {message && <div className="settings-message">{message}</div>}

      <div className="settings-section">
        <h3>{t('settings.general.llmSection')}</h3>
        <label>
          {t('settings.general.defaultProvider')}
          <select
            className="settings-select"
            value={defaultProvider}
            onChange={(e) => setDefaultProvider(e.target.value)}
          >
            {activeProviders.length === 0 && (
              <option value="openrouter">OpenRouter</option>
            )}
            {activeProviders.map(([pid, p]) => (
              <option key={pid} value={pid}>{p.name}</option>
            ))}
          </select>
          <small>{t('settings.general.defaultProviderHelp')}</small>
        </label>
        <label>
          {t('settings.general.defaultModel')}
          <div className="input-group">
            <input
              type="text"
              value={model}
              onChange={(e) => setModel(e.target.value)}
              placeholder="openai/gpt-4o-mini"
            />
            <button
              type="button"
              className="btn-load-models"
              onClick={handleLoadModels}
              disabled={loadingModels}
            >
              {loadingModels ? '...' : t('settings.general.load')}
            </button>
          </div>
          {modelsError && <small style={{ color: 'var(--accent-red, #e05252)' }}>{modelsError}</small>}
          {availableModels.length > 0 && (
            <select
              className="settings-select"
              value=""
              onChange={(e) => { if (e.target.value) setModel(e.target.value); }}
            >
              <option value="">{t('settings.general.selectModel')}</option>
              {availableModels.map(m => (
                <option key={m} value={m}>{m}</option>
              ))}
            </select>
          )}
          <small>{t('settings.general.modelHelp')}</small>
        </label>
        <label>
          {t('settings.general.temperature')}
          <select
            value={temperature}
            onChange={(e) => setTemperature(parseFloat(e.target.value))}
            className="settings-select"
          >
            <option value={0.1}>{t('settings.general.tempExact')}</option>
            <option value={0.5}>{t('settings.general.tempMid')}</option>
            <option value={0.8}>{t('settings.general.tempFree')}</option>
          </select>
          <small>{t('settings.general.temperatureHelp')}</small>
        </label>
        <label>
          {t('settings.general.timeout')}
          <input
            type="number"
            value={llmTimeout}
            onChange={(e) => setLlmTimeout(e.target.value)}
            placeholder="120"
            min="10"
            max="600"
          />
          <small>{t('settings.general.timeoutHelp')}</small>
        </label>
      </div>

      <div className="settings-section">
        <h3>{t('settings.general.audioSection')}</h3>
        <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
          <input
            type="checkbox"
            checked={useWhisper}
            onChange={(e) => setUseWhisper(e.target.checked)}
            style={{ width: 'auto', margin: 0 }}
          />
          {t('settings.general.useWhisper')}
        </label>
        {useWhisper ? (
          <label>
            {t('settings.general.openaiKey')}
            <div className="input-group">
              <input
                type={showOpenaiKey ? 'text' : 'password'}
                value={openaiKey}
                onChange={(e) => setOpenaiKey(e.target.value)}
                placeholder={openaiKeyMasked || 'sk-...'}
              />
              <button type="button" className="btn-toggle-key" onClick={() => setShowOpenaiKey(!showOpenaiKey)}>
                {showOpenaiKey ? t('settings.general.hide') : t('settings.general.show')}
              </button>
            </div>
            <small>{t('settings.general.whisperHelp')}</small>
          </label>
        ) : (
          <label>
            {t('settings.general.sttModel')}
            <input
              type="text"
              value={sttModel}
              onChange={(e) => setSttModel(e.target.value)}
              placeholder={t('settings.general.sttPlaceholder', { model })}
            />
            <small>Empfohlen: <code>google/gemini-2.5-flash</code></small>
          </label>
        )}
        <label>
          {t('settings.general.ttsModel')}
          <input
            type="text"
            value={ttsModel}
            onChange={(e) => setTtsModel(e.target.value)}
            placeholder={t('settings.general.ttsPlaceholder', { model })}
          />
          <small>{t('settings.general.ttsModelHelp')}</small>
        </label>
      </div>

      <button className="btn-save" onClick={handleSave} disabled={saving}>
        {saving ? t('settings.general.saving') : t('settings.general.save')}
      </button>
    </div>
  );
}
