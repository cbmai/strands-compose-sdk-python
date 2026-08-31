# Graph

> สายพานโรงงาน ลำดับกำหนดด้วย `edges` ตั้งแต่ตอนเขียน YAML
> ไฟล์ในโปรเจกต์: `config_graph.yaml` · `main_graph.py` · `main_graph_full.py`
>
> [← stands-compose101.md](../stands-compose101.md) · [เลือกโหมดยังไง](./brief-agent-mode.md) · [delegate](./delegate.md) · [graph](./graph.md) · [swarm](./swarm.md)

---

`edges` เป็นคนกำหนดลำดับ ไม่ใช่ LLM — ไม่ต้องมี coordinator

```yaml
orchestrations:
  pipeline:
    mode: graph
    entry_name: researcher              # node แรกที่รับ prompt ของ user
    edges:
      - { from: researcher, to: notetaker }
    node_timeout: 120.0                 # ต่อ node
    execution_timeout: 600.0            # ทั้ง graph
    # max_node_executions: 10           # กันลูปเมื่อมี cycle
    # reset_on_revisit: false           # true = ล้าง state ของ node เมื่อวนกลับมาซ้ำ
```

**`description:` ตายในโหมดนี้** — มันเป็น tool description ให้ coordinator เลือก graph ไม่มีใครต้องเลือก จึงไม่มีใครอ่าน

**graph ใช้ agent object ตัวเดิมเป็น node ไม่ fork** (ต่างจาก delegate ที่สร้าง `Agent` ตัวที่ 4)

```python
resolved.entry.nodes["researcher"].executor is resolved.agents["researcher"]   # True
```

ผลคือ SESSION START ขึ้นแค่ `researcher, notetaker` ไม่ใช่ 4 ชื่อ

## contract ระหว่าง node ต้องเขียนเอง

delegate มี coordinator แปลง prompt ให้ลูกน้อง (`'team-test.md: delegate ทำงานแล้ว'`)
graph ไม่มีใครแปลง — node ปลายทางได้ output ดิบของ node ต้นทาง **ต้องนัดแบบกันเองใน system_prompt**

```yaml
researcher:
  system_prompt: |
    Reply in exactly this shape and nothing else:
    FILENAME: <a short kebab-case name ending in .md>
    CONTENT:
    - <fact>

notetaker:
  system_prompt: |
    You receive a block that contains FILENAME: and CONTENT: from the previous agent.
    Call save_note once, using that FILENAME as `filename`.
    Do not invent a different filename.
```

**นี่คือภาระที่ graph ย้ายจาก runtime มาไว้ที่ design time** ไม่ได้หายไป

## entry เป็น Graph ไม่ใช่ Agent

```python
type(resolved.entry)                  # strands.multiagent.graph.Graph
hasattr(resolved.entry, "messages")   # False  ← debug loop แบบ delegate พังตรงนี้
```

| อยากได้ | delegate (Agent) | graph (Graph) |
|---|---|---|
| ลำดับที่รันจริง | อนุมานจาก toolUse | `result.execution_order` |
| สถานะราย node | ไม่มี | `result.results[nid].status` |
| token | `agent.event_loop_metrics` | `result.accumulated_usage` (ก้อนเดียว) |
| คำตอบสุดท้าย | ค่าที่ return | `result.results[<node ท้าย>].result` |
| tool call ของลูกทีม | วน `resolved.agents` | วน `resolved.agents` (เหมือนกัน) |

## เทียบเลขจริง — delegate vs graph

> วัดจาก prompt เดียวกัน (`จดโน้ตชื่อ bench.md ว่า VPC บน GCP เป็น global ส่วน subnet เป็น regional`) บน `qwen3.5:4b`

```
delegate                                graph
team         946 in / 165 out           researcher  1629 in / 462 out
notetaker    897 in / 196 out           notetaker   1173 in / 352 out
researcher     0 in /   0 out  ← ข้าม
coordinator    0 in /   0 out
──────────────────────────────          ─────────────────────────────
รวม 2,204 token                         รวม 3,616 token
```

`researcher` โดนข้ามเงียบ ๆ ใน delegate เพราะ LLM มองว่าไม่ต้องใช้ — graph บังคับรันทั้งคู่

**⚠️ ทิศทางต้นทุนกลับด้านจากที่เข้าใจกันทั่วไป** — graph แพงกว่า 1.6 เท่า เพราะจ่ายค่า node ที่ delegate เลือกจะข้าม
ประโยคที่ถูกคือ **delegate แพงกว่าต่อ node ที่ได้รัน / graph แพงกว่าต่อ 1 งาน**

## ด้านกลับของ "ทุก node ได้รันแน่นอน"

```bash
uv run python main_graph.py "มีโน้ตอะไรบ้าง"      # เป็นคำถาม ไม่ใช่คำสั่งบันทึก
```

`notetaker` ยังถูกบังคับให้รัน → สร้างไฟล์ขยะ `no-notes-info.md` ที่เขียนว่า "ไม่สามารถเข้าถึงข้อมูลโน้ตได้"

edge บอกให้รัน มันก็รัน ไม่มีใครถามว่าควรรันไหม ถ้าจะให้ข้ามต้องใช้ `condition:`

## condition — ไม่ใช่ expression string

```yaml
- { from: researcher, to: notetaker, condition: ./conditions.py:has_facts }
```

ต้องเป็น `path:callable` ที่ compose `import` ได้ รับ `GraphState` คืน `bool` (`false` = ตัด branch นั้นทิ้ง)
ถ้า resolve แล้วไม่ callable → `ConfigurationError` ตอน load
