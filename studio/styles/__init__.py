from studio.styles.base import StyleProfile
from studio.styles.clay_3d import Clay3DStyle
from studio.styles.journal_scrapbook import JournalScrapbookStyle
from studio.styles.minimal_black import MinimalBlackStyle
from studio.styles.modern_tech import ModernTechStyle

STYLE_REGISTRY = {
    "journal_scrapbook": JournalScrapbookStyle,
    "modern_tech": ModernTechStyle,
    "clay_3d": Clay3DStyle,
    "clay": Clay3DStyle,
    "minimal_black": MinimalBlackStyle,
    "minimal": MinimalBlackStyle,
    "custom": JournalScrapbookStyle,
}


def get_style(name: str | None) -> StyleProfile:
    if not name:
        return JournalScrapbookStyle()
    key = str(name).strip().lower().replace("-", "_")
    if key not in STYLE_REGISTRY:
        available = ", ".join(sorted(STYLE_REGISTRY))
        raise ValueError(f"Unknown style {name!r}. Available: {available}")
    return STYLE_REGISTRY[key]()
