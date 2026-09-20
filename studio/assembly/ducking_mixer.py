"""BGM sidechain ducking: compress music when voice is present."""

from __future__ import annotations

import os

from studio.core.proc import require_ffmpeg, run_command


class DuckingMixer:
    """Duck BGM from idle_volume (~25%) toward ducked_volume (~12%) while speech is present."""

    @staticmethod
    def build_filter_complex(
        ducked_volume: float = 0.12,
        idle_volume: float = 0.25,
    ) -> str:
        if idle_volume <= 0:
            raise ValueError("idle_volume must be > 0")
        if ducked_volume <= 0:
            raise ValueError("ducked_volume must be > 0")
        if ducked_volume >= idle_volume:
            raise ValueError("ducked_volume must be < idle_volume (talking quieter than pauses)")

        # BGM sits at idle_volume; compressor uses voice as the key (second input).
        # Ratio tracks the idle/ducked span so both yaml knobs appear in the graph.
        ratio = max(2.0, min(20.0, (idle_volume / ducked_volume) * 4.0))
        return (
            f"[1:a]aresample=44100,aformat=channel_layouts=stereo,"
            f"volume={idle_volume}[bgm];"
            f"[0:a]aresample=44100,aformat=channel_layouts=stereo[voice];"
            f"[bgm][voice]sidechaincompress=threshold=0.05:ratio={ratio:.3f}:"
            f"attack=30:release=350:level_sc=1[ducked];"
            f"[voice][ducked]amix=inputs=2:duration=first:dropout_transition=0:"
            f"normalize=0,alimiter=limit=0.98[aout]"
        )

    @staticmethod
    def mix(
        video_input: str,
        bgm_input: str,
        output_path: str,
        ducked_volume: float = 0.12,
        idle_volume: float = 0.25,
    ) -> str:
        require_ffmpeg()
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        filter_complex = DuckingMixer.build_filter_complex(ducked_volume, idle_volume)
        cmd = [
            "ffmpeg", "-y",
            "-hide_banner", "-loglevel", "error",
            "-i", video_input,
            "-stream_loop", "-1",
            "-i", bgm_input,
            "-filter_complex", filter_complex,
            "-map", "0:v",
            "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "320k",
            "-movflags", "+faststart",
            "-shortest",
            output_path,
        ]
        run_command(cmd)
        return output_path
