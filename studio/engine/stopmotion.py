"""Discrete jump-cuts between in-context masterframes. No sinusoidal wiggle."""

from __future__ import annotations

from PIL import Image


class StopMotionSequencer:
    """Holds the last pose during breath pauses; never interpolates characters."""

    def __init__(self, segments: list, pose_images: dict, default_img: Image.Image):
        self.segments = sorted(
            [s for s in segments if "start" in s and "end" in s],
            key=lambda s: s["start"],
        )
        self.pose_images = pose_images
        self.default_img = default_img

    def get_frame(self, t: float) -> Image.Image:
        active = None
        for seg in self.segments:
            if seg["start"] <= t < seg["end"]:
                active = seg
        if active is None:
            preceding = [s for s in self.segments if s["end"] <= t]
            if preceding:
                active = max(preceding, key=lambda s: s["end"])
            elif self.segments:
                active = self.segments[0]
        if not active:
            return self.default_img

        pose_key = active.get("pose", "")
        if pose_key in self.pose_images:
            return self.pose_images[pose_key]
        seg_id = active.get("id", "")
        if seg_id in self.pose_images:
            return self.pose_images[seg_id]
        return self.default_img
