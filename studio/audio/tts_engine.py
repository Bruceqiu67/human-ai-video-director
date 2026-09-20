"""Edge-TTS wrapper. Global rate only — never per-sentence atempo."""

from __future__ import annotations

import os

import edge_tts


class TTSEngine:
    """Wrapper around Edge-TTS for synthesizing clean speech audio segments."""

    def __init__(self, voice: str = "zh-CN-YunxiNeural", rate: str = "+20%"):
        self.voice = voice
        self.rate = rate

    async def synthesize(self, text: str, output_mp3_path: str) -> str:
        cleaned = (text or "").strip()
        if not cleaned:
            raise ValueError("Cannot synthesize empty dialogue text.")
        os.makedirs(os.path.dirname(os.path.abspath(output_mp3_path)), exist_ok=True)
        comm = edge_tts.Communicate(cleaned, self.voice, rate=self.rate)
        await comm.save(output_mp3_path)
        return output_mp3_path
