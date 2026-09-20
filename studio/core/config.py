"""Storyboard YAML/JSON loader — single source of truth for script structure."""

from __future__ import annotations

import json
import os

try:
    import yaml
except ImportError:
    yaml = None


class StoryboardConfig:
    """Parser and container for storyboard.yaml configuration."""

    def __init__(self, data: dict, config_path: str = ""):
        if not isinstance(data, dict):
            raise ValueError(f"Storyboard root must be a mapping, got {type(data).__name__}.")
        self.raw = data
        self.config_path = config_path
        self.project_dir = os.path.dirname(config_path) if config_path else os.getcwd()

        proj = data.get("project") or {}
        if not isinstance(proj, dict):
            raise ValueError("'project' must be a mapping.")

        self.name = proj.get("name", "untitled_project")
        self.title = proj.get("title", "未命名短视频")
        resolution = proj.get("resolution", [1080, 1920])
        if not isinstance(resolution, (list, tuple)) or len(resolution) != 2:
            raise ValueError("project.resolution must be [width, height].")
        self.resolution = (int(resolution[0]), int(resolution[1]))
        self.fps = int(proj.get("fps", 30))
        self.style_preset = proj.get("style_preset") or "journal_scrapbook"

        audio = proj.get("audio") or {}
        if not isinstance(audio, dict):
            raise ValueError("'project.audio' must be a mapping.")
        self.voice = audio.get("voice", "zh-CN-YunxiNeural")
        self.rate = audio.get("rate", "+20%")
        self.bgm_volume_active = float(audio.get("bgm_volume_active", 0.12))
        self.bgm_volume_idle = float(audio.get("bgm_volume_idle", 0.25))
        self.bgm_file = audio.get("bgm_file", "") or ""

        character = proj.get("character") or {}
        if isinstance(character, str):
            self.character_prompt = character
        elif isinstance(character, dict):
            self.character_prompt = character.get(
                "prompt",
                "a young presenter matching the user-supplied reference portrait; "
                "keep identity, hair, glasses and outfit consistent across poses",
            )
        else:
            raise ValueError("'project.character' must be a string or mapping.")

        if "scenes" not in data:
            scenes = []
        else:
            scenes = data.get("scenes")
        if not isinstance(scenes, list):
            raise ValueError("'scenes' must be a list.")
        for idx, sc in enumerate(scenes):
            if not isinstance(sc, dict):
                raise ValueError(f"Scene #{idx + 1} must be a mapping.")
            sid = (sc.get("id") or "").strip()
            if not sid:
                raise ValueError(f"Scene #{idx + 1} is missing a non-empty 'id'.")
            if ".." in sid or "/" in sid or "\\" in sid:
                raise ValueError(f"Invalid scene id {sid!r} (path separators not allowed).")
        self.scenes = scenes

    @classmethod
    def load(cls, file_path: str) -> "StoryboardConfig":
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Config file not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as handle:
            content = handle.read()

        try:
            if file_path.endswith((".yaml", ".yml")):
                if yaml is None:
                    raise ImportError("PyYAML is not installed. Please run 'pip install pyyaml'")
                data = yaml.safe_load(content)
            elif file_path.endswith(".json"):
                data = json.loads(content)
            elif yaml:
                try:
                    data = yaml.safe_load(content)
                except yaml.YAMLError as exc:
                    raise ValueError(f"Failed to parse {file_path} as YAML: {exc}") from exc
            else:
                data = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Failed to parse {file_path} as JSON: {exc}") from exc

        if not isinstance(data, dict):
            raise ValueError(f"Storyboard {file_path} is empty or not a mapping.")
        return cls(data, os.path.abspath(file_path))

    def get_scene(self, scene_id_or_num):
        """Retrieve scene config by string id (e.g. 'scene_01') or 1-based index."""
        try:
            num = int(scene_id_or_num)
            idx = num - 1
            if 0 <= idx < len(self.scenes):
                return self.scenes[idx]
        except (ValueError, TypeError):
            pass

        target = str(scene_id_or_num).strip().lower()
        for sc in self.scenes:
            sc_id = sc.get("id", "").lower()
            if sc_id == target or sc_id.replace("_", "") == target.replace("_", ""):
                return sc

        if target.isdigit():
            formatted = f"scene_{int(target):02d}"
            for sc in self.scenes:
                if sc.get("id", "").lower() == formatted:
                    return sc
        return None


ConfigParser = StoryboardConfig

__all__ = ["StoryboardConfig", "ConfigParser"]
