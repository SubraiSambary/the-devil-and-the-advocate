# =============================================================
# tts.py — Text to speech using edge-tts
# =============================================================
# edge-tts is completely free. No API key needed.
# It uses Microsoft Edge's built-in voices — 300+ options.
# Works locally and on cloud servers with no setup.
# =============================================================

import edge_tts


async def generate_speech(text: str, voice: str, output_path: str) -> None:
    """
    Converts text to speech and saves it as an MP3 file.

    Parameters:
        text        — the words to speak
        voice       — edge-tts voice name
        output_path — where to save the MP3

    Voice options for our characters:
        Devil     → "en-US-GuyNeural"          deep, gruff American male
        Devil alt → "en-GB-RyanNeural"          dry British male
        Advocate  → "en-US-JennyNeural"         bright, warm American female
        Advocate  → "en-US-AriaNeural"          expressive, upbeat
        Judge     → "en-US-ChristopherNeural"   calm, measured
        Judge alt → "en-GB-SoniaNeural"         cool, authoritative British
    """
    communicate = edge_tts.Communicate(text=text, voice=voice)
    await communicate.save(output_path)
