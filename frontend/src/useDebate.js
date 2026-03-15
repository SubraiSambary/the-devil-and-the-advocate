// =====================================================
// useDebate.js — WebSocket connection hook
// =====================================================
// A React "hook" is a function that manages state and
// side effects for a component. Custom hooks start
// with "use" by convention.
// =====================================================

import { useState, useRef, useCallback } from 'react'

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/debate'

export default function useDebate() {
  const [messages,  setMessages]  = useState([])   // all debate messages
  const [typing,    setTyping]    = useState(null)  // who is typing right now
  const [status,    setStatus]    = useState('idle') // idle | connecting | debating | done | error
  const [winner,    setWinner]    = useState(null)  // 'devil' | 'advocate' | 'draw'
  const wsRef = useRef(null)                         // holds the WebSocket object

  // Determine who speaks next (for typing indicator)
  const TURN_ORDER = ['devil', 'advocate', 'judge']

  const startDebate = useCallback((topic) => {
    // Reset everything for a fresh debate
    setMessages([])
    setTyping(null)
    setWinner(null)
    setStatus('connecting')

    // Create WebSocket connection
    const ws = new WebSocket(WS_URL)
    wsRef.current = ws

    ws.onopen = () => {
      setStatus('debating')
      // Send the topic to the backend
      ws.send(JSON.stringify({ topic }))
    }

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)

      if (data.type === 'status') {
        // Just a status update — don't add to chat
        return
      }

      if (data.type === 'done') {
        setTyping(null)
        setStatus('done')
        return
      }

      if (data.type === 'error') {
        setTyping(null)
        setStatus('error')
        setMessages(prev => [...prev, data])
        return
      }

      if (data.type === 'verdict' && data.winner) {
        setWinner(data.winner)
      }

      // Show typing indicator briefly before the message appears
      if (data.type === 'turn' || data.type === 'opening') {
        // Figure out who speaks next after this
        const nextAgent = data.agent === 'devil' ? 'advocate' : 'devil'
        setTimeout(() => setTyping(nextAgent), 500)
        setTimeout(() => setTyping(null), 2000)
      }

      if (data.type === 'judge') {
        setTimeout(() => setTyping(null), 500)
      }

      // Play audio if available
      if (data.audioUrl) {
        const audio = new Audio(data.audioUrl)
        audio.play().catch(() => {})  // ignore autoplay errors
      }

      // Add message to chat
      setMessages(prev => [...prev, { ...data, isNew: true }])
    }

    ws.onerror = () => {
      setStatus('error')
      setTyping(null)
    }

    ws.onclose = () => {
      if (status !== 'done') setStatus('idle')
    }
  }, [])

  const stopDebate = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    setStatus('idle')
    setTyping(null)
  }, [])

  return { messages, typing, status, winner, startDebate, stopDebate }
}