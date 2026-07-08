from typing import Optional


def parse_score(text: Optional[str]) -> Optional[float]:
    """Parse a Polish-locale decimal score like '7,6' into 7.6."""
    if not text:
        return None
    text = text.strip().replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return None
