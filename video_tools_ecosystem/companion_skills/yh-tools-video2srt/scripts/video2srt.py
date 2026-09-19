#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "elevenlabs>=2.58.0,<3",
# ]
# ///

"""Extract, transcribe, align, segment, and validate Chinese talking-head SRTs."""

from __future__ import annotations

import argparse
import dataclasses
import difflib
import getpass
import json
import math
import os
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path
from typing import Any, Iterable, Sequence
from unittest import mock


SCHEMA_VERSION = 1
PORTRAIT_LIMIT = 10
LANDSCAPE_LIMIT = 20
SEMANTIC_OVER_LIMIT_MULTIPLIER = 1.5
TRAILING_PUNCTUATION = set("。．.!！?？,，、;；:：")
TERMINAL_PUNCTUATION = set("。．.!！?？")
CLAUSE_PUNCTUATION = set("，,、;；:：")
SUBTITLE_BOUNDARY_PUNCTUATION = TERMINAL_PUNCTUATION | CLAUSE_PUNCTUATION
ASCII_PROTECTED = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_@#./:?&=%+-")
TIMESTAMP_RE = re.compile(
    r"^(\d{2,}):(\d{2}):(\d{2}),(\d{3}) --> "
    r"(\d{2,}):(\d{2}):(\d{2}),(\d{3})$"
)
KEYCHAIN_SERVICES = (
    "yh-tools-video2srt.elevenlabs-api-key",
    "yihui-video2srt.elevenlabs-api-key",
)
WORK_MARKER_FILENAME = ".yh-tools-video2srt-work.json"
LEGACY_WORK_MARKER_FILENAMES = (".yihui-video2srt-work.json",)
WORK_DIR_PREFIX = "yh-tools-video2srt-"
MANAGED_WORK_FILE_NAMES = {
    WORK_MARKER_FILENAME,
    *LEGACY_WORK_MARKER_FILENAMES,
    "manifest.json",
    "raw-transcript.txt",
    "raw-transcription.json",
    "reference.txt",
    "corrected-transcript.txt",
    "segmented-transcript.txt",
    "correction-report.json",
    "semantic-plan-report.json",
    "alignment.json",
}


class Video2SrtError(RuntimeError):
    """A user-facing, expected workflow failure."""


@dataclasses.dataclass(frozen=True)
class MediaInfo:
    video: Path
    encoded_width: int
    encoded_height: int
    display_width: int
    display_height: int
    rotation: int
    orientation: str
    max_visible_chars: int
    duration_seconds: float
    audio_stream_index: int


@dataclasses.dataclass(frozen=True)
class TimedUnit:
    text: str
    start: float
    end: float


@dataclasses.dataclass
class AtomicToken:
    units: list[TimedUnit]
    protected: bool = False

    @property
    def text(self) -> str:
        return "".join(unit.text for unit in self.units)

    @property
    def visible_count(self) -> int:
        return visible_count(self.text)

    @property
    def first_visible_start(self) -> float | None:
        for unit in self.units:
            if is_visible(unit.text):
                return unit.start
        return None

    @property
    def last_visible_end(self) -> float | None:
        for unit in reversed(self.units):
            if is_visible(unit.text):
                return unit.end
        return None


@dataclasses.dataclass
class Cue:
    text: str
    start: float
    end: float


@dataclasses.dataclass
class CueMs:
    text: str
    start_ms: int
    end_ms: int


def run_command(command: Sequence[str], *, label: str) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        list(command),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or f"exit {result.returncode}"
        raise Video2SrtError(f"{label} failed: {detail}")
    return result


def require_command(name: str) -> str:
    resolved = shutil.which(name)
    if not resolved:
        raise Video2SrtError(f"Required command not found: {name}")
    return resolved


def read_keychain_api_key() -> str:
    """Read the optional macOS Keychain fallback without exposing the secret."""
    if sys.platform != "darwin":
        return ""
    security = shutil.which("security")
    if not security:
        return ""
    for service in KEYCHAIN_SERVICES:
        result = subprocess.run(
            [
                security,
                "find-generic-password",
                "-a",
                getpass.getuser(),
                "-s",
                service,
                "-w",
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    return ""


def require_api_key(environ: dict[str, str] | os._Environ[str] = os.environ) -> str:
    key = environ.get("ELEVENLABS_API_KEY", "").strip()
    if not key and environ is os.environ:
        key = read_keychain_api_key()
    if not key:
        raise Video2SrtError(
            "ELEVENLABS_API_KEY is not set and no macOS Keychain fallback was found"
        )
    return key


def ensure_absent(path: Path, *, label: str) -> None:
    if path.exists():
        raise Video2SrtError(f"{label} already exists; refusing to overwrite: {path}")


def is_within(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def validate_managed_work_dir(path: Path, *, require_empty: bool = False) -> Path:
    resolved = path.expanduser().resolve()
    temp_root = Path(tempfile.gettempdir()).resolve()
    if resolved == temp_root or not is_within(resolved, temp_root):
        raise Video2SrtError(
            f"Work directory must be a dedicated directory created below {temp_root}: {resolved}"
        )
    if not resolved.exists() or not resolved.is_dir():
        raise Video2SrtError(f"Work directory does not exist: {resolved}")
    if require_empty:
        if resolved.parent != temp_root or not resolved.name.startswith(WORK_DIR_PREFIX):
            raise Video2SrtError(
                f"Work directory must be created directly below {temp_root} "
                f"with prefix {WORK_DIR_PREFIX!r}: {resolved}"
            )
        work_stat = resolved.stat()
        owner_mismatch = hasattr(os, "getuid") and work_stat.st_uid != os.getuid()
        permissions_too_open = os.name != "nt" and bool(work_stat.st_mode & 0o077)
        if owner_mismatch or permissions_too_open:
            raise Video2SrtError(
                f"Work directory must be private and owned by the current user: {resolved}"
            )
        if any(resolved.iterdir()):
            raise Video2SrtError(f"Work directory must be empty before prepare: {resolved}")
    return resolved


def model_to_plain(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): model_to_plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [model_to_plain(item) for item in value]
    if dataclasses.is_dataclass(value):
        return model_to_plain(dataclasses.asdict(value))
    if hasattr(value, "model_dump"):
        return model_to_plain(value.model_dump())
    if hasattr(value, "dict"):
        return model_to_plain(value.dict())
    if hasattr(value, "to_dict"):
        return model_to_plain(value.to_dict())
    if hasattr(value, "__dict__"):
        return {
            key: model_to_plain(item)
            for key, item in vars(value).items()
            if not key.startswith("_")
        }
    return str(value)


def get_field(value: Any, key: str, default: Any = None) -> Any:
    if isinstance(value, dict):
        return value.get(key, default)
    return getattr(value, key, default)


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    ensure_absent(temporary, label="Temporary output")
    try:
        temporary.write_text(content, encoding="utf-8")
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def atomic_write_json(path: Path, value: Any) -> None:
    atomic_write_text(
        path,
        json.dumps(model_to_plain(value), ensure_ascii=False, indent=2) + "\n",
    )


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise Video2SrtError(f"Could not read JSON file {path}: {exc}") from exc


def probe_media(video: Path) -> MediaInfo:
    ffprobe = require_command("ffprobe")
    if not video.exists() or not video.is_file():
        raise Video2SrtError(f"Video file not found: {video}")
    result = run_command(
        [ffprobe, "-v", "error", "-show_streams", "-show_format", "-of", "json", str(video)],
        label="ffprobe",
    )
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise Video2SrtError(f"ffprobe returned invalid JSON: {exc}") from exc

    streams = data.get("streams", [])
    video_stream = next((item for item in streams if item.get("codec_type") == "video"), None)
    audio_stream = next((item for item in streams if item.get("codec_type") == "audio"), None)
    if not video_stream:
        raise Video2SrtError(f"No video stream found: {video}")
    if not audio_stream:
        raise Video2SrtError(f"No audio stream found: {video}")

    try:
        width = int(video_stream["width"])
        height = int(video_stream["height"])
    except (KeyError, TypeError, ValueError) as exc:
        raise Video2SrtError("Could not determine encoded video dimensions") from exc

    rotation_value: Any = video_stream.get("tags", {}).get("rotate", 0)
    for side_data in video_stream.get("side_data_list", []):
        if "rotation" in side_data:
            rotation_value = side_data["rotation"]
            break
    try:
        rotation = int(round(float(rotation_value))) % 360
    except (TypeError, ValueError):
        rotation = 0
    if rotation in (90, 270):
        display_width, display_height = height, width
    else:
        display_width, display_height = width, height
    orientation = "portrait" if display_height > display_width else "landscape"
    max_chars = PORTRAIT_LIMIT if orientation == "portrait" else LANDSCAPE_LIMIT

    duration_value = data.get("format", {}).get("duration") or video_stream.get("duration")
    try:
        duration = float(duration_value)
    except (TypeError, ValueError) as exc:
        raise Video2SrtError("Could not determine video duration") from exc
    if not math.isfinite(duration) or duration <= 0:
        raise Video2SrtError(f"Invalid video duration: {duration_value}")

    return MediaInfo(
        video=video,
        encoded_width=width,
        encoded_height=height,
        display_width=display_width,
        display_height=display_height,
        rotation=rotation,
        orientation=orientation,
        max_visible_chars=max_chars,
        duration_seconds=duration,
        audio_stream_index=int(audio_stream.get("index", 0)),
    )


def extract_audio(video: Path, audio_out: Path) -> None:
    ffmpeg = require_command("ffmpeg")
    ensure_absent(audio_out, label="Audio output")
    audio_out.parent.mkdir(parents=True, exist_ok=True)
    command = [
        ffmpeg,
        "-v",
        "error",
        "-nostdin",
        "-n",
        "-i",
        str(video),
        "-map",
        "0:a:0",
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-codec:a",
        "libmp3lame",
        "-b:a",
        "64k",
        str(audio_out),
    ]
    try:
        run_command(command, label="ffmpeg audio extraction")
    except Exception:
        if audio_out.exists():
            audio_out.unlink()
        raise
    if not audio_out.exists() or audio_out.stat().st_size == 0:
        raise Video2SrtError(f"ffmpeg did not create a usable MP3: {audio_out}")


def validate_existing_audio(audio: Path) -> None:
    ffprobe = require_command("ffprobe")
    if not audio.exists() or not audio.is_file() or audio.stat().st_size == 0:
        raise Video2SrtError(f"Existing audio file is missing or empty: {audio}")
    result = run_command(
        [
            ffprobe,
            "-v",
            "error",
            "-select_streams",
            "a:0",
            "-show_entries",
            "stream=index",
            "-of",
            "csv=p=0",
            str(audio),
        ],
        label="ffprobe existing audio",
    )
    if not result.stdout.strip():
        raise Video2SrtError(f"No audio stream found in existing audio file: {audio}")


def create_elevenlabs_client(api_key: str) -> Any:
    try:
        import httpx
        from elevenlabs.client import ElevenLabs
    except ImportError as exc:
        raise Video2SrtError("The ElevenLabs SDK is unavailable; run this script with uv") from exc
    http_client = httpx.Client(timeout=240, follow_redirects=True, trust_env=False)
    return ElevenLabs(api_key=api_key, httpx_client=http_client)


def sanitized_exception(exc: Exception, secret: str | None = None) -> str:
    message = str(exc).strip() or exc.__class__.__name__
    if secret:
        message = message.replace(secret, "[REDACTED]")
    return message


def transcribe_audio(
    audio: Path,
    *,
    language: str,
    client: Any,
    secret: str | None = None,
) -> Any:
    try:
        with audio.open("rb") as stream:
            return client.speech_to_text.convert(
                file=stream,
                model_id="scribe_v2",
                language_code=language or None,
                tag_audio_events=False,
                diarize=False,
                timestamps_granularity="character",
                no_verbatim=False,
            )
    except Exception as exc:
        raise Video2SrtError(
            f"ElevenLabs transcription failed: {sanitized_exception(exc, secret)}"
        ) from exc


def force_align(
    audio: Path,
    text: str,
    *,
    client: Any,
    secret: str | None = None,
) -> Any:
    try:
        with audio.open("rb") as stream:
            return client.forced_alignment.create(file=stream, text=text)
    except Exception as exc:
        raise Video2SrtError(
            f"ElevenLabs forced alignment failed: {sanitized_exception(exc, secret)}"
        ) from exc


def graphemes(text: str) -> list[str]:
    clusters: list[str] = []
    for character in text:
        category = unicodedata.category(character)
        if clusters and (
            unicodedata.combining(character)
            or category in {"Mn", "Mc", "Me"}
            or character == "\ufe0f"
            or clusters[-1].endswith("\u200d")
        ):
            clusters[-1] += character
        else:
            clusters.append(character)
    return clusters


def is_visible(text: str) -> bool:
    return any(not character.isspace() for character in text)


def visible_count(text: str) -> int:
    return sum(1 for cluster in graphemes(text) if is_visible(cluster))


def normalize_for_guard(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text)
    return "".join(
        character
        for character in normalized
        if not character.isspace() and not unicodedata.category(character).startswith("P")
    )


def correction_stats(raw: str, corrected: str) -> dict[str, Any]:
    raw_normalized = normalize_for_guard(raw)
    corrected_normalized = normalize_for_guard(corrected)
    if not raw_normalized:
        raise Video2SrtError("Raw transcript is empty after normalization")
    matcher = difflib.SequenceMatcher(None, raw_normalized, corrected_normalized, autojunk=False)
    changed = sum(
        max(raw_end - raw_start, new_end - new_start)
        for opcode, raw_start, raw_end, new_start, new_end in matcher.get_opcodes()
        if opcode != "equal"
    )
    budget = max(10, math.ceil(len(raw_normalized) * 0.12))
    return {
        "raw_normalized_chars": len(raw_normalized),
        "corrected_normalized_chars": len(corrected_normalized),
        "length_ratio": len(corrected_normalized) / len(raw_normalized),
        "similarity": matcher.ratio(),
        "changed_chars": changed,
        "changed_char_budget": budget,
    }


def validate_correction(raw: str, corrected: str) -> dict[str, Any]:
    if not corrected.strip():
        raise Video2SrtError("Corrected transcript is empty")
    stats = correction_stats(raw, corrected)
    failures: list[str] = []
    if not 0.90 <= stats["length_ratio"] <= 1.10:
        failures.append(f"length ratio {stats['length_ratio']:.3f} is outside 0.90–1.10")
    if stats["similarity"] < 0.88:
        failures.append(f"similarity {stats['similarity']:.3f} is below 0.88")
    if stats["changed_chars"] > stats["changed_char_budget"]:
        failures.append(
            f"changed characters {stats['changed_chars']} exceed budget {stats['changed_char_budget']}"
        )
    if failures:
        raise Video2SrtError(
            "Corrected transcript differs too much from the audio transcript: " + "; ".join(failures)
        )
    return stats


def alignment_to_units(alignment: Any, corrected_text: str) -> list[TimedUnit]:
    plain = model_to_plain(alignment)
    characters = get_field(plain, "characters")
    if not isinstance(characters, list) or not characters:
        raise Video2SrtError("Forced Alignment returned no character timestamps")
    units: list[TimedUnit] = []
    for index, item in enumerate(characters):
        text = str(get_field(item, "text", ""))
        try:
            start = float(get_field(item, "start"))
            end = float(get_field(item, "end"))
        except (TypeError, ValueError) as exc:
            raise Video2SrtError(f"Invalid alignment timestamp at character {index}") from exc
        if not math.isfinite(start) or not math.isfinite(end) or start < 0 or end < start:
            raise Video2SrtError(f"Invalid alignment range at character {index}: {start}–{end}")
        clusters = graphemes(text)
        if not clusters:
            continue
        step = (end - start) / len(clusters)
        for offset, cluster in enumerate(clusters):
            unit_start = start + step * offset
            unit_end = end if offset == len(clusters) - 1 else start + step * (offset + 1)
            units.append(TimedUnit(cluster, unit_start, unit_end))
    reconstructed = "".join(unit.text for unit in units)
    if reconstructed != corrected_text:
        raise Video2SrtError(
            "Forced Alignment character output does not exactly match the corrected transcript"
        )
    return units


def is_ascii_protected_cluster(text: str) -> bool:
    return bool(text) and all(ord(character) < 128 and character in ASCII_PROTECTED for character in text)


def atomic_tokens(units: Sequence[TimedUnit]) -> list[AtomicToken]:
    tokens: list[AtomicToken] = []
    current: AtomicToken | None = None
    for unit in units:
        if unit.text.isspace():
            if current is None:
                current = AtomicToken([], protected=False)
                tokens.append(current)
            current.units.append(unit)
            current = None
            continue
        protected = is_ascii_protected_cluster(unit.text)
        if protected and current is not None and current.protected:
            current.units.append(unit)
            continue
        current = AtomicToken([unit], protected=protected)
        tokens.append(current)
        if not protected:
            current = None
    return tokens


def make_cue(tokens: Sequence[AtomicToken]) -> Cue | None:
    units = [unit for token in tokens for unit in token.units]
    while units and (
        not is_visible(units[0].text) or units[0].text in SUBTITLE_BOUNDARY_PUNCTUATION
    ):
        units.pop(0)
    while units and (
        not is_visible(units[-1].text) or units[-1].text in SUBTITLE_BOUNDARY_PUNCTUATION
    ):
        units.pop()
    if not units:
        return None
    visible_units = [unit for unit in units if is_visible(unit.text)]
    if not visible_units:
        return None
    text = "".join(unit.text for unit in units).strip()
    if not text:
        return None
    return Cue(text=text, start=visible_units[0].start, end=visible_units[-1].end)


def is_protected_text(text: str) -> bool:
    if not text or any(character.isspace() for character in text):
        return False
    return all(character in ASCII_PROTECTED for character in text)


def has_unprotected_boundary_punctuation(text: str) -> bool:
    synthetic_units = [TimedUnit(cluster, 0.0, 0.0) for cluster in graphemes(text)]
    for token in atomic_tokens(synthetic_units):
        if token.protected and any(character.isalnum() for character in token.text):
            continue
        if any(character in SUBTITLE_BOUNDARY_PUNCTUATION for character in token.text):
            return True
    return False


def validate_semantic_plan(
    corrected_text: str,
    segmented_text: str,
    *,
    max_visible_chars: int,
    allowed_semantic_over_limit_lines: set[int] | None = None,
) -> tuple[list[str], list[str], list[dict[str, Any]]]:
    if max_visible_chars <= 0:
        raise Video2SrtError("Subtitle character limit must be positive")
    if "\n" in corrected_text or "\r" in corrected_text:
        raise Video2SrtError("Corrected transcript must be one line before semantic segmentation")

    normalized_plan = segmented_text.replace("\r\n", "\n").replace("\r", "\n").strip()
    lines = normalized_plan.split("\n")
    if not lines or any(not line for line in lines):
        raise Video2SrtError("Semantic segmentation plan must contain one non-empty phrase per line")
    if any(line != line.strip() for line in lines):
        raise Video2SrtError("Semantic segmentation lines must not have leading or trailing spaces")
    if "".join(lines) != corrected_text:
        raise Video2SrtError(
            "Semantic segmentation plan must equal the corrected transcript with only line breaks added"
        )

    corrected_clusters = graphemes(corrected_text)
    protected_exceptions: list[str] = []
    semantic_exceptions: list[dict[str, Any]] = []
    allowed_lines = set(allowed_semantic_over_limit_lines or set())
    semantic_cap = int(math.floor(max_visible_chars * SEMANTIC_OVER_LIMIT_MULTIPLIER))
    cluster_offset = 0
    for line_number, line in enumerate(lines, start=1):
        clusters = graphemes(line)
        next_offset = cluster_offset + len(clusters)
        if line[0] in SUBTITLE_BOUNDARY_PUNCTUATION:
            raise Video2SrtError(
                f"Semantic segmentation line {line_number} starts with boundary punctuation"
            )
        if next_offset < len(corrected_clusters):
            previous_cluster = corrected_clusters[next_offset - 1]
            following_cluster = corrected_clusters[next_offset]
            if is_ascii_protected_cluster(previous_cluster) and is_ascii_protected_cluster(
                following_cluster
            ):
                raise Video2SrtError(
                    f"Semantic segmentation line {line_number} splits a protected ASCII token"
                )

        display_clusters = list(clusters)
        while display_clusters and display_clusters[-1] in SUBTITLE_BOUNDARY_PUNCTUATION:
            display_clusters.pop()
        display_text = "".join(display_clusters).strip()
        if not display_text:
            raise Video2SrtError(f"Semantic segmentation line {line_number} has no display text")
        if has_unprotected_boundary_punctuation(display_text):
            raise Video2SrtError(
                f"Semantic segmentation line {line_number} contains internal boundary punctuation"
            )
        count = visible_count(display_text)
        if count > max_visible_chars:
            if is_protected_text(display_text):
                protected_exceptions.append(display_text)
            elif line_number in allowed_lines and count <= semantic_cap:
                semantic_exceptions.append(
                    {
                        "cue": line_number,
                        "text": display_text,
                        "visible_chars": count,
                        "standard_limit": max_visible_chars,
                        "semantic_cap": semantic_cap,
                    }
                )
            else:
                raise Video2SrtError(
                    f"Semantic segmentation line {line_number} has {count} visible characters; "
                    f"revise the phrase boundary instead of hard-cutting above {max_visible_chars}, "
                    f"or explicitly approve a reviewed semantic exception up to {semantic_cap}"
                )
        cluster_offset = next_offset

    if cluster_offset != len(corrected_clusters):
        raise Video2SrtError("Semantic segmentation plan did not consume the corrected text")
    used_lines = {item["cue"] for item in semantic_exceptions}
    unused_lines = allowed_lines - used_lines
    if unused_lines:
        raise Video2SrtError(
            "Approved semantic over-limit lines were not valid over-limit exceptions: "
            + ", ".join(str(value) for value in sorted(unused_lines))
        )
    return lines, protected_exceptions, semantic_exceptions


def segment_units(
    units: Sequence[TimedUnit],
    *,
    corrected_text: str,
    segmented_text: str,
    max_visible_chars: int,
    allowed_semantic_over_limit_lines: set[int] | None = None,
) -> tuple[list[Cue], list[str], list[dict[str, Any]]]:
    lines, protected_exceptions, semantic_exceptions = validate_semantic_plan(
        corrected_text,
        segmented_text,
        max_visible_chars=max_visible_chars,
        allowed_semantic_over_limit_lines=allowed_semantic_over_limit_lines,
    )
    cues: list[Cue] = []
    unit_offset = 0
    for line_number, line in enumerate(lines, start=1):
        next_offset = unit_offset + len(graphemes(line))
        line_units = list(units[unit_offset:next_offset])
        if "".join(unit.text for unit in line_units) != line:
            raise Video2SrtError(
                f"Semantic segmentation line {line_number} does not match aligned text"
            )
        cue = make_cue(atomic_tokens(line_units))
        if cue is None:
            raise Video2SrtError(f"Semantic segmentation line {line_number} has no display text")
        cues.append(cue)
        unit_offset = next_offset

    if unit_offset != len(units):
        raise Video2SrtError("Semantic segmentation plan did not consume all aligned text")
    return cues, protected_exceptions, semantic_exceptions


def normalize_cue_milliseconds(cues: Sequence[Cue], duration_seconds: float) -> list[CueMs]:
    duration_ms = int(math.floor(duration_seconds * 1000))
    normalized: list[CueMs] = []
    for cue in cues:
        start_ms = max(0, int(round(cue.start * 1000)))
        end_ms = min(duration_ms, int(round(cue.end * 1000)))
        if end_ms <= start_ms:
            end_ms = min(duration_ms, start_ms + 1)
        if end_ms <= start_ms:
            raise Video2SrtError(f"Cue has no positive duration: {cue.text!r}")
        if normalized and start_ms <= normalized[-1].end_ms:
            shortened = start_ms - 1
            if shortened > normalized[-1].start_ms:
                normalized[-1].end_ms = shortened
            else:
                start_ms = normalized[-1].end_ms + 1
            if start_ms >= end_ms:
                raise Video2SrtError(f"Overlapping alignment could not be normalized: {cue.text!r}")
        normalized.append(CueMs(cue.text, start_ms, end_ms))
    return normalized


def format_timestamp(milliseconds: int) -> str:
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, millis = divmod(remainder, 1_000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"


def render_srt(cues: Sequence[CueMs]) -> str:
    blocks = [
        f"{index}\n{format_timestamp(cue.start_ms)} --> {format_timestamp(cue.end_ms)}\n{cue.text}"
        for index, cue in enumerate(cues, start=1)
    ]
    return "\n\n".join(blocks) + "\n"


def parse_timestamp_line(line: str) -> tuple[int, int]:
    match = TIMESTAMP_RE.fullmatch(line)
    if not match:
        raise Video2SrtError(f"Invalid SRT timestamp line: {line}")
    values = [int(value) for value in match.groups()]
    start = ((values[0] * 60 + values[1]) * 60 + values[2]) * 1000 + values[3]
    end = ((values[4] * 60 + values[5]) * 60 + values[6]) * 1000 + values[7]
    return start, end


def validate_srt_content(
    content: str,
    media: MediaInfo,
    *,
    allowed_semantic_over_limit_cues: set[int] | None = None,
) -> dict[str, Any]:
    stripped = content.strip()
    if not stripped:
        raise Video2SrtError("SRT file is empty")
    blocks = re.split(r"\r?\n\r?\n+", stripped)
    previous_end = -1
    exceptions: list[dict[str, Any]] = []
    semantic_exceptions: list[dict[str, Any]] = []
    allowed_cues = set(allowed_semantic_over_limit_cues or set())
    semantic_cap = int(math.floor(media.max_visible_chars * SEMANTIC_OVER_LIMIT_MULTIPLIER))
    for expected, block in enumerate(blocks, start=1):
        lines = block.splitlines()
        if len(lines) != 3:
            raise Video2SrtError(
                f"SRT cue {expected} must contain exactly index, timestamp, and one text line"
            )
        try:
            actual_index = int(lines[0])
        except ValueError as exc:
            raise Video2SrtError(f"Invalid SRT index at cue {expected}: {lines[0]}") from exc
        if actual_index != expected:
            raise Video2SrtError(f"Expected SRT index {expected}, found {actual_index}")
        start, end = parse_timestamp_line(lines[1])
        if start >= end:
            raise Video2SrtError(f"Cue {expected} has non-positive duration")
        if start <= previous_end:
            raise Video2SrtError(f"Cue {expected} overlaps the previous cue")
        if end > int(math.floor(media.duration_seconds * 1000)):
            raise Video2SrtError(f"Cue {expected} ends after the video duration")
        text = lines[2]
        if not text.strip():
            raise Video2SrtError(f"Cue {expected} has empty text")
        if text[0] in SUBTITLE_BOUNDARY_PUNCTUATION:
            raise Video2SrtError(f"Cue {expected} starts with boundary punctuation")
        if has_unprotected_boundary_punctuation(text):
            raise Video2SrtError(f"Cue {expected} contains standalone boundary punctuation")
        count = visible_count(text)
        if count > media.max_visible_chars:
            if is_protected_text(text):
                exceptions.append({"cue": expected, "text": text, "visible_chars": count})
            elif expected in allowed_cues and count <= semantic_cap:
                semantic_exceptions.append(
                    {
                        "cue": expected,
                        "text": text,
                        "visible_chars": count,
                        "standard_limit": media.max_visible_chars,
                        "semantic_cap": semantic_cap,
                    }
                )
            else:
                raise Video2SrtError(
                    f"Cue {expected} has {count} visible characters, above {media.max_visible_chars}"
                )
        if text[-1] in TRAILING_PUNCTUATION:
            raise Video2SrtError(f"Cue {expected} still has terminal punctuation")
        previous_end = end
    used_cues = {item["cue"] for item in semantic_exceptions}
    unused_cues = allowed_cues - used_cues
    if unused_cues:
        raise Video2SrtError(
            "Approved semantic over-limit cues were not valid over-limit exceptions: "
            + ", ".join(str(value) for value in sorted(unused_cues))
        )
    return {
        "cue_count": len(blocks),
        "orientation": media.orientation,
        "display_dimensions": [media.display_width, media.display_height],
        "max_visible_chars": media.max_visible_chars,
        "punctuation_free_cues": True,
        "protected_over_limit_exceptions": exceptions,
        "semantic_over_limit_exceptions": semantic_exceptions,
    }


def prepare_command(args: argparse.Namespace) -> dict[str, Any]:
    video = Path(args.video).expanduser().resolve()
    work_dir = validate_managed_work_dir(Path(args.work_dir), require_empty=True)
    if args.audio_in and args.audio_out:
        raise Video2SrtError("Use either --audio-in or --audio-out, not both")
    if args.audio_in:
        audio = Path(args.audio_in).expanduser().resolve()
        audio_source = "existing"
        if is_within(audio, work_dir):
            raise Video2SrtError("Existing audio must be outside the temporary work directory")
        validate_existing_audio(audio)
    else:
        audio = (
            Path(args.audio_out).expanduser().resolve()
            if args.audio_out
            else video.with_name(f"{video.stem}.audio.mp3")
        )
        audio_source = "extracted"
        if is_within(audio, work_dir):
            raise Video2SrtError("Audio output must be outside the temporary work directory")
        ensure_absent(audio, label="Audio output")
    key = require_api_key()
    media = probe_media(video)

    owner_token = secrets.token_urlsafe(32)
    marker = work_dir / WORK_MARKER_FILENAME
    atomic_write_json(
        marker,
        {
            "schema_version": SCHEMA_VERSION,
            "managed": True,
            "work_dir": str(work_dir),
            "owner_token": owner_token,
        },
    )
    if audio_source == "extracted":
        extract_audio(video, audio)
    client = create_elevenlabs_client(key)
    transcription = transcribe_audio(
        audio,
        language=args.language,
        client=client,
        secret=key,
    )
    plain = model_to_plain(transcription)
    raw_value = get_field(plain, "text", "")
    raw_text = raw_value.strip() if isinstance(raw_value, str) else ""
    if not raw_text:
        raise Video2SrtError("ElevenLabs returned an empty transcript")

    raw_text_path = work_dir / "raw-transcript.txt"
    raw_json_path = work_dir / "raw-transcription.json"
    manifest_path = work_dir / "manifest.json"
    atomic_write_text(raw_text_path, raw_text + "\n")
    atomic_write_json(raw_json_path, plain)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "video": str(video),
        "audio": str(audio),
        "audio_source": audio_source,
        "raw_transcript": str(raw_text_path),
        "raw_transcription_json": str(raw_json_path),
        "language": args.language,
        "model": "scribe_v2",
        "timestamps_granularity": "character",
        "owner_token": owner_token,
        "media": dataclasses.asdict(media),
    }
    atomic_write_json(manifest_path, manifest)
    return {
        "status": "prepared",
        "video": str(video),
        "audio": str(audio),
        "audio_source": audio_source,
        "work_dir": str(work_dir),
        "raw_transcript": str(raw_text_path),
        "orientation": media.orientation,
        "display_dimensions": [media.display_width, media.display_height],
        "max_visible_chars": media.max_visible_chars,
    }


def verify_work_manifest(work_dir: Path) -> dict[str, Any]:
    marker_candidates = (
        work_dir / WORK_MARKER_FILENAME,
        *(work_dir / name for name in LEGACY_WORK_MARKER_FILENAMES),
    )
    marker_path = next((path for path in marker_candidates if path.exists()), None)
    manifest_path = work_dir / "manifest.json"
    if marker_path is None or not manifest_path.exists():
        raise Video2SrtError(f"Work directory is not a completed prepare workspace: {work_dir}")
    marker = load_json(marker_path)
    if (
        marker.get("managed") is not True
        or Path(marker.get("work_dir", "")).resolve() != work_dir.resolve()
    ):
        raise Video2SrtError("Work directory safety marker is invalid")
    manifest = load_json(manifest_path)
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise Video2SrtError("Unsupported work manifest schema")
    if marker_path.name == WORK_MARKER_FILENAME:
        marker_token = marker.get("owner_token")
        if (
            not isinstance(marker_token, str)
            or len(marker_token) < 32
            or manifest.get("owner_token") != marker_token
        ):
            raise Video2SrtError("Work directory ownership token is invalid")
    return manifest


def cleanup_managed_work_dir(work_dir: Path) -> bool:
    """Remove only a verified new-format workspace with an expected flat file set."""
    marker_path = work_dir / WORK_MARKER_FILENAME
    manifest_path = work_dir / "manifest.json"
    if not marker_path.is_file() or not manifest_path.is_file():
        return False

    marker = load_json(marker_path)
    manifest = load_json(manifest_path)
    marker_token = marker.get("owner_token")
    if (
        marker.get("managed") is not True
        or Path(marker.get("work_dir", "")).resolve() != work_dir.resolve()
        or not isinstance(marker_token, str)
        or len(marker_token) < 32
        or manifest.get("owner_token") != marker_token
    ):
        return False

    entries = list(work_dir.iterdir())
    if any(entry.name not in MANAGED_WORK_FILE_NAMES or entry.is_dir() for entry in entries):
        return False

    try:
        for entry in entries:
            entry.unlink()
        work_dir.rmdir()
    except OSError:
        return False
    return True


def validate_plan_command(args: argparse.Namespace) -> dict[str, Any]:
    video = Path(args.video).expanduser().resolve()
    corrected_path = Path(args.corrected_text).expanduser().resolve()
    segmented_path = Path(args.segmented_text).expanduser().resolve()
    if not corrected_path.exists() or not segmented_path.exists():
        raise Video2SrtError("Corrected transcript or semantic segmentation plan is missing")
    media = probe_media(video)
    allowed_lines = set(args.allow_semantic_over_limit_line or [])
    lines, protected_exceptions, semantic_exceptions = validate_semantic_plan(
        corrected_path.read_text(encoding="utf-8").strip(),
        segmented_path.read_text(encoding="utf-8"),
        max_visible_chars=media.max_visible_chars,
        allowed_semantic_over_limit_lines=allowed_lines,
    )
    return {
        "status": "semantic-plan-valid",
        "video": str(video),
        "corrected_text": str(corrected_path),
        "segmented_text": str(segmented_path),
        "orientation": media.orientation,
        "display_dimensions": [media.display_width, media.display_height],
        "max_visible_chars": media.max_visible_chars,
        "cue_count": len(lines),
        "protected_over_limit_exceptions": sorted(set(protected_exceptions)),
        "semantic_over_limit_exceptions": semantic_exceptions,
        "automatic_hard_cutting": False,
        "semantic_review_required": True,
    }


def finalize_command(args: argparse.Namespace) -> dict[str, Any]:
    work_dir = validate_managed_work_dir(Path(args.work_dir))
    manifest = verify_work_manifest(work_dir)
    video = Path(manifest["video"]).resolve()
    audio = Path(manifest["audio"]).resolve()
    raw_path = Path(manifest["raw_transcript"]).resolve()
    corrected_path = Path(args.corrected_text).expanduser().resolve()
    segmented_path = Path(args.segmented_text).expanduser().resolve()
    if not is_within(corrected_path, work_dir):
        raise Video2SrtError("Corrected transcript must be stored inside the managed work directory")
    if not is_within(segmented_path, work_dir):
        raise Video2SrtError("Semantic segmentation plan must be inside the managed work directory")
    if not audio.exists():
        raise Video2SrtError(f"Prepared MP3 is missing: {audio}")
    if not raw_path.exists() or not corrected_path.exists() or not segmented_path.exists():
        raise Video2SrtError("Raw, corrected, or semantic segmentation text is missing")
    srt_out = (
        Path(args.srt_out).expanduser().resolve()
        if args.srt_out
        else video.with_name(f"{video.stem}.optimized.srt")
    )
    if is_within(srt_out, work_dir):
        raise Video2SrtError("Final SRT output must be outside the temporary work directory")
    ensure_absent(srt_out, label="SRT output")

    raw = raw_path.read_text(encoding="utf-8").strip()
    corrected = corrected_path.read_text(encoding="utf-8").strip()
    segmented = segmented_path.read_text(encoding="utf-8")
    correction_report = validate_correction(raw, corrected)
    atomic_write_json(work_dir / "correction-report.json", correction_report)
    media = probe_media(video)
    allowed_semantic_lines = set(args.allow_semantic_over_limit_line or [])
    plan_lines, plan_exceptions, semantic_plan_exceptions = validate_semantic_plan(
        corrected,
        segmented,
        max_visible_chars=media.max_visible_chars,
        allowed_semantic_over_limit_lines=allowed_semantic_lines,
    )
    atomic_write_json(
        work_dir / "semantic-plan-report.json",
        {
            "cue_count": len(plan_lines),
            "automatic_hard_cutting": False,
            "semantic_review_required": True,
            "protected_over_limit_exceptions": sorted(set(plan_exceptions)),
            "semantic_over_limit_exceptions": semantic_plan_exceptions,
        },
    )

    key = require_api_key()
    client = create_elevenlabs_client(key)
    alignment = force_align(audio, corrected, client=client, secret=key)
    plain_alignment = model_to_plain(alignment)
    atomic_write_json(work_dir / "alignment.json", plain_alignment)
    units = alignment_to_units(plain_alignment, corrected)
    cues, segmentation_exceptions, semantic_segmentation_exceptions = segment_units(
        units,
        corrected_text=corrected,
        segmented_text=segmented,
        max_visible_chars=media.max_visible_chars,
        allowed_semantic_over_limit_lines=allowed_semantic_lines,
    )
    cues_ms = normalize_cue_milliseconds(cues, media.duration_seconds)
    content = render_srt(cues_ms)
    validation = validate_srt_content(
        content,
        media,
        allowed_semantic_over_limit_cues=allowed_semantic_lines,
    )
    atomic_write_text(srt_out, content)

    work_dir_removed = cleanup_managed_work_dir(work_dir)
    retained_work_dir: str | None = None if work_dir_removed else str(work_dir)

    summary = {
        "status": "completed",
        "video": str(video),
        "audio": str(audio),
        "audio_source": manifest.get("audio_source", "extracted"),
        "srt": str(srt_out),
        "orientation": media.orientation,
        "display_dimensions": [media.display_width, media.display_height],
        "max_visible_chars": media.max_visible_chars,
        "punctuation_free_cues": validation["punctuation_free_cues"],
        "semantic_segmentation_plan": True,
        "automatic_hard_cutting": False,
        "correction": correction_report,
        "cue_count": validation["cue_count"],
        "protected_over_limit_exceptions": sorted(set(segmentation_exceptions)),
        "semantic_over_limit_exceptions": semantic_segmentation_exceptions,
        "work_dir_removed": work_dir_removed,
        "retained_work_dir": retained_work_dir,
    }
    return summary


def validate_command(args: argparse.Namespace) -> dict[str, Any]:
    video = Path(args.video).expanduser().resolve()
    srt = Path(args.srt).expanduser().resolve()
    if not srt.exists() or not srt.is_file():
        raise Video2SrtError(f"SRT file not found: {srt}")
    media = probe_media(video)
    report = validate_srt_content(
        srt.read_text(encoding="utf-8"),
        media,
        allowed_semantic_over_limit_cues=set(args.allow_semantic_over_limit_cue or []),
    )
    return {"status": "valid", "video": str(video), "srt": str(srt), **report}


def fake_alignment(text: str, *, step: float = 0.12, gap_after: int | None = None) -> dict[str, Any]:
    characters: list[dict[str, Any]] = []
    cursor = 0.0
    for index, cluster in enumerate(graphemes(text)):
        if gap_after is not None and index == gap_after:
            cursor += 0.5
        characters.append({"text": cluster, "start": cursor, "end": cursor + step})
        cursor += step
    return {"characters": characters, "words": [], "loss": 0.01}


class FakeSpeechToText:
    def __init__(self, response: Any = None, error: Exception | None = None) -> None:
        self.response = response
        self.error = error

    def convert(self, **_: Any) -> Any:
        if self.error:
            raise self.error
        return self.response


class FakeForcedAlignment:
    def __init__(self, response: Any = None, error: Exception | None = None) -> None:
        self.response = response
        self.error = error

    def create(self, **_: Any) -> Any:
        if self.error:
            raise self.error
        return self.response


class FakeClient:
    def __init__(self, *, transcript: Any = None, alignment: Any = None) -> None:
        self.speech_to_text = FakeSpeechToText(transcript)
        self.forced_alignment = FakeForcedAlignment(alignment)


def assert_raises(callable_value: Any, expected_text: str) -> None:
    try:
        callable_value()
    except Video2SrtError as exc:
        if expected_text not in str(exc):
            raise AssertionError(f"Expected {expected_text!r} in {str(exc)!r}") from exc
    else:
        raise AssertionError(f"Expected Video2SrtError containing {expected_text!r}")


def self_test_credentials_and_markers() -> None:
    assert require_api_key({"ELEVENLABS_API_KEY": "environment-key"}) == "environment-key"

    missing = subprocess.CompletedProcess([], 44, stdout="", stderr="")
    primary = subprocess.CompletedProcess([], 0, stdout="primary-key\n", stderr="")
    legacy = subprocess.CompletedProcess([], 0, stdout="legacy-key\n", stderr="")

    with (
        mock.patch.object(sys, "platform", "darwin"),
        mock.patch.object(shutil, "which", return_value="/usr/bin/security"),
        mock.patch.object(subprocess, "run", side_effect=[primary]) as run_mock,
    ):
        assert read_keychain_api_key() == "primary-key"
        assert run_mock.call_count == 1
        assert KEYCHAIN_SERVICES[0] in run_mock.call_args.args[0]

    with (
        mock.patch.object(sys, "platform", "darwin"),
        mock.patch.object(shutil, "which", return_value="/usr/bin/security"),
        mock.patch.object(subprocess, "run", side_effect=[missing, legacy]) as run_mock,
    ):
        assert read_keychain_api_key() == "legacy-key"
        assert run_mock.call_count == 2
        assert KEYCHAIN_SERVICES[1] in run_mock.call_args.args[0]

    with tempfile.TemporaryDirectory(prefix="yh-tools-video2srt-marker-test-") as directory:
        root = Path(directory)
        work_dirs: dict[str, Path] = {}
        for marker_name in (WORK_MARKER_FILENAME, *LEGACY_WORK_MARKER_FILENAMES):
            work_dir = root / marker_name.removeprefix(".").removesuffix(".json")
            work_dir.mkdir()
            work_dirs[marker_name] = work_dir
            owner_token = "t" * 43 if marker_name == WORK_MARKER_FILENAME else None
            marker_data: dict[str, Any] = {
                "schema_version": SCHEMA_VERSION,
                "managed": True,
                "work_dir": str(work_dir),
            }
            manifest_data: dict[str, Any] = {"schema_version": SCHEMA_VERSION}
            if owner_token:
                marker_data["owner_token"] = owner_token
                manifest_data["owner_token"] = owner_token
            atomic_write_json(
                work_dir / marker_name,
                marker_data,
            )
            atomic_write_json(work_dir / "manifest.json", manifest_data)
            assert verify_work_manifest(work_dir)["schema_version"] == SCHEMA_VERSION

        new_work_dir = work_dirs[WORK_MARKER_FILENAME]
        assert cleanup_managed_work_dir(new_work_dir) is True
        assert not new_work_dir.exists()

        legacy_work_dir = work_dirs[LEGACY_WORK_MARKER_FILENAMES[0]]
        assert cleanup_managed_work_dir(legacy_work_dir) is False
        assert legacy_work_dir.exists()

        unexpected = root / "unexpected-content"
        unexpected.mkdir()
        token = "u" * 43
        atomic_write_json(
            unexpected / WORK_MARKER_FILENAME,
            {
                "schema_version": SCHEMA_VERSION,
                "managed": True,
                "work_dir": str(unexpected),
                "owner_token": token,
            },
        )
        atomic_write_json(
            unexpected / "manifest.json",
            {"schema_version": SCHEMA_VERSION, "owner_token": token},
        )
        atomic_write_text(unexpected / "keep-me.txt", "unmanaged\n")
        assert cleanup_managed_work_dir(unexpected) is False
        assert (unexpected / "keep-me.txt").exists()

        invalid_token = root / "invalid-token"
        invalid_token.mkdir()
        atomic_write_json(
            invalid_token / WORK_MARKER_FILENAME,
            {
                "schema_version": SCHEMA_VERSION,
                "managed": True,
                "work_dir": str(invalid_token),
                "owner_token": "a" * 43,
            },
        )
        atomic_write_json(
            invalid_token / "manifest.json",
            {"schema_version": SCHEMA_VERSION, "owner_token": "b" * 43},
        )
        assert_raises(
            lambda: verify_work_manifest(invalid_token),
            "ownership token is invalid",
        )

        unmanaged = root / "unmanaged"
        unmanaged.mkdir()
        atomic_write_json(
            unmanaged / "manifest.json",
            {"schema_version": SCHEMA_VERSION},
        )
        assert_raises(
            lambda: verify_work_manifest(unmanaged),
            "not a completed prepare workspace",
        )


def self_test_media() -> None:
    require_command("ffmpeg")
    require_command("ffprobe")
    with tempfile.TemporaryDirectory(prefix="yh-tools-video2srt-test-") as directory:
        root = Path(directory)
        landscape = root / "landscape.mp4"
        portrait = root / "portrait.mp4"
        no_audio = root / "no-audio.mp4"
        rotated = root / "rotated.mp4"
        extracted = root / "audio.mp3"
        ffmpeg = require_command("ffmpeg")

        run_command(
            [
                ffmpeg,
                "-v",
                "error",
                "-f",
                "lavfi",
                "-i",
                "color=c=black:s=320x180:d=1",
                "-f",
                "lavfi",
                "-i",
                "sine=frequency=1000:duration=1",
                "-shortest",
                "-c:v",
                "mpeg4",
                "-c:a",
                "aac",
                str(landscape),
            ],
            label="self-test landscape fixture",
        )
        run_command(
            [
                ffmpeg,
                "-v",
                "error",
                "-f",
                "lavfi",
                "-i",
                "color=c=black:s=180x320:d=1",
                "-f",
                "lavfi",
                "-i",
                "sine=frequency=900:duration=1",
                "-shortest",
                "-c:v",
                "mpeg4",
                "-c:a",
                "aac",
                str(portrait),
            ],
            label="self-test portrait fixture",
        )
        run_command(
            [
                ffmpeg,
                "-v",
                "error",
                "-f",
                "lavfi",
                "-i",
                "color=c=black:s=320x180:d=1",
                "-c:v",
                "mpeg4",
                str(no_audio),
            ],
            label="self-test no-audio fixture",
        )
        run_command(
            [
                ffmpeg,
                "-v",
                "error",
                "-display_rotation:v:0",
                "90",
                "-i",
                str(landscape),
                "-c",
                "copy",
                str(rotated),
            ],
            label="self-test rotated fixture",
        )

        landscape_info = probe_media(landscape)
        portrait_info = probe_media(portrait)
        rotated_info = probe_media(rotated)
        assert landscape_info.orientation == "landscape"
        assert landscape_info.max_visible_chars == LANDSCAPE_LIMIT
        assert portrait_info.orientation == "portrait"
        assert portrait_info.max_visible_chars == PORTRAIT_LIMIT
        assert rotated_info.orientation == "portrait"
        assert (rotated_info.display_width, rotated_info.display_height) == (180, 320)
        extract_audio(landscape, extracted)
        assert extracted.exists() and extracted.stat().st_size > 0
        validate_existing_audio(extracted)
        assert_raises(lambda: extract_audio(landscape, extracted), "already exists")
        assert_raises(lambda: validate_existing_audio(root / "missing.mp3"), "missing or empty")
        assert_raises(lambda: probe_media(no_audio), "No audio stream")


def self_test_command(_: argparse.Namespace) -> dict[str, Any]:
    assert_raises(lambda: require_api_key({}), "ELEVENLABS_API_KEY")
    self_test_credentials_and_markers()
    raw = "今天我们使用 ChatGTP 完成这个任务。"
    corrected = "今天我们使用 ChatGPT 完成这个任务。"
    stats = validate_correction(raw, corrected)
    assert stats["similarity"] >= 0.88
    assert_raises(
        lambda: validate_correction(raw, "这是一篇完全不同并且不能来自音频的口播稿内容。"),
        "differs too much",
    )

    mock_audio = Path(__file__)
    fake_client = FakeClient(
        transcript={"text": raw, "words": []},
        alignment=fake_alignment(corrected),
    )
    transcription = transcribe_audio(mock_audio, language="zh", client=fake_client)
    assert get_field(transcription, "text") == raw
    alignment = force_align(mock_audio, corrected, client=fake_client)
    units = alignment_to_units(alignment, corrected)
    assert "".join(unit.text for unit in units) == corrected
    failing_transcription_client = FakeClient()
    failing_transcription_client.speech_to_text = FakeSpeechToText(error=RuntimeError("mock STT failure"))
    assert_raises(
        lambda: transcribe_audio(
            mock_audio,
            language="zh",
            client=failing_transcription_client,
        ),
        "transcription failed",
    )
    failing_alignment_client = FakeClient()
    failing_alignment_client.forced_alignment = FakeForcedAlignment(
        error=RuntimeError("mock alignment failure")
    )
    assert_raises(
        lambda: force_align(mock_audio, corrected, client=failing_alignment_client),
        "forced alignment failed",
    )
    assert_raises(
        lambda: alignment_to_units(fake_alignment("不匹配"), corrected),
        "does not exactly match",
    )

    def segment_fixture(
        text: str,
        plan: str,
        limit: int,
        allowed_semantic_lines: set[int] | None = None,
    ) -> tuple[list[Cue], list[str], list[dict[str, Any]]]:
        fixture_units = alignment_to_units(fake_alignment(text), text)
        return segment_units(
            fixture_units,
            corrected_text=text,
            segmented_text=plan,
            max_visible_chars=limit,
            allowed_semantic_over_limit_lines=allowed_semantic_lines,
        )

    vertical_text = "这是一个需要合理拆分的竖版字幕测试"
    vertical_cues, vertical_exceptions, vertical_semantic_exceptions = segment_fixture(
        vertical_text,
        "这是一个需要\n合理拆分的\n竖版字幕测试",
        PORTRAIT_LIMIT,
    )
    assert not vertical_exceptions
    assert not vertical_semantic_exceptions
    assert len(vertical_cues) == 3
    assert all(visible_count(cue.text) <= PORTRAIT_LIMIT for cue in vertical_cues)

    horizontal_text = "这是一个用于验证横版二十字限制并确保不会超出的字幕测试"
    horizontal_cues, _, _ = segment_fixture(
        horizontal_text,
        "这是一个用于验证横版二十字限制\n并确保不会超出的字幕测试",
        LANDSCAPE_LIMIT,
    )
    assert all(visible_count(cue.text) <= LANDSCAPE_LIMIT for cue in horizontal_cues)

    punctuated = "第一句话结束。第二句话继续，第三部分完成！"
    punctuated_cues, _, _ = segment_fixture(
        punctuated,
        "第一句话结束。\n第二句话继续，\n第三部分完成！",
        PORTRAIT_LIMIT,
    )
    assert [cue.text for cue in punctuated_cues] == [
        "第一句话结束",
        "第二句话继续",
        "第三部分完成",
    ]
    assert all(not has_unprotected_boundary_punctuation(cue.text) for cue in punctuated_cues)

    exact_limit_clause = "这些风格都是OpenAI官网里面有出现的，包括这种水果的风格"
    exact_limit_cues, _, _ = segment_fixture(
        exact_limit_clause,
        "这些风格都是OpenAI官网里面有出现的，\n包括这种水果的风格",
        LANDSCAPE_LIMIT,
    )
    assert [cue.text for cue in exact_limit_cues] == [
        "这些风格都是OpenAI官网里面有出现的",
        "包括这种水果的风格",
    ]

    comment_clause = "SKILL的下载和使用链接我放在了评论区，大家可以自取"
    comment_cues, _, _ = segment_fixture(
        comment_clause,
        "SKILL的下载和使用链接我放在了评论区，\n大家可以自取",
        LANDSCAPE_LIMIT,
    )
    assert [cue.text for cue in comment_cues] == [
        "SKILL的下载和使用链接我放在了评论区",
        "大家可以自取",
    ]

    semantic_text = "你可以通过这个SKILL扩展出非常多种颜色的风格"
    semantic_cues, _, _ = segment_fixture(
        semantic_text,
        "你可以通过这个SKILL\n扩展出非常多种颜色的风格",
        LANDSCAPE_LIMIT,
    )
    assert [cue.text for cue in semantic_cues] == [
        "你可以通过这个SKILL",
        "扩展出非常多种颜色的风格",
    ]

    assert_raises(
        lambda: segment_fixture(semantic_text, semantic_text, LANDSCAPE_LIMIT),
        "instead of hard-cutting",
    )
    reviewed_over_limit = "一个能一键创建OpenAI官网的这种风格的海报的SKILL"
    reviewed_cues, _, reviewed_exceptions = segment_fixture(
        reviewed_over_limit,
        reviewed_over_limit,
        LANDSCAPE_LIMIT,
        {1},
    )
    assert len(reviewed_cues) == 1
    assert reviewed_exceptions[0]["visible_chars"] == 29
    assert_raises(
        lambda: segment_fixture("OpenAI官网", "Open\nAI官网", LANDSCAPE_LIMIT),
        "splits a protected ASCII token",
    )
    assert_raises(
        lambda: segment_fixture(
            "第一句话，第二句话。",
            "第一句话，第二句话。",
            LANDSCAPE_LIMIT,
        ),
        "internal boundary punctuation",
    )
    assert_raises(
        lambda: segment_fixture("完整文本", "缺失文本", LANDSCAPE_LIMIT),
        "only line breaks added",
    )

    protected_text = "ElevenLabsPlatform"
    protected_cues, protected_exceptions, protected_semantic_exceptions = segment_fixture(
        protected_text,
        protected_text,
        PORTRAIT_LIMIT,
    )
    assert len(protected_cues) == 1
    assert protected_exceptions == [protected_text]
    assert not protected_semantic_exceptions

    media = MediaInfo(
        video=Path("fixture.mp4"),
        encoded_width=180,
        encoded_height=320,
        display_width=180,
        display_height=320,
        rotation=0,
        orientation="portrait",
        max_visible_chars=PORTRAIT_LIMIT,
        duration_seconds=30.0,
        audio_stream_index=1,
    )
    cues_ms = normalize_cue_milliseconds(punctuated_cues, media.duration_seconds)
    srt = render_srt(cues_ms)
    validation = validate_srt_content(srt, media)
    assert validation["cue_count"] == len(cues_ms)
    bad_punctuation_srt = "1\n00:00:00,000 --> 00:00:01,000\n区，大家可以自取\n"
    assert_raises(
        lambda: validate_srt_content(bad_punctuation_srt, media),
        "boundary punctuation",
    )

    self_test_media()
    return {
        "status": "self-test-passed",
        "tests": [
            "API-key guard",
            "environment and Keychain credential precedence",
            "new and legacy work-marker compatibility",
            "ownership-token and allowlisted workspace cleanup",
            "correction guard",
            "mock Scribe v2 response",
            "mock Forced Alignment response",
            "mock API failure handling",
            "alignment mismatch guard",
            "portrait 10-character segmentation",
            "landscape 20-character segmentation",
            "punctuation-free clause boundaries",
            "exact-limit punctuation regression cases",
            "explicit semantic phrase segmentation",
            "hard-cut rejection",
            "reviewed semantic over-limit exception",
            "protected-token split rejection",
            "segmentation-plan integrity guard",
            "protected-token exception",
            "SRT rendering and validation",
            "leading/internal boundary-punctuation rejection",
            "landscape/portrait/rotation media probes",
            "MP3 extraction",
            "existing-audio validation",
            "missing-audio and overwrite guards",
        ],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create timestamp-accurate Chinese SRT subtitles from video speech."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare = subparsers.add_parser(
        "prepare", help="Reuse existing audio or extract MP3, then transcribe with Scribe v2"
    )
    prepare.add_argument("--video", required=True)
    prepare.add_argument("--work-dir", required=True)
    prepare.add_argument("--audio-in")
    prepare.add_argument("--audio-out")
    prepare.add_argument("--language", default="zh")
    prepare.set_defaults(handler=prepare_command)

    validate_plan = subparsers.add_parser(
        "validate-plan", help="Reject hard cuts and validate explicit semantic cue boundaries"
    )
    validate_plan.add_argument("--video", required=True)
    validate_plan.add_argument("--corrected-text", required=True)
    validate_plan.add_argument("--segmented-text", required=True)
    validate_plan.add_argument(
        "--allow-semantic-over-limit-line",
        action="append",
        type=int,
        default=[],
    )
    validate_plan.set_defaults(handler=validate_plan_command)

    finalize = subparsers.add_parser(
        "finalize", help="Validate corrections, force-align, and generate the optimized SRT"
    )
    finalize.add_argument("--work-dir", required=True)
    finalize.add_argument("--corrected-text", required=True)
    finalize.add_argument("--segmented-text", required=True)
    finalize.add_argument(
        "--allow-semantic-over-limit-line",
        action="append",
        type=int,
        default=[],
    )
    finalize.add_argument("--srt-out")
    finalize.add_argument(
        "--punctuation",
        choices=["strip-boundary"],
        default="strip-boundary",
    )
    finalize.set_defaults(handler=finalize_command)

    validate = subparsers.add_parser("validate", help="Validate an SRT against its video")
    validate.add_argument("--video", required=True)
    validate.add_argument("--srt", required=True)
    validate.add_argument(
        "--allow-semantic-over-limit-cue",
        action="append",
        type=int,
        default=[],
    )
    validate.set_defaults(handler=validate_command)

    self_test = subparsers.add_parser("self-test", help="Run offline deterministic tests")
    self_test.set_defaults(handler=self_test_command)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = args.handler(args)
    except Video2SrtError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(model_to_plain(result), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
