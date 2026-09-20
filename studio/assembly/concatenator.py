"""Lossless concatenation of rendered scene MP4s."""

from __future__ import annotations

import os

from studio.core.proc import require_ffmpeg, run_command


class SceneConcatenator:
    """Losslessly concatenates rendered scene MP4 files using FFmpeg concat demuxer."""

    @staticmethod
    def format_concat_line(path: str) -> str:
        escaped = os.path.abspath(path).replace("\\", "/").replace("'", r"'\''")
        return f"file '{escaped}'"

    @staticmethod
    def concat(scene_mp4_paths: list[str], output_path: str) -> str:
        if not scene_mp4_paths:
            raise ValueError("No scene MP4 files provided for concatenation.")

        require_ffmpeg()
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        concat_txt = os.path.join(os.path.dirname(output_path), "concat_list.tmp.txt")
        try:
            # UTF-8 without BOM (FFmpeg concat demuxer fails on BOM with 'unknown keyword \ufefffile')
            with open(concat_txt, "w", encoding="utf-8") as handle:
                for path in scene_mp4_paths:
                    handle.write(SceneConcatenator.format_concat_line(path) + "\n")
            run_command([
                "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                "-f", "concat",
                "-safe", "0",
                "-i", concat_txt,
                "-c", "copy",
                output_path,
            ])
        except Exception:
            print(f"Concat list preserved for debugging: {concat_txt}")
            raise
        else:
            if os.path.exists(concat_txt):
                os.remove(concat_txt)
        return output_path
