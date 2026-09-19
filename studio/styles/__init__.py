from studio.styles.base import StyleProfile
from studio.styles.journal_scrapbook import JournalScrapbookStyle
from studio.styles.modern_tech import ModernTechStyle

STYLE_REGISTRY = {
    "journal_scrapbook": JournalScrapbookStyle,
    "modern_tech": ModernTechStyle,
}

def get_style(name: str) -> StyleProfile:
    cls = STYLE_REGISTRY.get(name.lower(), JournalScrapbookStyle)
    return cls()
