from studio.styles.base import StyleProfile
from studio.styles.journal_scrapbook import JournalScrapbookStyle
from studio.styles.modern_tech import ModernTechStyle

STYLE_REGISTRY = {
    "journal_scrapbook": JournalScrapbookStyle,
    "modern_tech": ModernTechStyle,
}


def get_style(name: str | None) -> StyleProfile:
    if not name:
        return JournalScrapbookStyle()
    key = str(name).strip().lower().replace("-", "_")
    if key not in STYLE_REGISTRY:
        available = ", ".join(sorted(STYLE_REGISTRY))
        raise ValueError(f"Unknown style {name!r}. Available: {available}")
    return STYLE_REGISTRY[key]()
