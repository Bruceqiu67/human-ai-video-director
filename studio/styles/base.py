"""Visual and aesthetic parameters shared by style presets."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class StyleProfile:
    """Encapsulates palette, captions, transitions, and prompt locks."""

    name: str = "base"
    description: str = "Base style profile"

    background_color: tuple[int, int, int] = (250, 247, 242)
    primary_accent: tuple[int, int, int] = (255, 107, 0)
    secondary_accent: tuple[int, int, int] = (16, 185, 129)
    text_color: tuple[int, int, int] = (24, 24, 27)

    subtitle_bg: tuple[int, int, int, int] = (24, 24, 27, 205)
    subtitle_text: tuple[int, int, int, int] = (255, 255, 255, 255)
    subtitle_font_size: int = 40
    subtitle_max_width: int = 920
    subtitle_y: int = 1680

    default_page_flip_dur: float = 0.65
    stamp_color: tuple[int, int, int] = (220, 38, 38)

    def subtitle_layout(self, resolution: tuple[int, int]) -> tuple[int, int]:
        """Scale caption width and y to the actual canvas."""
        width, height = resolution
        max_width = max(80, int(width * (self.subtitle_max_width / 1080)))
        y_center = int(height * (self.subtitle_y / 1920))
        return max_width, y_center

    def prompt_background_lines(self) -> list[str]:
        return [
            "- Warm off-white textured grid kraft paper background (#FAF7F2), vertical bookbinding crease with subtle soft center shadow, faint technical grid ruler lines, sleek silver mechanical pencil lying diagonally at the bottom left corner.",
        ]

    def prompt_character_lock(self) -> str:
        return "Character silhouette has a crisp, precise 15px pure white sticker paper-cut outline with a soft natural drop shadow."
