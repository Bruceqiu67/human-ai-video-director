"""Centered rounded-capsule subtitles with guaranteed width fit."""

from __future__ import annotations

import os

from PIL import Image, ImageDraw, ImageFont


class AdaptiveCapsuleSubtitle:
    """Modern centered rounded capsule. Text is shrunk and wrapped until it fits."""

    def __init__(
        self,
        font_path: str = "",
        default_font_size: int = 40,
        max_width: int = 920,
        fill: tuple[int, int, int, int] = (24, 24, 27, 205),
        text_fill: tuple[int, int, int, int] = (255, 255, 255, 255),
    ):
        self.font_path = font_path
        self.default_font_size = default_font_size
        self.max_width = max_width
        self.fill = fill
        self.text_fill = text_fill
        self._font_cache: dict[int, ImageFont.ImageFont] = {}

    def _get_font(self, size: int):
        if size not in self._font_cache:
            font = None
            if self.font_path and os.path.exists(self.font_path):
                try:
                    font = ImageFont.truetype(self.font_path, size)
                except Exception:
                    font = None
            if font is None:
                candidates = [
                    "C:/Windows/Fonts/msyh.ttc",
                    "C:/Windows/Fonts/simhei.ttf",
                    "C:/Windows/Fonts/msyhl.ttc",
                    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                ]
                for path in candidates:
                    if os.path.exists(path):
                        try:
                            font = ImageFont.truetype(path, size)
                            break
                        except Exception:
                            continue
            if font is None:
                font = ImageFont.load_default()
            self._font_cache[size] = font
        return self._font_cache[size]

    def _line_width(self, font, text: str) -> float:
        if not text:
            return 0.0
        try:
            return float(font.getlength(text))
        except Exception:
            return float(sum(font.getlength(ch) for ch in text))

    def _wrap(self, text: str, font) -> list[str]:
        if self._line_width(font, text) <= self.max_width:
            return [text]
        punct = "，、；。！？,;!? "
        lines: list[str] = []
        remaining = text
        while remaining:
            if self._line_width(font, remaining) <= self.max_width:
                lines.append(remaining)
                break
            cut = None
            for i in range(len(remaining) - 1, 0, -1):
                if self._line_width(font, remaining[:i]) <= self.max_width:
                    cut = i
                    break
            if cut is None:
                lines.append(remaining)
                break
            window = remaining[:cut]
            punct_at = max((window.rfind(p) for p in punct), default=-1)
            if punct_at >= max(1, int(len(window) * 0.35)):
                cut = punct_at + 1
            lines.append(remaining[:cut].strip())
            remaining = remaining[cut:].strip()
        return [ln for ln in lines if ln] or [text]

    def render(self, canvas: Image.Image, text: str, y_center: int = 1680) -> Image.Image:
        if not text:
            return canvas

        w, h = canvas.size
        max_width = min(self.max_width, max(40, w - 40))
        self.max_width = max_width

        target_size = self.default_font_size
        lines = [text]
        font = self._get_font(target_size)
        while target_size >= 18:
            font = self._get_font(target_size)
            lines = self._wrap(text, font)
            if all(self._line_width(font, ln) <= max_width for ln in lines):
                break
            target_size -= 2

        text_w = max(self._line_width(font, ln) for ln in lines)
        pad_x = 28
        pad_y = 14
        line_height = int(target_size * 1.25)
        capsule_w = int(min(w - 8, text_w + pad_x * 2))
        capsule_h = int(line_height * len(lines) + pad_y * 2)
        cap_x = max(4, min((w - capsule_w) // 2, w - capsule_w - 4))
        cap_y = max(4, min(y_center - capsule_h // 2, h - capsule_h - 4))

        overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        radius = min(24, max(4, capsule_h // 2))
        draw.rounded_rectangle(
            [cap_x, cap_y, cap_x + capsule_w, cap_y + capsule_h],
            radius=radius,
            fill=self.fill,
        )
        for idx, line in enumerate(lines):
            lw = self._line_width(font, line)
            line_x = cap_x + max(0, (capsule_w - lw) // 2)
            line_y = cap_y + pad_y + idx * line_height
            draw.text((line_x, line_y), line, font=font, fill=self.text_fill)

        canvas = canvas.copy()
        canvas.paste(overlay, (0, 0), overlay)
        return canvas
