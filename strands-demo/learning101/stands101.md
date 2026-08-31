# strands-agents คืออะไร แล้ว strands-compose เพิ่มอะไรจากนั้น

## 1. strands-agents คืออะไร

SDK สำหรับสร้าง AI agent จาก AWS (Apache-2.0, Python และ TypeScript)

หัวใจคือ **agent loop** — วงจรที่ model อ่าน context → ตัดสินใจ → เรียก tool → เอาผลกลับมาคิดต่อ → วนจนได้คำตอบ

จุดยืนของมันคือ **model-driven**: คุณให้แค่ model, system prompt, และชุด tool แล้วปล่อยให้ model ตัดสินใจเองว่าจะเรียกอะไรตอนไหน ต่างจาก framework ที่ให้คุณออกแบบ workflow เอง (chains, graphs, branching)

## 2. ต่างกับเขียน Python ธรรมดายังไง

### ถ้ายิง API เอง

```python
messages = [{"role": "user", "content": [{"text": "..."}]}]
while True:
    resp = bedrock.converse(modelId=..., messages=messages, toolConfig=my_schema)
    messages.append(resp["output"]["message"])
    if resp["stopReason"] != "tool_use":
        break
    results = []
    for block in resp["output"]["message"]["content"]:
        if "toolUse" in block:
            out = my_functions[block["toolUse"]["name"]](**block["toolUse"]["input"])
            results.append({"toolResult": {"toolUseId": block["toolUse"]["toolUseId"], ...}})
    messages.append({"role": "user", "content": results})
```

บวกกับต้องทำเองอีก:

- เขียน JSON schema ของทุก tool
- จัดการ context ที่ยาวเกิน limit
- retry ตอนโดน throttle
- เปลี่ยน provider = เขียนใหม่ เพราะ API แต่ละเจ้าคนละรูปแบบ

### ถ้าใช้ strands-agents

```python
from strands import Agent, tool

@tool
def current_time() -> str:
    """Return the current date and time."""
    return datetime.now().isoformat()

agent = Agent(model=model, tools=[current_time])
agent("What time is it now?")
```

`@tool` สร้าง schema ให้จาก type hint กับ docstring ส่วนสลับ provider (Bedrock / OpenAI / Ollama / Gemini) เปลี่ยนแค่บรรทัด model

**Strands ไม่ได้เพิ่มความสามารถที่ Python ทำไม่ได้ มันกำจัด boilerplate ที่ทุกคนต้องเขียนซ้ำ** — และไม่ได้ห่ออะไรไว้ ถ้าอยากลงไปคุมเองก็ยังทำได้

ของที่ติดมาในตัว: MCP, streaming, multi-agent (Graph / Swarm / Workflow), structured output, session management, hooks, OpenTelemetry

## 3. แล้ว compose เพิ่มอะไรจากนั้น

`strands-compose` เป็น **community project ไม่ได้สังกัด AWS** สโลแกนคือ "Think Docker Compose, but for AI agents"

มันไม่ได้เพิ่มความสามารถใหม่เลย — มันย้าย **wiring** จาก Python ไป YAML

### ระบบเดียวกัน เขียนสองแบบ

**strands-agents ล้วน:**

```python
model = BedrockModel(model_id="us.anthropic.claude-sonnet-4-6-v1:0")

researcher = Agent(model=model, system_prompt="You research topics.", tools=[http_request])
writer = Agent(model=model, system_prompt="You write reports.")

@tool
def do_research(q: str) -> str:
    return str(researcher(q))

@tool
def do_writing(q: str) -> str:
    return str(writer(q))

coordinator = Agent(model=model, system_prompt="Coordinate.", tools=[do_research, do_writing])
coordinator("Write a report about quantum computing.")
```

**compose:**

```yaml
agents:
  researcher:  {model: default, tools: [strands_tools.http_request], system_prompt: "You research topics."}
  writer:      {model: default, system_prompt: "You write reports."}
  coordinator: {model: default, system_prompt: "Coordinate."}

orchestrations:
  team_leader:
    mode: delegate
    entry_name: coordinator
    connections:
      - {agent: researcher, description: "Research a topic."}
      - {agent: writer, description: "Write the report."}
entry: team_leader
```

```python
load("config.yaml").entry("Write a report about quantum computing.")
```

ผลลัพธ์เหมือนกันเป๊ะ **หลัง `load()` สิ่งที่ได้คือ `strands.Agent` จริงๆ ไม่มี wrapper ไม่มี subclass**

### สิ่งที่ compose ให้เพิ่มจริงๆ

| | รายละเอียด |
|---|---|
| YAML wiring | model, agent, tool, hook, orchestration อยู่ในไฟล์เดียว |
| variable interpolation | `${VAR:-default}` แบบ Docker Compose + YAML anchor `&ref` / `*ref` |
| multi-file merge | `load(["base.yaml", "agents.yaml"])` |
| MCP wiring | ประกาศ server ใน YAML (`url:` / `command:`) + เดา transport จาก url + `${VAR}` ใน header |
| nested orchestration | topological sort สร้างวงในก่อน + ตรวจ circular dependency ตอน load |
| event streaming | `wire_event_queue()` ยิง event จากทุก agent ทุกชั้นเข้า queue เดียว |

**ทุกข้อในตารางนี้เป็นเรื่องความสะดวก ไม่มีข้อไหนเป็นความสามารถใหม่**

⚠️ เคยเข้าใจผิดว่า MCP lifecycle เป็นข้อที่หาที่อื่นไม่ได้ — **ไม่จริง** ไล่โค้ดแล้วพบว่า
`grep -rn "\.start()\|\.stop()\|readiness\|poll" src/strands_compose/` ไม่เจออะไรเลย
lifecycle ทั้งหมดอยู่ใน `strands.tools.mcp.MCPClient` ของ SDK ทางการ:

| ของ | อยู่ที่ไหนจริง ๆ |
|---|---|
| `start()` / `stop()` | `MCPClient` |
| poll readiness | `MCPClient._init_future.result(timeout=startup_timeout)` |
| graceful shutdown | refcount `_consumers` ปิดเมื่อ consumer ตัวสุดท้ายหลุด |
| "start ตามลำดับ" | **ไม่มีอยู่จริง** — `loaders.py` วน dict สร้าง object เฉย ๆ ไม่มี dependency graph |

`startup_timeout` ที่เขียนใน YAML แค่ถูก **ส่งผ่าน** ไปเป็น argument ของ `MCPClient`
MCP ใน compose ทั้งหมด 344 บรรทัด เป็น factory ล้วน ๆ ไม่มีโค้ด lifecycle เลย

## 4. มีขั้นตอนการเรียกทั้งหมด 3 layers ตามลำดับ

```
1. strands-compose     ← ทำงานตอน load() แล้วหายไป (ไม่ใช่ชั้นที่ call ผ่านทุกครั้ง)
2. strands-agents      ← agent loop + tool + multi-agent
3. boto3 / ollama SDK  ← ยิง HTTP ไปหา model
```

| อยากได้อะไร | ใช้อะไร |
|---|---|
| agent 1-3 ตัว | strands-agents ล้วน |
| agent เยอะแต่ topology แบน | strands-agents ล้วน (Python มี loop, YAML ไม่มี) |
| orchestration ซ้อน 2 ชั้นขึ้นไป | เริ่มคุ้มที่จะใช้ compose |
| MCP หลายตัว | เสมอกัน — lifecycle เป็นของ strands ทั้งคู่ compose ช่วยแค่ไม่ต้องเขียน transport เอง |
| อยาก generate config เป็น data ไปรัน CI | compose |
| อยากคุม *พฤติกรรม* agent ให้สม่ำเสมอ | คนละเรื่อง — ดู `agent-sop` |

## หมายเหตุเรื่องความเสี่ยง

แต่ exit cost ต่ำ เพราะมันคืน strands object ธรรมดา ถ้าเลิกใช้ก็แค่แปล YAML กลับเป็น Python — `tools.py` และ business logic ไม่ต้องแตะ

วิธีจำกัดความเสี่ยง: pin version ให้แน่น, ห่อ `load()` ไว้ในฟังก์ชันเดียวของตัวเอง, อย่าใช้ feature ที่แปลกที่สุดถ้าไม่จำเป็น