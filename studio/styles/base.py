from dataclasses import dataclass, field

@dataclass
class StyleProfile:
    """Encapsulates all visual and aesthetic parameters to decouple theme from render engine."""
    name: str = "base"
    description: str = "Base style profile"
    
    # Palette
    background_color: tuple[int, int, int] = (250, 247, 242) # Warm kraft off-white
    primary_accent: tuple[int, int, int] = (255, 107, 0)     # Neon orange
    secondary_accent: tuple[int, int, int] = (16, 185, 129)  # Emerald green
    text_color: tuple[int, int, int] = (24, 24, 27)          # Print black
    
    # Subtitle styling
    subtitle_bg: tuple[int, int, int, int] = (24, 24, 27, 205)
    subtitle_text: tuple[int, int, int, int] = (255, 255, 255, 255)
    subtitle_font_size: int = 40
    subtitle_max_width: int = 920
    subtitle_y: int = 1680
    
    # Transition defaults
    default_page_flip_dur: float = 0.65
    
    # Stamp defaults
    stamp_color: tuple[int, int, int] = (220, 38, 38) # Vintage cinnabar red
