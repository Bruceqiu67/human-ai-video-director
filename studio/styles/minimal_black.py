from studio.styles.base import StyleProfile


class MinimalBlackStyle(StyleProfile):
    """Monochrome, high-contrast modern minimalist aesthetic."""

    def __init__(self):
        super().__init__(
            name="minimal_black",
            description="极简黑白高反差风 · 纯粹理性设计",
            background_color=(18, 18, 18),
            primary_accent=(245, 245, 245),
            secondary_accent=(163, 163, 163),
            text_color=(245, 245, 245),
            subtitle_bg=(245, 245, 245, 235),
            subtitle_text=(18, 18, 18, 255),
            subtitle_font_size=38,
            subtitle_max_width=920,
            subtitle_y=1680,
            stamp_color=(245, 245, 245),
        )

    def prompt_background_lines(self) -> list[str]:
        return [
            "- Pure monochrome minimal dark background (#121212), crisp architectural typography grid, stark studio rim lighting, bold high-contrast Bauhaus layout, zero decorative clutter.",
        ]

    def prompt_character_lock(self) -> str:
        return "Character is a clean monochrome or high-contrast silhouette cutout with sharp rim highlights; keep identity locked across poses."
