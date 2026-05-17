"""Whitelist категорий долгосрочной памяти (редактируемый список)."""

ALLOWED_MEMORY_CATEGORIES: frozenset[str] = frozenset(
    {
        "name",
        "hobby",
        "preference",
        "progress",
        "note",
    }
)
