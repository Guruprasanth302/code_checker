"""
utils.py — Helper utilities for the Code Quality Checker.
"""

import re


def parse_checklist(raw_text: str) -> list[str]:
    """
    Parses a multi-line checklist string into a clean list of items.

    Handles formats like:
      - "1. Item text"
      - "- Item text"
      - "* Item text"
      - "Item text"  (plain lines)
    """
    items = []
    for line in raw_text.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        # Strip leading bullets / numbers: "1.", "-", "*", "•"
        cleaned = re.sub(r"^[\d]+[.)]\s*|^[-*•]\s*", "", line).strip()
        if cleaned:
            items.append(cleaned)
    return items
