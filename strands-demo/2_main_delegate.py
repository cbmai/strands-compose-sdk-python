"""Delegate multi-agent demo — coordinator dispatches to sub-agents."""

from __future__ import annotations

# Case: multiple-agent (delegate) with tools

import sys
from strands_compose import load

PROMPT = sys.argv[1] if len(sys.argv) > 1 else "มีโน้ตอะไรบ้าง"

resolved = load("config_delegate.yaml")
print(resolved.entry(PROMPT))


# --- debug only, can delete ---
print("\n--- tool calls ---")
for name, agent in {"team": resolved.entry, **resolved.agents}.items():
    for message in agent.messages:
        for block in message["content"]:
            if "toolUse" in block:
                print(f"[{name}] -> {block['toolUse']['name']} {block['toolUse']['input']}")