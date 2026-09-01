"""Local hooks for the strands-compose demo — จบ turn ทันทีที่ handoff แล้ว."""

from __future__ import annotations

from typing import Any

from strands.hooks import AfterToolCallEvent, AfterToolsEvent, HookProvider, HookRegistry

HANDOFF_TOOL = "handoff_to_agent"


class HandoffOnce(HookProvider):
    """จบ turn ทันทีหลัง handoff_to_agent ทำงาน — กันโมเดลเรียกซ้ำวนลูป.

    ทำไมต้องมี: handoff_to_agent แค่ "ปักธง" ว่าคนต่อไปคือใคร แล้ว return
    {"status": "success"} ทันที — swarm สลับคนหลังจบ turn เท่านั้น ไม่ได้สลับตรงนั้น
    โมเดลเล็กเลยไม่เห็นอะไรเปลี่ยน แล้วเรียกซ้ำอีกรอบ ๆ จนกว่าจะยอมพ่น text
    (ของจริงที่เจอ: researcher เรียก 10-11 ครั้งใน turn เดียว กิน input ไป ~30k tokens)

    ธงเก็บได้คนเดียวอยู่แล้ว เรียกซ้ำจึงไม่ได้ประโยชน์อะไรเลย นอกจากเผา token

    AfterToolsEvent.end_turn คือปุ่มที่ strands เตรียมไว้ให้: ตั้งค่าแล้ว event loop
    จะไม่ยิงโมเดลต่อ และปิดท้ายด้วย assistant message ที่เราใส่ (stop_reason = "end_turn")
    """

    def __init__(self, end_turn_text: str = "Handed off to the next agent.") -> None:
        """Args: end_turn_text: ข้อความปิด turn ที่จะถูกเก็บเป็น assistant message."""
        self.end_turn_text = end_turn_text
        self._handed_off = False

    def register_hooks(self, registry: HookRegistry, **kwargs: Any) -> None:
        """ดัก 2 จุด: รู้ชื่อ tool ที่ AfterToolCall, จบ turn ที่ AfterTools."""
        registry.add_callback(AfterToolCallEvent, self._on_after_tool_call)
        registry.add_callback(AfterToolsEvent, self._on_after_tools)

    def _on_after_tool_call(self, event: AfterToolCallEvent) -> None:
        # AfterToolsEvent ถือแต่ toolResult (ไม่มีชื่อ tool) เลยต้องมาจดชื่อไว้ตรงนี้ก่อน
        if event.tool_use.get("name") == HANDOFF_TOOL:
            self._handed_off = True

    def _on_after_tools(self, event: AfterToolsEvent) -> None:
        # เคลียร์ธงทุกครั้ง — node เดิมถูกเรียกซ้ำได้ (reviewer โยนกลับ writer)
        if self._handed_off:
            self._handed_off = False
            event.end_turn = self.end_turn_text
