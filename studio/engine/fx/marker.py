"""Fluorescent highlighter sweep. Mutates a copy only."""

from __future__ import annotations

from PIL import Image, ImageDraw


class MarkerFX:
    """Semi-transparent highlighter stroke growing from left to right."""

    @staticmethod
    def apply(
        canvas: Image.Image,
        bbox: tuple[int, int, int, int],
        progress: float,
        color: tuple[int, int, int, int] = (255, 107, 0, 110),
    ) -> Image.Image:
        canvas = canvas.copy()
        if progress <= 0.0:
            return canvas

        p = min(1.0, progress)
        x1, y1, x2, y2 = bbox
        if x2 < x1:
            x1, x2 = x2, x1
        if y2 < y1:
            y1, y2 = y2, y1
        current_x2 = int(x1 + (x2 - x1) * p)
        if current_x2 <= x1:
            return canvas

        overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        radius = max(1, abs(y2 - y1) // 3)
        draw.rounded_rectangle([x1, y1, current_x2, y2], radius=radius, fill=color)
        canvas.paste(overlay, (0, 0), overlay)
        return canvas
