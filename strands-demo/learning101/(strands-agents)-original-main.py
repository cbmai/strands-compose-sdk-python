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