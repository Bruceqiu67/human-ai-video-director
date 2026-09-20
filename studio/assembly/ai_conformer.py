"""Conforms external AI-generated video clips (1080x1920, 30fps) and locks with master audio."""

from __future__ import annotations

import os
from studio.audio.silence_trimmer import SilenceTrimmer
from studio.core.proc import run_command


class AIConformer:
    """Conforms one or more external AI video clips to project standard and remuxes with master audio.

    Guarantees:
    1. Zero voiceover loss: Audio duration is the absolute source of truth.
    2. Zero black frame or abrupt truncation: If video is shorter than audio, last frame clones smoothly via tpad.
    3. Unified geometry and timebase: All clips scaled/cropped to width x height, setsar=1, 30fps, yuv420p.
    4. Multi-pose clip assembly: Multi-pose clips are concatenated seamlessly in order before audio lock.
    """

    @classmethod
    def conform_and_remux(
        cls,
        video_clips: list[str],
        output_path: str,
        master_audio: str | None = None,
        width: int = 1080,
        height: int = 1920,
        fps: int = 30,
    ) -> str:
        if not video_clips:
            raise ValueError("No video clips provided for AI conforming.")

        for clip in video_clips:
            if not os.path.isfile(clip):
                raise FileNotFoundError(f"AI video clip not found: {clip}")

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        num_clips = len(video_clips)

        # Build FFmpeg command
        cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]
        for clip in video_clips:
            cmd.extend(["-i", clip])

        filter_parts = []
        for i in range(num_clips):
            filter_parts.append(
                f"[{i}:v]scale={width}:{height}:force_original_aspect_ratio=increase,"
                f"crop={width}:{height},setsar=1,fps={fps},format=yuv420p[v{i}]"
            )

        if num_clips == 1:
            concat_label = "[v0]"
        else:
            joined_labels = "".join(f"[v{i}]" for i in range(num_clips))
            filter_parts.append(f"{joined_labels}concat=n={num_clips}:v=1:a=0[vconcat]")
            concat_label = "[vconcat]"

        if master_audio and os.path.isfile(master_audio):
            audio_idx = num_clips
            cmd.extend(["-i", master_audio])
            audio_dur = SilenceTrimmer.get_duration(master_audio)
            if audio_dur <= 0.05:
                raise RuntimeError(f"Master audio too short ({audio_dur:.3f}s): {master_audio}")

            # Pad with cloned last frame in case video is shorter than audio
            filter_parts.append(f"{concat_label}tpad=stop_mode=clone:stop_duration=180[vfinal]")
            filter_str = ";".join(filter_parts)

            cmd.extend([
                "-filter_complex", filter_str,
                "-map", "[vfinal]",
                "-map", f"{audio_idx}:a",
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "18",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-b:a", "192k",
                "-t", f"{audio_dur:.3f}",
                output_path,
            ])
        else:
            # No master audio: output conformed video as-is
            filter_str = ";".join(filter_parts)
            cmd.extend([
                "-filter_complex", filter_str,
                "-map", concat_label,
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "18",
                "-pix_fmt", "yuv420p",
                output_path,
            ])

        run_command(cmd)
        return output_path
