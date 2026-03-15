// =====================================================
// ChatBubble.jsx
// Renders one message in the group chat
// =====================================================

// Agent configuration — colors, names, emojis
const AGENTS = {
  devil: {
    name:   'The Devil',
    emoji:  '😈',
    color:  '#ff4444',
    bg:     '#2a1010',
    side:   'left',
  },
  advocate: {
    name:   'The Advocate',
    emoji:  '😇',
    color:  '#4488ff',
    bg:     '#101828',
    side:   'right',
  },
  judge: {
    name:   'The Judge',
    emoji:  '⚖️',
    color:  '#44bb44',
    bg:     '#101a10',
    side:   'left',
  },
}

export default function ChatBubble({ event, isNew }) {
  const agent  = AGENTS[event.agent] || AGENTS.judge
  const isLeft = agent.side === 'left'

  // Reaction messages — just an emoji, shown inline small
  if (event.type === 'reaction') {
    return (
      <div style={{
        display:    'flex',
        justifyContent: isLeft ? 'flex-start' : 'flex-end',
        padding:    '2px 16px',
      }}>
        <span style={{
          fontSize:   '20px',
          opacity:    0.85,
          animation:  isNew ? 'popIn 0.2s ease' : 'none',
        }}>
          {event.text}
        </span>
      </div>
    )
  }

  // Judge short mid-debate comment — centered
  if (event.type === 'judge' && !event.winner) {
    return (
      <div style={{
        display:        'flex',
        justifyContent: 'center',
        padding:        '6px 16px',
      }}>
        <div style={{
          background:   '#1a1a1a',
          border:       '1px solid #333',
          borderRadius: '20px',
          padding:      '4px 14px',
          fontSize:     '13px',
          color:        '#888',
          animation:    isNew ? 'fadeIn 0.3s ease' : 'none',
        }}>
          ⚖️ {event.text}
        </div>
      </div>
    )
  }

  // Final verdict — full width special card
  if (event.type === 'verdict') {
    return (
      <div style={{
        margin:       '16px',
        background:   '#1a1a0a',
        border:       '1px solid #554400',
        borderRadius: '12px',
        padding:      '16px',
        animation:    isNew ? 'fadeIn 0.5s ease' : 'none',
      }}>
        <div style={{
          fontSize:     '12px',
          color:        '#aa8800',
          fontWeight:   600,
          marginBottom: '8px',
          letterSpacing: '0.05em',
        }}>
          ⚖️ FINAL VERDICT
          {event.winner && event.winner !== 'draw' && (
            <span style={{ marginLeft: '8px', color: '#ffcc00' }}>
              🏆 {event.winner === 'devil' ? 'The Devil wins' : 'The Advocate wins'}
            </span>
          )}
        </div>
        <div style={{
          fontSize:   '14px',
          color:      '#dddddd',
          lineHeight: 1.7,
          whiteSpace: 'pre-wrap',
        }}>
          {event.text}
        </div>
      </div>
    )
  }

  // Regular message bubble (opening or turn)
  return (
    <div style={{
      display:        'flex',
      flexDirection:  isLeft ? 'row' : 'row-reverse',
      alignItems:     'flex-end',
      gap:            '8px',
      padding:        '4px 16px',
      animation:      isNew ? 'slideIn 0.3s ease' : 'none',
    }}>

      {/* Avatar circle */}
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

      {/* Bubble */}
      <div style={{ maxWidth: '72%' }}>

        {/* Name + timestamp */}
        <div style={{
          display:        'flex',
          alignItems:     'center',
          gap:            '6px',
          marginBottom:   '3px',
          flexDirection:  isLeft ? 'row' : 'row-reverse',
        }}>
          <span style={{
            fontSize:   '12px',
            fontWeight: 600,
            color:      agent.color,
          }}>
            {agent.name}
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
        </div>

        {/* Message text */}
        <div style={{
          background:   agent.bg,
          border:       `1px solid ${agent.color}22`,
          borderRadius: isLeft ? '4px 16px 16px 16px' : '16px 4px 16px 16px',
          padding:      '10px 14px',
          fontSize:     '14px',
          lineHeight:   1.6,
          color:        '#eeeeee',
          whiteSpace:   'pre-wrap',
          wordBreak:    'word-break',
        }}>
          {event.text}
        </div>

      </div>
    </div>
  )
}