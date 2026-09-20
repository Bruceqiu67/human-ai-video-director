"""Shared subprocess helpers for FFmpeg / FFprobe."""

from __future__ import annotations

import shutil
import subprocess
from typing import Sequence


def require_ffmpeg() -> None:
    missing = [name for name in ("ffmpeg", "ffprobe") if shutil.which(name) is None]
    if missing:
        raise RuntimeError(
            "Required binary not found in PATH: "
            + ", ".join(missing)
            + ". Install FFmpeg (with ffprobe) and retry."
        )


def run_command(
    cmd: Sequence[str],
    *,
    stdin=subprocess.DEVNULL,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    """Run a subprocess with stdin closed so FFmpeg cannot steal the parent pipe."""
    try:
        result = subprocess.run(
            list(cmd),
            stdin=stdin,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
        )
    except FileNotFoundError as exc:
        raise RuntimeError(
            f"Executable not found: {cmd[0]}. Install FFmpeg and ensure it is on PATH."
        ) from exc
    if check and result.returncode != 0:
        raise RuntimeError(
            f"Command failed ({cmd[0]}, code {result.returncode}):\n{result.stderr}"
        )
    return result
