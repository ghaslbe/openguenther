import React, { useState, useEffect } from 'react';
import {
  fetchAutoprompts, createAutoprompt, updateAutoprompt,
  deleteAutoprompt, runAutopromptNow, fetchAgents
} from '../../services/api';

const WEEKDAYS = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag'];

const EMPTY_FORM = {
  name: '',
  prompt: '',
  enabled: true,
  schedule_type: 'daily',
  interval_minutes: 60,
  daily_time: '08:00',
  weekly_day: 0,
  agent_id: '',
};

function scheduleLabel(ap) {
  if (ap.schedule_type === 'interval') {
    const m = parseInt(ap.interval_minutes, 10);
    if (m >= 60 && m % 60 === 0) return `Alle ${m / 60}h`;
    return `Alle ${m} min`;
  }
  if (ap.schedule_type === 'weekly') {
    return `${WEEKDAYS[ap.weekly_day] || 'Mo'} ${ap.daily_time}`;
  }
  return `Täglich ${ap.daily_time}`;
}

export default function SettingsAutoprompts() {
  const [autoprompts, setAutoprompts] = useState([]);
  const [agents, setAgents] = useState([]);
  const [form, setForm] = useState(EMPTY_FORM);
  const [editingId, setEditingId] = useState(null);
  const [message, setMessage] = useState('');

  useEffect(() => {
    load();
  }, []);

  async function load() {
    const [aps, ags] = await Promise.all([fetchAutoprompts(), fetchAgents()]);
    setAutoprompts(aps);
    setAgents(ags);
  }

  function showMessage(msg) {
    setMessage(msg);
    setTimeout(() => setMessage(''), 3000);
  }

  function startEdit(ap) {
    setEditingId(ap.id);
    setForm({
      name: ap.name,
      prompt: ap.prompt,
      enabled: ap.enabled,
      schedule_type: ap.schedule_type,
      interval_minutes: ap.interval_minutes,
      daily_time: ap.daily_time,
      weekly_day: ap.weekly_day,
      agent_id: ap.agent_id || '',
    });
  }

  function cancelEdit() {
    setEditingId(null);
    setForm(EMPTY_FORM);
  }

  async function handleSave() {
    if (!form.name.trim() || !form.prompt.trim()) return;
    const payload = { ...form, agent_id: form.agent_id || null };
    if (editingId) {
      await updateAutoprompt(editingId, payload);
      showMessage('Autoprompt aktualisiert!');
    } else {
      await createAutoprompt(payload);
      showMessage('Autoprompt erstellt!');
    }
    setEditingId(null);
    setForm(EMPTY_FORM);
    await load();
  }

  async function handleDelete(id) {
    if (!window.confirm('Autoprompt wirklich löschen?')) return;
    await deleteAutoprompt(id);
    await load();
  }

  async function handleToggle(ap) {
    await updateAutoprompt(ap.id, { ...ap, enabled: !ap.enabled, agent_id: ap.agent_id || null });
    await load();
  }

  async function handleRunNow(id) {
    await runAutopromptNow(id);
    showMessage('Wird ausgeführt...');
    setTimeout(load, 2000);
  }

  return (
    <div>
      {message && <div className="settings-message">{message}</div>}
      <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '16px' }}>
        Autoprompts werden automatisch zu festgelegten Zeiten ausgeführt. Das Ergebnis landet in einem dedizierten Chat im Verlauf.
      </p>

      <div className="settings-section">
        <h3>Konfigurierte Autoprompts</h3>
        <div className="agents-list">
          {autoprompts.map(ap => (
            <div key={ap.id} className="agent-item" style={{ flexWrap: 'wrap', gap: '8px' }}>
              <div className="agent-item-info" style={{ flex: 1, minWidth: 0 }}>
                <strong style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span
                    style={{
                      display: 'inline-block', width: '8px', height: '8px', borderRadius: '50%',
                      background: ap.enabled ? 'var(--accent)' : 'var(--text-secondary)',
                      flexShrink: 0,
                    }}
                  />
                  {ap.name}
                </strong>
                <span className="agent-item-desc" style={{ fontSize: '12px' }}>
                  {scheduleLabel(ap)}
                  {ap.last_run && ` · Zuletzt: ${new Date(ap.last_run).toLocaleString('de-DE')}`}
                  {ap.last_error && <span style={{ color: '#ef5350' }}> · Fehler!</span>}
                </span>
              </div>
              <div className="agent-item-actions">
                <button className="btn-edit-agent" onClick={() => handleRunNow(ap.id)} title="Jetzt ausführen">▶</button>
                <button className="btn-edit-agent" onClick={() => handleToggle(ap)}>
                  {ap.enabled ? 'Pause' : 'Aktiv'}
                </button>
                <button className="btn-edit-agent" onClick={() => startEdit(ap)}>Bearbeiten</button>
                <button className="btn-delete-agent" onClick={() => handleDelete(ap.id)}>Löschen</button>
              </div>
            </div>
          ))}
          {autoprompts.length === 0 && (
            <div className="agents-empty">Keine Autoprompts konfiguriert</div>
          )}
        </div>
      </div>

      <div className="settings-section">
        <h3>{editingId ? 'Autoprompt bearbeiten' : 'Neuen Autoprompt erstellen'}</h3>
        <div className="agent-form">
          <label className="agent-form-label">Name</label>
          <input
            type="text"
            placeholder="z.B. Tagesüberblick"
            value={form.name}
            onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
          />

          <label className="agent-form-label">Prompt</label>
          <textarea
            className="agent-prompt-textarea"
            placeholder="z.B. Gib mir eine kurze Zusammenfassung der heutigen Nachrichten."
            value={form.prompt}
            rows={5}
            onChange={e => setForm(f => ({ ...f, prompt: e.target.value }))}
          />

          <label className="agent-form-label">Zeitplan</label>
          <select
            value={form.schedule_type}
            onChange={e => setForm(f => ({ ...f, schedule_type: e.target.value }))}
            style={{ marginBottom: '8px' }}
          >
            <option value="interval">Intervall (alle X Minuten/Stunden)</option>
            <option value="daily">Täglich zu einer Uhrzeit</option>
            <option value="weekly">Wöchentlich</option>
          </select>

          {form.schedule_type === 'interval' && (
            <>
              <label className="agent-form-label">Intervall (Minuten)</label>
              <input
                type="number"
                min={1}
                value={form.interval_minutes}
                onChange={e => setForm(f => ({ ...f, interval_minutes: parseInt(e.target.value) || 60 }))}
              />
            </>
          )}

          {(form.schedule_type === 'daily' || form.schedule_type === 'weekly') && (
            <>
              {form.schedule_type === 'weekly' && (
                <>
                  <label className="agent-form-label">Wochentag</label>
                  <select
                    value={form.weekly_day}
                    onChange={e => setForm(f => ({ ...f, weekly_day: parseInt(e.target.value) }))}
                    style={{ marginBottom: '8px' }}
                  >
                    {WEEKDAYS.map((d, i) => <option key={i} value={i}>{d}</option>)}
                  </select>
                </>
              )}
              <label className="agent-form-label">Uhrzeit (HH:MM)</label>
              <input
                type="time"
                value={form.daily_time}
                onChange={e => setForm(f => ({ ...f, daily_time: e.target.value }))}
              />
            </>
          )}

          <label className="agent-form-label">Agent <span className="agent-form-optional">(optional)</span></label>
          <select
            value={form.agent_id}
            onChange={e => setForm(f => ({ ...f, agent_id: e.target.value }))}
          >
            <option value="">Standard (kein Agent)</option>
            {agents.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
          </select>

          <label className="agent-form-label" style={{ marginTop: '8px' }}>
            <input
              type="checkbox"
              checked={form.enabled}
              onChange={e => setForm(f => ({ ...f, enabled: e.target.checked }))}
              style={{ marginRight: '6px' }}
            />
            Aktiviert
          </label>

          <div className="agent-form-actions">
            <button
              className="btn-save-agent"
              onClick={handleSave}
              disabled={!form.name.trim() || !form.prompt.trim()}
            >
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
