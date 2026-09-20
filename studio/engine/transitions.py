"""2.5D-style page wipe with a crease shadow (hard crop, no text feathering)."""

from __future__ import annotations

import math

from PIL import Image, ImageDraw


class PageFlipTransition:
    """Right-to-left fold wipe. progress 0 = previous page, 1 = next page."""

    @staticmethod
    def render(prev_img: Image.Image, next_img: Image.Image, progress: float) -> Image.Image:
        if progress <= 0.0:
            return prev_img.copy()
        if progress >= 1.0:
            return next_img.copy()

        w, h = prev_img.size
        p = 0.5 - 0.5 * math.cos(progress * math.pi)
        fold_x = int(w * (1.0 - p))
        canvas = next_img.copy()

        if fold_x > 0:
            left_slice = prev_img.crop((0, 0, fold_x, h))
            canvas.paste(left_slice, (0, 0))
            shadow_w = min(48, int(w * 0.05), fold_x)
            if shadow_w > 0:
                shadow_x = fold_x - shadow_w
                shadow_overlay = Image.new("RGBA", (shadow_w, h), (0, 0, 0, 0))
                draw = ImageDraw.Draw(shadow_overlay)
                for i in range(shadow_w):
                    alpha = int(140 * (i / shadow_w) * (1.0 - p * 0.5))
                    draw.line([(i, 0), (i, h)], fill=(20, 15, 10, alpha))
                canvas.paste(shadow_overlay, (shadow_x, 0), shadow_overlay)
        return canvas
