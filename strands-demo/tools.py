"""Local tools for the strands-compose demo — current time and note management."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from strands import tool

NOTES_DIR = Path(__file__).parent / "notes"


@tool
def current_time() -> str:
    """Return the current date and time in Bangkok."""
    return datetime.now(ZoneInfo("Asia/Bangkok")).strftime("%Y-%m-%d %H:%M:%S (%Z)")


@tool
def save_note(filename: str, content: str) -> str:
    """Save a note to a text file on disk.

    Args:
        filename: File name to save, e.g. "meeting.md".
        content: The text content of the note.
    """
    NOTES_DIR.mkdir(exist_ok=True)
    path = NOTES_DIR / filename
    path.write_text(content, encoding="utf-8")
    return f"Saved {len(content)} characters to {path}"


@tool
def list_notes() -> str:
    """List the notes saved so far."""
    NOTES_DIR.mkdir(exist_ok=True)
    files = sorted(p.name for p in NOTES_DIR.iterdir() if p.is_file())
    return "\n".join(files) if files else "(no notes yet)"