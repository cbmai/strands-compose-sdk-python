# Delegate

> หัวหน้าแจกงาน ลูกน้องทำเสร็จส่งกลับโต๊ะหัวหน้า
> ไฟล์ในโปรเจกต์: `config_delegate.yaml` · `main_delegate.py` · `main_delegate_full.py`
>
> [← stands-compose101.md](../stands-compose101.md) · [เลือกโหมดยังไง](./brief-agent-mode.md) · [delegate](./delegate.md) · [graph](./graph.md) · [swarm](./swarm.md)

---

**`description:` ของ agent สำคัญพอ ๆ กับ docstring ของ tool** — ตอน delegate สมาชิกทีมกลายเป็น tool ของ coordinator คำอธิบายนี้คือสิ่งที่ใช้ตัดสินใจว่าจะส่งงานให้ใคร

## อ่าน tool-call dump

```
[team] -> 'notetaker'   {'input': 'team-test.md: delegate ทำงานแล้ว'}
[notetaker] -> 'save_note'  {'filename': 'team-test.md', 'content': 'delegate ทำงานแล้ว'}
[notetaker] complete  (876 input, 133 output tokens)
[team]      complete  (920 input, 170 output tokens)
```

- coordinator เลือกลูกน้องถูกคน (`Agent.as_tool()` — sub-agent รับ `input` เป็น string ก้อนเดียว)
- notetaker แตก string เป็น argument 2 ตัว (นี่คือผลของ docstring + type hint)
- **นับ token แยกกัน** — delegate 1 ครั้ง = ยิง model 2 รอบ ซ้อนลึกยิ่งคูณ
- SESSION START ขึ้น `agents: researcher, notetaker, coordinator, team` — `team` เป็นตัวที่ 4 เพราะ delegate สร้าง `Agent` ใหม่ (fork จาก coordinator + เสียบ sub-agent เป็น tool) ไม่ได้ใช้ coordinator ตัวเดิม

## tool call ของลูกทีมอยู่ที่ลูกทีม

```python
for name, agent in {"team": resolved.entry, **resolved.agents}.items():
    for message in agent.messages:
        for block in message["content"]:
            if "toolUse" in block:
                print(f"[{name}] -> {block['toolUse']['name']} {block['toolUse']['input']}")
```

`coordinator.messages` เห็นแค่ระดับ delegate — ต้องวนทุก agent ถึงจะเห็น tool จริง
