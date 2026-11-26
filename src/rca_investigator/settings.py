"""Settings you can change from the control centre, saved to a small JSON file.

Behaviour settings are applied to the running app straight away; appearance settings
are sent to the chat page as CSS variables. Anything not set keeps its default.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from . import chat, documents, sufficiency
from .llm import DEFAULT_MODEL

DEFAULT_PATH = Path.home() / ".rca-investigator" / "settings.json"

FIELDS: dict[str, dict[str, Any]] = {
    # behaviour
    "model": {"default": DEFAULT_MODEL, "type": "text", "group": "Brain",
              "help": "Ollama model that writes the answers (e.g. qwen2.5:3b, qwen2.5:7b)."},
    "sufficient_at": {"default": 0.7, "type": "number", "min": 0.3, "max": 0.95, "step": 0.05,
                      "group": "Brain", "help": "Score needed to say 'sure' (sufficient)."},
    "partial_at": {"default": 0.45, "type": "number", "min": 0.1, "max": 0.9, "step": 0.05,
                   "group": "Brain", "help": "Score needed to say 'partly sure'."},
    "model_chunks": {"default": 6, "type": "number", "min": 1, "max": 20, "step": 1,
                     "group": "Brain",
                     "help": "Document pieces the AI reads closely (more = slower, more thorough)."},
    "paste_doc_chars": {"default": 400, "type": "number", "min": 100, "max": 5000, "step": 50,
                        "group": "Brain",
                        "help": "Pasted messages at least this long are read as a document."},
    "charts_default": {"default": "labels", "type": "choice",
                       "choices": ["labels", "local", "cloud"], "group": "Brain",
                       "help": "How charts in PDFs are read unless the user picks otherwise."},
    # appearance (sent to the chat page)
    "font": {"default": "system", "type": "choice", "group": "Look",
             "choices": ["system", "rounded", "serif", "mono"], "help": "Font of the chat page."},
    "font_size": {"default": 16, "type": "number", "min": 12, "max": 22, "step": 1,
                  "group": "Look", "help": "Base text size in pixels."},
    "accent": {"default": "#4f6bed", "type": "color", "group": "Look",
               "help": "Accent colour for buttons, your messages and highlights."},
    "radius": {"default": 16, "type": "number", "min": 0, "max": 28, "step": 2, "group": "Look",
               "help": "Roundness of bubbles and cards."},
    "composer_lines": {"default": 1, "type": "number", "min": 1, "max": 6, "step": 1,
                       "group": "Look", "help": "Height of the message box, in lines."},
    "density": {"default": "comfortable", "type": "choice", "group": "Look",
                "choices": ["compact", "comfortable", "roomy"], "help": "Spacing between messages."},
}
APPEARANCE = [k for k, f in FIELDS.items() if f["group"] == "Look"]
FONTS = {"system": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif",
         "rounded": "ui-rounded, 'SF Pro Rounded', 'Nunito', 'Segoe UI', sans-serif",
         "serif": "ui-serif, Georgia, 'Times New Roman', serif",
         "mono": "ui-monospace, 'SF Mono', Menlo, Consolas, monospace"}
SPACING = {"compact": 8, "comfortable": 14, "roomy": 22}


class Settings:
    def __init__(self, path: str | Path | None = DEFAULT_PATH):
        self.path = Path(path).expanduser() if path else None
        self.values = {k: f["default"] for k, f in FIELDS.items()}
        if self.path and self.path.exists():
            try:
                self.update(json.loads(self.path.read_text()), save=False)
            except (json.JSONDecodeError, ValueError):
                pass  # a broken file falls back to the defaults
        self.apply()

    def update(self, changes: dict, save: bool = True) -> dict:
        for key, value in changes.items():
            if key not in FIELDS:
                raise ValueError(f"Unknown setting: {key}")
            self.values[key] = self._check(key, value)
        if self.values["partial_at"] >= self.values["sufficient_at"]:
            raise ValueError("'partly sure' must need a lower score than 'sure'.")
        if save and self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(self.values, indent=2))
        self.apply()
        return self.values

    def reset(self) -> dict:
        self.values = {k: f["default"] for k, f in FIELDS.items()}
        if self.path and self.path.exists():
            self.path.unlink()
        self.apply()
        return self.values

    @staticmethod
    def _check(key: str, value: Any) -> Any:
        field = FIELDS[key]
        if field["type"] == "number":
            value = float(value)
            if not field["min"] <= value <= field["max"]:
                raise ValueError(f"{key} must be between {field['min']} and {field['max']}.")
            return int(value) if float(field["step"]).is_integer() else round(value, 3)
        if field["type"] == "choice" and value not in field["choices"]:
            raise ValueError(f"{key} must be one of {field['choices']}.")
        if field["type"] == "color" and not re.fullmatch(r"#[0-9a-fA-F]{6}", str(value)):
            raise ValueError("Colours look like #4f6bed.")
        if field["type"] == "text" and not re.fullmatch(r"[\w.:/-]{1,80}", str(value)):
            raise ValueError(f"{key} has characters that aren't allowed.")
        return value

    def apply(self) -> None:
        """Push behaviour settings into the running code."""
        sufficiency.SUFFICIENT_AT = self.values["sufficient_at"]
        sufficiency.PARTIAL_AT = self.values["partial_at"]
        documents.MODEL_CHUNKS = self.values["model_chunks"]
        chat.PASTE_DOC_CHARS = self.values["paste_doc_chars"]

    def css(self) -> str:
        """Appearance settings as CSS variables for the chat page."""
        v = self.values
        return (":root{"
                f"--font:{FONTS[v['font']]};--font-size:{v['font_size']}px;"
                f"--accent:{v['accent']};--user:{v['accent']};--radius:{v['radius']}px;"
                f"--composer-lines:{v['composer_lines']};--gap:{SPACING[v['density']]}px}}")
