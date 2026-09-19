import os
import json

try:
    import yaml
except ImportError:
    yaml = None

class StoryboardConfig:
    """Parser and container for storyboard.yaml configuration."""
    
    def __init__(self, data: dict, config_path: str = ""):
        self.raw = data
        self.config_path = config_path
        self.project_dir = os.path.dirname(config_path) if config_path else os.getcwd()
        
        # Project metadata
        proj = data.get("project", {})
        self.name = proj.get("name", "untitled_project")
        self.title = proj.get("title", "未命名短视频")
        self.resolution = tuple(proj.get("resolution", [1080, 1920]))
        self.fps = proj.get("fps", 30)
        self.style_preset = proj.get("style_preset", "journal_scrapbook")
        
        # Audio configuration
        audio = proj.get("audio", {})
        self.voice = audio.get("voice", "zh-CN-YunxiNeural")
        self.rate = audio.get("rate", "+20%")
        self.bgm_volume_active = audio.get("bgm_volume_active", 0.12)
        self.bgm_volume_idle = audio.get("bgm_volume_idle", 0.25)
        self.bgm_file = audio.get("bgm_file", "")
        
        # Scenes list
        self.scenes = data.get("scenes", [])
        
    @classmethod
    def load(cls, file_path: str) -> "StoryboardConfig":
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Config file not found: {file_path}")
            
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        if file_path.endswith(".yaml") or file_path.endswith(".yml"):
            if yaml is None:
                raise ImportError("PyYAML is not installed. Please run 'pip install pyyaml'")
            data = yaml.safe_load(content)
        elif file_path.endswith(".json"):
            data = json.loads(content)
        else:
            if yaml:
                try:
                    data = yaml.safe_load(content)
                except Exception:
                    data = json.loads(content)
            else:
                data = json.loads(content)
                
        return cls(data, os.path.abspath(file_path))

    def get_scene(self, scene_id_or_num):
        """Retrieve scene config by string id (e.g. 'scene_01') or 1-based index / number string."""
        # Try numeric index first
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
                
        # Try matching scene_XX
        if target.isdigit():
            formatted = f"scene_{int(target):02d}"
            for sc in self.scenes:
                if sc.get("id", "").lower() == formatted:
                    return sc
                    
        return None

# Backward compatibility & ergonomic alias
ConfigParser = StoryboardConfig

__all__ = ["StoryboardConfig", "ConfigParser"]

