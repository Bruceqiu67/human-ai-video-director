"""Masterframe discovery and pose matching (no silent fallbacks)."""

from __future__ import annotations

import os
import re
from typing import Iterable

IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp")
PLATE_TOKENS = ("参考", "结尾", "底板", "background", "anchor", "end_frame", "endframe")
PATCH_TOKENS = ("合规", "修补", "patched", "fixed", "compliant")


def parse_scene_number(scene_id: str) -> int | None:
    digits = "".join(ch for ch in scene_id if ch.isdigit())
    return int(digits) if digits else None


def filename_belongs_to_scene(fname: str, scene_id: str) -> bool:
    """True only when the file's SceneNN token equals this scene's integer id."""
    fl = fname.lower()
    if not fl.endswith(IMAGE_EXTS):
        return False
    n = parse_scene_number(scene_id)
    if n is None:
        token = scene_id.replace("_", "").lower()
        return token in fl.replace("_", "").replace("-", "")
    return re.search(rf"(?:^|[^0-9a-z])scene[_-]?0*{n}(?!\d)", fl) is not None


def is_excluded_plate(fname: str) -> bool:
    lower = fname.lower()
    return any(tok.lower() in lower for tok in PLATE_TOKENS)


def _pose_token_matches(fname: str, pose_index: int) -> bool:
    fl = fname.lower()
    return re.search(rf"(?:^|[^0-9a-z])pose[_-]?0*{pose_index}(?!\d)", fl) is not None


def _patch_score(fname: str) -> int:
    lower = fname.lower()
    return 1 if any(tok.lower() in lower for tok in PATCH_TOKENS) else 0


def match_pose_filename(
    pose_name: str,
    pose_index: int,
    filenames: list[str],
) -> str | None:
    """Pick one filename for a pose.

    1. Prefer files whose name contains the pose string (patched variants win).
    2. Else match a bounded pose_N / poseN token using the unique-pose index.
    3. Else None — callers must fail, not index-fallback into unrelated plates.
    """
    if not filenames:
        return None

    pose_key = (pose_name or "").strip().lower()
    if pose_key:
        named = [fn for fn in filenames if pose_key in fn.lower()]
        if named:
            named.sort(key=lambda fn: (-_patch_score(fn), fn.lower()))
            return named[0]

    token_hits = [fn for fn in filenames if _pose_token_matches(fn, pose_index)]
    if token_hits:
        token_hits.sort(key=lambda fn: (-_patch_score(fn), fn.lower()))
        return token_hits[0]
    return None


def unique_pose_index(segments: list[dict], pose_name: str, segment_index: int) -> int:
    """1-based index among first occurrences of each pose name."""
    seen: list[str] = []
    for idx, seg in enumerate(segments):
        name = (seg.get("pose") or "").strip() or f"__seg_{idx}"
        if name not in seen:
            seen.append(name)
        if idx == segment_index:
            return seen.index(name) + 1
    return segment_index + 1


def list_scene_masterframes(search_dirs: Iterable[str], scene_id: str) -> list[str]:
    """Return sorted absolute paths of masterframes for this scene, excluding plates."""
    found: list[str] = []
    seen: set[str] = set()
    for sdir in search_dirs:
        if not os.path.isdir(sdir):
            continue
        for fname in sorted(os.listdir(sdir), key=str.lower):
            if not filename_belongs_to_scene(fname, scene_id):
                continue
            if is_excluded_plate(fname):
                continue
            full = os.path.abspath(os.path.join(sdir, fname))
            key = os.path.normcase(full)
            if key in seen:
                continue
            seen.add(key)
            found.append(full)
    found.sort(key=lambda p: os.path.basename(p).lower())
    return found
