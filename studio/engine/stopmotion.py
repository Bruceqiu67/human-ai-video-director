import os
from PIL import Image

class StopMotionSequencer:
    """
    Manages discrete jump-cuts between model-native in-context masterframes.
    Enforces the Non-Negotiable Red Line: ZERO sinusoidal continuous wobble.
    """
    
    def __init__(self, segments: list, pose_images: dict, default_img: Image.Image):
        self.segments = segments
        self.pose_images = pose_images
        self.default_img = default_img
        
    def get_frame(self, t: float) -> Image.Image:
        """Determines which pose image should be shown at timestamp t."""
        active_seg = None
        for seg in self.segments:
            if seg["start"] <= t <= seg["end"]:
                active_seg = seg
                break
                
        # If between segments or after last segment, find the closest preceding segment
        if not active_seg:
            preceding = [s for s in self.segments if s["end"] <= t]
            if preceding:
                active_seg = preceding[-1]
            elif self.segments:
                active_seg = self.segments[0]
                
        if not active_seg:
            return self.default_img
            
        pose_key = active_seg.get("pose", "")
        # Look up image by pose name or by segment index
        if pose_key in self.pose_images:
            return self.pose_images[pose_key]
            
        seg_id = active_seg.get("id", "")
        if seg_id in self.pose_images:
            return self.pose_images[seg_id]
            
        return self.default_img
