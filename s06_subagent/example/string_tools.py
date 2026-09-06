"""string_tools: small string manipulation helpers.

Currently provides ``slugify``, which converts arbitrary text into a
URL-friendly slug.
"""

import re
import unicodedata


def slugify(text: str) -> str:
    """Convert ``text`` into a URL-friendly slug.

    The result is lowercase, has runs of whitespace and non-alphanumeric
    characters collapsed into single hyphens, and has no leading or
    trailing hyphens. Unicode characters are normalized and reasonable
    transliterations are applied (e.g. accents are stripped), so "Café"
    becomes "cafe".

    Examples:
        >>> slugify("Hello, World!")
        'hello-world'
        >>> slugify("  Foo   Bar  ")
        'foo-bar'
        >>> slugify("Café")
        'cafe'
    """
    # Normalize unicode (NFKD) and strip combining marks, so e.g. "é" -> "e".
    normalized = unicodedata.normalize("NFKD", text)
    ascii_ish = normalized.encode("ascii", "ignore").decode("ascii")

    # Lowercase, then replace any run of non-alphanumeric characters
    # (including whitespace) with a single hyphen.
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_ish.lower())

    # Remove leading/trailing hyphens.
    return slug.strip("-")
