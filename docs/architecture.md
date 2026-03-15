# The Devil & The Advocate — Architecture

## The three characters
- 😈 Devil — argues all cons, sarcastic, relentless
- 😇 Advocate — argues all pros, passionate, never gives up  
- ⚖️ Judge — watches silently, declares winner at the end

## Tech stack
- Backend: Python + FastAPI + WebSockets
- AI: Ollama running LLaMA 3.1 8B locally
- Frontend: React
- Voice: edge-tts (free, no API key)

## How it works
1. User types a topic
2. Backend starts a debate session
3. Devil and Advocate take turns arguing
4. Each turn streams to browser via WebSocket
5. Judge gives final verdict