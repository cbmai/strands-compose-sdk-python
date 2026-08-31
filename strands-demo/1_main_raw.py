# main_raw.py —  working like main.py but not using strands call Ollama directly with stdlib only (urllib + json)
# run with uv run python main_raw.py "What time is it now?"

import json
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

HOST = "http://localhost:11434"
MODEL = "qwen3.5:4b"
MAX_TURNS = 10

SYSTEM_PROMPT = """You are a concise assistant.

Answer directly from your own knowledge whenever you can.
Only use a tool when the request truly needs it:
- current_time: only when asked about the current date or time
- save_note: ONLY when the user explicitly asks to save or write a note
- list_notes: only when asked what notes exist
Never save a note unless asked. After a tool runs, reply to the user in text."""

NOTES_DIR = Path(__file__).parent / "notes"


# ─── 1. tool ─────────────────────────────────────────────────────────────
# like as tools.py everything except without @tool


def current_time() -> str:
    return datetime.now(ZoneInfo("Asia/Bangkok")).strftime("%Y-%m-%d %H:%M:%S (%Z)")


def save_note(filename: str, content: str) -> str:
    NOTES_DIR.mkdir(exist_ok=True)
    path = NOTES_DIR / filename
    path.write_text(content, encoding="utf-8")
    return f"Saved {len(content)} characters to {path}"


def list_notes() -> str:
    NOTES_DIR.mkdir(exist_ok=True)
    files = sorted(p.name for p in NOTES_DIR.iterdir() if p.is_file())
    return "\n".join(files) if files else "(no notes yet)"


REGISTRY = {"current_time": current_time, "save_note": save_note, "list_notes": list_notes}


# ─── 2. JSON schema that strands have generate — write by yourself ────────────
# and need to maintain match with above and must maintain match with signature above

TOOL_SPECS = [
    {
        "type": "function",
        "function": {
            "name": "current_time",
            "description": "Return the current date and time in Bangkok.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "save_note",
            "description": "Save a note to a text file on disk.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": 'File name, e.g. "meeting.md".'},
                    "content": {"type": "string", "description": "The text content of the note."},
                },
                "required": ["filename", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_notes",
            "description": "List the notes saved so far.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]


# ─── 3. level that call with provider — format work with Ollama only ────────────


def call_model(messages: list[dict]) -> dict:
    body = json.dumps(
        {"model": MODEL, "messages": messages, "tools": TOOL_SPECS, "stream": False}
    ).encode()
    req = urllib.request.Request(
        f"{HOST}/api/chat", data=body, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            return json.loads(resp.read())["message"]
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"ollama {e.code}: {e.read().decode()[:200]}") from None
    except urllib.error.URLError as e:
        raise RuntimeError(f"ต่อ ollama ไม่ได้ที่ {HOST}: {e.reason}") from None


# ─── 4. agent loop — core that strands do ─────────────────────────────────


def run(prompt: str) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]

    for _ in range(MAX_TURNS):
        reply = call_model(messages)
        messages.append(reply)

        calls = reply.get("tool_calls")
        if not calls:
            return reply.get("content", "")

        for call in calls:
            name = call["function"]["name"]
            args = call["function"]["arguments"]
            if isinstance(args, str):          # some model send arguments in string format
                args = json.loads(args or "{}")

            print(f"→ called: {name} {args}")

            fn = REGISTRY.get(name)
            if fn is None:                     # model หลอนชื่อ tool ที่ไม่มีจริง
                result = f"Error: unknown tool '{name}'"
            else:
                try:
                    result = fn(**args)
                except TypeError as e:         # argument ไม่ครบ / ผิดชื่อ
                    result = f"Error: bad arguments for {name}: {e}"
                except Exception as e:         # tool พังเอง — ต้องบอก model ไม่ใช่ crash
                    result = f"Error running {name}: {e}"

            messages.append({"role": "tool", "tool_name": name, "content": str(result)})

    return "(stop at MAX_TURNS — model loop can't finish tool calls)"


if __name__ == "__main__":
    print(run(sys.argv[1] if len(sys.argv) > 1 else "What time is it now?"))