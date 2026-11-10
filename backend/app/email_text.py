import re


def norm(text: str) -> str:
    """Lowercase and collapse everything that is not a letter or digit into single spaces."""
    return re.sub(r"[^a-z0-9]+", " ", (text or "").lower()).strip()
