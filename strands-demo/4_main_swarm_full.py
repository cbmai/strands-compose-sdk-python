"""Swarm multi-agent demo with full event streaming."""

from __future__ import annotations

# Case: multiple-agent (swarm) with tools (peer handoff) - full event stream (see every event of each agent)
#
# โครงเดียวกับ main_graph_full.py เปลี่ยนแค่ชื่อ config
# swarm เป็นโหมดเดียวที่ยิง event `handoff` ออกมา (delegate/graph ไม่มี)

import asyncio
import sys

from strands_compose import AnsiRenderer, load

PROMPT = sys.argv[1] if len(sys.argv) > 1 else "จดโน้ตชื่อ swarm-test.md ว่า swarm โยนงานกันเอง"


async def main():
    resolved = load("config_swarm.yaml")
    queue = resolved.wire_event_queue()      # inject EventPublisher ให้ทุก agent + ตัว Swarm เอง
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
    finally:
        await queue.close()
        await printer

    # print หลัง await printer เท่านั้น ไม่งั้น FINAL จะโผล่แทรกกลาง event ที่ยังค้างอยู่ใน queue
    print("\n=== FINAL ===\n", result.results[result.node_history[-1].node_id].result)
    print("\nhandoff path:", " -> ".join(n.node_id for n in result.node_history))


asyncio.run(main())
