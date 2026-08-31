# https://github.com/strands-compose/sdk-python

# Install uv and init
brew install uv
cd your_project
uv init strands-demo && cd ~/strands-demo
uv add "strands-compose[ollama]"    # default is bedrock -> uv add "strands-compose"

# Install ollama
brew install ollama
brew services start ollama
check at curl http://localhost:11434 -> you will see Ollama is running
brew services stop ollama

ollama list
ollama pull llama3.2:3b
ollama pull qwen2.5:7b

# If run on this repo it will activate 'strands-compose' if you want to turnoff just run deactivate
thanaphat@Cards-MacBook-Pro sdk-python %  source /Users/thanaphat/Documents/sdk-python/.venv/bin/activate
(strands-compose) thanaphat@Cards-MacBook-Pro sdk-python %
run $deactivate


# Run
-- check config is correct
uv run strands-compose check config.yaml

-- test run
uv run python main.py "Hello"

-- run with using tools for check current time
uv run python main.py "What time is it?"

-- run with using tools for create note
uv run python main.py "จดโน้ตชื่อ gcp.md ว่า VPC บน GCP เป็น global ส่วน subnet เป็น regional"
uv run python main.py "มีโน้ตอะไรบ้าง"


# Ready-made tools
uv add strands-agents-tools
insert into config.yaml
    tools:
      - ./tools.py
      - strands_tools.calculator
      - strands_tools.http_request
      - strands_tools.file_read

-- example tools inside strands-agents-tools
strands_tools.calculator	            คำนวณเลข (LLM คำนวณเองมั่วบ่อย)
strands_tools.current_time	            วันเวลาปัจจุบัน
strands_tools.http_request	            ยิง HTTP ออกไปข้างนอก
strands_tools.file_read / file_write	อ่าน/เขียนไฟล์
strands_tools.shell	                    รันคำสั่ง shell
strands_tools.python_repl	            รัน Python
strands_tools.use_aws	                เรียก AWS API (boto3)
strands_tools.retrieve	                ดึงจาก Bedrock Knowledge Base

uv run strands-compose check config_delegate.yaml
uv run python main_delegate.py "จดโน้ตชื่อ team-delegate.md ว่า delegate ทำงานแล้ว"


# ==============================================================
# multi-agent — graph / swarm
# ==============================================================

uv run strands-compose check config_graph.yaml
uv run python main_graph.py "จดโน้ตชื่อ team-graph.md ว่า graph รันครบทุก node"

uv run strands-compose check config_swarm.yaml
uv run python main_swarm.py "จดโน้ตชื่อ team-swarm.md ว่า swarm โยนงานกันเอง"

-- เวอร์ชัน event stream (เห็นทุก event ระหว่างรัน)
uv run python main_delegate_full.py "..."
uv run python main_graph_full.py "..."
uv run python main_swarm_full.py "..."

-- swarm กิน context เยอะกว่าโหมดอื่นมาก ต้องขยาย num_ctx ไม่งั้นเจอ "EOF (status code: -1)"
   config_swarm.yaml -> params.options.num_ctx: 16384
ollama ps          # เช็คคอลัมน์ CONTEXT ว่าขยายแล้วจริง


# ==============================================================
# MCP — ใช้ server ของคนอื่น ไม่ต้องตั้งเอง
# ==============================================================

ยิงไป DeepWiki (https://mcp.deepwiki.com/mcp) เป็น public MCP server ไม่ต้อง auth
ได้ tool: read_wiki_structure / read_wiki_contents / ask_question  (ถามเรื่อง repo บน GitHub)

-- validate อย่างเดียว ไม่ต่อ server
uv run strands-compose check config_mcp.yaml

-- ต่อ server จริง + ยิง ListTools แต่ยังไม่เรียก model
   ใช้จับปัญหาฝั่ง MCP ได้เร็ว (url ผิด / server ล่ม / startup_timeout ไม่พอ) โดยไม่ต้องรอ LLM
uv run strands-compose load config_mcp.yaml

-- รันจริง
uv run python main_mcp.py "repo strands-compose/sdk-python คืออะไร ตอบสั้นๆ"
uv run python main_mcp.py "repo modelcontextprotocol/python-sdk มีหัวข้อเอกสารอะไรบ้าง"

-- ดู tool ทั้งหมดโดยไม่เรียก model (MCP tool ปนอยู่กับ local tool ในรายชื่อเดียว)
uv run python -c "from strands_compose import load; print(sorted(load('config_mcp.yaml').entry.tool_names))"
-> ['ask_question', 'current_time', 'list_notes', 'read_wiki_contents', 'read_wiki_structure', 'save_note']

-- log รกที่ไม่ใช่ error กรองทิ้งได้
uv run python main_mcp.py "..." 2>&1 | grep -v "IncompleteField\|INFO "

⚠️ prompt กับ argument ที่ agent ส่งเข้า tool จะไปถึงเครื่องเจ้าของ server
   อย่าส่งอะไรที่เป็นความลับเข้า MCP server ของคนอื่น
