"""Expanding click ripple. Mutates a copy only."""

from __future__ import annotations

from PIL import Image, ImageDraw


class PulseFX:
    """Circular shockwave for button click / challenge start."""

    @staticmethod
    def apply(
        canvas: Image.Image,
        center: tuple[int, int],
        t: float,
        trigger_time: float,
        duration: float = 0.8,
        max_radius: int = 120,
        color: tuple[int, int, int] = (255, 107, 0),
    ) -> Image.Image:
        canvas = canvas.copy()
        if t < trigger_time or t > trigger_time + duration:
            return canvas

        dt = (t - trigger_time) / duration
        radius = max(1, int(max_radius * dt))
        alpha = int(220 * (1.0 - dt))
        overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        cx, cy = center
        draw.ellipse(
            [cx - radius, cy - radius, cx + radius, cy + radius],
            outline=(*color, alpha),
            width=3,
        )
        canvas.paste(overlay, (0, 0), overlay)
        return canvas
