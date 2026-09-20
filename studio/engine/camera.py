"""Subtle Ken Burns push-in and Stop-Motion Kinetic Bounce. Always copies the input frame."""

from __future__ import annotations

import math
from PIL import Image


class KenBurnsZoom:
    """Organic slow zoom (1.000x -> ~1.03x) without motion sickness."""

    @staticmethod
    def get_scale(progress: float, max_scale: float = 1.030) -> float:
        if progress <= 0.0:
            return 1.0
        return 1.0 + (max_scale - 1.0) * max(0.0, min(1.0, progress))

    @staticmethod
    def apply(frame: Image.Image, progress: float, max_scale: float = 1.030) -> Image.Image:
        scale = KenBurnsZoom.get_scale(progress, max_scale)
        return CameraDirector.apply_scale(frame, scale)


class StopMotionBounce:
    """Organic spring punch (Scale: 1.000 -> ~1.024 -> 0.995 -> 1.000) on jump-cut pose transitions.

    Mimics handcrafted claymation/puppetry tactile kinetic response when changing poses.
    """

    @staticmethod
    def get_scale(
        t: float,
        cut_times: list[float],
        duration: float = 0.16,
        max_punch: float = 0.024,
    ) -> float:
        """Calculates kinetic spring bounce factor at time t."""
        if not cut_times:
            return 1.0

        recent_cut = -1.0
        for ct in cut_times:
            if ct <= t < ct + duration:
                recent_cut = ct
                break

        if recent_cut < 0:
            return 1.0

        tau = (t - recent_cut) / duration
        spring = math.sin(math.pi * tau) * (1.0 - 0.35 * tau)
        return 1.0 + max_punch * spring


class CameraDirector:
    """Single-pass subpixel camera cropping and resampling engine."""

    @staticmethod
    def apply_scale(frame: Image.Image, scale: float) -> Image.Image:
        frame = frame.copy()
        if abs(scale - 1.0) < 0.0005:
            return frame

        w, h = frame.size
        crop_w = max(2, int(w / scale))
        crop_h = max(2, int(h / scale))
        if crop_w % 2:
            crop_w -= 1
        if crop_h % 2:
            crop_h -= 1
        left = (w - crop_w) // 2
        top = (h - crop_h) // 2
        cropped = frame.crop((left, top, left + crop_w, top + crop_h))
        return cropped.resize((w, h), Image.Resampling.BILINEAR)

    @classmethod
    def apply_combined(
        cls,
        frame: Image.Image,
        push_progress: float,
        t: float,
        cut_times: list[float],
        max_zoom: float = 1.030,
    ) -> Image.Image:
        """Applies slow Ken Burns zoom AND stop-motion kinetic punch in a single resampling pass."""
        zoom_scale = KenBurnsZoom.get_scale(push_progress, max_zoom)
        bounce_scale = StopMotionBounce.get_scale(t, cut_times)
        combined_scale = zoom_scale * bounce_scale
        return cls.apply_scale(frame, combined_scale)
