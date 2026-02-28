import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { fetchToolSettings, updateToolSettings } from '../services/api';

export default function ToolSettings({ toolName, onClose }) {
  const { t } = useTranslation();
  const [schema, setSchema] = useState([]);
  const [values, setValues] = useState({});
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [showPasswords, setShowPasswords] = useState({});

  useEffect(() => {
    load();
  }, [toolName]);

  async function load() {
    const data = await fetchToolSettings(toolName);
    setSchema(data.schema || []);
    // Merge defaults with saved values
    const vals = {};
    for (const field of (data.schema || [])) {
      vals[field.key] = data.values?.[field.key] ?? field.default ?? '';
    }
    setValues(vals);
  }

  function handleChange(key, value) {
    setValues(prev => ({ ...prev, [key]: value }));
  }

  async function handleSave() {
    setSaving(true);
    await updateToolSettings(toolName, values);
    setMessage(t('toolSettings.saved'));
    setSaving(false);
    setTimeout(() => setMessage(''), 3000);
  }

  function togglePassword(key) {
    setShowPasswords(prev => ({ ...prev, [key]: !prev[key] }));
  }

  return (
    <div className="settings-overlay" onClick={onClose}>
      <div className="settings-modal tool-settings-modal" onClick={(e) => e.stopPropagation()}>
        <div className="settings-header">
          <h2>
            <span className="tool-settings-icon">*</span>
            {toolName}
          </h2>
          <button className="btn-close" onClick={onClose}>x</button>
        </div>

        <div className="settings-body">
          {message && <div className="settings-message">{message}</div>}

          <div className="settings-section">
            {schema.map((field, idx) => (
              <label key={field.key} className={idx > 0 && schema[0].key === 'model' && idx === 1 ? 'tool-settings-divider' : ''}>
                {field.label}
                {field.type === 'password' ? (
                  <div className="input-group">
                    <input
                      type={showPasswords[field.key] ? 'text' : 'password'}
                      value={values[field.key] || ''}
                      onChange={(e) => handleChange(field.key, e.target.value)}
                      placeholder={field.placeholder || ''}
                    />
                    <button
                      type="button"
                      className="btn-toggle-key"
                      onClick={() => togglePassword(field.key)}
                    >
                      {showPasswords[field.key] ? t('toolSettings.hide') : t('toolSettings.show')}
                    </button>
                  </div>
                ) : (
                  <input
                    type="text"
                    value={values[field.key] || ''}
                    onChange={(e) => handleChange(field.key, e.target.value)}
                    placeholder={field.placeholder || ''}
                  />
                )}
                {field.description && (
                  <small>{field.description}</small>
                )}
              </label>
            ))}

            <button className="btn-save" onClick={handleSave} disabled={saving}>
              {saving ? t('toolSettings.saving') : t('toolSettings.save')}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
