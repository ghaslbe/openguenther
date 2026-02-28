import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { updateProvider, testProvider, fetchUsageStats, resetUsageStats } from '../../services/api';

function formatBytes(n) {
  if (n == null || n === 0) return '0 B';
  if (n >= 1024 * 1024) return (n / (1024 * 1024)).toFixed(1) + ' MB';
  if (n >= 1024) return (n / 1024).toFixed(1) + ' KB';
  return n + ' B';
}

const SSH_INFO = {
  ollama: {
    port: 11434,
    default_url: 'http://host.docker.internal:11434/v1',
    label: 'Ollama',
  },
  lmstudio: {
    port: 1234,
    default_url: 'http://host.docker.internal:1234/v1',
    label: 'LM Studio',
  },
};

const PROVIDER_ORDER = ['openrouter', 'mistral', 'ollama', 'lmstudio'];

export default function SettingsProviders({ providers, onProvidersChange }) {
  const { t } = useTranslation();
  const [expanded, setExpanded] = useState({});
  const [editState, setEditState] = useState({});
  const [showKeys, setShowKeys] = useState({});
  const [serverIp, setServerIp] = useState(null);
  const [saving, setSaving] = useState({});
  const [testing, setTesting] = useState({});
  const [testResult, setTestResult] = useState({});
  const [message, setMessage] = useState('');
  const [usagePeriod, setUsagePeriod] = useState('today');
  const [usageStats, setUsageStats] = useState([]);
  const [loadingUsage, setLoadingUsage] = useState(false);
  const [confirmReset, setConfirmReset] = useState(false);

  useEffect(() => {
    fetch('/api/system/info').then(r => r.json()).then(d => {
      if (d.public_ip) setServerIp(d.public_ip);
    }).catch(() => {});
  }, []);

  useEffect(() => {
    setLoadingUsage(true);
    fetchUsageStats(usagePeriod)
      .then(data => setUsageStats(Array.isArray(data) ? data : []))
      .catch(() => setUsageStats([]))
      .finally(() => setLoadingUsage(false));
  }, [usagePeriod]);

  async function handleResetUsage() {
    await resetUsageStats();
    setConfirmReset(false);
    setUsageStats([]);
  }

  function getEdit(pid) {
    return editState[pid] || {
      name: providers[pid]?.name || '',
      base_url: providers[pid]?.base_url || '',
      api_key: '',
    };
  }

  function setEdit(pid, field, value) {
    setEditState(prev => ({
      ...prev,
      [pid]: { ...getEdit(pid), [field]: value }
    }));
  }

  function toggleExpand(pid) {
    setExpanded(prev => ({ ...prev, [pid]: !prev[pid] }));
    // Initialize edit state with current values
    if (!expanded[pid] && providers[pid]) {
      setEditState(prev => ({
        ...prev,
        [pid]: { name: providers[pid].name, base_url: providers[pid].base_url, api_key: '' }
      }));
    }
  }

  async function handleToggleEnabled(pid, e) {
    e.stopPropagation();
    const current = providers[pid] || {};
    await updateProvider(pid, { enabled: !current.enabled });
    onProvidersChange();
  }

  async function handleTest(pid) {
    const edit = getEdit(pid);
    const base_url = edit.base_url || providers[pid]?.base_url || '';
    const api_key = edit.api_key || '';
    if (!base_url) {
      setTestResult(prev => ({ ...prev, [pid]: { success: false, error: t('settings.providers.noBaseUrl') } }));
      return;
    }
    setTesting(prev => ({ ...prev, [pid]: true }));
    setTestResult(prev => ({ ...prev, [pid]: null }));
    const result = await testProvider(base_url, api_key, pid);
    setTesting(prev => ({ ...prev, [pid]: false }));
    setTestResult(prev => ({ ...prev, [pid]: result }));
  }

  async function handleSave(pid) {
    setSaving(prev => ({ ...prev, [pid]: true }));
    const edit = getEdit(pid);
    await updateProvider(pid, edit);
    onProvidersChange();
    setEditState(prev => ({ ...prev, [pid]: { ...edit, api_key: '' } }));
    setMessage(t('settings.providers.saved'));
    setSaving(prev => ({ ...prev, [pid]: false }));
    setTimeout(() => setMessage(''), 3000);
  }

  const orderedProviders = [
    ...PROVIDER_ORDER.filter(pid => providers[pid]),
    ...Object.keys(providers).filter(pid => !PROVIDER_ORDER.includes(pid)),
  ];

  return (
    <div>
      {message && <div className="settings-message">{message}</div>}
      <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '20px' }}>
        {t('settings.providers.description')}
      </p>

      {orderedProviders.map(pid => {
        const p = providers[pid] || {};
        const edit = getEdit(pid);
        const isExpanded = expanded[pid];
        const isSaving = saving[pid];
        const isTesting = testing[pid];
        const tResult = testResult[pid];
        const sshInfo = SSH_INFO[pid];

        return (
          <div key={pid} className="provider-card">
            <div className="provider-card-header" onClick={() => toggleExpand(pid)}>
              <span className="provider-name">
                {p.name || pid}
                {t(`settings.providers.subtitles.${pid}`, { defaultValue: '' }) && (
                  <span style={{ opacity: 0.5, fontSize: '11px', fontWeight: 'normal', marginLeft: '7px' }}>
                    ({t(`settings.providers.subtitles.${pid}`)})
                  </span>
                )}
              </span>
              <span className={`provider-badge ${p.enabled ? 'active' : 'inactive'}`}>
                {p.enabled ? t('settings.providers.active') : t('settings.providers.inactive')}
              </span>
              <label className="provider-toggle" onClick={(e) => e.stopPropagation()}>
                <input
                  type="checkbox"
                  checked={!!p.enabled}
                  onChange={(e) => handleToggleEnabled(pid, e)}
                />
                <span className="provider-toggle-slider" />
              </label>
              <span className={`provider-expand-icon ${isExpanded ? 'open' : ''}`}>▼</span>
            </div>

            {isExpanded && (
              <div className="provider-card-body">
                <div className="settings-section" style={{ marginTop: '12px', marginBottom: 0 }}>
                  <label>
                    {t('settings.providers.name')}
                    <input
                      type="text"
                      value={edit.name}
                      onChange={(e) => setEdit(pid, 'name', e.target.value)}
                      placeholder={p.name || pid}
                    />
                  </label>
                  <label>
                    {t('settings.providers.baseUrl')}
                    <input
                      type="text"
                      value={edit.base_url}
                      onChange={(e) => setEdit(pid, 'base_url', e.target.value)}
                      placeholder="https://openrouter.ai/api/v1"
                    />
                    <small>{t('settings.providers.baseUrlHelp')}</small>
                  </label>
                  <label>
                    {t('settings.providers.apiKey')} {pid !== 'openrouter' && <span style={{ opacity: 0.6 }}>{t('settings.providers.apiKeyOptional')}</span>}
                    <div className="input-group">
                      <input
                        type={showKeys[pid] ? 'text' : 'password'}
                        value={edit.api_key}
                        onChange={(e) => setEdit(pid, 'api_key', e.target.value)}
                        placeholder={p.api_key_masked || (pid === 'openrouter' ? 'sk-or-v1-...' : t('settings.providers.apiKeyHelp'))}
                      />
                      <button
                        type="button"
                        className="btn-toggle-key"
                        onClick={() => setShowKeys(prev => ({ ...prev, [pid]: !prev[pid] }))}
                      >
                        {showKeys[pid] ? t('settings.providers.hide') : t('settings.providers.show')}
                      </button>
                    </div>
                    <small>{t('settings.providers.apiKeyHelp')}</small>
                  </label>
                  {sshInfo && (
                    <div className="provider-ssh-info">
                      <strong>{t('settings.providers.sshTitle')}</strong>
                      <p>{t('settings.providers.sshDesc', { label: sshInfo.label })}</p>
                      <code>ssh -R {sshInfo.port}:localhost:{sshInfo.port} user@{serverIp || 'server-ip'} -N</code>
                      <p>{t('settings.providers.sshUrlTitle')}</p>
                      <code>{sshInfo.default_url}</code>
                      <p className="provider-ssh-note">{t('settings.providers.sshNote')}</p>
                      <strong style={{marginTop: '12px'}}>{t('settings.providers.sshPrereqTitle')}</strong>
                      <p>{t('settings.providers.sshPrereqDesc')}</p>
                      <code>AllowTcpForwarding yes{'\n'}GatewayPorts yes</code>
                      <p>{t('settings.providers.sshRestartDesc')}</p>
                      <code>sudo systemctl restart sshd</code>
                    </div>
                  )}
                  <div className="provider-action-row">
                    <button className="btn-save" onClick={() => handleSave(pid)} disabled={isSaving}>
                      {isSaving ? t('settings.providers.saving') : t('settings.providers.save')}
                    </button>
                    <button className="btn-test-provider" onClick={() => handleTest(pid)} disabled={isTesting}>
                      {isTesting ? t('settings.providers.testing') : t('settings.providers.test')}
                    </button>
                  </div>
                  {tResult && (
                    <div className={`provider-test-result ${tResult.success ? 'ok' : 'err'}`}>
                      {tResult.success
                        ? <>{t('settings.providers.testOk', { count: tResult.model_count })}{tResult.models?.length ? `: ${tResult.models.join(', ')}` : ''}</>
                        : t('settings.providers.testErr', { error: tResult.error })
                      }
                    </div>
                  )}
                  {pid === 'openrouter' && (
                    <div className="provider-help-links">
                      <a href="https://openrouter.ai/settings/keys" target="_blank" rel="noopener noreferrer">{t('settings.providers.openrouterKeys')}</a>
                      <a href="https://openrouter.ai/settings/credits" target="_blank" rel="noopener noreferrer">{t('settings.providers.openrouterUsage')}</a>
                    </div>
                  )}
                  {pid === 'mistral' && (
                    <div className="provider-help-links">
                      <a href="https://console.mistral.ai/api-keys" target="_blank" rel="noopener noreferrer">{t('settings.providers.mistralKeys')}</a>
                      <a href="https://docs.mistral.ai/api" target="_blank" rel="noopener noreferrer">{t('settings.providers.mistralDocs')}</a>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        );
      })}

      {/* Usage stats section */}
      <div style={{ marginTop: '32px' }}>
        <h3 style={{ fontSize: '14px', fontWeight: 600, marginBottom: '12px', color: 'var(--text-primary)' }}>
          {t('settings.usage.title')}
        </h3>
        <div style={{ display: 'flex', gap: '6px', marginBottom: '12px', flexWrap: 'wrap' }}>
          {['today', 'week', 'month', 'all'].map(p => (
            <button
              key={p}
              onClick={() => setUsagePeriod(p)}
              style={{
                padding: '4px 12px',
                fontSize: '12px',
                borderRadius: '4px',
                border: '1px solid var(--border)',
                background: usagePeriod === p ? 'var(--accent)' : 'var(--bg-secondary)',
                color: usagePeriod === p ? '#fff' : 'var(--text-primary)',
                cursor: 'pointer',
              }}
            >
              {t(`settings.usage.${p}`)}
            </button>
          ))}
        </div>

        {loadingUsage ? (
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>…</p>
        ) : usageStats.length === 0 ? (
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>{t('settings.usage.noData')}</p>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border)', color: 'var(--text-secondary)' }}>
                  <th style={{ textAlign: 'left', padding: '4px 8px' }}>{t('settings.usage.provider')}</th>
                  <th style={{ textAlign: 'left', padding: '4px 8px' }}>{t('settings.usage.model')}</th>
                  <th style={{ textAlign: 'right', padding: '4px 8px' }}>{t('settings.usage.requests')}</th>
                  <th style={{ textAlign: 'right', padding: '4px 8px' }}>{t('settings.usage.sent')}</th>
                  <th style={{ textAlign: 'right', padding: '4px 8px' }}>{t('settings.usage.received')}</th>
                  <th style={{ textAlign: 'right', padding: '4px 8px' }}>{t('settings.usage.tokens')}</th>
                </tr>
              </thead>
              <tbody>
                {usageStats.map((row, i) => {
                  const hasTokens = row.prompt_tokens != null || row.completion_tokens != null;
                  return (
                    <tr key={i} style={{ borderBottom: '1px solid var(--border)' }}>
                      <td style={{ padding: '4px 8px' }}>{row.provider_id}</td>
                      <td style={{ padding: '4px 8px', color: 'var(--text-secondary)', maxWidth: '180px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{row.model}</td>
                      <td style={{ textAlign: 'right', padding: '4px 8px' }}>{row.requests}</td>
                      <td style={{ textAlign: 'right', padding: '4px 8px' }}>{formatBytes(row.bytes_sent)}</td>
                      <td style={{ textAlign: 'right', padding: '4px 8px' }}>{formatBytes(row.bytes_received)}</td>
                      <td style={{ textAlign: 'right', padding: '4px 8px', color: 'var(--text-secondary)' }}>
                        {hasTokens ? `${(row.prompt_tokens || 0) + (row.completion_tokens || 0)}` : '—'}
                      </td>
                    </tr>
                  );
                })}
                <tr style={{ borderTop: '2px solid var(--border)', fontWeight: 600 }}>
                  <td style={{ padding: '4px 8px' }}>{t('settings.usage.all')}</td>
                  <td />
                  <td style={{ textAlign: 'right', padding: '4px 8px' }}>{usageStats.reduce((s, r) => s + r.requests, 0)}</td>
                  <td style={{ textAlign: 'right', padding: '4px 8px' }}>{formatBytes(usageStats.reduce((s, r) => s + (r.bytes_sent || 0), 0))}</td>
                  <td style={{ textAlign: 'right', padding: '4px 8px' }}>{formatBytes(usageStats.reduce((s, r) => s + (r.bytes_received || 0), 0))}</td>
                  <td />
                </tr>
              </tbody>
            </table>
          </div>
        )}

        <div style={{ marginTop: '12px' }}>
          {confirmReset ? (
            <span style={{ fontSize: '13px' }}>
              {t('settings.usage.resetConfirm')}{' '}
              <button onClick={handleResetUsage} style={{ fontSize: '12px', color: 'var(--error, #e53e3e)', background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}>
                {t('settings.usage.reset')}
              </button>
              {' '}
              <button onClick={() => setConfirmReset(false)} style={{ fontSize: '12px', background: 'none', border: 'none', cursor: 'pointer', padding: 0, color: 'var(--text-secondary)' }}>
                {t('settings.usage.resetCancel')}
              </button>
            </span>
          ) : (
            <button
              onClick={() => setConfirmReset(true)}
              style={{ fontSize: '12px', padding: '4px 10px', borderRadius: '4px', border: '1px solid var(--border)', background: 'var(--bg-secondary)', color: 'var(--text-secondary)', cursor: 'pointer' }}
            >
              {t('settings.usage.reset')}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
