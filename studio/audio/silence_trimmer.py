"""Trim leading/trailing silence and probe duration via FFmpeg."""

from __future__ import annotations

import os

from studio.core.proc import run_command


class SilenceTrimmer:
    """Uses FFmpeg to accurately trim head and tail silence and probe duration."""

    @staticmethod
    def trim_silence(input_path: str, output_path: str, threshold_db: float = -45.0) -> float:
        if not os.path.isfile(input_path):
            raise FileNotFoundError(f"TTS output not found: {input_path}")
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        af_filter = (
            f"silenceremove=start_periods=1:start_duration=0.01:start_threshold={threshold_db}dB,"
            f"areverse,silenceremove=start_periods=1:start_duration=0.01:start_threshold={threshold_db}dB,areverse"
        )
        run_command([
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-i", input_path,
            "-af", af_filter,
            output_path,
        ])
        return SilenceTrimmer.get_duration(output_path)

    @staticmethod
    def get_duration(audio_path: str) -> float:
        result = run_command([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", audio_path,
        ])
        text = (result.stdout or "").strip()
        try:
            return float(text)
        except ValueError as exc:
            raise RuntimeError(f"Could not parse duration from ffprobe for {audio_path}: {text!r}") from exc
