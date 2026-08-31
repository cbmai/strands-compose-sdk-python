# Skills ใน .kiro — อธิบายภาพรวม

โปรเจกต์นี้มี 2 skills อยู่ใน `.kiro/skills/` ซึ่งทำหน้าที่เป็น **คู่มือสำหรับ AI agent** ให้รู้วิธีทำงานกับ codebase อย่างถูกต้อง

---

## 1. library-development

**ไฟล์:** `.kiro/skills/library-development/SKILL.md`

**หน้าที่:** กำหนดกฎและ conventions สำหรับการเขียน/แก้ไข source code ของ library (`src/strands_compose/`)

### สิ่งที่ skill นี้ครอบคลุม

| หัวข้อ | สรุป |
|--------|------|
| Core Principles | ต้อง strands-first (ใช้ของ strands ตรงๆ ห้าม re-implement), เป็น thin wrapper (แปล YAML → strands objects แล้วหลบไป), return plain objects ไม่ subclass |
| The Pipeline | mental model หลัก: `text → dict → validated schema (*Def) → live strands objects` — แบ่งเป็น parse side กับ resolve side ห้ามข้ามฝั่งกัน |
| Resolver Contract | ทุก resolver มีรูปร่างเดียวกัน: dispatch built-in vs custom → validate result type → fail fast with contextual message |
| Schema Rules | `schema.py` เก็บ Pydantic models เท่านั้น, ห้าม import strands runtime types, เป็น pure data + validation |
| Dependency Direction | imports ไหลทางเดียว: loaders → schema ← resolvers → strands objects — inner layers ห้าม import outward |
| Streaming/Manifest/MCP | `EventPublisher` แปล strands events → `StreamEvent`, manifest เป็น pure introspection, MCP lifecycle เป็นของ strands ไม่ใช่ของเรา |
| Python Conventions | `from __future__ import annotations` ทุกไฟล์, fully typed, Google-style docstrings, early returns, `%s` logging (ห้าม f-strings ใน logger) |
| Errors | ใช้ `ConfigurationError` subclass, error messages สำหรับคนอ่าน YAML, ห้าม swallow exceptions |
| Verify | `uv run just check` + `uv run just test` ต้องผ่านก่อนถือว่าเสร็จ |

### หลักการสำคัญที่สุด

- **ห้าม re-implement สิ่งที่ strands มีอยู่แล้ว** — เช็ค SDK ก่อนเสมอ
- **ห้ามข้ามเส้น parse/resolve** — parsing สร้าง data, resolving สร้าง live objects
- **อ่าน sibling ก่อนสร้างของใหม่** — copy shape จากไฟล์ที่ทำหน้าที่เดียวกัน
- **Smallest reasonable change** — แก้เฉพาะที่ task ต้องการ

---

## 2. library-testing

**ไฟล์:** `.kiro/skills/library-testing/SKILL.md`

**หน้าที่:** กำหนดกฎและ doctrine สำหรับการเขียน/แก้ไข tests (`tests/`)

### สิ่งที่ skill นี้ครอบคลุม

| หัวข้อ | สรุป |
|--------|------|
| Core Principles | test behaviour/contracts/wiring ไม่ใช่ implementation, ห้าม mock ของที่ไม่ใช่ของเรา (strands, Pydantic, PyYAML), deterministic เท่านั้น |
| What to Test | resolution/wiring (core), schema validation contracts, pure transforms (interpolation, sanitize), runtime edges (streaming, guards), pipeline end-to-end |
| What NOT to Test | private methods/attrs, mock interactions, log messages, error text, strands behaviour, trivial assignments, exact event counts |
| Folder Structure | `tests/` mirror pipeline stages ไม่ใช่ source tree — `parse/`, `schema/`, `resolve/`, `runtime/`, `pipeline/`, `property/`, `contract/`, `fakes/` |
| Mocking Policy | fake ที่ seam ของเรา (`resolve_model`, `resolve_mcp_client`) — ห้าม mock strands internals, prefer fakes over Mock, ใช้ real strands objects กับ FakeModel |
| Test Data | ใช้ builder functions ใน `factories.py`, DAMP over DRY, inline arrange step ให้อ่านเป็นเรื่อง |
| Property-Based Testing | Hypothesis สำหรับ pure transforms ที่มี invariant ชัด: sanitization, interpolation, merge |
| Coverage | เป็น floor ไม่ใช่ goal, assertion quality สำคัญกว่า coverage number |
| Conventions | test ชื่อบอก behaviour + expectation, Arrange-Act-Assert, `pytest.raises` assert type ไม่ใช่ text |

### หลักการสำคัญที่สุด

- **Test catches real regression เท่านั้น** — ถ้า refactor ไม่เปลี่ยน behaviour แล้ว test พัง = test ผิด
- **Fake at our seam, never mock strands** — ใช้ `FakeModel`, `FakeMCPClient` แทน mock
- **Real code through public seam** — ใช้ real `load_config`, real schema, real `load_object`
- **One behaviour per test, one reason to fail**
- **ห้าม flaky** — no network, no sleep, no shared state

---

## ความสัมพันธ์ระหว่าง 2 Skills

```
library-development          library-testing
(กฎสำหรับเขียน source)       (กฎสำหรับเขียน test)
         │                           │
         └────── share ──────────────┘
              Core Principles:
              - strands-first
              - thin wrapper
              - explicit over implicit
              - verify with `just check` + `just test`
```

ทั้งคู่ complement กัน:
- `library-development` บอกว่า code ต้องมีหน้าตาอย่างไร, pipeline ทำงานยังไง, dependency flow ไปทิศไหน
- `library-testing` บอกว่าต้อง test อะไร, test ยังไง, อะไรห้าม test, fakes/mocks ใช้ตรงไหน

ถ้าแก้ source → อ่าน `library-development` ก่อน
ถ้าแก้ test → อ่าน `library-testing` ก่อน
ถ้าแก้ทั้งคู่ → อ่านทั้งสอง
