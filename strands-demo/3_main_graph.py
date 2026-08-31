"""Graph multi-agent demo — DAG pipeline with fixed execution order."""

from __future__ import annotations

# Case: multiple-agent (pipeline) with tools (graph agents)
#
# ต่างจาก main_delegate.py ตรงที่ resolved.entry เป็น strands.multiagent.graph.Graph ไม่ใช่ Agent ทำให้ไม่มี .messages 
# และ debug loop แบบ delegate ใช้ไม่ได้ตรง ๆ แลกมาด้วย GraphResult ที่บอกได้ว่า node ไหนรันจริง ตามลำดับไหน

import sys
from strands_compose import load

PROMPT = sys.argv[1] if len(sys.argv) > 1 else "จดโน้ตชื่อ graph-test.md ว่า graph รันครบทุก node"

resolved = load("config_graph.yaml")
result = resolved.entry(PROMPT)         # send back GraphResult not text

# คำตอบต้องดึงจาก node ตัวท้าย result.results[last].result (Graph ไม่ได้คืน text ก้อนเดียวเหมือน Agent)
last = result.execution_order[-1].node_id
print("\n--- answer ---")
print(result.results[last].result)


# --- debug only, can delete ---

# 1) node ไหนรันบ้าง — ของที่ delegate ตอบไม่ได้ (delegate ข้าม agent ได้)
print("--- nodes ---")
for node in result.execution_order:
    node_result = result.results[node.node_id]
    usage = node_result.accumulated_usage
    print(
        f"[{node.node_id}] {node_result.status.value} "
        f"({usage['inputTokens']} in, {usage['outputTokens']} out)"
    )

# 2) tool call อยู่ที่ตัว agent เหมือนเดิม — แต่ไม่ต้องใส่ resolved.entry เพราะ Graph ไม่มี .messages
print("\n--- tool calls ---")
for name, agent in resolved.agents.items():
    for message in agent.messages:
        for block in message["content"]:
            if "toolUse" in block:
                print(f"[{name}] -> {block['toolUse']['name']} {block['toolUse']['input']}")

# 3) token รวมทั้ง graph — Graph นับให้ก้อนเดียว ไม่ต้องไล่บวกเองแบบ delegate
print("\n--- total ---")
print(f"{result.execution_count} nodes, {result.accumulated_usage['totalTokens']} tokens")
