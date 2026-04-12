import React, { useState, useEffect } from 'react';

function formatBytes(bytes) {
  if (!bytes || bytes === 0) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  const val = bytes / Math.pow(1024, i);
  return `${i === 0 ? val : val.toFixed(1)} ${units[i]}`;
}

const CATEGORIES = [
  { key: 'files',    label: 'Chat-Dateien', color: '#4db6ac', icon: '📁' },
  { key: 'uploads',  label: 'Uploads',      color: '#7986cb', icon: '📤' },
  { key: 'database', label: 'Datenbank',    color: '#ffb74d', icon: '🗄️' },
  { key: 'other',    label: 'Konfig',       color: '#90a4ae', icon: '⚙️'  },
];

export default function SettingsSpeicher() {
  const [info, setInfo]               = useState(null);
  const [loading, setLoading]         = useState(true);
  const [error, setError]             = useState('');
  const [confirmDelete, setConfirmDelete] = useState(null); // relative_path
  const [deleting, setDeleting]       = useState(null);
  const [statusMsg, setStatusMsg]     = useState('');

  useEffect(() => { loadInfo(); }, []);

  async function loadInfo() {
    setLoading(true);
    setError('');
    try {
      const res = await fetch('/api/storage/info');
      if (!res.ok) throw new Error('Fehler beim Laden');
      setInfo(await res.json());
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete(path) {
    setDeleting(path);
    try {
      const res = await fetch('/api/storage/file', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path }),
      });
      if (!res.ok) throw new Error('Löschen fehlgeschlagen');
      setConfirmDelete(null);
      setStatusMsg('Datei gelöscht.');
      setTimeout(() => setStatusMsg(''), 2500);
      await loadInfo();
    } catch (e) {
      setError(e.message);
    } finally {
      setDeleting(null);
    }
  }

  function handleDownload(relativePath, name) {
    const a = document.createElement('a');
    a.href = `/api/storage/download?path=${encodeURIComponent(relativePath)}`;
    a.download = name;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  }

  /* ── Render helpers ─────────────────────────────────────── */

  if (loading) {
    return (
      <div style={{ color: 'var(--text-secondary)', fontSize: '14px', padding: '20px 0' }}>
        Lade Speicherinformationen…
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ color: '#ef5350', fontSize: '14px', padding: '20px 0' }}>
        ⚠ {error}
        <button onClick={loadInfo} style={btnStyle('secondary', true)}>Nochmal versuchen</button>
      </div>
    );
  }

  if (!info) return null;

  const { total_size, breakdown, top_files, file_count } = info;

  return (
    <div style={{ maxWidth: '820px' }}>

      {/* ── Kopfzeile ── */}
      <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', marginBottom: '20px', gap: '12px', flexWrap: 'wrap' }}>
        <div>
          <div style={{ fontSize: '30px', fontWeight: '700', color: 'var(--text-primary)', lineHeight: 1 }}>
            {formatBytes(total_size)}
          </div>
          <div style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '4px' }}>
            {file_count} Datei{file_count !== 1 ? 'en' : ''} insgesamt
          </div>
        </div>
        <button onClick={loadInfo} style={btnStyle('secondary')}>🔄 Aktualisieren</button>
      </div>

      {/* ── Breakdown-Bar ── */}
      {total_size > 0 && (
        <div style={{ marginBottom: '24px' }}>
          <div style={{ display: 'flex', height: '10px', borderRadius: '5px', overflow: 'hidden', marginBottom: '12px', background: 'var(--border)' }}>
            {CATEGORIES.map(cat => {
              const pct = total_size > 0 ? (breakdown[cat.key] / total_size) * 100 : 0;
              return pct > 0 ? (
                <div key={cat.key} style={{ width: `${pct}%`, background: cat.color, transition: 'width 0.4s' }} title={`${cat.label}: ${formatBytes(breakdown[cat.key])}`} />
              ) : null;
            })}
          </div>
          <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
            {CATEGORIES.map(cat => (
              <div key={cat.key} style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: 'var(--text-secondary)' }}>
                <span style={{ width: '10px', height: '10px', borderRadius: '2px', background: cat.color, flexShrink: 0 }} />
                <span>{cat.icon} {cat.label}</span>
                <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{formatBytes(breakdown[cat.key])}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Status-Meldung ── */}
      {statusMsg && (
        <div style={{ fontSize: '13px', color: '#4db6ac', marginBottom: '12px' }}>✓ {statusMsg}</div>
      )}

      {/* ── Datei-Tabelle ── */}
      {top_files.length === 0 ? (
        <div style={{ color: 'var(--text-secondary)', fontSize: '14px', padding: '20px 0' }}>
          Keine Dateien gefunden.
        </div>
      ) : (
        <div>
          <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '8px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            Größte Dateien{top_files.length < file_count ? ` (Top ${top_files.length} von ${file_count})` : ''}
          </div>
          <div style={{ border: '1px solid var(--border)', borderRadius: '8px', overflow: 'hidden' }}>
            {/* Tabellen-Header */}
            <div style={{ ...rowStyle, background: 'var(--bg-tertiary)', borderBottom: '1px solid var(--border)', fontWeight: 600, fontSize: '11px', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              <span style={{ flex: '1 1 180px' }}>Dateiname</span>
              <span style={{ flex: '0 0 70px', textAlign: 'right' }}>Größe</span>
              <span style={{ flex: '1 1 160px', paddingLeft: '12px' }}>Chat / Quelle</span>
              <span style={{ flex: '0 0 80px', textAlign: 'center' }}>Typ</span>
              <span style={{ flex: '0 0 120px', textAlign: 'right' }}>Aktionen</span>
            </div>

            {/* Datei-Zeilen */}
            {top_files.map((file, idx) => {
              const isConfirming = confirmDelete === file.relative_path;
              const isDeleting   = deleting === file.relative_path;
              const cat = CATEGORIES.find(c => c.key === file.category);
              const displayName = file.name.length > 36
                ? file.name.slice(0, 16) + '…' + file.name.slice(-16)
                : file.name;
              const chatLabel = file.chat_title
                ? (file.chat_title.length > 28 ? file.chat_title.slice(0, 26) + '…' : file.chat_title)
                : '—';

              return (
                <div
                  key={file.relative_path}
                  style={{
                    ...rowStyle,
                    borderBottom: idx < top_files.length - 1 ? '1px solid var(--border)' : 'none',
                    background: isConfirming ? 'rgba(239,83,80,0.06)' : 'transparent',
                    fontSize: '13px',
                  }}
                >
                  {/* Dateiname */}
                  <span style={{ flex: '1 1 180px', color: 'var(--text-primary)', fontFamily: 'monospace', fontSize: '12px', overflow: 'hidden', whiteSpace: 'nowrap' }}
                        title={file.name}>
                    {displayName}
                  </span>

                  {/* Größe */}
                  <span style={{ flex: '0 0 70px', textAlign: 'right', color: 'var(--text-primary)', fontWeight: 600, fontSize: '12px', whiteSpace: 'nowrap' }}>
                    {formatBytes(file.size)}
                  </span>

                  {/* Chat-Titel */}
                  <span style={{ flex: '1 1 160px', paddingLeft: '12px', color: 'var(--text-secondary)', overflow: 'hidden', whiteSpace: 'nowrap' }}
                        title={file.chat_title || ''}>
                    {chatLabel}
                  </span>

                  {/* Kategorie-Badge */}
                  <span style={{ flex: '0 0 80px', textAlign: 'center' }}>
                    <span style={{
                      display: 'inline-block',
                      padding: '2px 7px',
                      borderRadius: '10px',
                      fontSize: '10px',
                      fontWeight: 600,
                      background: cat ? cat.color + '22' : '#88888822',
                      color: cat ? cat.color : '#888',
                      border: `1px solid ${cat ? cat.color + '55' : '#88888855'}`,
                      whiteSpace: 'nowrap',
                    }}>
                      {cat ? cat.icon : '?'} {cat ? cat.label : file.category}
                    </span>
                  </span>

                  {/* Aktionen */}
                  <span style={{ flex: '0 0 120px', textAlign: 'right', display: 'flex', gap: '6px', justifyContent: 'flex-end', alignItems: 'center' }}>
                    {!isConfirming ? (
                      <>
                        {/* Download */}
                        <button
                          onClick={() => handleDownload(file.relative_path, file.name)}
                          style={iconBtnStyle('#4db6ac')}
                          title="Herunterladen"
                        >⬇</button>

                        {/* Löschen (erstes Klick → Confirm) */}
                        <button
                          onClick={() => setConfirmDelete(file.relative_path)}
                          style={iconBtnStyle('#ef5350')}
                          title="Löschen"
                        >🗑</button>
                      </>
                    ) : (
                      <>
                        {/* Bestätigen */}
                        <button
                          onClick={() => handleDelete(file.relative_path)}
                          disabled={isDeleting}
                          style={{ ...iconBtnStyle('#ef5350'), background: '#ef535022', padding: '3px 8px', fontSize: '11px', fontWeight: 600 }}
                        >
                          {isDeleting ? '…' : '✓ Löschen'}
                        </button>
                        {/* Abbrechen */}
                        <button
                          onClick={() => setConfirmDelete(null)}
                          disabled={isDeleting}
                          style={{ ...iconBtnStyle('#888'), padding: '3px 6px', fontSize: '11px' }}
                        >✕</button>
                      </>
                    )}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

/* ── Shared styles ── */

const rowStyle = {
  display: 'flex',
  alignItems: 'center',
  padding: '9px 14px',
  gap: '8px',
};

function btnStyle(variant, hasMargin) {
  const base = {
    padding: '7px 14px',
    borderRadius: '6px',
    border: '1px solid var(--border)',
    fontSize: '13px',
    cursor: 'pointer',
    fontWeight: 600,
    marginLeft: hasMargin ? '12px' : 0,
  };
  if (variant === 'secondary') {
    return { ...base, background: 'var(--bg-secondary)', color: 'var(--text-primary)' };
  }
  return base;
}

function iconBtnStyle(color) {
  return {
    background: 'transparent',
    border: `1px solid ${color}44`,
    borderRadius: '5px',
    color: color,
    cursor: 'pointer',
    fontSize: '13px',
    padding: '3px 7px',
    lineHeight: 1,
    transition: 'background 0.15s',
  };
}
