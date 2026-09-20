from studio.styles.base import StyleProfile


class ModernTechStyle(StyleProfile):
    """Modern tech / SaaS style: deep navy, cyber cyan, glass captions."""

    def __init__(self):
        super().__init__(
            name="modern_tech",
            description="现代极客科技 SaaS 风",
            background_color=(15, 23, 42),
            primary_accent=(56, 189, 248),
            secondary_accent=(168, 85, 247),
            text_color=(241, 245, 249),
            subtitle_bg=(15, 23, 42, 220),
            subtitle_text=(248, 250, 252, 255),
            subtitle_font_size=38,
            subtitle_max_width=920,
            subtitle_y=1680,
            stamp_color=(56, 189, 248),
        )

    def prompt_background_lines(self) -> list[str]:
        return [
            "- Deep navy (#0F172A) technical grid, faint cyan circuit traces, glassmorphism cards with hairline borders, no kraft paper, no pencil.",
        ]

    def prompt_character_lock(self) -> str:
        return "Character is a clean vector-adjacent cutout with a thin cyan rim light; keep identity locked across poses."
