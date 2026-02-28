from __future__ import annotations

import re
from urllib.parse import urlparse


_CAMPAIGN_RE = re.compile(r"/campaigns/(\d+)")
_CHARACTER_RE = re.compile(r"/characters/(\d+)")


def extract_campaign_id(url: str) -> str | None:
    path = urlparse(url).path
    match = _CAMPAIGN_RE.search(path)
    return match.group(1) if match else None


def extract_character_id(url: str) -> str | None:
    path = urlparse(url).path
    match = _CHARACTER_RE.search(path)
    return match.group(1) if match else None
