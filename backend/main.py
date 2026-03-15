# =============================================================
# main.py — FastAPI server with WebSocket endpoint
# =============================================================
#
# PYTHON LESSON: This file teaches you:
# - What a web server is and how FastAPI creates one
# - What a WebSocket is vs regular HTTP
# - How to handle errors with try/except
# - What JSON is and how Python converts to/from it
# - What __name__ == "__main__" means
# =============================================================

import os
import json
import asyncio
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from agents import DebateSession
from tts import generate_speech

load_dotenv()

# =============================================================
# PYTHON LESSON: Creating the FastAPI app
# --------------------------------------------------------------
# FastAPI() creates the web application object.
# Everything in this file attaches to this object —
# routes, middleware, static files, etc.
# =============================================================

app = FastAPI(
    title="The Devil & The Advocate",
    description="Two AI agents debate any topic 😈😇",
    version="1.0.0",
)

# =============================================================
# PYTHON LESSON: Middleware
# --------------------------------------------------------------
# Middleware runs on EVERY request before your code sees it.
# Think of it as a security guard at the door.
#
# CORS (Cross-Origin Resource Sharing) is a browser security
# rule. Your React app runs on localhost:5173 and your backend
# runs on localhost:8000 — those are different "origins".
# Without CORS middleware, the browser blocks the connection.
# This middleware tells the browser: "it's okay, I allow this."
# =============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],    # allow all origins (fine for development)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create the audio folder if it doesn't exist
# parents=True — also create any missing parent folders
# exist_ok=True — don't crash if it already exists
Path("audio").mkdir(parents=True, exist_ok=True)

# Serve audio files so the browser can fetch them by URL
# e.g. http://localhost:8000/audio/devil_round1.mp3
app.mount("/audio", StaticFiles(directory="audio"), name="audio")


# =============================================================
# HTTP routes — regular request/response endpoints
# =============================================================

@app.api_route("/", methods=["GET", "HEAD"])
async def root():
    """Health check endpoint."""
    return {"status": "running", "app": "The Devil & The Advocate 😈😇"}


@app.get("/health")
async def health():
    """Used by Render.com to check if the server is alive."""
    return {"status": "healthy"}

@app.get("/audio-test")
async def audio_test():
    """Lists all generated audio files."""
    audio_dir = Path(__file__).parent / "audio"
    if not audio_dir.exists():
        return {"error": "audio folder does not exist"}
    files = list(audio_dir.glob("*.mp3"))
    return {
        "folder": str(audio_dir),
        "count": len(files),
        "files": [f.name for f in files[-5:]]  # last 5 files
    }

# =============================================================
# WebSocket endpoint — the heart of the app
# =============================================================

@app.websocket("/debate")
async def debate_websocket(websocket: WebSocket):
    """
    Handles one complete debate session over WebSocket.

    PYTHON LESSON: WebSocket vs HTTP
    --------------------------------------------------------------
    HTTP  → browser asks a question, server answers, done.
             Like sending a letter and getting one reply.

    WebSocket → connection stays open, both sides can send
                messages at any time, in any order.
                Like a phone call that stays connected.

    Our debate needs WebSocket because:
    - We need to stream 20+ messages over several minutes
    - We want the browser to receive each message the moment
      it's ready, not wait for the entire debate to finish

    PYTHON LESSON: try/except/finally
    --------------------------------------------------------------
    try:        run this code
    except X:   if error X happens, run this instead
    finally:    ALWAYS run this, whether error happened or not

    WebSocketDisconnect is raised when the user closes their
    browser tab. Without catching it, the server would crash.
    --------------------------------------------------------------
    """
    # Accept the WebSocket connection (complete the handshake)
    await websocket.accept()

    try:
        # Step 1: Receive the topic from the browser
        raw_message = await websocket.receive_text()

        # PYTHON LESSON: JSON
        # --------------------------------------------------------------
        # JSON is a text format for sending structured data over networks.
        # It looks like a Python dict: {"key": "value"}
        #
        # json.loads()  converts a JSON string → Python dict
        # json.dumps()  converts a Python dict → JSON string
        # --------------------------------------------------------------
        data  = json.loads(raw_message)
        topic = data.get("topic", "").strip()

        # Validate — don't start if topic is empty
        if not topic:
            await websocket.send_text(json.dumps({
                "type": "error",
                "text": "Please enter a debate topic!"
            }))
            return

        # Step 2: Tell the browser we're starting
        await websocket.send_text(json.dumps({
            "type":  "status",
            "text":  f"Starting debate: {topic}"
        }))

        # Step 3: Create a debate session and run it
        session = DebateSession(topic=topic)

        # async for loops over the values yielded by session.run()
        # Each yielded value is one debate event (a message, reaction, etc.)
        async for event in session.run():

            # Step 4: Generate voice audio for main messages
            if event.get("type") in ("opening", "turn", "verdict", "judge"):
                audio_url = await _make_audio(event)
                if audio_url:
                    event["audioUrl"] = audio_url

            # Step 5: Send the event to the browser as JSON
            await websocket.send_text(json.dumps(event))

            # Small breathing room between messages
            await asyncio.sleep(0.05)

    except WebSocketDisconnect:
        # User closed browser tab — totally normal, not an error
        print("Client disconnected")

    except Exception as e:
        # Something unexpected went wrong
        print(f"Error during debate: {e}")
        try:
            await websocket.send_text(json.dumps({
                "type": "error",
                "text": f"Something went wrong: {str(e)}"
            }))
        except Exception:
            pass    # connection might already be closed


# =============================================================
# Helper functions
# =============================================================

async def _make_audio(event: dict) -> str:
    """Generates TTS audio and returns the URL for the browser."""

    voices = {
        "devil":    "en-US-GuyNeural",
        "advocate": "en-US-JennyNeural",
        "judge":    "en-US-ChristopherNeural",
    }

    agent     = event.get("agent", "")
    text      = event.get("text", "")
    round_num = event.get("round", 0)

    if not text or len(text.strip()) < 3:
        return ""

    voice    = voices.get(agent, "en-US-GuyNeural")

    # Use absolute path so it works regardless of where Python is run from
    base_dir = Path(__file__).parent
    audio_dir = base_dir / "audio"
    audio_dir.mkdir(exist_ok=True)

    filename     = f"{agent}_r{round_num}_{abs(hash(text)) % 100000}.mp3"
    full_path    = audio_dir / filename
    browser_url  = f"/audio/{filename}"

    try:
        await generate_speech(text=text, voice=voice, output_path=str(full_path))
        return browser_url
    except Exception as e:
        print(f"TTS failed for {agent}: {e}")
        return ""


# =============================================================
# PYTHON LESSON: __name__ == "__main__"
# --------------------------------------------------------------
# When you run `python main.py` directly, Python sets the
# special variable __name__ to the string "__main__".
#
# When another file imports this file, __name__ is set to
# "main" (the module name) — NOT "__main__".
#
# So this block only runs when you execute this file directly.
# It won't run if someone imports it. This is the standard
# Python pattern for "run only when executed directly."
# =============================================================

if __name__ == "__main__":
    import uvicorn

    # Render.com sets PORT automatically — we read it here
    # so the same code works both locally and in the cloud
    port = int(os.getenv("PORT", "8000"))

    uvicorn.run(
        "main:app",       # "filename:variable_name"
        host="0.0.0.0",   # listen on all network interfaces
        port=port,
        reload=True,      # auto-restart when you save a file (dev only)
    )