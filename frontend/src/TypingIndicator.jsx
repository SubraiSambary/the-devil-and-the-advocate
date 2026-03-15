// =====================================================
// TypingIndicator.jsx
// Shows "Devil is typing..." with animated dots
// =====================================================

const AGENTS = {
  devil:    { name: 'The Devil',    emoji: '😈', color: '#ff4444' },
  advocate: { name: 'The Advocate', emoji: '😇', color: '#4488ff' },
  judge:    { name: 'The Judge',    emoji: '⚖️', color: '#44bb44' },
}

export default function TypingIndicator({ agent }) {
  const config = AGENTS[agent] || AGENTS.devil

  return (
    <div style={{
      display:    'flex',
      alignItems: 'center',
      gap:        '8px',
      padding:    '6px 16px',
      animation:  'fadeIn 0.2s ease',
    }}>

      {/* Avatar */}
      <div style={{
        width:          '28px',
        height:         '28px',
        borderRadius:   '50%',
        border:         `2px solid ${config.color}`,
        display:        'flex',
        alignItems:     'center',
        justifyContent: 'center',
        fontSize:       '14px',
      }}>
        {config.emoji}
      </div>

      {/* Name + dots */}
      <div style={{
        display:      'flex',
        alignItems:   'center',
        gap:          '6px',
        background:   '#1a1a1a',
        borderRadius: '20px',
        padding:      '5px 12px',
      }}>
        <span style={{ fontSize: '12px', color: '#666' }}>
          {config.name} is typing
        </span>
        <div style={{ display: 'flex', gap: '3px', alignItems: 'center' }}>
          <span style={{ animation: 'bounce 1s infinite 0.0s',
                         display: 'inline-block', color: '#666',
                         fontSize: '18px', lineHeight: 1 }}>.</span>
          <span style={{ animation: 'bounce 1s infinite 0.2s',
                         display: 'inline-block', color: '#666',
                         fontSize: '18px', lineHeight: 1 }}>.</span>
          <span style={{ animation: 'bounce 1s infinite 0.4s',
                         display: 'inline-block', color: '#666',
                         fontSize: '18px', lineHeight: 1 }}>.</span>
        </div>
      </div>

    </div>
  )
}