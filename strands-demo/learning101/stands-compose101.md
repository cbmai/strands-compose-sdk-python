# strands-compose — สรุป

---

## 1. มันคืออะไร

[strands-compose](https://github.com/strands-compose/sdk-python) = declarative orchestration ที่วางทับ **strands-agents SDK**
สโลแกน: *"Think Docker Compose, but for AI agents"* — ประกาศทั้งระบบใน YAML ไฟล์เดียว แล้วเรียก `load()` ครั้งเดียว

### มีขั้นตอนการเรียกทั้งหมด 3 layers ตามลำดับ

```
1. strands-compose     ← YAML wiring (ชั้นที่ทำอยู่)
2. strands-agents      ← agent loop + tool + multi-agent
3. boto3 / ollama SDK  ← ยิง HTTP ไปหา model
```

### จุดสำคัญ: ไม่มี wrapper

`load()` คืน object ของ strands ล้วน ๆ — ตรวจ MRO แล้วไม่มี class ของ strands_compose โผล่เลย
แปลว่าถอด library ออกได้ตลอดเวลา — เขียน Python 15 บรรทัดแทน YAML แล้วลบ dependency ทิ้ง code แอปที่เหลือไม่ต้องแก้
หรือ ถ้าต้องการกลับไปใช้ strands-agents แบบเดิม ก็สามารถทำได้

```
entry               strands.agent.agent.Agent
team_graph          strands.multiagent.graph.Graph
team_swarm          strands.multiagent.swarm.Swarm
model               strands.models.ollama.OllamaModel
mro entry           ['Agent', 'AgentBase', 'Protocol', 'Generic', 'object']
```

### สถานะ project

Apache 2.0 · community project ไม่สังกัด AWS · สร้าง มี.ค. 2026 ·

---

## 2. ติดตั้ง

```bash
brew install uv
uv init strands-demo && cd ~/strands-demo
uv add "strands-compose[ollama]"
uv add strands-agents-tools          # tool สำเร็จรูป (module ชื่อ strands_tools)

brew install ollama
brew services start ollama
ollama pull qwen2.5:7b               # ต้องรองรับ tool calling
```

- Python 3.11+
- extras: `bedrock` (default ไม่ต้องใส่), `anthropic`, `openai`, `gemini`, `ollama`, `agentcore-memory`
- ชื่อ package `strands-agents-tools` แต่ import ว่า `strands_tools`

---

## 3. โครงโปรเจกต์

```
~/strands-demo/
├── .venv/                  ← uv จัดการให้ ไม่ต้อง activate (ใช้ uv run)
├── pyproject.toml
├── config.yaml               ← single agent
├── config_delegate.yaml      ← delegate  (LLM เลือกเองว่าจะเรียกใคร)
├── config_graph.yaml         ← graph     (เรากำหนดลำดับด้วย edges)
├── config_swarm.yaml         ← swarm     (agent โยนงานกันเอง)
├── config_mcp.yaml           ← single agent + MCP server ภายนอก
├── tools.py                  ← tool ของเราเอง
├── main.py                   ← single agent
├── main_delegate.py          ← delegate แบบสั้น
├── main_delegate_full.py     ← delegate + event stream
├── main_graph.py             ← graph แบบสั้น
├── main_graph_full.py        ← graph + event stream
├── main_swarm.py             ← swarm แบบสั้น
├── main_swarm_full.py        ← swarm + event stream
├── main_mcp.py               ← single agent + MCP
├── main_raw.py               ← ตัวอย่างไฟล์แบบไม่ใช้ strands เลย
└── notes/                    ← agent เขียนไฟล์ลงตรงนี้
```

**ข้อบังคับ**: รันจาก `~/strands-demo` เสมอ เพราะ `load("config.yaml")` และ tool path `./tools.py`

---

## 4. Config anatomy

### single agent

```yaml
models:
  local:
    provider: ollama
    model_id: qwen2.5:7b
    params:
      host: http://localhost:11434     # ollama ต้องมี host เสมอ ไม่มี default

agents:
  assistant:
    model: local
    system_prompt: "You are a concise assistant."
    tools:
      - ./tools.py                     # ทุก @tool ในไฟล์
      - strands_tools.http_request     # tool สำเร็จรูป
    agent_kwargs:
      callback_handler: null           # ปิด stream print (กัน print ซ้ำ)

entry: assistant
```

### ชื่อที่ต้องตรงกัน

```
models: local          ←── agents.*.model: local
agents: researcher     ←── connections[].agent / entry_name
orchestrations: team   ←── entry: team
```

ชื่อ **ไฟล์** ไม่เกี่ยวกับ `entry:` เลย — เปลี่ยนชื่อไฟล์ได้อิสระ แก้แค่ `load("...")` กับคำสั่ง CLI

### tool spec formats

| รูปแบบ | ได้อะไร |
|---|---|
| `./tools.py` | ทุกฟังก์ชันที่ติด `@tool` ในไฟล์ |
| `./tools.py:save_note` | เฉพาะฟังก์ชันนั้น |
| `strands_tools.http_request` | ทุก tool ใน module |
| `strands.vended_tools:bash` | ฟังก์ชันเดียวจาก module |

**ชื่อชนกัน = ตัวที่อยู่ทีหลังใน list ชนะ** (ทดสอบแล้ว: `./tools.py` + `strands_tools.current_time` → เหลือ built-in)

---

## 5. Tool

### 5.1 เขียนเอง

```python
from strands import tool

@tool
def save_note(filename: str, content: str) -> str:
    """Save a note to a text file on disk.

    Args:
        filename: File name to save, e.g. "meeting.md".
        content: The text content of the note.
    """
    ...
```

**docstring + type hint = spec ที่ model เห็น** ไม่ใช่ comment — strands generate JSON schema ให้อัตโนมัติ:

```json
{
  "name": "save_note",
  "description": "Save a note to a text file on disk.",
  "inputSchema": {"json": {
    "properties": {
      "filename": {"type": "string", "description": "File name to save, e.g. \"meeting.md\"."},
      "content":  {"type": "string", "description": "The text content of the note."}
    },
    "required": ["filename", "content"], "type": "object"
  }}
}
```

### 5.2 tool สำเร็จรูป

`strands_tools.` + `calculator` (deprecated) · `current_time` · `http_request` · `file_read` / `file_write` · `shell` ⚠️ · `python_repl` ⚠️ · `use_aws` · `retrieve`

⚠️ `shell` / `python_repl` รันคำสั่งบนเครื่องจริงตามที่ model สั่ง — อย่าเปิดคู่กับ input จากภายนอก

### 5.3 MCP — tool จาก server ภายนอก

5.1 กับ 5.2 คือ tool ที่ `import` เข้ามาในโปรเซสเดียวกัน ส่วน MCP คือ tool ที่อยู่บน **server คนละตัว**
คุยกันด้วย protocol กลาง — จะเป็น subprocess บนเครื่องเรา หรือ HTTP ไปเครื่องคนอื่นก็ได้

```yaml
# mcp_clients เป็น namespace ของตัวเอง ชื่อชนกับ agents/orchestrations ได้ไม่เป็นไร
mcp_clients:
  deepwiki:
    url: https://mcp.deepwiki.com/mcp     # public server ไม่ต้อง auth
    transport: streamable-http            # เดาจาก url ได้ ไม่ใส่ก็ได้
    params:
      startup_timeout: 30                 # ส่งต่อให้ strands MCPClient ตรง ๆ
    # transport_options:                  # ถ้า server ต้อง auth
    #   headers:
    #     Authorization: "Bearer ${MCP_TOKEN}"

agents:
  assistant:
    tools: [./tools.py]                   # tool ในโปรเซส
    mcp:   [deepwiki]                     # tool จาก server ภายนอก — อ้างด้วยชื่อ
```

#### url: vs command:

| | `command:` (stdio) | `url:` (http) |
|---|---|---|
| server มาจากไหน | compose spawn subprocess ให้ | ของคนอื่น มีอยู่แล้ว |
| จำนวนโปรเซส | **1 ตัวต่อ 1 `load()`** — 100 session = 100 subprocess | **ไม่มีเลย** |
| ข้อมูลออกนอกเครื่อง | ไม่ | **ใช่** |
| ควบคุม tool ได้แค่ไหน | เต็มที่ | เจ้าของ server เปลี่ยนได้ทุกเมื่อ |

**ใช้ `url:` ถ้าทำได้** — `command:` เหมาะกับ server ที่ต้องแตะไฟล์บนเครื่องเราจริง ๆ เท่านั้น

⚠️ prompt กับ argument ที่ agent ส่งเข้า tool **ไปถึงเครื่องเจ้าของ server** อย่าส่งความลับเข้า MCP server ของคนอื่น

#### agent แยกไม่ออกว่า tool มาจากไหน

```
tools: ask_question, current_time, list_notes, read_wiki_contents, read_wiki_structure, save_note
       └─ MCP ─┘   └─ ในโปรเซส ─┘└ ในโปรเซส ┘ └───── MCP ─────┘  └───── MCP ─────┘  └ ในโปรเซส ┘
```

รายชื่อเดียว เรียงตามตัวอักษร ไม่มีอะไรกำกับที่มา — และ MCP tool ยิง event `tool_start` / `tool_end`
**เหมือน tool ธรรมดาทุกประการ** ไม่มี event เฉพาะของ MCP เลย (นี่คือเหตุผลที่ไม่มี `main_mcp_full.py`)

#### lifecycle เป็นของ strands ไม่ใช่ compose

subprocess / connection เกิดตอน **`load()`** ไม่ใช่ตอนเรียก agent ครั้งแรก —
`uv run strands-compose load config_mcp.yaml` ที่ไม่ยิง model เลย ก็เห็น `ListToolsRequest` แล้ว

| ของ | อยู่ที่ไหน |
|---|---|
| `start()` / `stop()` · poll readiness · graceful shutdown | `strands.tools.mcp.MCPClient` |
| เลือก transport จาก `url`/`command` · `${VAR}` ใน header · validate ชื่อตอน load | compose |

`grep -rn "\.start()\|\.stop()\|readiness" src/strands_compose/` ไม่เจออะไรเลย — MCP ใน compose เป็น factory ล้วน ๆ

#### ResolvedConfig ไม่มี mcp_clients

```python
resolved = load("config_mcp.yaml")
resolved.mcp_clients          # AttributeError — เก็บแค่ agents / orchestrators / entry
resolved.entry.tool_names     # ทางเดียวที่จะเห็นว่า MCP tool เข้ามาแล้ว
```

---

## 6. Multi-agent

compose รองรับ 3 โหมด อยู่ใต้ `orchestrations:` เหมือนกันหมด ต่างกันที่ `mode:`

| mode | หนึ่งประโยค | คนตัดสินว่าใครทำต่อ |
|---|---|---|
| `delegate` | หัวหน้าแจกงาน ลูกน้องทำเสร็จส่งกลับโต๊ะหัวหน้า | coordinator (LLM) |
| `graph` | สายพานโรงงาน ไหลตาม `edges` ที่วางไว้ | **เรา** ตอนเขียน YAML |
| `swarm` | ส่งไม้ผลัด ไม่มีหัวหน้า | คนที่เพิ่งทำงานเสร็จ (LLM) |

```yaml
orchestrations:
  team:                      # delegate — entry_name + connections
    mode: delegate
    entry_name: coordinator
    connections: [{agent: researcher, description: "..."}]

  pipeline:                  # graph — edges
    mode: graph
    entry_name: researcher
    edges: [{from: researcher, to: notetaker}]

  swarm_team:                # swarm — agents + entry_name
    mode: swarm
    agents: [researcher, notetaker]
    entry_name: researcher
```

**สิ่งที่ทุกโหมดเหมือนกัน**: `load()` คืน object ของ strands ล้วน (`Agent` / `Graph` / `Swarm`)
เรียกแบบ `x("prompt")` ได้เหมือนกันหมด — runner 4 บรรทัดตัวเดียวรันได้ทั้ง 3 โหมด

**สิ่งที่ต่างกันจริง ๆ** อยู่ที่ว่า *ใครตัดสินว่าใครทำต่อ และตอนตัดสินเขารู้อะไรบ้าง*
→ [agents-mode/brief-agent-mode.md](./agents-mode/brief-agent-mode.md)

### รายละเอียดแต่ละโหมด

| | กลไก · กับดัก · trace จริง |
|---|---|
| **delegate** | [agents-mode/delegate.md](./agents-mode/delegate.md) — `Agent.as_tool()` · `description` สำคัญยังไง · tool call ของลูกทีมอยู่ที่ไหน |
| **graph** | [agents-mode/graph.md](./agents-mode/graph.md) — `edges` · contract ระหว่าง node · `condition:` · `Graph` ไม่มี `.messages` |
| **swarm** | [agents-mode/swarm.md](./agents-mode/swarm.md) — `handoff_to_agent` เป็นการปักธง · `max_calls` เป็นโควตาทั้งฝูง · `num_ctx` |

## 7. runner 8 แบบ

| ไฟล์ | โค้ดจริง | ได้อะไร |
|---|---|---|
| `main.py` | 4 บรรทัด | agent เดี่ยว |
| `main_mcp.py` | 4 บรรทัด | agent เดี่ยว + MCP — **เท่ากัน** ต่างแค่ชื่อ config |
| `main_delegate.py` | 4 บรรทัด | delegate — **เท่ากัน** |
| `main_graph.py` | 4 บรรทัด + ~15 อ่าน `GraphResult` | graph |
| `main_swarm.py` | 4 บรรทัด + ~20 อ่าน `SwarmResult` | swarm (มี `node_history` เพิ่ม) |
| `main_delegate_full.py` | ~25 บรรทัด | delegate + event stream |
| `main_graph_full.py` | ~28 บรรทัด | graph + event stream (มี `node_start` เพิ่ม) |
| `main_swarm_full.py` | ~38 บรรทัด | swarm + event stream |

โค้ด 4 บรรทัดเดียวกันนี้รันได้ทั้ง agent เดี่ยว, delegate, และ graph — เพราะ `Agent`, `Swarm`, `Graph` เรียกแบบ `x("prompt")` ได้เหมือนกันหมด

```python
import sys
from strands_compose import load

resolved = load("config_delegate.yaml")
print(resolved.entry(sys.argv[1]))
```

**สิ่งที่ต้องแก้ main.py / ไม่ต้องแก้**

| เปลี่ยนอะไร | แก้ main.py ไหม |
|---|---|
| 1 agent → 3 agents + delegate | ไม่ต้อง |
| delegate → graph / swarm (แค่รันให้จบ) | ไม่ต้อง |
| delegate → graph **แล้วอยากอ่าน debug ด้วย** | **ต้อง** — `Graph` ไม่มี `.messages` |
| ollama → bedrock | ไม่ต้อง |
| เพิ่ม/ลด tool | ไม่ต้อง |
| อยากได้ event streaming | **ต้อง** |
| อยากได้ async | **ต้อง** |

### event streaming (main_delegate_full.py)

```python
resolved = load("config_delegate.yaml")
queue = resolved.wire_event_queue()      # inject EventPublisher ให้ทุก agent ทุกชั้น
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
```

`wire_event_queue()` เขียนทับ `callback_handler` ให้เอง — ฉะนั้นไม่ต้องใส่ `callback_handler: null` ใน config เมื่อใช้แบบนี้

#### event ไหนออกในโหมดไหน

| event | delegate | graph | swarm |
|---|---|---|---|
| `agent_start` `token` `tool_start` `tool_end` `agent_complete` | ✅ | ✅ | ✅ |
| `node_start` / `node_stop` | ❌ | ✅ | ✅ |
| `multiagent_start` / `multiagent_complete` | ❌ | ✅ | ✅ |
| `handoff` | ❌ | ❌ | ❌ **(วัดจริงแล้วไม่ออก)** |

`EventType.HANDOFF` มีจริงและ `AnsiRenderer` เรนเดอร์ได้ แต่มันมาทาง **`callback_handler`** ไม่ใช่ hook
(`event_publisher.py:359` ดัก `type == "multiagent_handoff"`) — ส่วน `wire.py:243` ตั้ง `callback_handler`
ให้ orchestrator เฉพาะตอนที่เป็น `Agent` เท่านั้น `Swarm` ไม่ใช่ `Agent` event ก้อนนี้เลยตกหล่น

ดู handoff ได้จาก 2 ทางแทน: `result.node_history` (หลังจบ) หรือ `tool_start` ของ `handoff_to_agent` (ระหว่างรัน)

---

## 8. ทำไมต้องมี strands (เทียบกับเขียนเอง)

`main_raw.py` = ทำงานเหมือน `main.py` แต่ยิง Ollama ตรงด้วย stdlib

| | บรรทัด |
|---|---|
| `main_raw.py` | 100~ |
| `main.py` + `tools.py` + `config.yaml` | 60~ |

100~ บรรทัดนั้นยัง **ไม่มี** streaming, retry ตอน throttle, context window management, session persistence, multi-agent, hooks, provider ที่สอง

### เมื่อไหร่ไม่ต้องใช้

- ยิง prompt ครั้งเดียวจบ ไม่มี tool → เรียก API ตรง
- tool ตัวเดียว logic ตายตัว → if-else ชัดกว่า
- ต้องคุมทุก byte ที่ส่งเข้า model (บีบ cost, prompt caching ละเอียด)

จุดคุ้มทุน = **tool หลายตัว + loop + หลาย provider**

---

## 9. คำสั่งที่ใช้บ่อย

```bash
cd ~/strands-demo

uv run strands-compose check config_delegate.yaml     # validate อย่างเดียว ไม่ต่อ network → ใส่ CI ได้
uv run strands-compose load  config_delegate.yaml     # build จริง จับ import พัง / extra ไม่ได้ลง
uv run python main_delegate.py "จดโน้ตชื่อ x.md ว่า hello"

uv run strands-compose check config_graph.yaml        # graph
uv run python main_graph.py "จดโน้ตชื่อ x.md ว่า hello"

uv run strands-compose check config_swarm.yaml        # swarm
uv run python main_swarm.py "จดโน้ตชื่อ x.md ว่า hello"

uv run strands-compose check config_mcp.yaml          # mcp — ไม่ต่อ server
uv run strands-compose load  config_mcp.yaml          # ต่อ server จริง จับ MCP พังโดยไม่ต้องรอ LLM
uv run python main_mcp.py "repo owner/name คืออะไร"

ollama list                                           # เช็คชื่อ model ต้องตรงกับ model_id เป๊ะ รวม tag
ollama ps                                             # เช็ค CONTEXT ว่าพอไหม (swarm กินเยอะ)
```

---

## 10. ปัญหาที่เจอมาแล้ว + วิธีแก้

| อาการ | สาเหตุ | แก้ |
|---|---|---|
| `model 'llama3.2:3b' not found (404)` | ยังไม่ pull | `ollama pull ...` แล้วเช็คชื่อด้วย `ollama list` |
| `Config file not found` | cd ผิดโฟลเดอร์ | `cd ~/strands-demo` ก่อนรัน |
| ตอบซ้ำ 2 รอบ | strands print stream เอง + เรา `print()` อีก | `agent_kwargs: {callback_handler: null}` |
| รันแล้วเงียบ ไม่มีคำตอบ | model จบ turn ที่ tool call | เติม "After a tool runs, reply to the user in text." |
| เรียก tool ทั้งที่ไม่ควร | prompt กว้างไป + model เล็ก | เขียนเงื่อนไข "ห้ามเรียกเมื่อไหร่" ให้ชัด |
| `calculator is deprecated` | จะเป็น error log ใน v0.9.0 | เอาออก หรือใช้ `strands.vended_tools:bash` (แต่ security boundary ต่างกันมาก) |
| `${VAR}` ใน flow mapping พัง | `params: { host: ${HOST} }` — `{` ซ้อน | แตกหลายบรรทัด หรือ quote `"${HOST}"` |
| delegate ไม่ยอมเรียกครบ 2 agent | ข้อจำกัดของ model เล็ก ไม่ใช่ config ผิด | ใช้ model ใหญ่ขึ้น หรือใช้ graph mode |
| `AttributeError: 'Graph' object has no attribute 'messages'` | เอา debug loop ของ delegate มาใช้กับ graph | ตัด `resolved.entry` ออกจาก loop ใช้ `resolved.agents` อย่างเดียว |
| `=== FINAL ===` โผล่แทรกกลาง event | print ก่อน queue drain เสร็จ | ย้าย `print` ออกไปหลัง `await printer` |
| graph สร้างไฟล์ขยะจาก prompt ที่ไม่เกี่ยว | ทุก node ถูกบังคับรัน | ใส่ `condition:` บน edge หรือใช้ delegate สำหรับงานที่ input ไม่แน่นอน |
| `EOF (status code: -1)` จาก ollama | context ล้น (`num_ctx` default 4096) | `options: {num_ctx: 16384}` เช็คด้วย `ollama ps` |
| swarm จบก่อนถึง node สุดท้าย ทั้งที่ trace มี handoff | `max_calls` เป็นโควตาทั้งฝูง → handoff โดน `cancel_tool` | เพิ่ม `max_calls` ให้พอทั้ง swarm (เช่น 20) |
| `IndexError` ที่ `node_history[-1]` | swarm ล้มก่อนใครได้ทำงาน | เช็ค `if not result.node_history` ก่อน |
| `AttributeError: 'ResolvedConfig' object has no attribute 'mcp_clients'` | ResolvedConfig เก็บแค่ agents/orchestrators/entry | ดู MCP tool ผ่าน `entry.tool_names` แทน |
| MCP tool ไม่โผล่ใน `tool_names` | ประกาศใน `mcp_clients:` แล้วแต่ลืมใส่ `mcp: [ชื่อ]` ที่ agent | เติม `mcp:` ให้ agent (compose validate ให้เฉพาะกรณีอ้างชื่อผิด) |
| `IncompleteFieldDefinitionWarning: Field 'lifespan'` | warning ภายในของ pydantic-settings ไม่ใช่ error | ปล่อยไว้ หรือ `2>&1 \| grep -v IncompleteField` |

---

## 11. TODO

- [x] **graph mode** — DAG กำหนดลำดับตายตัว `edges: [{from: researcher, to: notetaker}]` การันตีว่าทุก node ได้รัน ต่างจาก delegate ที่ LLM ตัดสินใจเอง
  - ✅ `config_graph.yaml` + `main_graph.py` + `main_graph_full.py` — ดู §6.2
  - ยังไม่ได้ลอง: conditional edge, cycle (`reset_on_revisit`)
- [x] **swarm mode** — peer handoff, agent ส่งงานกันเองโดยไม่มี coordinator
  - ✅ `config_swarm.yaml` + `main_swarm.py` + `main_swarm_full.py` — ดู §6.3
  - ⚠️ swarm ซ้อน orchestration ไม่ได้ (nested ต้องใช้ graph เป็นโครงนอก)
- [ ] **nested orchestration** — เอา graph เป็นโครงหลัก แล้วเสียบ delegate เป็น node เดียวตรงจุดที่ต้องการความยืดหยุ่น
- [x] **MCP** — `mcp_clients:` ต่อ MCP server (`url:` HTTP หรือ `command:` stdio) แล้วอ้างใน `mcp:` ของ agent
  - ✅ `config_mcp.yaml` + `main_mcp.py` ยิงไป DeepWiki (public ไม่ต้อง auth) — ดู §5.3
  - ⚠️ `command:` (stdio) = 1 subprocess ต่อ 1 `load()` — server ที่มี 100 session = 100 subprocess ใช้ `url:` ถ้าทำได้
  - ยังไม่ได้ลอง: `command:` stdio จริง, server ที่ต้อง auth ผ่าน header
- [ ] **session persistence** — `session_manager:` provider `file` / `s3` / `agentcore`
- [ ] **สลับไป Bedrock** — แก้แค่ block `models:` เทียบคุณภาพ delegate กับ model ใหญ่
- [ ] **deploy** — long-running server pattern: `load_config()` ครั้งเดียวตอน boot → `load(app_config, session_id=...)` ต่อ session (อย่าแชร์ agent instance ข้าม user เพราะ `messages` อยู่ในตัว agent)

### delegate vs graph vs swarm — เลือกยังไง

คำถามที่แยก 3 โหมดออกจากกันไม่ใช่ *"LLM ตัดสินหรือเราตัดสิน"* (delegate กับ swarm ก็ LLM ทั้งคู่)
แต่คือ **"ใครตัดสินว่าใครทำต่อ — และตอนที่เขาตัดสิน เขารู้อะไรบ้าง"**

| | delegate | graph | swarm |
|---|---|---|---|
| ใครตัดสินว่าใครทำต่อ | coordinator — **หัวหน้าที่ไม่ได้จับงาน** | **เรา** ตอนเขียน edges | **คนที่เพิ่งทำงานเสร็จ** |
| ตัดสินตอนไหน | ก่อนงานเริ่ม | ตอนพิมพ์ YAML | หลังทำงานเสร็จ |
| ตอนตัดสินมีข้อมูลอะไร | prompt + `description` ของลูกน้อง | ไม่มีเลย | prompt + `description` + **ผลงานจริงที่เพิ่งทำ** |
| ลูกทีมส่งงานหากันเองได้ไหม | ไม่ได้ | ไม่ได้ (ท่อวางไว้แล้ว) | ได้ |
| ทำเสร็จแล้ว control ไปไหน | **กลับหาหัวหน้า** | ไหลตาม edge ไม่กลับ | ไปหาคนถัดไป ไม่กลับ |
| ใครพูดประโยคสุดท้ายกับ user | หัวหน้า | node ท้ายท่อ (รู้ล่วงหน้า) | คนสุดท้ายที่ถือไม้ (**ไม่รู้ล่วงหน้า**) |
| node ปลายทางได้รันแน่ไหม | ไม่แน่ | **แน่นอน** | ไม่แน่ — เฉพาะคนที่ถูกเอ่ยชื่อ |
| ยืดหยุ่นกับ input แปลก ๆ | ได้ | ไม่ได้ | ได้ |
| ต้นทุนต่อ 1 งาน (วัดจริง) | **2,204** ถูกสุด ข้าม node ได้ | 3,616 จ่ายทุก node เสมอ | 18,474 (4 agent) |
| โครงสร้าง | เรียกฟังก์ชัน (มี stack) | ท่อประปา | ส่งไม้ผลัด (ทางเดียว) |
| เหมาะกับ | ต้องมีคนคุมและสรุป | pipeline ขั้นตอนตายตัว | อยากให้คนเห็นงานจริงเป็นคนตัดสิน |

**หลักคิด**: ถ้าลำดับงานเป็นสิ่งที่รู้อยู่แล้ว อย่าให้ LLM ตัดสินใจ — ดูรายละเอียดพร้อมภาพและ trace จริงที่ [agents-mode/brief-agent-mode.md](./agents-mode/brief-agent-mode.md)
