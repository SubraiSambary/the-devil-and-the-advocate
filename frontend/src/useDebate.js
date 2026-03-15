import { useState, useRef, useCallback } from 'react'

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/debate'
const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

export default function useDebate() {
  const [messages,  setMessages]  = useState([])
  const [typing,    setTyping]    = useState(null)
  const [status,    setStatus]    = useState('idle')
  const [winner,    setWinner]    = useState(null)
  const wsRef         = useRef(null)
  const typingTimer   = useRef(null)
  const currentAudio  = useRef(null)
  const messageQueue  = useRef([])      // holds incoming events
  const isProcessing  = useRef(false)   // is a message currently being shown

  const showTyping = (agent, duration = 2500) => {
    if (typingTimer.current) clearTimeout(typingTimer.current)
    setTyping(agent)
    typingTimer.current = setTimeout(() => setTyping(null), duration)
  }

  const clearTyping = () => {
    if (typingTimer.current) {
      clearTimeout(typingTimer.current)
      typingTimer.current = null
    }
    setTyping(null)
  }

  // Process one message at a time from the queue
  const processNext = useCallback(() => {
    if (messageQueue.current.length === 0) {
      isProcessing.current = false
      return
    }

    isProcessing.current = true
    const data = messageQueue.current.shift()

    // Handle control messages immediately
    if (data.type === 'done') {
      clearTyping()
      setStatus('done')
      isProcessing.current = false
      return
    }

    if (data.type === 'error') {
      clearTyping()
      setStatus('error')
      setMessages(prev => [...prev, data])
      isProcessing.current = false
      return
    }

    if (data.type === 'verdict' && data.winner) {
      setWinner(data.winner)
    }

    // Update typing indicator
    if (data.type === 'opening' || data.type === 'turn') {
      clearTyping()
      const nextAgent = data.agent === 'devil' ? 'advocate' : 'devil'
      setTimeout(() => showTyping(nextAgent, 4000), 400)
    }

    if (data.type === 'judge' || data.type === 'verdict') {
      clearTyping()
    }

    // Add message to chat immediately
    setMessages(prev => {
      const isDuplicate = prev.some(m => m.text === data.text && m.agent === data.agent)
      if (isDuplicate) return prev
      return [...prev, { ...data, isNew: true }]
    })

    // If there's audio — play it fully before processing next message
    if (data.audioUrl) {
      if (currentAudio.current) {
        currentAudio.current.pause()
        currentAudio.current = null
      }
      const audio = new Audio(`${API_BASE}${data.audioUrl}`)
      currentAudio.current = audio

      audio.onended = () => {
        currentAudio.current = null
        // Small natural pause between messages
        setTimeout(() => processNext(), 300)
      }
      audio.onerror = () => {
        currentAudio.current = null
        setTimeout(() => processNext(), 300)
      }
      audio.play().catch(() => {
        // Autoplay blocked — move on after short delay
        setTimeout(() => processNext(), 500)
      })
    } else {
      // No audio — small pause then next message
      setTimeout(() => processNext(), 200)
    }
  }, [])

  const enqueue = useCallback((data) => {
    messageQueue.current.push(data)
    if (!isProcessing.current) {
      processNext()
    }
  }, [processNext])

  const startDebate = useCallback((topic) => {
    if (currentAudio.current) {
      currentAudio.current.pause()
      currentAudio.current = null
    }
    messageQueue.current = []
    isProcessing.current = false

    setMessages([])
    clearTyping()
    setWinner(null)
    setStatus('connecting')

    const ws = new WebSocket(WS_URL)
    wsRef.current = ws

    ws.onopen = () => {
      setStatus('debating')
      ws.send(JSON.stringify({ topic }))
      showTyping('devil', 3000)
    }

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type === 'status') return
      enqueue(data)
    }

    ws.onerror = () => {
      setStatus('error')
      clearTyping()
    }

    ws.onclose = () => {
      clearTyping()
    }
  }, [enqueue])

  const stopDebate = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    if (currentAudio.current) {
      currentAudio.current.pause()
      currentAudio.current = null
    }
    messageQueue.current = []
    isProcessing.current = false
    clearTyping()
    setStatus('idle')
  }, [])

  return { messages, typing, status, winner, startDebate, stopDebate }
}