import os
import json

class TimestampManifest:
    """Manages the timestamps manifest - Single Source of Truth for subtitles and sync."""
    
    def __init__(self, data: dict = None, file_path: str = ""):
        self.data = data or {}
        self.file_path = file_path
        
    @classmethod
    def load(cls, file_path: str) -> "TimestampManifest":
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return cls(data, file_path)
        return cls({}, file_path)
        
    def save(self, file_path: str = ""):
        target = file_path or self.file_path
        if not target:
            raise ValueError("No file path specified for saving manifest.")
        os.makedirs(os.path.dirname(os.path.abspath(target)), exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
            
    def set_scene_segments(self, scene_id: str, segments: list, total_duration: float):
        self.data[scene_id] = {
            "total_duration": round(total_duration, 3),
            "segments": segments
        }
        
    def get_scene(self, scene_id: str):
        return self.data.get(scene_id)
