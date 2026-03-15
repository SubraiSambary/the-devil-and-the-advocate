# =============================================================
# tts.py — Text to speech
# Local:  edge-tts (better quality, Microsoft voices)
# Cloud:  gTTS (Google TTS, works on all servers)
# =============================================================

import os
from dotenv import load_dotenv
load_dotenv()

MODE = os.getenv("MODE", "local")

# Voice speed and tone per character using gTTS
# gTTS doesn't support different voices natively
# but we can use different languages/accents as a workaround
GTTS_LANGS = {
    "devil":    {"lang": "en", "tld": "co.uk", "slow": False},  # British accent — gruff
    "advocate": {"lang": "en", "tld": "com",   "slow": False},  # American — upbeat
    "judge":    {"lang": "en", "tld": "com.au", "slow": False}, # Australian — calm
}


async def generate_speech(text: str, voice: str, output_path: str) -> None:
    """
    Converts text to speech and saves as MP3.
    Uses edge-tts locally, gTTS on cloud deployment.
    """
    if MODE == "cloud":
        await _gtts_speech(text, voice, output_path)
    else:
        await _edge_tts_speech(text, voice, output_path)


async def _gtts_speech(text: str, voice: str, output_path: str) -> None:
    """
    Google TTS — works on cloud servers, completely free.
    Different accents give each character a distinct sound.
    """
    import asyncio
    from gtts import gTTS

    # Map edge-tts voice names to gTTS accent settings
    accent_map = {
        "en-US-GuyNeural":          GTTS_LANGS["devil"],
        "en-US-JennyNeural":        GTTS_LANGS["advocate"],
        "en-US-ChristopherNeural":  GTTS_LANGS["judge"],
    }
    settings = accent_map.get(voice, GTTS_LANGS["devil"])

    # gTTS is synchronous so we run it in a thread
    def _generate():
        tts = gTTS(
            text=text,
            lang=settings["lang"],
            tld=settings["tld"],
            slow=settings["slow"]
        )
        tts.save(output_path)

    await asyncio.to_thread(_generate)


async def _edge_tts_speech(text: str, voice: str, output_path: str) -> None:
    """
    Microsoft Edge TTS — better quality, for local development only.
    """
    import edge_tts
    communicate = edge_tts.Communicate(text=text, voice=voice)
    await communicate.save(output_path)