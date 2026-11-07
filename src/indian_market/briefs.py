"""Check that a research or SWOT note cites a source on every bullet."""

from __future__ import annotations

import re
from pathlib import Path

RESEARCH_HEADINGS = (
    "business",
    "last quarter",
    "shareholding",
    "announcements",
    "peers",
    "open questions",
)
SWOT_HEADINGS = (
    "strengths",
    "weaknesses",
    "opportunities",
    "threats",
    "what would flip",
)
CONCALL_HEADINGS = (
    "guidance",
    "capex",
    "declined",
)

_HEADING = re.compile(r"^#{1,3}\s+(.+?)\s*$", re.MULTILINE)
_BULLET = re.compile(r"^-\s+(.+)$", re.MULTILINE)
_SOURCE = re.compile(r"source:\s*(\S+)", re.IGNORECASE)
_ALLOWED_SOURCE = re.compile(r"^(https?://|NSE\b|BSE\b|fixture:)", re.IGNORECASE)
_VERDICT = re.compile(r"^\s*#{0,3}\s*(recommendation|verdict)\b.*\b(buy|sell)\b", re.IGNORECASE | re.MULTILINE)
_STRONG = re.compile(r"\bstrong\s+(buy|sell)\b", re.IGNORECASE)


def _sections(text: str) -> list[tuple[str, str]]:
    matches = list(_HEADING.finditer(text))
    sections: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections.append((match.group(1).strip().lower(), text[start:end]))
    return sections


def check_brief(path: Path, kind: str) -> dict:
    text = path.read_text(encoding="utf-8")
    problems: list[str] = []
    if "not investment advice" not in text.lower():
        problems.append("Missing the line: Not investment advice.")
    if _VERDICT.search(text) or _STRONG.search(text):
        problems.append("The note contains a buy or sell verdict. Leave the view to the reader.")

    required = {"research": RESEARCH_HEADINGS, "swot": SWOT_HEADINGS, "concall": CONCALL_HEADINGS}.get(kind)
    if required is None:
        return {"ok": False, "problems": [f"Unknown kind {kind}."]}

    found = {title: body for title, body in _sections(text)}
    for heading in required:
        body = found.get(heading)
        if body is None:
            problems.append(f"Missing heading: {heading}.")
            continue
        for bullet in _BULLET.findall(body):
            source = _SOURCE.search(bullet)
            if not source:
                problems.append(f"Bullet under {heading} has no source: {bullet[:80]}")
                continue
            token = source.group(1)
            if not _ALLOWED_SOURCE.match(token):
                problems.append(
                    f"Source under {heading} must be an http(s) URL, an NSE or BSE filing id, or fixture: {token}"
                )

    return {"ok": not problems, "kind": kind, "path": str(path), "problems": problems}
