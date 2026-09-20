"""Subtle Ken Burns push-in. Always copies the input frame."""

from __future__ import annotations

from PIL import Image


class KenBurnsZoom:
    """Organic slow zoom (1.000x -> ~1.03x) without motion sickness."""

    @staticmethod
    def apply(frame: Image.Image, progress: float, max_scale: float = 1.030) -> Image.Image:
        frame = frame.copy()
        if progress <= 0.0:
            return frame

        w, h = frame.size
        scale = 1.0 + (max_scale - 1.0) * max(0.0, min(1.0, progress))
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
