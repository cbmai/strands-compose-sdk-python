"""Delegate multi-agent demo with full event streaming."""

from __future__ import annotations

# Case: multiple-agent (delegate) with tools - full debug mode (see every event of each agent)

import asyncio
import sys

from strands_compose import AnsiRenderer, load

PROMPT = sys.argv[1] if len(sys.argv) > 1 else "Hello"


async def main():
    resolved = load("config_delegate.yaml")
    queue = resolved.wire_event_queue()      # see every event of each agent
    renderer = AnsiRenderer()

    async def consume():
        while True:
            event = await queue.get()
            if event is None:
                break
            renderer.render(event)
        renderer.flush()

    printer = asyncio.create_task(consume())
    try:
        result = await resolved.entry.invoke_async(PROMPT)
        print("\n\n=== FINAL ===\n", result)
    finally:
        await queue.close()
        await printer


asyncio.run(main())