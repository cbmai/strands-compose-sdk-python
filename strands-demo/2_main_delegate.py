"""Delegate multi-agent — coordinator dispatches to sub-agents."""

from __future__ import annotations

import sys
import time

from strands_compose import load

PROMPT = sys.argv[1] if len(sys.argv) > 1 else "มีโน้ตอะไรบ้าง"

resolved = load("config_delegate.yaml")

started = time.perf_counter()
print(resolved.entry(PROMPT))
elapsed = time.perf_counter() - started


# --- debug only, can delete ---
print("\n--- tool calls ---")
for name, agent in {"team": resolved.entry, **resolved.agents}.items():
    for message in agent.messages:
        for block in message["content"]:
            if "toolUse" in block:
                print(f"[{name}] -> {block['toolUse']['name']} {block['toolUse']['input']}")

print(f"\n--- time used ---\n{elapsed:.2f}s")