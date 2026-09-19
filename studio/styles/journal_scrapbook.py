from studio.styles.base import StyleProfile

class JournalScrapbookStyle(StyleProfile):
    """
    Classic vintage journal / scrapbook paper cutout style:
    Warm off-white textured kraft (#FAF7F2), Song/Hei print black,
    neon orange highlighter, cinnabar red stamp impact.
    """
    def __init__(self):
        super().__init__(
            name="journal_scrapbook",
            description="杂志折页手账风 · 纸片人定格拼贴",
            background_color=(250, 247, 242),
            primary_accent=(255, 107, 0),
            secondary_accent=(16, 185, 129),
            text_color=(24, 24, 27),
            subtitle_bg=(24, 24, 27, 205),
            subtitle_text=(255, 255, 255, 255),
            subtitle_font_size=40,
            subtitle_max_width=920,
            subtitle_y=1680,
            stamp_color=(220, 38, 38)
        )
