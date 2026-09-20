"""Vintage seal slam. Mutates a copy only."""

from __future__ import annotations

import math

from PIL import Image


class StampFX:
    """Damped spring stamp. Visible from trigger_time onward."""

    @staticmethod
    def apply(
        canvas: Image.Image,
        stamp_img: Image.Image,
        t: float,
        trigger_time: float,
        pos: tuple[int, int],
        duration: float = 0.45,
    ) -> Image.Image:
        if t < trigger_time:
            return canvas.copy()

        canvas = canvas.copy()
        dt = t - trigger_time
        if dt < duration:
            scale = 1.0 + 0.35 * math.exp(-12.0 * dt) * math.cos(30.0 * dt)
            shake_y = int(5.0 * math.exp(-10.0 * dt) * math.sin(40.0 * dt))
        else:
            scale = 1.0
            shake_y = 0

        sw, sh = stamp_img.size
        new_w = max(1, int(sw * scale))
        new_h = max(1, int(sh * scale))
        scaled_stamp = stamp_img.resize((new_w, new_h), Image.Resampling.BILINEAR)
        target_x = pos[0] - new_w // 2
        target_y = pos[1] - new_h // 2 + shake_y
        overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        overlay.paste(scaled_stamp, (target_x, target_y), scaled_stamp if scaled_stamp.mode == "RGBA" else None)
        canvas.paste(overlay, (0, 0), overlay)
        return canvas
