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
  const [errorPopup, setErrorPopup] = useState(null);
  const [logPopup, setLogPopup] = useState(null);

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
                  {ap.last_status === 'success' && !ap.last_error && (
                    <button
                      onClick={() => setLogPopup({ name: ap.name, log: ap.last_log || '(kein Log)' })}
                      style={{
                        background: 'none', border: 'none', padding: '0 0 0 4px',
                        color: '#66bb6a', cursor: 'pointer', fontSize: 'inherit',
                        textDecoration: 'underline', fontFamily: 'inherit',
                      }}
                    >· Erfolgreich</button>
                  )}
                  {ap.last_error && (<>
                    <button
                      onClick={() => setErrorPopup({ name: ap.name, error: ap.last_error })}
                      style={{
                        background: 'none', border: 'none', padding: '0 0 0 4px',
                        color: '#ef5350', cursor: 'pointer', fontSize: 'inherit',
                        textDecoration: 'underline', fontFamily: 'inherit',
                      }}
                    >· Fehler</button>
                    {ap.last_log && (
                      <button
                        onClick={() => setLogPopup({ name: ap.name, log: ap.last_log })}
                        style={{
                          background: 'none', border: 'none', padding: '0 0 0 4px',
                          color: 'var(--text-secondary)', cursor: 'pointer', fontSize: 'inherit',
                          textDecoration: 'underline', fontFamily: 'inherit',
                        }}
                      >Log</button>
                    )}
                  </>)}
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
            placeholder={"z.B. Gib mir eine Zusammenfassung der heutigen Nachrichten und sende sie mit Telegram an @mama75.\n\n(Hinweis: Der Empfänger muss dem Bot vorher mindestens einmal geschrieben haben, damit Telegram das erlaubt.)"}
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
      {logPopup && (
        <div
          onClick={() => setLogPopup(null)}
          style={{
            position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            zIndex: 9999,
          }}
        >
          <div
            onClick={e => e.stopPropagation()}
            style={{
              background: 'var(--bg-sidebar)', border: '1px solid var(--border)',
              borderRadius: '8px', padding: '24px', maxWidth: '680px', width: '90%',
              boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
            }}
          >
            <p style={{ fontWeight: '700', color: 'var(--text-primary)', marginBottom: '12px', fontSize: '14px' }}>
              Log: {logPopup.name}
            </p>
            <pre style={{
              background: 'var(--bg-dark)', border: '1px solid var(--border)',
              borderRadius: '4px', padding: '12px', fontSize: '11px',
              color: 'var(--text-primary)', whiteSpace: 'pre-wrap', wordBreak: 'break-all',
              maxHeight: '400px', overflowY: 'auto', margin: 0, lineHeight: '1.6',
            }}>
              {logPopup.log}
            </pre>
            <button onClick={() => setLogPopup(null)} className="btn-save-agent" style={{ marginTop: '16px' }}>
              Schließen
            </button>
          </div>
        </div>
      )}

      {errorPopup && (
        <div
          onClick={() => setErrorPopup(null)}
          style={{
            position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            zIndex: 9999,
          }}
        >
          <div
            onClick={e => e.stopPropagation()}
            style={{
              background: 'var(--bg-sidebar)', border: '1px solid var(--border)',
              borderRadius: '8px', padding: '24px', maxWidth: '560px', width: '90%',
              boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
            }}
          >
            <p style={{ fontWeight: '700', color: '#ef5350', marginBottom: '12px', fontSize: '14px' }}>
              Fehler: {errorPopup.name}
            </p>
            <pre style={{
              background: 'var(--bg-dark)', border: '1px solid var(--border)',
              borderRadius: '4px', padding: '12px', fontSize: '12px',
              color: 'var(--text-primary)', whiteSpace: 'pre-wrap', wordBreak: 'break-all',
              maxHeight: '300px', overflowY: 'auto', margin: 0,
            }}>
              {errorPopup.error}
            </pre>
            <button
              onClick={() => setErrorPopup(null)}
              className="btn-save-agent"
              style={{ marginTop: '16px' }}
            >
              Schließen
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
