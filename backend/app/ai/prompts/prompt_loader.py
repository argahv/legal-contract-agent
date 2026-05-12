"""Filesystem-backed prompts — versioned markdown keeps product/legal review diffs readable."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

_PROMPT_DIR = Path(__file__).resolve().parent


@lru_cache
def read_prompt_file(filename: str) -> str:
    return (_PROMPT_DIR / filename).read_text(encoding="utf-8")
