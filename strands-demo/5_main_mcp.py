"""Single-agent demo with MCP — tools from an external MCP server over HTTP."""

from __future__ import annotations

# Case: single-agent + MCP (tool จาก MCP server ของคนอื่น ผ่าน HTTP)
#
# ต่างจาก main.py แค่ชื่อ config — resolved.entry ยังเป็น strands.Agent ตัวเดิม
# ของที่เพิ่มมาคือ tool_names จะมีทั้ง tool ในโปรเซส (tools.py) และ tool จาก MCP server

import sys

from strands_compose import load

PROMPT = sys.argv[1] if len(sys.argv) > 1 else "repo strands-compose/sdk-python คืออะไร"

resolved = load("config_mcp.yaml")

# ⚠️ ResolvedConfig เก็บแค่ agents / orchestrators / entry — ไม่มี mcp_clients ให้หยิบ
# MCP client ถูกเสียบเป็น tool provider ของ Agent ไปแล้ว ดูได้ทางเดียวคือผ่าน tool_names
print("tools:", ", ".join(sorted(resolved.entry.tool_names)))
print()

print(resolved.entry(PROMPT))


# --- debug only, can delete ---
print("\n--- tool calls ---")
for message in resolved.entry.messages:
    for block in message["content"]:
        if "toolUse" in block:
            print(f"-> {block['toolUse']['name']} {block['toolUse']['input']}")
