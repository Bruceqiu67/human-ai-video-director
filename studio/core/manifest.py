"""Timestamp manifest — subtitle/pose clock produced by audio build."""

from __future__ import annotations

import json
import os


class TimestampManifest:
    """Manages the timestamps manifest — clock for subtitles and stop-motion."""

    def __init__(self, data: dict | None = None, file_path: str = ""):
        self.data = data or {}
        self.file_path = file_path

    @classmethod
    def load(cls, file_path: str) -> "TimestampManifest":
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as handle:
                    data = json.load(handle)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Corrupt timestamp manifest {file_path}: {exc}") from exc
            if not isinstance(data, dict):
                raise ValueError(f"Timestamp manifest {file_path} must be a JSON object.")
            return cls(data, file_path)
        return cls({}, file_path)

    def save(self, file_path: str = "") -> None:
        target = file_path or self.file_path
        if not target:
            raise ValueError("No file path specified for saving manifest.")
        os.makedirs(os.path.dirname(os.path.abspath(target)), exist_ok=True)
        with open(target, "w", encoding="utf-8") as handle:
            json.dump(self.data, handle, ensure_ascii=False, indent=2)

    def set_scene_segments(self, scene_id: str, segments: list, total_duration: float) -> None:
        self.data[scene_id] = {
            "total_duration": round(total_duration, 3),
            "segments": segments,
        }

    def get_scene(self, scene_id: str):
        return self.data.get(scene_id)

    def assert_matches_storyboard(self, scene: dict) -> None:
        scene_id = scene.get("id")
        data = self.get_scene(scene_id)
        if not data:
            raise ValueError(
                f"Manifest has no record for {scene_id}. Run 'python -m studio audio build' first."
            )
        yaml_segs = scene.get("dialogue_segments") or []
        man_segs = data.get("segments") or []
        if len(yaml_segs) != len(man_segs):
            raise ValueError(
                f"Manifest for {scene_id} has {len(man_segs)} segments but storyboard has "
                f"{len(yaml_segs)}. Re-run: python -m studio audio build"
            )
        for yaml_seg, man_seg in zip(yaml_segs, man_segs):
            yaml_text = (yaml_seg.get("text") or "").strip()
            man_text = (man_seg.get("text") or "").strip()
            if yaml_text != man_text:
                raise ValueError(
                    f"Storyboard/manifest text mismatch for {yaml_seg.get('id', scene_id)}.\n"
                    f"  yaml: {yaml_text}\n"
                    f"  manifest: {man_text}\n"
                    "Re-run: python -m studio audio build"
                )
            yaml_pose = (yaml_seg.get("pose") or "").strip()
            man_pose = (man_seg.get("pose") or "").strip()
            if yaml_pose and man_pose and yaml_pose != man_pose:
                raise ValueError(
                    f"Storyboard/manifest pose mismatch for {yaml_seg.get('id', scene_id)}: "
                    f"{yaml_pose!r} vs {man_pose!r}. Re-run audio build."
                )
