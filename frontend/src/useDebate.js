// =====================================================
// useDebate.js — WebSocket connection hook
// =====================================================

import { useState, useRef, useCallback } from 'react'

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/debate'

export default function useDebate() {
  const [messages,  setMessages]  = useState([])
  const [typing,    setTyping]    = useState(null)
  const [status,    setStatus]    = useState('idle')
  const [winner,    setWinner]    = useState(null)
  const wsRef        = useRef(null)
  const typingTimer  = useRef(null)   // tracks the typing indicator timer

  // Helper — show typing indicator for a given agent
  // then auto-clear after `duration` milliseconds
  const showTyping = (agent, duration = 2500) => {
    // Cancel any existing timer first
    if (typingTimer.current) {
      clearTimeout(typingTimer.current)
    }
    setTyping(agent)
    typingTimer.current = setTimeout(() => {
      setTyping(null)
    }, duration)
  }

  const clearTyping = () => {
    if (typingTimer.current) {
      clearTimeout(typingTimer.current)
      typingTimer.current = null
    }
    setTyping(null)
  }

  const startDebate = useCallback((topic) => {
    setMessages([])
    clearTyping()
    setWinner(null)
    setStatus('connecting')

    const ws = new WebSocket(WS_URL)
    wsRef.current = ws

    ws.onopen = () => {
      setStatus('debating')
      ws.send(JSON.stringify({ topic }))
      // Show Devil typing first — they always open
      showTyping('devil', 3000)
    }

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)

      if (data.type === 'status') return

      if (data.type === 'done') {
        clearTyping()
        setStatus('done')
        return
      }

      if (data.type === 'error') {
        clearTyping()
        setStatus('error')
        setMessages(prev => [...prev, data])
        return
      }

      if (data.type === 'verdict' && data.winner) {
        setWinner(data.winner)
      }

      // When a real message arrives, clear typing indicator
      // then immediately show the NEXT agent typing
      if (data.type === 'opening' || data.type === 'turn') {
        clearTyping()

        // Show the other agent typing while we wait for their reply
        const nextAgent = data.agent === 'devil' ? 'advocate' : 'devil'
        // Small delay before showing next typing indicator
        setTimeout(() => showTyping(nextAgent, 4000), 400)
      }

      if (data.type === 'judge') {
        clearTyping()
      }

      if (data.type === 'verdict') {
        clearTyping()
      }

      // Play audio if available
      if (data.audioUrl) {
        const audio = new Audio(data.audioUrl)
        audio.play().catch(() => {})
      }

      // Add message to chat
      setMessages(prev => [...prev, { ...data, isNew: true }])
    }

    ws.onerror = () => {
      setStatus('error')
      clearTyping()
    }

    ws.onclose = () => {
      clearTyping()
      if (status !== 'done') setStatus('idle')
    }
  }, [])

  const stopDebate = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    clearTyping()
    setStatus('idle')
  }, [])

  return { messages, typing, status, winner, startDebate, stopDebate }
}