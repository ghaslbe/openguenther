import React, { useState, useRef, useEffect, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';

/**
 * Split message content into text parts and embedded base64 images.
 * Matches: ![alt](data:image/...;base64,...)
 */
function parseContent(content) {
  if (!content) return [{ type: 'text', value: '' }];

  const imageRegex = /!\[([^\]]*)\]\((data:image\/[^)]+)\)/g;
  const audioRegex = /!\[audio\]\((data:audio\/[^)]+)\)/g;

  // Collect all matches with their positions
  const matches = [];
  let m;

  while ((m = imageRegex.exec(content)) !== null) {
    matches.push({ index: m.index, end: m.index + m[0].length, type: 'image', alt: m[1], src: m[2] });
  }
  while ((m = audioRegex.exec(content)) !== null) {
    matches.push({ index: m.index, end: m.index + m[0].length, type: 'audio', src: m[1] });
  }

  matches.sort((a, b) => a.index - b.index);

  const parts = [];
  let lastIndex = 0;

  for (const match of matches) {
    if (match.index > lastIndex) {
      const text = content.slice(lastIndex, match.index).trim();
      if (text) parts.push({ type: 'text', value: text });
    }
    if (match.type === 'image') {
      parts.push({ type: 'image', alt: match.alt, src: match.src });
    } else {
      parts.push({ type: 'audio', src: match.src });
    }
    lastIndex = match.end;
  }

  if (lastIndex < content.length) {
    const text = content.slice(lastIndex).trim();
    if (text) parts.push({ type: 'text', value: text });
  }

  if (parts.length === 0) {
    parts.push({ type: 'text', value: content });
  }

  return parts;
}

function MessageContent({ content }) {
  const parts = parseContent(content);

  return (
    <>
      {parts.map((part, i) => {
        if (part.type === 'image') {
          return (
            <img
              key={i}
              src={part.src}
              alt={part.alt || 'Generiertes Bild'}
              style={{ maxWidth: '100%', borderRadius: '8px', marginTop: '8px', display: 'block' }}
            />
          );
        }
        if (part.type === 'audio') {
          return (
            <audio key={i} controls autoPlay style={{ maxWidth: '100%', marginTop: '8px', display: 'block' }}>
              <source src={part.src} type="audio/mpeg" />
            </audio>
          );
        }
        return (
          <ReactMarkdown key={i} components={{
            img: ({ node, ...props }) => (
              <img {...props} style={{ maxWidth: '100%', borderRadius: '8px', marginTop: '8px' }} />
            )
          }}>
            {part.value}
          </ReactMarkdown>
        );
      })}
    </>
  );
}

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

const CopyIcon = () => (
  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
  </svg>
);

function getTextForCopy(content) {
  if (!content) return '';
  return content
    .replace(/!\[[^\]]*\]\(data:[^)]+\)/g, '[Bild]')
    .trim();
}

function CopyButton({ text, align }) {
  const [copied, setCopied] = React.useState(false);
  const handleCopy = () => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    });
  };
  return (
    <div className={`message-copy-row message-copy-row--${align}`}>
      <button className="btn-copy-msg" onClick={handleCopy} title="Kopieren">
        {copied ? <span className="copy-check">✓</span> : <CopyIcon />}
      </button>
    </div>
  );
}

export default function ChatWindow({ messages, onSendMessage, isLoading, currentTool, currentToolLog, activeChatId, agents, selectedAgentId, onAgentChange, activeAgentName }) {
  const [input, setInput] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [attachedFile, setAttachedFile] = useState(null); // {name, content}
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const recognitionRef = useRef(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    inputRef.current?.focus();
  }, [activeChatId]);

  const handleSubmit = (e) => {
    e.preventDefault();
    const text = input.trim();
    if (!text && !attachedFile) return;
    if (isLoading) return;
    if (recognitionRef.current) {
      recognitionRef.current.onresult = null;
      recognitionRef.current.stop();
      recognitionRef.current = null;
      setIsRecording(false);
    }
    onSendMessage(text, attachedFile);
    setInput('');
    setAttachedFile(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      setAttachedFile({ name: file.name, content: ev.target.result });
    };
    reader.readAsText(file, 'utf-8');
  };

  const toggleRecording = useCallback(() => {
    if (!SpeechRecognition) return;

    if (isRecording) {
      recognitionRef.current?.stop();
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = 'de-DE';
    recognition.interimResults = true;
    recognition.continuous = false;

    recognition.onstart = () => setIsRecording(true);

    recognition.onresult = (e) => {
      const transcript = Array.from(e.results)
        .map(r => r[0].transcript)
        .join('');
      setInput(transcript);
    };

    recognition.onend = () => {
      setIsRecording(false);
      recognitionRef.current = null;
      inputRef.current?.focus();
    };

    recognition.onerror = () => {
      setIsRecording(false);
      recognitionRef.current = null;
    };

    recognitionRef.current = recognition;
    recognition.start();
  }, [isRecording]);

  return (
    <div className="chat-window">
      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="chat-empty">
            <div className="chat-empty-icon">G</div>
            <p>Willkommen bei Guenther!</p>
            <p className="chat-empty-sub">Sende eine Nachricht, um zu beginnen.</p>
          </div>
        )}
        {messages.map((msg, idx) => (
          <div key={idx} className={`message message-${msg.role}`}>
            <div className="message-role">
              {msg.role === 'user' ? 'Du' : (activeAgentName || 'Guenther')}
            </div>
            <div className="message-content">
              <MessageContent content={msg.content} />
            </div>
            <CopyButton text={getTextForCopy(msg.content)} align={msg.role === 'user' ? 'right' : 'left'} />
          </div>
        ))}
        {isLoading && (
          <div className="message message-assistant">
            <div className="message-role">{activeAgentName || 'Guenther'}</div>
            <div className="message-content">
              <div className="typing-indicator">
                <span></span><span></span><span></span>
                {(currentTool || currentToolLog) && (
                  <div className="typing-tool-info">
                    {currentTool && <span className="typing-tool-name">{currentTool}</span>}
                    {currentToolLog && <span className="typing-tool-log">{currentToolLog}</span>}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      {!activeChatId && agents && agents.length > 0 && (
        <div className="agent-picker">
          <label htmlFor="agent-select">Agent:</label>
          <select
            id="agent-select"
            value={selectedAgentId}
            onChange={e => onAgentChange(e.target.value)}
          >
            <option value="">Kein Agent (Standard)</option>
            {agents.map(a => (
              <option key={a.id} value={a.id}>{a.name}</option>
            ))}
          </select>
        </div>
      )}
      {attachedFile && (
        <div className="file-attachment-bar">
          <span className="file-attachment-name">📎 {attachedFile.name}</span>
          <button
            type="button"
            className="file-attachment-remove"
            onClick={() => { setAttachedFile(null); if (fileInputRef.current) fileInputRef.current.value = ''; }}
          >✕</button>
        </div>
      )}
      <form className="chat-input-form" onSubmit={handleSubmit}>
        <input
          ref={fileInputRef}
          type="file"
          style={{ display: 'none' }}
          onChange={handleFileChange}
          accept=".csv,.json,.xml,.txt,.tsv,.yaml,.yml,.log"
        />
        <button
          type="button"
          className="btn-upload"
          onClick={() => fileInputRef.current?.click()}
          title="Datei hochladen"
          disabled={isLoading}
        >
          📎
        </button>
        <input
          ref={inputRef}
          type="text"
          className="chat-input"
          placeholder="Nachricht eingeben... oder frag Guenther was er kann"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={isLoading}
        />
        {SpeechRecognition && (
          <button
            type="button"
            className={`btn-mic${isRecording ? ' btn-mic--active' : ''}`}
            onClick={toggleRecording}
            title={isRecording ? 'Aufnahme stoppen' : 'Spracheingabe starten'}
            disabled={isLoading}
          >
            {isRecording ? (
              <span className="mic-recording-dots">
                <span /><span /><span />
              </span>
            ) : (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 14a3 3 0 0 0 3-3V5a3 3 0 0 0-6 0v6a3 3 0 0 0 3 3zm5-3a5 5 0 0 1-10 0H5a7 7 0 0 0 6 6.92V20H9v2h6v-2h-2v-2.08A7 7 0 0 0 19 11h-2z"/>
              </svg>
            )}
          </button>
        )}
        <button type="submit" className="btn-send" disabled={isLoading || (!input.trim() && !attachedFile)}>
          Senden
        </button>
      </form>
    </div>
  );
}
