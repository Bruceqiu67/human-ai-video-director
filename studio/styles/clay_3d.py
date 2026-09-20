from studio.styles.base import StyleProfile


class Clay3DStyle(StyleProfile):
    """Warm, tactile 3D polymer clay / stop-motion aesthetic."""

    def __init__(self):
        super().__init__(
            name="clay_3d",
            description="3D 黏土定格风 · 软萌实体感",
            background_color=(245, 240, 235),
            primary_accent=(234, 88, 12),
            secondary_accent=(132, 169, 140),
            text_color=(38, 38, 38),
            subtitle_bg=(40, 40, 40, 210),
            subtitle_text=(255, 255, 255, 255),
            subtitle_font_size=40,
            subtitle_max_width=920,
            subtitle_y=1680,
            stamp_color=(225, 29, 72),
        )

    def prompt_background_lines(self) -> list[str]:
        return [
            "- Warm soft studio matte background, tactile polymer clay textures, subtle handcrafted clay thumbprints, soft diffused tabletop studio lighting and gentle ambient occlusion shadows, miniature diorama aesthetic.",
        ]

    def prompt_character_lock(self) -> str:
        return "Character is sculpted from colorful polymer clay (Plasticine / Fimo style), visible subtle tactile texture, matte surface with soft ambient occlusion; keep identity locked across poses."
