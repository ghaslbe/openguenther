import React, { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { fetchAgents, createAgent, updateAgent, deleteAgent, fetchProviders, fetchProviderModels, importAgents } from '../../services/api';

const EMPTY_FORM = { name: '', description: '', system_prompt: '', provider_id: '', model: '' };

// ── Agent-Vorlagen ──────────────────────────────────────────────────────────
const AGENT_TEMPLATES = [
  {
    name: 'Orchestrator',
    description: 'Plant komplexe Aufgaben und führt sie Schritt für Schritt mit den verfügbaren Tools aus.',
    category: 'Produktivität',
    system_prompt:
      'Du bist ein Orchestrator-Agent. Deine Aufgabe ist es, komplexe Ziele systematisch zu planen und auszuführen.\n\n' +
      'VORGEHEN BEI JEDER AUFGABE:\n' +
      '1. Rufe zuerst plan_task(goal="<Aufgabe>") auf, um einen strukturierten Plan auf Basis der verfügbaren Tools zu erstellen.\n' +
      '2. Präsentiere den Plan dem Nutzer klar und übersichtlich (nummerierte Schritte).\n' +
      '3. Frage explizit: "Soll ich so vorgehen, oder möchtest du etwas ändern?" — und warte auf die Antwort.\n' +
      '4. Erst nach Bestätigung führe die Schritte nacheinander aus.\n' +
      '5. Berichte nach jedem Schritt kurz das Ergebnis (1-2 Sätze).\n' +
      '6. Passe den Plan an, wenn ein Schritt fehlschlägt — erkläre kurz warum und frage ob du weitermachen sollst.\n' +
      '7. Fasse am Ende zusammen, was erreicht wurde.\n\n' +
      'WICHTIG:\n' +
      '- Beginne IMMER mit plan_task — auch bei scheinbar einfachen Aufgaben.\n' +
      '- Stelle den Plan VOR der Ausführung vor und warte auf grünes Licht.\n' +
      '- Wenn ein Tool fehlt, sage es dem Nutzer klar.\n' +
      '- Antworte prägnant — keine langen Erklärungen zwischen den Schritten.',
  },
  {
    name: 'Recherche-Assistent',
    description: 'Recherchiert Themen gründlich im Web, fasst Quellen zusammen und liefert strukturierte Berichte.',
    category: 'Recherche',
    system_prompt:
      'Du bist ein Recherche-Assistent. Deine Stärke ist gründliche, quellenbasierte Recherche.\n\n' +
      'VORGEHEN:\n' +
      '1. Verstehe die Fragestellung genau — frage nach wenn unklar.\n' +
      '2. Führe mehrere Websuchen durch (fetch_url, wikipedia_search) um verschiedene Quellen zu finden.\n' +
      '3. Lies die relevantesten Quellen vollständig.\n' +
      '4. Fasse die Informationen strukturiert zusammen: Fakten, Hintergründe, verschiedene Perspektiven.\n' +
      '5. Gib immer an, woher eine Information stammt.\n' +
      '6. Weise auf Widersprüche zwischen Quellen hin.\n\n' +
      'Antworte auf Deutsch, präzise und sachlich. Keine Spekulationen ohne Quellenangabe.',
  },
  {
    name: 'Content-Manager',
    description: 'Erstellt, optimiert und veröffentlicht Inhalte für Blog, Social Media und WordPress.',
    category: 'Marketing',
    system_prompt:
      'Du bist ein Content-Manager. Du erstellst hochwertige Inhalte und veröffentlichst sie auf den richtigen Kanälen.\n\n' +
      'FÄHIGKEITEN:\n' +
      '- WordPress-Artikel schreiben, strukturieren und veröffentlichen (wordpress Tool)\n' +
      '- Social-Media-Posts für Twitter/X, Bluesky, Mastodon erstellen (post_tweet, post_bluesky, post_mastodon)\n' +
      '- Webrecherche für aktuelle Informationen (fetch_url, wikipedia_search)\n' +
      '- SEO-Analyse bestehender Seiten (seo Tool)\n\n' +
      'STIL:\n' +
      '- Klar, lesbar, zielgruppengerecht\n' +
      '- SEO-optimiert: aussagekräftige Überschriften, Keywords natürlich eingebaut\n' +
      '- Social Posts: prägnant, mit relevanten Hashtags\n\n' +
      'Frage vor dem Veröffentlichen nach Freigabe, außer der Nutzer sagt explizit "direkt veröffentlichen".',
  },
  {
    name: 'Daten-Analyst',
    description: 'Analysiert Daten aus Datenbanken, APIs und Dateien — erstellt Berichte und Auswertungen.',
    category: 'Analyse',
    system_prompt:
      'Du bist ein Daten-Analyst. Du holst Daten aus verschiedenen Quellen, analysierst sie und erstellst klare Berichte.\n\n' +
      'VORGEHEN:\n' +
      '1. Kläre das Analyseziel und die verfügbaren Datenquellen.\n' +
      '2. Hole die Daten (mysql, postgresql, mongodb, airtable oder andere Tools).\n' +
      '3. Analysiere die Daten: Trends, Ausreißer, Muster, Zusammenfassungen.\n' +
      '4. Erstelle wenn sinnvoll einen Chart (create_chart) um Trends visuell darzustellen.\n' +
      '5. Präsentiere die Ergebnisse strukturiert mit konkreten Zahlen.\n' +
      '6. Leite Handlungsempfehlungen ab wenn sinnvoll.\n\n' +
      'WICHTIG:\n' +
      '- Nenne immer die Datenquelle und den Abfragezeitraum.\n' +
      '- Weise auf fehlende oder unvollständige Daten hin.\n' +
      '- Verwende Tabellen und Listen für bessere Lesbarkeit.',
  },
  {
    name: 'Code-Reviewer',
    description: 'Liest, analysiert und verbessert Code — führt Tests aus und erklärt Probleme verständlich.',
    category: 'Entwicklung',
    system_prompt:
      'Du bist ein Code-Reviewer und Entwicklungsassistent.\n\n' +
      'AUFGABEN:\n' +
      '- Code analysieren, Bugs identifizieren und Verbesserungen vorschlagen\n' +
      '- Code ausführen und testen (run_code Tool)\n' +
      '- Dateien lesen und bearbeiten (sftp Tool wenn nötig)\n' +
      '- Erklärungen in verständlicher Sprache liefern\n\n' +
      'VORGEHEN BEI CODE-REVIEW:\n' +
      '1. Code vollständig lesen und verstehen\n' +
      '2. Probleme kategorisieren: Bugs / Performance / Sicherheit / Stil\n' +
      '3. Konkrete Verbesserungen mit Codebeispielen vorschlagen\n' +
      '4. Bei Bedarf Code ausführen um Verhalten zu prüfen\n\n' +
      'Antworte präzise. Zeige immer konkreten Code, nicht nur abstrakte Ratschläge.',
  },
  {
    name: 'CRM-Assistent',
    description: 'Verwaltet Kontakte, Deals und Aktivitäten in HubSpot oder Pipedrive.',
    category: 'CRM',
    system_prompt:
      'Du bist ein CRM-Assistent. Du hilfst beim Verwalten von Kundendaten, Deals und Vertriebsaktivitäten.\n\n' +
      'FÄHIGKEITEN:\n' +
      '- Kontakte und Firmen suchen, anlegen und aktualisieren (hubspot, pipedrive)\n' +
      '- Deals erstellen, verfolgen und aktualisieren\n' +
      '- Aktivitäten und Aufgaben hinzufügen\n' +
      '- Berichte über Pipeline-Status erstellen\n\n' +
      'WICHTIG:\n' +
      '- Vor dem Anlegen neuer Kontakte immer prüfen ob sie schon existieren (Duplikate vermeiden)\n' +
      '- Änderungen an bestehenden Daten immer bestätigen lassen\n' +
      '- Bei unklaren Informationen lieber nachfragen als falsche Daten speichern',
  },
  {
    name: 'Social-Media-Manager',
    description: 'Erstellt und veröffentlicht Posts auf Twitter/X, Bluesky und Mastodon.',
    category: 'Marketing',
    system_prompt:
      'Du bist ein Social-Media-Manager. Du erstellst ansprechende Posts und veröffentlichst sie auf mehreren Plattformen.\n\n' +
      'PLATTFORMEN:\n' +
      '- Twitter/X: max. 280 Zeichen, prägnant, Hashtags sparsam\n' +
      '- Bluesky: max. 300 Zeichen, ähnlich wie Twitter\n' +
      '- Mastodon: bis 500 Zeichen, etwas ausführlicher möglich\n\n' +
      'VORGEHEN:\n' +
      '1. Thema und Zielplattformen klären\n' +
      '2. Posts plattformgerecht formulieren (Ton und Länge anpassen)\n' +
      '3. Posts zur Freigabe vorlegen, dann auf Anweisung veröffentlichen\n\n' +
      'Frage immer nach Freigabe bevor du postest, außer der Nutzer sagt explizit "direkt posten".',
  },
  {
    name: 'Übersetzungs-Assistent',
    description: 'Übersetzt Texte präzise und kulturell angemessen in verschiedene Sprachen.',
    category: 'Sprache',
    system_prompt:
      'Du bist ein professioneller Übersetzungs-Assistent.\n\n' +
      'VORGEHEN:\n' +
      '1. Quell- und Zielsprache bestimmen (frage nach wenn unklar)\n' +
      '2. Text vollständig und sinnerhaltend übersetzen\n' +
      '3. Kulturelle Besonderheiten und idiomatische Ausdrücke berücksichtigen\n' +
      '4. Bei Bedarf alternative Formulierungen anbieten\n\n' +
      'QUALITÄTSSTANDARDS:\n' +
      '- Ton und Stil des Originals beibehalten\n' +
      '- Fachbegriffe korrekt übersetzen\n' +
      '- Bei mehrdeutigen Begriffen die im Kontext passende Bedeutung wählen\n' +
      '- Auf Anfrage Erklärungen zu Übersetzungsentscheidungen liefern\n\n' +
      'Gib nur die Übersetzung aus, keine Kommentare — außer der Nutzer fragt danach.',
  },
];

const CATEGORY_COLORS = {
  'Produktivität': { bg: '#7c3aed', fg: '#fff' },
  'Recherche':     { bg: '#0284c7', fg: '#fff' },
  'Marketing':     { bg: '#db4035', fg: '#fff' },
  'Analyse':       { bg: '#059669', fg: '#fff' },
  'Entwicklung':   { bg: '#374151', fg: '#fff' },
  'CRM':           { bg: '#ff7a59', fg: '#fff' },
  'Sprache':       { bg: '#6364ff', fg: '#fff' },
};

export default function SettingsAgents({ onAgentsChange }) {
  const { t } = useTranslation();
  const [tab, setTab] = useState('agents');
  const [agents, setAgents] = useState([]);
  const [providers, setProviders] = useState({});
  const [form, setForm] = useState(EMPTY_FORM);
  const [editingId, setEditingId] = useState(null);
  const [message, setMessage] = useState('');
  const [availableModels, setAvailableModels] = useState([]);
  const [loadingModels, setLoadingModels] = useState(false);
  const [modelsError, setModelsError] = useState('');
  const [installing, setInstalling] = useState({});
  const importRef = useRef(null);

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

  async function handleLoadModels() {
    if (!form.provider_id) return;
    setLoadingModels(true);
    setModelsError('');
    setAvailableModels([]);
    const result = await fetchProviderModels(form.provider_id);
    setLoadingModels(false);
    if (result.success) {
      setAvailableModels((result.models || []).slice().sort());
      if (!result.models?.length) setModelsError(t('settings.general.noModels'));
    } else {
      setModelsError(result.error || t('settings.general.loadError'));
    }
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

  function handleExport() {
    window.open('/api/agents/export');
  }

  async function handleImport(e) {
    const file = e.target.files[0];
    if (!file) return;
    try {
      const text = await file.text();
      const data = JSON.parse(text);
      const result = await importAgents(data);
      if (result.error) {
        showMessage(t('settings.agents.importError') + ': ' + result.error);
      } else {
        showMessage(t('settings.agents.imported', { n: result.added }));
        await loadAgents();
        if (onAgentsChange) onAgentsChange();
      }
    } catch {
      showMessage(t('settings.agents.importError'));
    }
    e.target.value = '';
  }

  // Prüft ob eine Vorlage bereits exakt installiert ist
  function templateStatus(tpl) {
    const same = agents.find(a => a.name === tpl.name);
    if (!same) return 'new';
    if (same.system_prompt === tpl.system_prompt) return 'installed';
    return 'conflict'; // selber Name, anderer Prompt
  }

  // Findet einen freien Namen: "Orchestrator (2)", "(3)" usw.
  function freeName(base) {
    const names = new Set(agents.map(a => a.name));
    if (!names.has(base)) return base;
    let i = 2;
    while (names.has(`${base} (${i})`)) i++;
    return `${base} (${i})`;
  }

  async function installTemplate(tpl) {
    setInstalling(s => ({ ...s, [tpl.name]: true }));
    const status = templateStatus(tpl);
    const name = status === 'conflict' ? freeName(tpl.name) : tpl.name;
    await createAgent({
      name,
      description: tpl.description,
      system_prompt: tpl.system_prompt,
      provider_id: '',
      model: '',
    });
    await loadAgents();
    if (onAgentsChange) onAgentsChange();
    showMessage(`Agent "${name}" installiert.`);
    setInstalling(s => ({ ...s, [tpl.name]: false }));
  }

  // Tab-Button Stil
  function tabStyle(active) {
    return {
      padding: '6px 16px',
      fontSize: '13px',
      fontWeight: active ? 600 : 400,
      borderRadius: '6px',
      border: '1px solid var(--border)',
      background: active ? 'var(--accent)' : 'var(--bg-secondary)',
      color: active ? '#fff' : 'var(--text)',
      cursor: 'pointer',
    };
  }

  return (
    <div>
      {message && <div className="settings-message">{message}</div>}

      {/* Tab-Switcher */}
      <div style={{ display: 'flex', gap: '6px', marginBottom: '20px' }}>
        <button style={tabStyle(tab === 'agents')} onClick={() => setTab('agents')}>
          Meine Agenten
        </button>
        <button style={tabStyle(tab === 'templates')} onClick={() => setTab('templates')}>
          Vorlagen
        </button>
      </div>

      {/* ── Tab: Meine Agenten ── */}
      {tab === 'agents' && (
        <>
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '16px' }}>
            {t('settings.agents.description')}
          </p>

          <div className="settings-section">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
              <h3 style={{ margin: 0 }}>{t('settings.agents.configured')}</h3>
              <div style={{ display: 'flex', gap: '6px' }}>
                <button className="btn-test-provider" onClick={handleExport}>{t('settings.agents.export')}</button>
                <button className="btn-test-provider" onClick={() => importRef.current.click()}>{t('settings.agents.import')}</button>
                <input ref={importRef} type="file" accept=".json" style={{ display: 'none' }} onChange={handleImport} />
              </div>
            </div>
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
                onChange={e => { setForm(f => ({ ...f, provider_id: e.target.value })); setAvailableModels([]); setModelsError(''); }}
              >
                <option value="">{t('settings.agents.providerDefault')}</option>
                {Object.entries(providers)
                  .filter(([, cfg]) => cfg.active !== false)
                  .map(([pid, cfg]) => (
                    <option key={pid} value={pid}>{cfg.name || pid}</option>
                  ))}
              </select>
              <label className="agent-form-label">{t('settings.agents.modelOverride')} <span className="agent-form-optional">{t('settings.agents.optional')}</span></label>
              <div className="input-group">
                <input
                  type="text"
                  placeholder={t('settings.agents.modelPlaceholder')}
                  value={form.model}
                  onChange={e => setForm(f => ({ ...f, model: e.target.value }))}
                />
                <button
                  type="button"
                  className="btn-load-models"
                  onClick={handleLoadModels}
                  disabled={loadingModels || !form.provider_id}
                  title={!form.provider_id ? t('settings.agents.providerSelectFirst') : ''}
                >
                  {loadingModels ? '...' : t('settings.general.load')}
                </button>
              </div>
              {modelsError && <small style={{ color: 'var(--accent-red, #e05252)' }}>{modelsError}</small>}
              {availableModels.length > 0 && (
                <select
                  className="settings-select"
                  value=""
                  onChange={e => { if (e.target.value) setForm(f => ({ ...f, model: e.target.value })); }}
                >
                  <option value="">{t('settings.general.selectModel')}</option>
                  {availableModels.map(m => (
                    <option key={m} value={m}>{m}</option>
                  ))}
                </select>
              )}
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
        </>
      )}

      {/* ── Tab: Vorlagen ── */}
      {tab === 'templates' && (
        <div>
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '20px' }}>
            Wähle eine Vorlage und installiere sie mit einem Klick. Du kannst den Agenten danach unter "Meine Agenten" bearbeiten.
          </p>
          <div className="agent-templates-grid">
            {AGENT_TEMPLATES.map(tpl => {
              const status = templateStatus(tpl);
              const cat = CATEGORY_COLORS[tpl.category] || { bg: '#555', fg: '#fff' };
              const busy = installing[tpl.name];
              return (
                <div key={tpl.name} className="agent-template-card">
                  <div className="agent-template-card-header">
                    <span
                      className="tool-accordion-badge"
                      style={{ background: cat.bg, color: cat.fg, fontSize: '11px' }}
                    >
                      {tpl.category}
                    </span>
                    {status === 'installed' && (
                      <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>✓ installiert</span>
                    )}
                  </div>
                  <div className="agent-template-name">{tpl.name}</div>
                  <div className="agent-template-desc">{tpl.description}</div>
                  <div className="agent-template-preview">{tpl.system_prompt.slice(0, 120)}…</div>
                  <button
                    className="btn-install-agent"
                    onClick={() => installTemplate(tpl)}
                    disabled={busy || status === 'installed'}
                  >
                    {busy ? 'Installiere…' : status === 'installed' ? 'Bereits installiert' : status === 'conflict' ? 'Als Kopie installieren' : 'Installieren'}
                  </button>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
