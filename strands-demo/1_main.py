"""Single-agent — load config and run a prompt with tools."""

from __future__ import annotations

import sys
import time

from strands_compose import load

resolved = load("config.yaml")
print("tools:", list(resolved.entry.tool_names), "\n")

started = time.perf_counter()
print(resolved.entry(sys.argv[1] if len(sys.argv) > 1 else "What time is it now?"))
elapsed = time.perf_counter() - started

print(f"\n--- time used ---\n{elapsed:.2f}s")


######################################################################
"""Single-agent — load config and run a prompt without tools."""

# from strands_compose import load

# resolved = load("config.yaml")
# print(resolved.entry("What is AI Engineer?, Brief in 3 lines"))
