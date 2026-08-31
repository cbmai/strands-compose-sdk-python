# convert-back-to-strands-agents

## ไฟล์ไหนต้องแตะบ้าง

| ไฟล์ | ต้องแก้ |
|---|---|
| `tools.py` | ไม่ต้องแตะเลยสักบรรทัด |
| `config.yaml` | ลบทิ้ง |
| `main.py` | ย้าย config เข้ามา |

`tools.py` รอดเพราะมันเป็น `@tool` ของ strands แท้ๆ อยู่แล้ว compose แค่ไปอ่านไฟล์นี้เฉยๆ ไม่ได้แปลงอะไร

## main.py เวอร์ชัน strands-agents ล้วน

```python
import sys

from strands import Agent
from strands.models.ollama import OllamaModel
from strands_tools import http_request, file_read

from tools import current_time, save_note, list_notes

model = OllamaModel(
    host="http://localhost:11434",
    model_id="qwen3.5:4b",
)

assistant = Agent(
    model=model,
    system_prompt="""You are a concise assistant.

Answer directly from your own knowledge whenever you can.
Only use a tool when the request truly needs it:
- current_time: only when asked about the current date or time
- save_note: ONLY when the user explicitly asks to save or write a note
- list_notes: only when asked what notes exist
Never save a note unless asked. After a tool runs, reply to the user in text.""",
    tools=[current_time, save_note, list_notes],
    callback_handler=None,
)

print("tools:", list(assistant.tool_names), "\n")
print(assistant(sys.argv[1] if len(sys.argv) > 1 else "What time is it now?"))
```

## แมปทีละบรรทัด

| config.yaml | Python |
|---|---|
| `provider: ollama` + `params.host` | `OllamaModel(host=...)` |
| `model_id: qwen3.5:4b` | `model_id="qwen3.5:4b"` |
| `system_prompt: \|` | `system_prompt="""..."""` |
| `tools: [./tools.py]` | `from tools import current_time, save_note, list_notes` |
| `tools: [strands_tools.http_request]` | `from strands_tools import http_request` |
| `agent_kwargs: {callback_handler: null}` | `callback_handler=None` |
| `entry: assistant` | ชื่อตัวแปร `assistant` |

`resolved.entry.tool_names` → `assistant.tool_names` — property เดียวกันเป๊ะ เพราะ `resolved.entry` มันคือ `strands.Agent` อยู่แล้ว

จุดเดียวที่ต้องเช็คเอกสารคือชื่อ parameter ของ `OllamaModel` — ที่เหลือแมปตรงตัว


## ประเด็นอาจจะอยู่ที่ถ้า agents มีจำนวนมาก

### 10 agents ด้วย strands-agents ล้วน

```python
SPECS = {
    "researcher": ("You research topics.", [http_request]),
    "writer":     ("You write reports.", []),
    "reviewer":   ("You review drafts.", []),
    # ... อีก 7 ตัว
}

agents = {
    name: Agent(model=model, system_prompt=prompt, tools=tools)
    for name, (prompt, tools) in SPECS.items()
}
```

จำนวน agent เพิ่มขึ้น แต่โค้ด wiring **ไม่โตตาม** — เพราะ Python มี loop ส่วน YAML ไม่มี ใน compose คุณต้องเขียน block ซ้ำ 10 รอบ (มี anchor ช่วยได้บ้าง แต่ก็ยังยาวกว่า)

เพราะงั้น "agent เยอะ" อย่างเดียวกลับเข้าทาง Python มากกว่าด้วยซ้ำ

### ตัวแปรที่ตัดสินจริงๆ มี 3 อัน

**1. topology ซับซ้อนแค่ไหน** — 10 agent เรียงกันแบน ๆ ใน delegate เดียว ไม่ยาก แต่ swarm ซ้อนใน delegate ซ้อนใน graph โดยที่ compose จัดลำดับ topological sort ให้ สร้างวงในก่อน แล้วต่อเป็น tool ให้วงนอก พร้อมตรวจ circular dependency ตอน load — ส่วนนี้เขียนเองน่ารำคาญจริง

**2. MCP กี่ตัว** — ~~จุดที่ compose ชนะขาด~~ **ไล่โค้ดแล้วไม่ใช่** lifecycle (start / readiness / shutdown)
เป็นของ `strands.tools.mcp.MCPClient` ทั้งหมด compose มีแค่ factory 344 บรรทัดที่เลือก transport ให้
เขียนเองก็แค่ `MCPClient(transport_callable=streamable_http_transport(url))` ต่อ server หนึ่งตัว
ที่ compose ช่วยจริงคือไม่ต้อง import transport เอง กับใส่ `${VAR}` ใน header ได้ — สะดวก แต่ไม่ถึงกับชนะขาด

**3. ใครแก้ config** — ถ้าเป็นคุณคนเดียว Python ชนะ ถ้ามีคนที่ไม่ใช่ dev ต้องแก้ prompt YAML ชนะ
