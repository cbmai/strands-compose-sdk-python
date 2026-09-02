"""Delegate multi-agent with full event streaming. (It shows every event of each agent)"""

from __future__ import annotations

import asyncio
import sys
import time

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
    started = time.perf_counter()
    try:
        result = await resolved.entry.invoke_async(PROMPT)
        print("\n\n=== FINAL ===\n", result)
    finally:
        elapsed = time.perf_counter() - started
        await queue.close()
        await printer

    print(f"\n--- time used ---\n{elapsed:.2f}s")


asyncio.run(main())