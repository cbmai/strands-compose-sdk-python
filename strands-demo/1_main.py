"""Single-agent demo — load config and run a prompt with tools."""

from __future__ import annotations

## Case: single-agent (assistant) with tools (without given defaultprompt)

# from strands_compose import load

# resolved = load("config.yaml")
# print(resolved.entry("What is AI Engineer?, Brief in 3 lines"))

######################################################################
## Case: single-agent (assistant) with tools

import sys
from strands_compose import load

resolved = load("config.yaml")
print("tools:", list(resolved.entry.tool_names), "\n")

# uv run python main.py "What is AI Engineer?, Brief in 3 lines"    # send "What is AI Engineer?, Brief in 3 lines" to entry()
# uv run python main.py                                             # send nothing → use "What time is it now?"
print(resolved.entry(sys.argv[1] if len(sys.argv) > 1 else "What time is it now?"))
