import React, { useState, useEffect } from 'react';
import { fetchSettings, updateSettings } from '../../services/api';

export default function SettingsGeneral({ providers }) {
  const [model, setModel] = useState('openai/gpt-4o-mini');
  const [temperature, setTemperature] = useState(0.5);
  const [defaultProvider, setDefaultProvider] = useState('openrouter');
  const [sttModel, setSttModel] = useState('');
  const [ttsModel, setTtsModel] = useState('');
  const [imageGenModel, setImageGenModel] = useState('');
  const [openaiKey, setOpenaiKey] = useState('');
  const [openaiKeyMasked, setOpenaiKeyMasked] = useState('');
  const [showOpenaiKey, setShowOpenaiKey] = useState(false);
  const [useWhisper, setUseWhisper] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');

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
    setImageGenModel(s.image_gen_model || '');
    setOpenaiKeyMasked(s.openai_api_key_masked || '');
    setUseWhisper(s.use_openai_whisper || false);
  }

  async function handleSave() {
    setSaving(true);
    const data = {
      model, temperature, default_provider: defaultProvider,
      stt_model: sttModel, tts_model: ttsModel, image_gen_model: imageGenModel,
      use_openai_whisper: useWhisper,
    };
    if (openaiKey) data.openai_api_key = openaiKey;
    await updateSettings(data);
    setMessage('Gespeichert!');
    setSaving(false);
    setTimeout(() => setMessage(''), 3000);
  }

  const activeProviders = Object.entries(providers || {}).filter(([, p]) => p.enabled);

  return (
    <div>
      {message && <div className="settings-message">{message}</div>}

      <div className="settings-section">
        <h3>LLM</h3>
        <label>
          Standard-Provider
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
          <small>Welcher Provider standardmäßig für den Chat verwendet wird</small>
        </label>
        <label>
          Standard-Modell
          <input
            type="text"
            value={model}
            onChange={(e) => setModel(e.target.value)}
            placeholder="openai/gpt-4o-mini"
          />
          <small>z.B. openai/gpt-4o, anthropic/claude-3.5-sonnet, llama3.2 — je nach Provider</small>
        </label>
        <label>
          Kreativität (Temperatur)
          <select
            value={temperature}
            onChange={(e) => setTemperature(parseFloat(e.target.value))}
            className="settings-select"
          >
            <option value={0.1}>Genau (0.1) — präzise, deterministisch</option>
            <option value={0.5}>Mittel (0.5) — ausgewogen</option>
            <option value={0.8}>Frei (0.8) — kreativ, variabel</option>
          </select>
          <small>Bestimmt wie kreativ / unvorhersehbar die Antworten sind</small>
        </label>
      </div>

      <div className="settings-section">
        <h3>Audio / Sprache</h3>
        <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
          <input
            type="checkbox"
            checked={useWhisper}
            onChange={(e) => setUseWhisper(e.target.checked)}
            style={{ width: 'auto', margin: 0 }}
          />
          OpenAI Whisper für Spracherkennung (STT) verwenden
        </label>
        {useWhisper ? (
          <label>
            OpenAI API Key
            <div className="input-group">
              <input
                type={showOpenaiKey ? 'text' : 'password'}
                value={openaiKey}
                onChange={(e) => setOpenaiKey(e.target.value)}
                placeholder={openaiKeyMasked || 'sk-...'}
              />
              <button type="button" className="btn-toggle-key" onClick={() => setShowOpenaiKey(!showOpenaiKey)}>
                {showOpenaiKey ? 'Verbergen' : 'Anzeigen'}
              </button>
            </div>
            <small>Verwendet <code>whisper-1</code> — zuverlässiger als OpenRouter für Audio</small>
          </label>
        ) : (
          <label>
            Speech-to-Text Modell via OpenRouter
            <input
              type="text"
              value={sttModel}
              onChange={(e) => setSttModel(e.target.value)}
              placeholder={`leer = Chat-Modell (${model}) verwenden`}
            />
            <small>Empfohlen: <code>google/gemini-2.5-flash</code></small>
          </label>
        )}
        <label>
          Text-to-Speech Modell (TTS)
          <input
            type="text"
            value={ttsModel}
            onChange={(e) => setTtsModel(e.target.value)}
            placeholder={`leer = Chat-Modell (${model}) verwenden`}
          />
          <small>Für Sprachausgabe (zukünftige Funktion)</small>
        </label>
        <label>
          Bildgenerierungs-Modell
          <input
            type="text"
            value={imageGenModel}
            onChange={(e) => setImageGenModel(e.target.value)}
            placeholder={`leer = Chat-Modell (${model}) verwenden`}
          />
          <small>Empfohlen: <code>google/gemini-2.5-flash-image-preview</code> oder <code>black-forest-labs/flux-1.1-pro</code></small>
        </label>
      </div>

      <button className="btn-save" onClick={handleSave} disabled={saving}>
        {saving ? 'Speichere...' : 'Speichern'}
      </button>
    </div>
  );
}
