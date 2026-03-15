# =============================================================
# tts.py — Text to speech using edge-tts v7+
# =============================================================

import edge_tts


async def generate_speech(text: str, voice: str, output_path: str) -> None:
    """
    Converts text to speech and saves it as an MP3 file.

    Parameters:
        text        — the words to speak
        voice       — edge-tts voice name
        output_path — where to save the MP3

    Voice options:
        Devil     → "en-US-GuyNeural"
        Advocate  → "en-US-JennyNeural"
        Judge     → "en-US-ChristopherNeural"
    """
    communicate = edge_tts.Communicate(text=text, voice=voice)
    await communicate.save(output_path)