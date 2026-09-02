"""Single-agent demo with MCP — tools from an external MCP server over HTTP."""

# ต่างจาก main.py แค่ชื่อ config — resolved.entry ยังเป็น strands.Agent ตัวเดิม
# ของที่เพิ่มมาคือ tool_names จะมีทั้ง tool ในโปรเซส (tools.py) และ tool จาก MCP server

from __future__ import annotations

import sys
import time

from strands_compose import load

PROMPT = sys.argv[1] if len(sys.argv) > 1 else "repo strands-compose/sdk-python คืออะไร"

resolved = load("config_mcp.yaml")

# ⚠️ ResolvedConfig เก็บแค่ agents / orchestrators / entry — ไม่มี mcp_clients ให้หยิบ
# MCP client ถูกเสียบเป็น tool provider ของ Agent ไปแล้ว ดูได้ทางเดียวคือผ่าน tool_names
print("tools:", ", ".join(sorted(resolved.entry.tool_names)))
print()

started = time.perf_counter()
print(resolved.entry(PROMPT))
elapsed = time.perf_counter() - started


# --- debug only, can delete ---
print("\n--- tool calls ---")
for message in resolved.entry.messages:
    for block in message["content"]:
        if "toolUse" in block:
            print(f"-> {block['toolUse']['name']} {block['toolUse']['input']}")

print(f"\n--- time used ---\n{elapsed:.2f}s")
