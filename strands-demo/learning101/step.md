# https://github.com/strands-compose/sdk-python

# Step1: Install uv and init
brew install uv
cd your_project
uv init strands-demo && cd ~/strands-demo
uv add "strands-compose[ollama]"    # default is bedrock -> uv add "strands-compose"
uv add "strands-compose[openai]"    # add for HuggingFace


# Step2: If select ollama (Option1 - Gernarel)
brew install ollama
brew services start ollama
check at curl http://localhost:11434 -> you will see Ollama is running
brew services stop ollama

ollama list
ollama pull llama3.2:3b
ollama pull qwen3:4b

# Step2: If select HuggingFace (Option2 - Using with MacOS)
uv tool install mlx-lm
uv tool install huggingface_hub
   ## download model
hf download Qwen/Qwen3-4B-MLX-4bit
   ## test
mlx_lm.generate --model Qwen/Qwen3-4B-MLX-4bit --prompt "Reply with exactly: pong" --max-tokens 20
   ## open server (OpenAI-compatible)
mlx_lm.server --model Qwen/Qwen3-4B-MLX-4bit --port 11534
   ## check
curl http://localhost:11534/v1/models

   ## list model
mlx_lm.manage --scan --pattern MLX
   ## stop
pkill -f mlx_lm.server
   ## delete
hf cache rm model/Qwen/Qwen3-4B-MLX-4bit --dry-run
hf cache rm model/Qwen/Qwen3-4B-MLX-4bit --yes


# Step3: Run prompt
-- check config is correct
uv run strands-compose check config.yaml

-- test run
uv run python 1_main.py "Hello"
uv run python 1_main.py "What is AI Engineer?, Brief in 3 lines"    # send "What is AI Engineer?, Brief in 3 lines" to entry()
uv run python 1_main.py                                             # send nothing → use "What time is it now?"

-- run with using tools for check current time
uv run python 1_main.py "What time is it?"

-- run with using tools for create note
uv run python 1_main.py "จดโน้ตชื่อ gcp.md ว่า VPC บน GCP เป็น global ส่วน subnet เป็น regional"
uv run python 1_main.py "มีโน้ตอะไรบ้าง"


# Issue
## Issue1: If run on this repo it will activate 'strands-compose' if you want to turnoff just run deactivate
thanaphat@Cards-MacBook-Pro sdk-python %  source /Users/thanaphat/Documents/sdk-python/.venv/bin/activate
(strands-compose) thanaphat@Cards-MacBook-Pro sdk-python %
run $deactivate

## Issue2: AI models are slow to give answers
      Cause1: รันครั้งแรกแล้วปล่อยทิ้งไว้ (ต่อให้รัน warmup ในครั้งแรกแล้ว)
      RAM 16 GB เต็ม; macOS เลยย้ายหน่วยความจำ 5-7 GB ของ mlx server ออกไปเก็บที่อื่น (บีบอัด + เขียนลงดิสก์) ตอนที่ไม่ได้ใช้งาน
      พอรันใหม่ มันต้องขนของทั้งหมดกลับเข้า RAM ก่อนถึงจะเริ่มคำนวณได้
      Cause2: รันซ้ำทันที
      ของยังอยู่ใน RAM ให้คำตอบได้ทันที


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


# ==============================================================
# multi-agent — delegrate / graph / swarm
# ==============================================================

uv run strands-compose check config_delegate.yaml
uv run python 2_main_delegate.py "จดโน้ตชื่อ team-delegate.md ว่า delegate ทำงานแล้ว"

uv run strands-compose check config_graph.yaml
uv run python 3_main_graph.py "จดโน้ตชื่อ team-graph.md ว่า graph รันครบทุก node"

uv run strands-compose check config_swarm.yaml
uv run python 4_main_swarm.py "จดโน้ตชื่อ team-swarm.md ว่า swarm โยนงานกันเอง"

-- เวอร์ชัน event stream (เห็นทุก event ระหว่างรัน)
uv run python 2_main_delegate_full.py "..."
uv run python 3_main_graph_full.py "..."
uv run python 4_main_swarm_full.py "..."


# ==============================================================
# MCP
# ==============================================================

ยิงไป DeepWiki (https://mcp.deepwiki.com/mcp) เป็น public MCP server ไม่ต้อง auth
ได้ tool: read_wiki_structure / read_wiki_contents / ask_question  (ถามเรื่อง repo บน GitHub)

-- validate อย่างเดียว ไม่ต่อ server
uv run strands-compose check config_mcp.yaml

-- ต่อ server จริง + ยิง ListTools แต่ยังไม่เรียก model
   ใช้จับปัญหาฝั่ง MCP ได้เร็ว (url ผิด / server ล่ม / startup_timeout ไม่พอ) โดยไม่ต้องรอ LLM
uv run strands-compose load config_mcp.yaml

-- รันจริง
uv run python 5_main_mcp.py "repo strands-compose/sdk-python คืออะไร ตอบสั้นๆ"
uv run python 5_main_mcp.py "repo modelcontextprotocol/python-sdk มีหัวข้อเอกสารอะไรบ้าง"

-- ดู tool ทั้งหมดโดยไม่เรียก model (MCP tool ปนอยู่กับ local tool ในรายชื่อเดียว)
uv run python -c "from strands_compose import load; print(sorted(load('config_mcp.yaml').entry.tool_names))"
-> ['ask_question', 'current_time', 'list_notes', 'read_wiki_contents', 'read_wiki_structure', 'save_note']

-- log รกที่ไม่ใช่ error กรองทิ้งได้
uv run python main_mcp.py "..." 2>&1 | grep -v "IncompleteField\|INFO "
