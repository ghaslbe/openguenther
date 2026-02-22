import React, { useState, useEffect } from 'react';
import { fetchAgents, createAgent, updateAgent, deleteAgent } from '../../services/api';

const EMPTY_FORM = { name: '', description: '', system_prompt: '' };

export default function SettingsAgents({ onAgentsChange }) {
  const [agents, setAgents] = useState([]);
  const [form, setForm] = useState(EMPTY_FORM);
  const [editingId, setEditingId] = useState(null);
  const [message, setMessage] = useState('');

  useEffect(() => {
    loadAgents();
  }, []);

  async function loadAgents() {
    const data = await fetchAgents();
    setAgents(data);
  }

  function showMessage(msg) {
    setMessage(msg);
    setTimeout(() => setMessage(''), 3000);
  }

  function startEdit(agent) {
    setEditingId(agent.id);
    setForm({ name: agent.name, description: agent.description || '', system_prompt: agent.system_prompt });
  }

  function cancelEdit() {
    setEditingId(null);
    setForm(EMPTY_FORM);
  }

  async function handleSave() {
    if (!form.name.trim() || !form.system_prompt.trim()) return;
    if (editingId) {
      await updateAgent(editingId, form);
      showMessage('Agent aktualisiert!');
    } else {
      await createAgent(form);
      showMessage('Agent erstellt!');
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
        Agenten haben einen eigenen System-Prompt. Beim Start eines neuen Chats kannst du einen Agenten auswählen.
      </p>

      <div className="settings-section">
        <h3>Konfigurierte Agenten</h3>
        <div className="agents-list">
          {agents.map(a => (
            <div key={a.id} className="agent-item">
              <div className="agent-item-info">
                <strong>{a.name}</strong>
                {a.description && <span className="agent-item-desc">{a.description}</span>}
              </div>
              <div className="agent-item-actions">
                <button className="btn-edit-agent" onClick={() => startEdit(a)}>Bearbeiten</button>
                <button className="btn-delete-agent" onClick={() => handleDelete(a.id)}>Löschen</button>
              </div>
            </div>
          ))}
          {agents.length === 0 && (
            <div className="agents-empty">Keine Agenten konfiguriert</div>
          )}
        </div>
      </div>

      <div className="settings-section">
        <h3>{editingId ? 'Agent bearbeiten' : 'Neuen Agenten erstellen'}</h3>
        <div className="agent-form">
          <input
            type="text"
            placeholder="Name (z.B. Poet)"
            value={form.name}
            onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
          />
          <input
            type="text"
            placeholder="Kurzbeschreibung (optional)"
            value={form.description}
            onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
          />
          <textarea
            className="agent-prompt-textarea"
            placeholder="System-Prompt (z.B. Antworte immer in Reimen.)"
            value={form.system_prompt}
            rows={6}
            onChange={e => setForm(f => ({ ...f, system_prompt: e.target.value }))}
          />
          <div className="agent-form-actions">
            <button className="btn-save-agent" onClick={handleSave} disabled={!form.name.trim() || !form.system_prompt.trim()}>
              {editingId ? 'Speichern' : 'Erstellen'}
            </button>
            {editingId && (
              <button className="btn-cancel-agent" onClick={cancelEdit}>Abbrechen</button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
