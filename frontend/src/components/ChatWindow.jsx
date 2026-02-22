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
            <audio key={i} controls style={{ maxWidth: '100%', marginTop: '8px', display: 'block' }}>
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

export default function ChatWindow({ messages, onSendMessage, isLoading, activeChatId }) {
  const [input, setInput] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const recognitionRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    inputRef.current?.focus();
  }, [activeChatId]);

  const handleSubmit = (e) => {
    e.preventDefault();
    const text = input.trim();
    if (!text || isLoading) return;
    onSendMessage(text);
    setInput('');
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
              {msg.role === 'user' ? 'Du' : 'Guenther'}
            </div>
            <div className="message-content">
              <MessageContent content={msg.content} />
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="message message-assistant">
            <div className="message-role">Guenther</div>
            <div className="message-content">
              <div className="typing-indicator">
                <span></span><span></span><span></span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      <form className="chat-input-form" onSubmit={handleSubmit}>
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
        <button type="submit" className="btn-send" disabled={isLoading || !input.trim()}>
          Senden
        </button>
      </form>
    </div>
  );
}
