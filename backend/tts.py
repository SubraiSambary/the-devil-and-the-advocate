# =============================================================
# tts.py — Text to speech
# Local:  edge-tts (better quality, Microsoft voices)
# Cloud:  gTTS (Google TTS, works on all servers)
# =============================================================

import os
import asyncio
from dotenv import load_dotenv
load_dotenv()

MODE = os.getenv("MODE", "local")

GTTS_LANGS = {
    "devil":    {"lang": "en", "tld": "co.uk", "slow": False},  # British male
    "advocate": {"lang": "en", "tld": "co.in", "slow": False},  # Indian male
    "judge":    {"lang": "en", "tld": "ca",     "slow": False}, # Canadian male
}

VOICE_MAP = {
    "en-US-GuyNeural":         "devil",
    "en-US-JennyNeural":       "advocate",
    "en-US-ChristopherNeural": "judge",
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
    """Google TTS — works on cloud servers, completely free."""
    from gtts import gTTS

    character = VOICE_MAP.get(voice, "devil")
    settings  = GTTS_LANGS.get(character, GTTS_LANGS["devil"])

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
    """Microsoft Edge TTS — better quality, local development only."""
    import edge_tts
    communicate = edge_tts.Communicate(text=text, voice=voice)
    await communicate.save(output_path)