// =====================================================
// App.jsx — Main group chat UI
// =====================================================

import { useState, useEffect, useRef } from 'react'
import ChatBubble      from './ChatBubble'
import TypingIndicator from './TypingIndicator'
import useDebate       from './useDebate'

export default function App() {
  const [topic, setTopic]     = useState('')
  const bottomRef             = useRef(null)
  const { messages, typing, status, winner, startDebate, stopDebate } = useDebate()

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, typing])

  const handleStart = () => {
    if (topic.trim() && status !== 'debating') {
      startDebate(topic.trim())
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') handleStart()
  }

  return (
    <div style={{
      display:       'flex',
      flexDirection: 'column',
      height:        '100vh',
      background:    '#0a0a0a',
    }}>

      {/* ── Header ── */}
      <div style={{
        padding:      '14px 20px',
        background:   '#111111',
        borderBottom: '1px solid #222',
        display:      'flex',
        alignItems:   'center',
        gap:          '12px',
        flexShrink:   0,
      }}>
        <div style={{ fontSize: '24px' }}>😈😇</div>
        <div>
          <div style={{ fontWeight: 700, fontSize: '16px' }}>
            The Devil & The Advocate
          </div>
          <div style={{ fontSize: '12px', color: '#666' }}>
            {status === 'idle'      && 'Enter a topic to start a debate'}
            {status === 'connecting'&& 'Connecting...'}
            {status === 'debating'  && `Debating: ${topic}`}
            {status === 'done'      && `Debate over${winner ? ` — ${winner === 'devil' ? '😈 The Devil' : winner === 'advocate' ? '😇 The Advocate' : '🤝 Draw'} wins!` : ''}`}
            {status === 'error'     && 'Something went wrong'}
          </div>
        </div>

        {/* Online indicators */}
        <div style={{
          marginLeft: 'auto',
          display:    'flex',
          gap:        '12px',
          fontSize:   '12px',
          color:      '#666',
        }}>
          <span>😈 <span style={{ color: '#ff4444' }}>Devil</span></span>
          <span>😇 <span style={{ color: '#4488ff' }}>Advocate</span></span>
          <span>⚖️ <span style={{ color: '#44bb44' }}>Judge</span></span>
        </div>
      </div>

      {/* ── Chat area ── */}
      <div style={{
        flex:       1,
        overflowY:  'auto',
        padding:    '12px 0',
        display:    'flex',
        flexDirection: 'column',
        gap:        '4px',
      }}>

        {/* Empty state */}
        {messages.length === 0 && status === 'idle' && (
          <div style={{
            flex:           1,
            display:        'flex',
            flexDirection:  'column',
            alignItems:     'center',
            justifyContent: 'center',
            color:          '#333',
            gap:            '12px',
          }}>
            <div style={{ fontSize: '48px' }}>😈⚖️😇</div>
            <div style={{ fontSize: '16px' }}>
              Drop a topic. Watch the chaos unfold.
            </div>
          </div>
        )}

        {/* Messages */}
        {messages.map((msg, i) => (
          <ChatBubble
            key={i}
            event={msg}
            isNew={msg.isNew}
          />
        ))}

        {/* Typing indicator */}
        {typing && <TypingIndicator agent={typing} />}

        {/* Thinking indicator — shows when LLM is working */}
        {status === 'debating' && !typing && messages.length > 0 && (
          <div style={{
            display:        'flex',
            justifyContent: 'center',
            padding:        '8px',
          }}>
            <div style={{
              fontSize:     '12px',
              color:        '#444',
              background:   '#111',
              padding:      '4px 12px',
              borderRadius: '20px',
              animation:    'fadeIn 0.3s ease',
            }}>
              thinking...
            </div>
          </div>
        )}
        
        {/* Scroll anchor */}
        <div ref={bottomRef} />
      </div>

      {/* ── Input bar ── */}
      <div style={{
        padding:      '12px 16px',
        background:   '#111111',
        borderTop:    '1px solid #222',
        display:      'flex',
        gap:          '10px',
        flexShrink:   0,
      }}>
        <input
          type="text"
          value={topic}
          onChange={e => setTopic(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Enter a debate topic... e.g. Is social media good for society?"
          disabled={status === 'debating' || status === 'connecting'}
          style={{
            flex:         1,
            background:   '#1a1a1a',
            border:       '1px solid #333',
            borderRadius: '24px',
            padding:      '10px 18px',
            color:        '#ffffff',
            fontSize:     '14px',
            outline:      'none',
          }}
        />
        {status === 'debating' ? (
          <button
            onClick={stopDebate}
            style={{
              background:   '#440000',
              border:       '1px solid #ff4444',
              borderRadius: '24px',
              padding:      '10px 20px',
              color:        '#ff4444',
              fontSize:     '14px',
              cursor:       'pointer',
              whiteSpace:   'nowrap',
            }}
          >
            Stop
          </button>
        ) : (
          <button
            onClick={handleStart}
            disabled={!topic.trim() || status === 'connecting'}
            style={{
              background:   topic.trim() ? '#1a3a1a' : '#111',
              border:       `1px solid ${topic.trim() ? '#44bb44' : '#333'}`,
              borderRadius: '24px',
              padding:      '10px 20px',
              color:        topic.trim() ? '#44bb44' : '#444',
              fontSize:     '14px',
              cursor:       topic.trim() ? 'pointer' : 'default',
              whiteSpace:   'nowrap',
            }}
          >
            Start Debate 🔥
          </button>
        )}
      </div>

      {/* CSS animations */}
      <style>{`
        @keyframes slideIn {
          from { opacity: 0; transform: translateY(10px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        @keyframes fadeIn {
          from { opacity: 0; }
          to   { opacity: 1; }
        }
        @keyframes popIn {
          from { transform: scale(0.5); opacity: 0; }
          to   { transform: scale(1);   opacity: 1; }
        }
        @keyframes bounce {
          0%, 100% { transform: translateY(0); }
          50%       { transform: translateY(-4px); }
        }
        input::placeholder { color: #444; }
        input:focus { border-color: #555 !important; }
      `}</style>

    </div>
  )
}