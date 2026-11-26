"""Case notes: CuteBot's memory of past investigations, kept on this computer only.

Only used when the user switches memory on. After each investigation CuteBot writes a
tiny Markdown note (what happened, the cause, the fix, how sure it was). Next time it
looks through its notes for a similar case, and if the user corrects it ("no, it was
actually the database"), the correction is added to the note and remembered.

No model training happens and nothing leaves the computer: the notes are plain text
files the user can read, edit or delete (`rca memory --forget`, or Forget on the page).
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .schema import RCAReport

DEFAULT_DIR = Path.home() / ".rca-investigator" / "cases"
SIMILAR_AT = 0.35
CORRECTION = re.compile(
    r"^\s*(no\b|nope\b|actually\b|that'?s (not right|wrong|incorrect)|wrong\b|incorrect\b|"
    r"not quite\b)|\bthe (real|actual) (root )?cause (was|is)\b|\bit was actually\b", re.IGNORECASE)


def _field(text: str, name: str) -> str:
    m = re.search(rf"^- \*\*{name}:\*\* (.*)$", text, re.MULTILINE)
    return m.group(1).strip() if m else ""


class CaseNotes:
    def __init__(self, folder: str | Path = DEFAULT_DIR):
        self.folder = Path(folder).expanduser()

    def _files(self) -> list[Path]:
        return sorted(self.folder.glob("case-*.md")) if self.folder.exists() else []

    def save(self, report: RCAReport, mode: str) -> Path:
        self.folder.mkdir(parents=True, exist_ok=True)
        now = datetime.now(timezone.utc)
        top = report.contributing_factors[0] if report.contributing_factors else None
        wc = report.what_changed
        happened = report.summary or (
            f"{wc.metric} in {', '.join(wc.segment.values()) or 'all'} changed "
            f"{wc.relative_change:+.0%} at {wc.change_start}" if wc else "unclear")
        fix = report.actions[0].action if report.actions else "none recorded"
        slug = re.sub(r"[^a-z0-9]+", "-", report.question.lower()).strip("-")[:40] or "case"
        path = self.folder / f"case-{now:%Y%m%d-%H%M%S}-{slug}.md"
        path.write_text(
            f"# {report.question}\n\n"
            f"- **date:** {now:%Y-%m-%d %H:%M} UTC\n"
            f"- **based on:** {mode}\n"
            f"- **what happened:** {happened}\n"
            f"- **cause:** {top.description if top else 'not found'}"
            f"{f' ({top.category.value})' if top else ''}\n"
            f"- **fix:** {fix}\n"
            f"- **verdict:** {report.sufficiency.verdict.value} "
            f"({report.sufficiency.score:.2f})\n\n"
            "## Corrections\n", encoding="utf-8")
        return path

    def add_correction(self, path: str | Path, text: str) -> None:
        path = Path(path)
        if path.exists():
            with path.open("a", encoding="utf-8") as f:
                f.write(f"- {datetime.now(timezone.utc):%Y-%m-%d}: {text.strip()}\n")

    def cases(self) -> list[dict]:
        out = []
        for path in self._files():
            text = path.read_text(encoding="utf-8")
            corrections = text.split("## Corrections", 1)[-1].strip()
            out.append({
                "path": path, "title": text.splitlines()[0].lstrip("# ").strip(),
                "date": _field(text, "date")[:10], "happened": _field(text, "what happened"),
                "cause": _field(text, "cause"), "fix": _field(text, "fix"),
                "corrections": [ln[2:].split(": ", 1)[-1] for ln in corrections.splitlines()
                                if ln.startswith("- ")],
                "text": text,
            })
        return out

    def recall(self, query: str, exclude: Path | None = None) -> dict | None:
        """The most similar past case, if it is similar enough."""
        cases = [c for c in self.cases() if c["path"] != exclude]
        if not cases or not query.strip():
            return None
        # compare the parts that matter (not the date/verdict lines every note shares)
        keys = [" ".join([c["title"], c["happened"], c["cause"], *c["corrections"]])
                for c in cases]
        matrix = TfidfVectorizer(stop_words="english").fit_transform([query] + keys)
        scores = cosine_similarity(matrix[0], matrix[1:]).ravel()
        best = int(scores.argmax())
        return {**cases[best], "score": float(scores[best])} if scores[best] >= SIMILAR_AT \
            else None

    def forget_all(self) -> int:
        files = self._files()
        for path in files:
            path.unlink()
        return len(files)


def recall_message(case: dict) -> str:
    """How CuteBot mentions a similar past case in the chat."""
    lines = [f"🧠 **This reminds me of a past case** ({case['date']}): *{case['title']}*",
             f"Back then the cause was: {case['cause']}"]
    if case["corrections"]:
        lines.append(f"…but you corrected me: **{case['corrections'][-1]}**")
    if case["fix"] and case["fix"] != "none recorded":
        lines.append(f"What fixed it: {case['fix']}")
    return "\n".join(lines)
