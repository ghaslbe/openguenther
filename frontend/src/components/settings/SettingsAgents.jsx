import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { fetchAgents, createAgent, updateAgent, deleteAgent, fetchProviders } from '../../services/api';

const EMPTY_FORM = { name: '', description: '', system_prompt: '', provider_id: '', model: '' };

export default function SettingsAgents({ onAgentsChange }) {
  const { t } = useTranslation();
  const [agents, setAgents] = useState([]);
  const [providers, setProviders] = useState({});
  const [form, setForm] = useState(EMPTY_FORM);
  const [editingId, setEditingId] = useState(null);
  const [message, setMessage] = useState('');

  useEffect(() => {
    loadAgents();
    loadProviders();
  }, []);

  async function loadAgents() {
    const data = await fetchAgents();
    setAgents(data);
  }

  async function loadProviders() {
    const data = await fetchProviders();
    setProviders(data || {});
  }

  function showMessage(msg) {
    setMessage(msg);
    setTimeout(() => setMessage(''), 3000);
  }

  function startEdit(agent) {
    setEditingId(agent.id);
    setForm({
      name: agent.name,
      description: agent.description || '',
      system_prompt: agent.system_prompt,
      provider_id: agent.provider_id || '',
      model: agent.model || '',
    });
  }

  function cancelEdit() {
    setEditingId(null);
    setForm(EMPTY_FORM);
  }

  async function handleSave() {
    if (!form.name.trim() || !form.system_prompt.trim()) return;
    if (editingId) {
      await updateAgent(editingId, form);
      showMessage(t('settings.agents.updated'));
    } else {
      await createAgent(form);
      showMessage(t('settings.agents.created'));
    }
    setEditingId(null);
    setForm(EMPTY_FORM);
    await loadAgents();
    if (onAgentsChange) onAgentsChange();
  }

  async function handleDelete(id) {
    await deleteAgent(id);
    await loadAgents();
    if (onAgentsChange) onAgentsChange();
  }

  return (
    <div>
      {message && <div className="settings-message">{message}</div>}
      <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '16px' }}>
        {t('settings.agents.description')}
      </p>

      <div className="settings-section">
        <h3>{t('settings.agents.configured')}</h3>
        <div className="agents-list">
          {agents.map(a => (
            <div key={a.id} className="agent-item">
              <div className="agent-item-info">
                <strong>{a.name}</strong>
                {a.description && <span className="agent-item-desc">{a.description}</span>}
                {(a.provider_id || a.model) && (
                  <span className="agent-item-llm">
                    {a.provider_id && (providers[a.provider_id]?.name || a.provider_id)}
                    {a.provider_id && a.model && ' · '}
                    {a.model}
                  </span>
                )}
              </div>
              <div className="agent-item-actions">
                <button className="btn-edit-agent" onClick={() => startEdit(a)}>{t('settings.agents.edit')}</button>
                <button className="btn-delete-agent" onClick={() => handleDelete(a.id)}>{t('settings.agents.delete')}</button>
              </div>
            </div>
          ))}
          {agents.length === 0 && (
            <div className="agents-empty">{t('settings.agents.empty')}</div>
          )}
        </div>
      </div>

      <div className="settings-section">
        <h3>{editingId ? t('settings.agents.editTitle') : t('settings.agents.newTitle')}</h3>
        <div className="agent-form">
          <label className="agent-form-label">{t('settings.agents.name')}</label>
          <input
            type="text"
            placeholder={t('settings.agents.namePlaceholder')}
            value={form.name}
            onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
          />
          <label className="agent-form-label">
            {t('settings.agents.descField')} <span className="agent-form-optional">{t('settings.agents.optional')}</span>
          </label>
          <input
            type="text"
            placeholder={t('settings.agents.descPlaceholder')}
            value={form.description}
            onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
          />
          <label className="agent-form-label">{t('settings.agents.systemPrompt')}</label>
          <textarea
            className="agent-prompt-textarea"
            placeholder={t('settings.agents.systemPromptPlaceholder')}
            value={form.system_prompt}
            rows={6}
            onChange={e => setForm(f => ({ ...f, system_prompt: e.target.value }))}
          />
          <label className="agent-form-label" style={{ marginTop: '12px' }}>
            {t('settings.agents.providerOverride')} <span className="agent-form-optional">{t('settings.agents.optional')}</span>
          </label>
          <select
            value={form.provider_id}
            onChange={e => setForm(f => ({ ...f, provider_id: e.target.value }))}
          >
            <option value="">{t('settings.agents.providerDefault')}</option>
            {Object.entries(providers)
              .filter(([, cfg]) => cfg.active !== false)
              .map(([pid, cfg]) => (
                <option key={pid} value={pid}>{cfg.name || pid}</option>
              ))}
          </select>
          <label className="agent-form-label">{t('settings.agents.modelOverride')} <span className="agent-form-optional">{t('settings.agents.optional')}</span></label>
          <input
            type="text"
            placeholder={t('settings.agents.modelPlaceholder')}
            value={form.model}
            onChange={e => setForm(f => ({ ...f, model: e.target.value }))}
          />
          <div className="agent-form-actions">
            <button className="btn-save-agent" onClick={handleSave} disabled={!form.name.trim() || !form.system_prompt.trim()}>
              {editingId ? t('settings.agents.save') : t('settings.agents.create')}
            </button>
            {editingId && (
              <button className="btn-cancel-agent" onClick={cancelEdit}>{t('settings.agents.cancel')}</button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
