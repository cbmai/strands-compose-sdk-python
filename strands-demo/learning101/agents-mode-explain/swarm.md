# Swarm

> ส่งไม้ผลัด ไม่มีหัวหน้า คนที่เพิ่งทำเสร็จเป็นคนตัดสินว่าใครต่อ
> ไฟล์ในโปรเจกต์: `config_swarm.yaml` · `main_swarm.py` · `main_swarm_full.py`
>
> [← stands-compose101.md](../stands-compose101.md) · [เลือกโหมดยังไง](./brief-agent-mode.md) · [delegate](./delegate.md) · [graph](./graph.md) · [swarm](./swarm.md)

---

ไม่มี coordinator ไม่มี edges — มีแค่ "ใครอยู่ในฝูง" กับ "ใครเริ่ม"

```yaml
orchestrations:
  swarm_team:
    mode: swarm
    agents: [researcher, writer, reviewer, notetaker]
    entry_name: researcher          # คนแรกที่รับ prompt ของ user
    max_handoffs: 8
    max_iterations: 8               # ทั้งคู่นับ len(node_history) เหมือนกัน
    node_timeout: 300.0
    execution_timeout: 1800.0
```

strands ยัด tool `handoff_to_agent(agent_name, message, context)` ให้ทุก node เอง
⚠️ ถ้า agent มี tool ชื่อนี้อยู่แล้ว → `ValueError` ตอน build

## handoff_to_agent = "ปักธง" ไม่ใช่ "เรียก"

ชื่อมันหลอก ทำให้คิดว่าเรียกแล้วปลายทางจะทำงานแล้วส่งผลกลับ — **ไม่ใช่**

```python
# swarm.py:634 — _handle_handoff ทั้งฟังก์ชันทำแค่นี้
self.state.handoff_node    = target_node      # ปักธงว่า "คนต่อไปคือใคร"
self.state.handoff_message = message
for key, value in context.items():
    self.shared_context.add_context(current_node, key, value)
# จบ — ไม่มีการรัน target ตรงนี้เลย
```

แล้ว return `{"status": "success"}` ทันที **การสลับคนเกิดหลัง turn จบ** (`swarm.py:883`)

```
┌─ turn ของ researcher ──────────────────────────┐
│  เรียก handoff_to_agent → ปักธง → return       │
│  model เห็น "success" แต่ **ยังไม่จบ turn**     │
│  คิดต่อ / เรียก tool อีก / พ่นข้อความ            │
│  turn จบตรงนี้                                  │
└─────────────────────────────────────────────────┘
        ↓  swarm เช็ค if state.handoff_node:
   current_node = notetaker
```

**ธงเก็บได้คนเดียว** เรียกซ้ำ = ทับของเดิม ตัวสุดท้ายที่ *ได้รันจริง* ชนะ (ไม่ใช่ตัวสุดท้ายที่ model พูด — ดูกับดักข้อ 1)

## 3 พารามิเตอร์ไปคนละที่

| param | ไปไหน | ใครเห็น |
|---|---|---|
| `agent_name` | `state.handoff_node` — ธงว่าใครต่อ | swarm loop |
| `message` | ขึ้นหัว input ของคนถัดไป | **เฉพาะคนถัดไป** |
| `context` | `shared_context[ผู้ส่ง]` | **ทุกคนตลอดไป** สะสมเรื่อย ๆ |

`message` = ฝากถึงคนต่อไป · `context` = ฝากไว้บนกระดานกลาง

## node ถัดไปไม่ได้เห็น messages ของคนก่อน

swarm **สร้าง input ก้อนใหม่จากศูนย์** ทุกครั้ง (`_build_node_input`)

```
Handoff Message: <message ที่ฝากไว้ตอนปักธง>

User Request: <prompt ตั้งต้นของ user>

Previous agents who worked on this: researcher → writer

Shared knowledge from previous agents:
• researcher: {'filename': 'swarm4.md', ...}      ← มาจาก param context

Other agents available for collaboration:
Agent name: reviewer.  Agent description: Checks a draft note for errors.
...
If you don't hand off to another agent, the swarm will consider the task complete.
```

บรรทัดสุดท้ายคือ **กฎจบงาน**: swarm จบเมื่อมี turn ที่ไม่มีใครปักธง ไม่ใช่เมื่อครบทุกคน

**นี่คือที่มาของ token ที่บวม** — ทุก turn ต้องพก node_history + กระดานทั้งใบ + รายชื่อเพื่อนไปด้วย

## description กลับมามีความหมาย

ตรงข้ามกับ graph ที่ `description:` ตายสนิท — swarm ยัดเข้า context ให้เพื่อนอ่านตรง ๆ
เขียนให้บอก **ทั้งสิ่งที่ทำได้และทำไม่ได้** ("Cannot write or save.") เพื่อนจะได้ไม่โยนงานผิดคน

## entry เป็น Swarm ไม่ใช่ Agent

```python
type(resolved.entry)                  # strands.multiagent.swarm.Swarm
hasattr(resolved.entry, "messages")   # False — เหมือน Graph
```

| อยากได้ | graph | swarm |
|---|---|---|
| เส้นทางที่เดินจริง | `result.execution_order` | `result.node_history` (ซ้ำได้ วนได้) |
| คำตอบสุดท้าย | `result.results[<node ท้ายท่อ>]` | `result.results[node_history[-1].node_id]` |
| token | `result.accumulated_usage` | เหมือนกัน |

⚠️ `node_history` **ว่างได้** ถ้า swarm ล้มก่อนใครได้ทำงาน — `[-1]` จะ `IndexError` ต้องเช็คก่อน

## swarm ซ้อน orchestration ไม่ได้

node ทุกตัวต้องเป็น `Agent` ล้วน ถ้าใส่ orchestration เป็น node จะได้
`ConfigurationError: Swarm does not support nested orchestrations — use Graph mode instead.`

## เทียบเลขจริง

> วัดจาก prompt เดียวกัน (`จดโน้ตชื่อ bench.md ว่า VPC บน GCP เป็น global ส่วน subnet เป็น regional`) บน `qwen3.5:4b`

```
delegate 2,204        graph 3,616        swarm (4 agent) 18,474
```

**swarm แพงกว่า delegate 8.4 เท่า** สำหรับงานเดียวกัน

4 agent เดินครบเส้น:
```
node_history: researcher → writer → reviewer → notetaker
[researcher] 6270 in /  929 out
[writer]     3628 in / 1134 out
[reviewer]   3412 in / 1148 out
[notetaker]  1703 in /  250 out
```

input token ไม่ได้ลดลงตามคิว — `writer` กับ `reviewer` ยังกิน 3,400-3,600 ทั้งที่ไม่มี tool สักตัว
เพราะต้องพก node_history + shared_context + รายชื่อเพื่อนไปด้วยทุกเทิร์น
`reviewer` เป็นทางแยกจริง — prompt ให้เลือกเอง ผ่าน → notetaker / ไม่ผ่าน → กลับ writer
**config เดิมเป๊ะ ๆ รันสองครั้งได้คนละ path**

## 4 กับดักที่เจอมาแล้ว

**1. `max_calls` เป็นโควตาทั้งฝูง ไม่ใช่ต่อ agent**
`MaxToolCallsGuard` เก็บ counter ใน `invocation_state` ซึ่งปกติสร้างใหม่ทุก `agent()` — แต่
`swarm.py:836` ส่ง **dict ก้อนเดียวกัน** ให้ทุก node

```
researcher 2 calls → count 2
writer     2 calls → count 4      ← เกิน max_calls: 3 แล้ว
reviewer   เรียกที่ 5 → cancel_tool → _handle_handoff ไม่ได้รัน
                     → ธงไม่ถูกปัก → swarm เห็นว่า "no handoff" → จบทันที
```

อาการคือ **swarm จบเงียบ ๆ ทั้งที่ trace มี handoff อยู่ชัด ๆ** เพราะ toolUse block โผล่ใน
`messages` แม้ tool จะถูก cancel — หลอกตามาก · delegate/graph ไม่เจอเพราะแยก `invocation_state` กัน

**2. `num_ctx: 4096` (default ของ ollama) ไม่พอ**
delegate ~950 · graph ~1600 ผ่านสบาย แต่ swarm ยิง 6,000-20,000 ต่อ turn → หลุดเป็น
`ollama._types.ResponseError: EOF (status code: -1)` ซึ่ง**ไม่ได้บอกว่า context ล้น**

```yaml
params:
  host: http://localhost:11434
  options:
    num_ctx: 16384
```
เช็คด้วย `ollama ps` คอลัมน์ `CONTEXT`

**3. model เล็กเรียก handoff ซ้ำ ๆ**
เพราะ tool คืน `"success"` เปล่า ๆ ไม่มีผลงานตามมา model สรุปว่า "คงไม่สำเร็จ ลองใหม่"
เคยเห็นเรียก 9 ครั้งติดในเทิร์นเดียว แก้ด้วยการเขียน prompt ให้ตรง:
```
Call it EXACTLY ONCE. The tool returns "success" immediately but that does NOT
mean the next agent has finished — the swarm switches agents only after your turn ends.
After the tool returns, say nothing more and end your turn.
```

**4. tool โกหกได้**
ถ้า `completion_status != EXECUTING` แล้ว `_handle_handoff` จะ `return` เงียบ ๆ ไม่ปักธง
**แต่ tool ยังคืน `"success"` เหมือนเดิม** (`swarm.py:627` กับ `637` คนละบรรทัดกัน)
