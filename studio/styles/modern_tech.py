from studio.styles.base import StyleProfile

class ModernTechStyle(StyleProfile):
    """
    Modern tech / SaaS style:
    Deep dark navy background (#0F172A), cyber cyan / neon blue accents,
    glassmorphism subtitles, glowing highlights.
    """
    def __init__(self):
        super().__init__(
            name="modern_tech",
            description="现代极客科技 SaaS 风",
            background_color=(15, 23, 42),
            primary_accent=(56, 189, 248),   # Cyber sky blue
            secondary_accent=(168, 85, 247), # Cyber purple
            text_color=(241, 245, 249),
            subtitle_bg=(15, 23, 42, 220),
            subtitle_text=(248, 250, 252, 255),
            subtitle_font_size=38,
            subtitle_max_width=920,
            subtitle_y=1680,
            stamp_color=(56, 189, 248)
        )
