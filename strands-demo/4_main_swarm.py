"""Swarm multi-agent — peer handoff without a coordinator."""

# resolved.entry เป็น strands.multiagent.swarm.Swarm — ไม่มี .messages เหมือน Graph
# ของที่ Swarm มีแต่ Graph ไม่มีคือ node_history: ใครถือ turn ต่อจากใคร (ซ้ำได้ วนกลับได้)

from __future__ import annotations

import sys
import time

from strands_compose import load

PROMPT = sys.argv[1] if len(sys.argv) > 1 else "จดโน้ตชื่อ swarm-test.md ว่า swarm โยนงานกันเอง"

resolved = load("config_swarm.yaml")

started = time.perf_counter()
result = resolved.entry(PROMPT)
elapsed = time.perf_counter() - started

# node_history ว่าง = swarm ล้มก่อนใครได้ทำงาน (เช่น node timeout) — ไม่งั้น [-1] จะ IndexError
if not result.node_history:
    print(f"swarm ไม่ได้รันสักคน (status={result.status}) — ดู node_timeout / ollama")
    raise SystemExit(1)

# คำตอบสุดท้าย = ผลของคนที่ถือ turn คนสุดท้าย (ไม่ใช่ entry เสมอไป)
last = result.node_history[-1].node_id
print("\n--- answer ---")
print(result.results[last].result)


# --- debug only, can delete ---

# 1) เส้นทางการโยนงาน — ของที่มีเฉพาะ swarm (graph บอกได้แค่ลำดับตาม edges ที่เราเขียนเอง)
print("--- handoff path ---")
print(" -> ".join(node.node_id for node in result.node_history))

# 2) สถานะ + token ราย node
print("\n--- nodes ---")
for node_id, node_result in result.results.items():
    usage = node_result.accumulated_usage
    print(
        f"[{node_id}] {node_result.status.value} "
        f"({usage['inputTokens']} in, {usage['outputTokens']} out)"
    )

# 3) tool call อยู่ที่ตัว agent เหมือนเดิม — handoff_to_agent จะโผล่ปนกับ tool ปกติ
print("\n--- tool calls ---")
for name, agent in resolved.agents.items():
    for message in agent.messages:
        for block in message["content"]:
            if "toolUse" in block:
                print(f"[{name}] -> {block['toolUse']['name']} {block['toolUse']['input']}")

print("\n--- total ---")
print(f"{len(result.node_history)} turns, {result.accumulated_usage['totalTokens']} tokens")

print(f"\n--- time used ---\n{elapsed:.2f}s")
