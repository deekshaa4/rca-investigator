"""Everyday chat ("hi", "I'll send it in a minute", "thanks") answered from replies.md.

The replies live in a plain Markdown file, not in code, so they're easy to read and
extend. Matching is simple word matching: no language model, so replies are instant.
"""

from __future__ import annotations

import random
import re
from collections import deque
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

REPLIES_FILE = Path(__file__).parent / "replies.md"
MAX_SMALLTALK_CHARS = 300


@dataclass
class Intent:
    name: str
    patterns: list[re.Pattern]
    replies: list[str]


@lru_cache(maxsize=4)
def load_intents(path: Path = REPLIES_FILE) -> tuple[Intent, ...]:
    intents, current = [], None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            current = Intent(line[3:].strip(), [], [])
            intents.append(current)
        elif current is not None and line.lower().startswith("match:"):
            for phrase in line.split(":", 1)[1].split(","):
                phrase = phrase.strip().lower()
                if phrase:
                    current.patterns.append(
                        re.compile(rf"(?<![a-z']){re.escape(phrase)}(?![a-z'])"))
        elif current is not None and line.startswith("- "):
            current.replies.append(line[2:].strip())
    return tuple(i for i in intents if i.replies)


def match_intent(message: str, path: Path = REPLIES_FILE) -> Intent | None:
    """The first situation (in file order) whose words appear in the message."""
    text = re.sub(r"[’`]", "'", message.lower())
    if not text.strip() or len(text) > MAX_SMALLTALK_CHARS:
        return None
    return next((i for i in load_intents(path) if any(p.search(text) for p in i.patterns)), None)


def reply_for(name: str, recent: deque, **fill: str) -> str:
    """A reply from a named section (used by code, e.g. "share_first"), with {fields} filled."""
    intent = next(i for i in load_intents() if i.name == name)
    return pick_reply(intent, recent).format(**fill)


def pick_reply(intent: Intent, recent: deque) -> str:
    """A reply for this situation that hasn't been used recently."""
    fresh = [r for r in intent.replies if r not in recent] or intent.replies
    reply = random.choice(fresh)
    recent.append(reply)
    return reply
