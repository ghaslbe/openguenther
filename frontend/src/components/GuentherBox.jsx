import React, { useRef, useEffect, useState, useCallback } from 'react';

function syntaxHighlight(json) {
  if (typeof json !== 'string') {
    json = JSON.stringify(json, null, 2);
  }
  // Escape HTML
  json = json.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  // Syntax highlight
  return json.replace(
    /("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g,
    (match) => {
      let cls = 'json-number';
      if (/^"/.test(match)) {
        if (/:$/.test(match)) {
          cls = 'json-key';
        } else {
          cls = 'json-string';
        }
      } else if (/true|false/.test(match)) {
        cls = 'json-boolean';
      } else if (/null/.test(match)) {
        cls = 'json-null';
      }
      return `<span class="${cls}">${match}</span>`;
    }
  );
}

function LogEntry({ entry }) {
  const [collapsed, setCollapsed] = useState(false);

  // Legacy format: plain string
  if (typeof entry === 'string') {
    return <div className="guenther-line">{entry}</div>;
  }

  // Legacy format: {message: string} without type
  if (!entry.type && entry.message && typeof entry.message === 'string') {
    return <div className="guenther-line">{entry.message}</div>;
  }

  const type = entry.type || 'text';

  if (type === 'header') {
    return (
      <div className="guenther-header-line">
        ═══ {entry.message} ═══
      </div>
    );
  }

  if (type === 'json') {
    const jsonStr = JSON.stringify(entry.data, null, 2);
    const lines = jsonStr.split('\n').length;
    const isLarge = lines > 8;

    return (
      <div className="guenther-json-block">
        <div
          className="guenther-json-label"
          onClick={() => isLarge && setCollapsed(!collapsed)}
          style={isLarge ? { cursor: 'pointer' } : {}}
        >
          {isLarge && (
            <span className="json-toggle">{collapsed ? '+ ' : '- '}</span>
          )}
          {entry.label || 'data'} {isLarge && collapsed && <span className="json-preview">({lines} Zeilen)</span>}
        </div>
        {!collapsed && (
          <pre
            className="guenther-json-content"
            dangerouslySetInnerHTML={{ __html: syntaxHighlight(entry.data) }}
          />
        )}
      </div>
    );
  }

  // type === 'text' or anything else
  return <div className="guenther-line">{entry.message}</div>;
}

export default function GuentherBox({ logs, width, onResizeStart }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  return (
    <div className="guenther-box" style={{ width: `${width}px`, minWidth: `${width}px` }}>
      <div className="guenther-resize-handle" onMouseDown={onResizeStart} />
      <div className="guenther-header">
        <span className="guenther-title">GUENTHER</span>
        <span className="guenther-subtitle">MCP Terminal</span>
      </div>
      <div className="guenther-terminal">
        {logs.map((log, idx) => (
          <LogEntry key={idx} entry={log} />
        ))}
        {logs.length === 0 && (
          <div className="guenther-line dim">Warte auf Aktivitaet...</div>
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
