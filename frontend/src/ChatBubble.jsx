// =====================================================
// ChatBubble.jsx
// =====================================================

const AGENTS = {
  devil: {
    name:  'The Devil',
    emoji: '😈',
    color: '#ff4444',
    bg:    '#2a1010',
    side:  'left',
  },
  advocate: {
    name:  'The Advocate',
    emoji: '😇',
    color: '#4488ff',
    bg:    '#101828',
    side:  'right',
  },
  judge: {
    name:  'The Judge',
    emoji: '⚖️',
    color: '#44bb44',
    bg:    '#101a10',
    side:  'left',
  },
}

// Renders **bold** markdown inline
function RenderText({ text, bold = false }) {
  if (!bold || !text.includes('**')) {
    return (
      <span style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
        {text}
      </span>
    )
  }
  const parts = text.split(/\*\*(.*?)\*\*/g)
  return (
    <span style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
      {parts.map((part, i) =>
        i % 2 === 1
          ? <strong key={i} style={{ color: '#ffffff', fontWeight: 700 }}>{part}</strong>
          : <span key={i}>{part}</span>
      )}
    </span>
  )
}

export default function ChatBubble({ event, isNew }) {
  const agent  = AGENTS[event.agent] || AGENTS.judge
  const isLeft = agent.side === 'left'
  const isVerdict = event.type === 'verdict'

  // Skip empty messages entirely
  if (!event.text || event.text.trim().length < 4 || event.text.trim() === '...') return null

  // ── Emoji reaction ──
  if (event.type === 'reaction') {
    return (
      <div style={{
        display:        'flex',
        justifyContent: isLeft ? 'flex-start' : 'flex-end',
        padding:        '1px 60px',
      }}>
        <span style={{
          fontSize:  '18px',
          opacity:   0.8,
          animation: isNew ? 'popIn 0.2s ease' : 'none',
        }}>
          {event.text}
        </span>
      </div>
    )
  }

  // ── All message types — same bubble layout ──
  return (
    <div style={{
      display:       'flex',
      flexDirection: isLeft ? 'row' : 'row-reverse',
      alignItems:    'flex-end',
      gap:           '8px',
      padding:       '4px 16px',
      animation:     isNew ? 'slideIn 0.3s ease' : 'none',
    }}>

      {/* Avatar */}
      <div style={{
        width:          '36px',
        height:         '36px',
        borderRadius:   '50%',
        background:     agent.bg,
        border:         `2px solid ${agent.color}`,
        display:        'flex',
        alignItems:     'center',
        justifyContent: 'center',
        fontSize:       '18px',
        flexShrink:     0,
      }}>
        {agent.emoji}
      </div>

      {/* Bubble content */}
      <div style={{ maxWidth: '72%' }}>

        {/* Name row */}
        <div style={{
          display:       'flex',
          alignItems:    'center',
          gap:           '6px',
          marginBottom:  '3px',
          flexDirection: isLeft ? 'row' : 'row-reverse',
        }}>
          <span style={{
            fontSize:   '12px',
            fontWeight: 600,
            color:      agent.color,
          }}>
            {agent.name}
            {isVerdict && ' — Verdict'}
          </span>
          <span style={{ fontSize: '11px', color: '#555' }}>
            {event.timestamp}
          </span>
          {event.round && (
            <span style={{
              fontSize:     '10px',
              color:        '#444',
              background:   '#1a1a1a',
              padding:      '1px 6px',
              borderRadius: '10px',
            }}>
              Round {event.round}
            </span>
          )}
          {isVerdict && event.winner && event.winner !== 'draw' && (
            <span style={{
              fontSize:     '11px',
              background:   '#2a2a00',
              color:        '#ffcc00',
              padding:      '1px 8px',
              borderRadius: '10px',
              fontWeight:   600,
            }}>
              🏆 {event.winner === 'devil' ? 'Devil wins' : 'Advocate wins'}
            </span>
          )}
        </div>

        {/* Message bubble */}
        <div style={{
          background:   isVerdict ? '#141a0a' : agent.bg,
          border:       `1px solid ${isVerdict ? '#445522' : agent.color + '33'}`,
          borderRadius: isLeft ? '4px 16px 16px 16px' : '16px 4px 16px 16px',
          padding:      isVerdict ? '14px 16px' : '10px 14px',
          fontSize:     '14px',
          lineHeight:   1.75,
          color:        '#dddddd',
        }}>
          <RenderText text={event.text} bold={isVerdict} />
        </div>

      </div>
    </div>
  )
}