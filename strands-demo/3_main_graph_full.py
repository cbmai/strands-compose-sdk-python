"""Graph multi-agent with full event streaming. (It shows every event of each agent, including node_start/node_stop events)"""

# โครงเดียวกับ main_delegate_full.py เปลี่ยนแค่ชื่อ config แต่ได้ event เพิ่มที่ delegate ไม่มีวันออก:
#   node_start / node_stop            <- Graph ยิง (delegate entry เป็น Agent ธรรมดา ไม่มี BeforeNodeCallEvent)
#   multiagent_start / multiagent_complete

from __future__ import annotations

import asyncio
import sys
import time

from strands_compose import AnsiRenderer, load

PROMPT = sys.argv[1] if len(sys.argv) > 1 else "จดโน้ตชื่อ graph-test.md ว่า graph รันครบทุก node"


async def main():
    resolved = load("config_graph.yaml")
    queue = resolved.wire_event_queue()      # inject EventPublisher ให้ทุก agent + ตัว Graph เอง
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
    finally:
        elapsed = time.perf_counter() - started
        await queue.close()
        await printer

    # print หลัง await printer เท่านั้น ไม่งั้น FINAL จะโผล่แทรกกลาง event ที่ยังค้างอยู่ใน queue
    print("\n=== FINAL ===\n", result.results[result.execution_order[-1].node_id].result)

    print(f"\n--- time used ---\n{elapsed:.2f}s")


asyncio.run(main())
