import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';

/**
 * Split message content into text parts and embedded base64 images.
 * Matches: ![alt](data:image/...;base64,...)
 */
function parseContent(content) {
  if (!content) return [{ type: 'text', value: '' }];

  const regex = /!\[([^\]]*)\]\((data:image\/[^;]+;base64,[A-Za-z0-9+/=]+)\)/g;
  const parts = [];
  let lastIndex = 0;
  let match;

  while ((match = regex.exec(content)) !== null) {
    // Text before the image
    if (match.index > lastIndex) {
      const text = content.slice(lastIndex, match.index).trim();
      if (text) parts.push({ type: 'text', value: text });
    }
    parts.push({ type: 'image', alt: match[1], src: match[2] });
    lastIndex = match.index + match[0].length;
  }

  // Remaining text after last image
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

export default function ChatWindow({ messages, onSendMessage, isLoading, activeChatId }) {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

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
        <button type="submit" className="btn-send" disabled={isLoading || !input.trim()}>
          Senden
        </button>
      </form>
    </div>
  );
}
