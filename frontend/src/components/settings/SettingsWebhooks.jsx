import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { fetchWebhooks, createWebhook, updateWebhook, deleteWebhook, fetchAgents } from '../../services/api';

const EMPTY_FORM = { name: '', chat_id: '', agent_id: '' };

export default function SettingsWebhooks() {
  const { t } = useTranslation();
  const [webhooks, setWebhooks] = useState([]);
  const [agents, setAgents] = useState([]);
  const [form, setForm] = useState(EMPTY_FORM);
  const [editingId, setEditingId] = useState(null);
  const [editForm, setEditForm] = useState({});
  const [message, setMessage] = useState('');
  const [curlOpen, setCurlOpen] = useState({});
  const [copied, setCopied] = useState({});
  // Store real tokens for newly created webhooks (backend returns full token only on creation)
  const [realTokens, setRealTokens] = useState({});

  useEffect(() => {
    load();
    fetchAgents().then(setAgents).catch(() => {});
  }, []);

  async function load() {
    const data = await fetchWebhooks();
    setWebhooks(data);
  }

  function showMessage(msg) {
    setMessage(msg);
    setTimeout(() => setMessage(''), 3000);
  }

  async function handleCreate(e) {
    e.preventDefault();
    if (!form.name.trim()) return;
    const payload = {
      name: form.name.trim(),
      chat_id: form.chat_id ? parseInt(form.chat_id, 10) || null : null,
      agent_id: form.agent_id || '',
    };
    const created = await createWebhook(payload);
    if (created.error) { showMessage(created.error); return; }
    // Store the real token before it gets masked on reload
    setRealTokens(prev => ({ ...prev, [created.id]: created.token }));
    setForm(EMPTY_FORM);
    await load();
    showMessage(t('settings.webhooks.created'));
  }

  async function handleUpdate(id) {
    const payload = {
      name: editForm.name || '',
      chat_id: editForm.chat_id ? parseInt(editForm.chat_id, 10) || null : null,
      agent_id: editForm.agent_id || '',
    };
    await updateWebhook(id, payload);
    setEditingId(null);
    await load();
    showMessage(t('settings.webhooks.updated'));
  }

  async function handleDelete(id) {
    if (!window.confirm(t('settings.webhooks.deleteConfirm'))) return;
    await deleteWebhook(id);
    setRealTokens(prev => { const n = {...prev}; delete n[id]; return n; });
    await load();
  }

  function startEdit(wh) {
    setEditingId(wh.id);
    setEditForm({
      name: wh.name,
      chat_id: wh.chat_id != null ? String(wh.chat_id) : '',
      agent_id: wh.agent_id || '',
    });
  }

  function cancelEdit() {
    setEditingId(null);
    setEditForm({});
  }

  function toggleCurl(id) {
    setCurlOpen(prev => ({ ...prev, [id]: !prev[id] }));
  }

  function buildCurl(wh) {
    const token = realTokens[wh.id] || wh.token;
    const origin = window.location.origin;
    return `curl -X POST ${origin}/webhook/${wh.id} \\\n  -H "Authorization: Bearer ${token}" \\\n  -H "Content-Type: application/json" \\\n  -d '{"message": "Deine Nachricht hier"}'`;
  }

  async function copyToken(wh) {
    const token = realTokens[wh.id] || wh.token;
    await navigator.clipboard.writeText(token);
    setCopied(prev => ({ ...prev, [wh.id]: true }));
    setTimeout(() => setCopied(prev => ({ ...prev, [wh.id]: false })), 2000);
  }

  async function copyCurl(wh) {
    await navigator.clipboard.writeText(buildCurl(wh));
    const key = `curl_${wh.id}`;
    setCopied(prev => ({ ...prev, [key]: true }));
    setTimeout(() => setCopied(prev => ({ ...prev, [key]: false })), 2000);
  }

  const agentName = (id) => {
    if (!id) return t('settings.webhooks.noAgent');
    const a = agents.find(a => a.id === id);
    return a ? a.name : id;
  };

  return (
    <div style={{ maxWidth: '640px' }}>
      <p style={{ color: 'var(--text-secondary)', fontSize: '14px', marginBottom: '16px' }}>
        {t('settings.webhooks.description')}
      </p>

      <div style={{
        background: 'rgba(var(--accent-rgb, 99, 102, 241), 0.07)',
        border: '1px solid rgba(var(--accent-rgb, 99, 102, 241), 0.25)',
        borderRadius: '8px',
        padding: '12px 14px',
        fontSize: '13px',
        color: 'var(--text-secondary)',
        marginBottom: '24px',
        lineHeight: '1.7',
      }}>
        {t('settings.webhooks.info')}
      </div>

      {message && (
        <div style={{ color: 'var(--accent)', fontSize: '13px', marginBottom: '12px' }}>
          {message}
        </div>
      )}

      <h4 style={{ fontSize: '13px', fontWeight: '600', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.6px', marginBottom: '12px' }}>
        {t('settings.webhooks.configured')}
      </h4>

      {webhooks.length === 0 ? (
        <p style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '24px' }}>
          {t('settings.webhooks.empty')}
        </p>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '28px' }}>
          {webhooks.map(wh => (
            <div key={wh.id} style={{
              background: 'var(--surface)',
              border: '1px solid var(--border)',
              borderRadius: '8px',
              padding: '12px 14px',
            }}>
              {editingId === wh.id ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  <input
                    className="input"
                    value={editForm.name}
                    onChange={e => setEditForm(f => ({ ...f, name: e.target.value }))}
                    placeholder={t('settings.webhooks.name')}
                  />
                  <input
                    className="input"
                    value={editForm.chat_id}
                    onChange={e => setEditForm(f => ({ ...f, chat_id: e.target.value }))}
                    placeholder={t('settings.webhooks.chatIdPlaceholder')}
                  />
                  <select
                    className="input"
                    value={editForm.agent_id}
                    onChange={e => setEditForm(f => ({ ...f, agent_id: e.target.value }))}
                  >
                    <option value="">{t('settings.webhooks.noAgent')}</option>
                    {agents.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
                  </select>
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <button className="btn btn-primary" onClick={() => handleUpdate(wh.id)}>
                      {t('settings.webhooks.save')}
                    </button>
                    <button className="btn" onClick={cancelEdit}>
                      {t('settings.webhooks.cancel')}
                    </button>
                  </div>
                </div>
              ) : (
                <>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '8px' }}>
                    <div>
                      <div style={{ fontWeight: '600', fontSize: '14px', color: 'var(--text-primary)', marginBottom: '4px' }}>
                        {wh.name}
                      </div>
                      <div style={{ fontSize: '12px', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '2px' }}>
                        <span>
                          {t('settings.webhooks.token')}:{' '}
                          <code style={{ fontFamily: 'monospace', fontSize: '11px' }}>{realTokens[wh.id] || wh.token}</code>
                          {' '}
                          <button
                            style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--accent)', fontSize: '12px', padding: '0' }}
                            onClick={() => copyToken(wh)}
                            title={t('settings.webhooks.copy')}
                          >
                            {copied[wh.id] ? t('settings.webhooks.copied') : '📋'}
                          </button>
                        </span>
                        <span>
                          {t('settings.webhooks.chatId')}:{' '}
                          {wh.chat_id != null ? `#${wh.chat_id}` : t('settings.webhooks.newChatEach')}
                        </span>
                        <span>
                          {t('settings.webhooks.agent')}: {agentName(wh.agent_id)}
                        </span>
                      </div>
                    </div>
                    <div style={{ display: 'flex', gap: '6px', flexShrink: 0 }}>
                      <button className="btn" style={{ fontSize: '12px', padding: '4px 10px' }} onClick={() => startEdit(wh)}>
                        {t('settings.webhooks.edit')}
                      </button>
                      <button className="btn" style={{ fontSize: '12px', padding: '4px 10px', color: '#ef5350' }} onClick={() => handleDelete(wh.id)}>
                        {t('settings.webhooks.delete')}
                      </button>
                    </div>
                  </div>

                  <div style={{ marginTop: '8px' }}>
                    <button
                      style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--accent)', fontSize: '12px', padding: '0' }}
                      onClick={() => toggleCurl(wh.id)}
                    >
                      {curlOpen[wh.id] ? t('settings.webhooks.hideCurl') : t('settings.webhooks.showCurl')}
                    </button>
                    {curlOpen[wh.id] && (
                      <div style={{ marginTop: '8px', position: 'relative' }}>
                        <pre style={{
                          background: 'var(--guenther-bg)',
                          color: 'var(--guenther-text)',
                          fontFamily: 'monospace',
                          fontSize: '11px',
                          padding: '10px 12px',
                          borderRadius: '6px',
                          overflowX: 'auto',
                          margin: 0,
                          whiteSpace: 'pre-wrap',
                          wordBreak: 'break-all',
                        }}>
                          {buildCurl(wh)}
                        </pre>
                        <button
                          style={{ position: 'absolute', top: '6px', right: '8px', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--accent)', fontSize: '12px', padding: '0' }}
                          onClick={() => copyCurl(wh)}
                        >
                          {copied[`curl_${wh.id}`] ? t('settings.webhooks.copied') : '📋'}
                        </button>
                      </div>
                    )}
                  </div>
                </>
              )}
            </div>
          ))}
        </div>
      )}

      <h4 style={{ fontSize: '13px', fontWeight: '600', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.6px', marginBottom: '12px' }}>
        {t('settings.webhooks.newTitle')}
      </h4>

      <form onSubmit={handleCreate} style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        <div>
          <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '4px' }}>
            {t('settings.webhooks.name')} *
          </label>
          <input
            className="input"
            value={form.name}
            onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
            placeholder={t('settings.webhooks.namePlaceholder')}
            required
          />
        </div>
        <div>
          <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '4px' }}>
            {t('settings.webhooks.chatId')} <span style={{ opacity: 0.6 }}>({t('settings.webhooks.optional')})</span>
          </label>
          <input
            className="input"
            value={form.chat_id}
            onChange={e => setForm(f => ({ ...f, chat_id: e.target.value }))}
            placeholder={t('settings.webhooks.chatIdPlaceholder')}
            type="number"
            min="1"
          />
          <p style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '4px', opacity: 0.8 }}>
            {t('settings.webhooks.chatIdHelp')}
          </p>
        </div>
        <div>
          <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '4px' }}>
            {t('settings.webhooks.agent')} <span style={{ opacity: 0.6 }}>({t('settings.webhooks.optional')})</span>
          </label>
          <select
            className="input"
            value={form.agent_id}
            onChange={e => setForm(f => ({ ...f, agent_id: e.target.value }))}
          >
            <option value="">{t('settings.webhooks.noAgent')}</option>
            {agents.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
          </select>
        </div>
        <button className="btn btn-primary" type="submit" style={{ alignSelf: 'flex-start' }}>
          {t('settings.webhooks.create')}
        </button>
      </form>
    </div>
  );
}
