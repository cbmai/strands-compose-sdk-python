# MLX vs GGUF on Apple Silicon

## ปูพื้นก่อน

**Format ไม่ใช่ precision** — เป็นความสับสนหลักของเรื่องนี้ทั้งหมด

- **safetensors** = container format บอกแค่ว่า "เก็บ tensor ลงไฟล์ยังไง" ข้างในจะเป็น bf16 หรือ 4-bit ก็ได้
- **GGUF** = container ของ llama.cpp รวม weights + tokenizer + metadata ไว้ในไฟล์เดียว มี quantization scheme ของตัวเอง (Q4_K_M, Q5_K_M, Q8_0)
- **quantization** = การลด precision ของ weights เพื่อให้เล็กลงและเร็วขึ้น เป็นคนละเรื่องกับ format

**MLX** คือ ML framework ของ Apple สำหรับ Apple Silicon เทียบได้กับ PyTorch แต่ route ไป Metal และใช้ unified memory โดยตรง

**สำคัญ: ไม่มีไฟล์นามสกุล `.mlx`** — MLX ยืม safetensors มาใช้เลย เพราะ memory-map ได้และ interop กับ Hugging Face ได้ทันที คำว่า MLX ในชื่อ repo เป็นแค่ naming convention บอกว่า convert มาให้ MLX รันได้

**Ollama** เดิมเป็น CLI wrapper รอบ llama.cpp โหลด GGUF มาเก็บใน local registry แล้วเปิด REST API ที่ port 11434 — แต่ตั้งแต่ 0.19 ไม่ใช่แค่นั้นแล้ว

---

## 1. Ollama ก่อน / หลัง 0.19

Ollama 0.19 (มี.ค. 2026) เพิ่ม MLX backend ที่ bypass llama.cpp ไปเลย เป็นครั้งแรกที่ Apple Silicon ถูกปฏิบัติเหมือน first-class platform ไม่ใช่แค่ GPU ที่ Metal รองรับ

| หัวข้อ | ก่อน 0.19 | 0.19 ขึ้นไป |
|---|---|---|
| Backend บน Mac | llama.cpp + Metal อย่างเดียว | llama.cpp + Metal **หรือ** MLX backend |
| Format ที่รองรับ | GGUF เท่านั้น | GGUF + safetensors (MLX) + NVFP4 |
| Tag ใน library | `qwen3.5:4b`, `:4b-q4_K_M` | เพิ่ม `:4b-mlx`, `:4b-nvfp4` |
| เปิดใช้ | — | `export OLLAMA_BACKEND=mlx` หรือ pull tag `-mlx` ตรง ๆ |
| Throughput เทียบ pure MLX | ~70-85% | ราว 85% ของ MLX แท้ |
| จุดที่ควรรู้ | macOS 26 + Ollama 0.18.2 บน M4/M5 มีบั๊ก Metal shader crash ตอนใช้งานหนัก | แก้แล้วใน 0.19 |

> **`-mlx` เป็นแค่ tag name** เหมือน `-q4_K_M` หรือ `-nvfp4` ไม่ได้บอกนามสกุลไฟล์ และไม่ว่า tag ไหน Ollama ก็เก็บเป็น blob `sha256-xxxx` เหมือนกันหมด

---

## 2. เทียบ 3 ทางที่จะรัน MLX

ทั้งสามทางรัน weights ชุดเดียวกัน ต่างกันที่ ergonomics และสิ่งที่ทำต่อได้

| | Ollama `-mlx` tag | HF `mlx-community` + mlx-lm | LM Studio |
|---|---|---|---|
| Format จริง | safetensors (MLX 4-bit) | safetensors (MLX 4-bit) | safetensors (MLX 4-bit) |
| ไฟล์บนดิสก์ | blob `sha256-xxxx` หลายก้อน + manifest | `model*.safetensors` + config + tokenizer ~6-8 ไฟล์ | เหมือน HF |
| ที่เก็บ | `~/.ollama/models/` | `~/.cache/huggingface/hub/` | โฟลเดอร์ของ LM Studio |
| เปิดไฟล์ดูได้ | ไม่ได้ | ได้ | ได้ |
| Setup | 1 คำสั่ง | ต้องมี Python env | คลิกเดียว มี GUI |
| API | REST พร้อมใช้ port 11434 | ต้องรัน server เอง | OpenAI-compatible built-in |
| Fine-tune / LoRA | ไม่ได้ | ได้ (`mlx_lm.lora`) | ไม่ได้ |
| ความเร็ว | ~85% ของ MLX แท้ | 100% | ~100% |

**เลือกยังไง:** อยากรันเฉย ๆ / เรียก API → Ollama · อยาก fine-tune หรือแก้ config → HF + mlx-lm · อยากได้ GUI → LM Studio

---

## 3. Format ที่เจอทั้งหมด

| Format | Quantization | Engine | ไฟล์ |
|---|---|---|---|
| GGUF | Q4_K_M, Q5_K_M, Q8_0 | llama.cpp | 1 ไฟล์รวมทุกอย่าง |
| safetensors (MLX) | MLX 4/6/8-bit | MLX | หลายไฟล์แยก config/tokenizer |
| safetensors (HF ปกติ) | bf16 / fp16 | transformers, vLLM | หลายไฟล์ |
| NVFP4 | 4-bit float ของ NVIDIA | MLX (ผ่าน Ollama) | ห่อใน blob |

เทียบคุณภาพคร่าว ๆ: **MLX 4-bit ≈ GGUF Q4_K_M** และ **MLX 8-bit ≈ GGUF Q8_0**

NVFP4 เป็นของ NVIDIA ที่ contribute เข้ามาใน Ollama MLX backend เหตุผลคือ cloud provider หลายเจ้า deploy ด้วย NVFP4 ถ้า local ใช้ format เดียวกัน output จะสอดคล้องกับตอน deploy จริง

---

## คำสั่งที่ใช้ตรวจสอบ

เช็คว่า blob เป็น format อะไร:

```bash
# หา blob ก้อนใหญ่
ls -alhS ~/.ollama/models/blobs/ | head -5

# อ่าน magic bytes
xxd -l 4 -p ~/.ollama/models/blobs/sha256-<hash>
```

อ่านผล:
- `47475546` = ตัวอักษร `GGUF`
- `78000000` หรือเลขอื่นตามด้วย `00` = safetensors header length (little-endian)

นับจำนวนไฟล์:

```bash
# ฝั่ง Ollama
jq -r '.layers | length' ~/.ollama/models/manifests/registry.ollama.ai/library/qwen3.5/4b-mlx

# ฝั่ง HF
ls ~/.cache/huggingface/hub/models--*/snapshots/*/
```

เช็คว่ารันด้วย backend ไหนจริง:

```bash
ollama run qwen3.5:4b-mlx --verbose
```

---

## สรุปสั้นที่สุด

| ที่มา | Format | Quantization |
|---|---|---|
| Ollama `qwen3.5:4b-mlx` | safetensors | MLX 4-bit |
| Ollama `qwen3.5:4b` | GGUF | Q4_K_M |
| HF `mlx-community/Qwen3.5-4B-4bit` | safetensors | MLX 4-bit |

สองอันที่เป็น MLX คือของเดียวกัน ต่างแค่วิธีเก็บบนดิสก์

---

## ภาคผนวก — แล้วฝั่ง CUDA ใช้ไฟล์อะไร

**GGUF เหมือนกันเป๊ะ** — จุดขายของ GGUF คือ cross-platform ไฟล์ก้อนเดียวกันรันได้ทั้ง CUDA / ROCm / Metal / Vulkan เพราะ llama.cpp compile backend ตามเครื่องที่ติดตั้ง

`ollama pull qwen3.5:4b` บน Mac กับบนเครื่อง Linux + RTX 4090 ได้ **ไฟล์เดียวกัน hash เดียวกัน** ต่างแค่ตอนรัน llama.cpp เลือกใช้ Metal shader กับ CUDA kernel

### Tag ไหนรันที่ไหนได้

| Platform | tag ที่ใช้ | Format | Engine |
|---|---|---|---|
| Mac (Apple Silicon) | `qwen3.5:4b` | GGUF | llama.cpp + Metal |
| Mac (0.19+, 32GB+) | `qwen3.5:4b-mlx` | safetensors | MLX |
| Mac (0.19+) | `qwen3.5:4b-nvfp4` | NVFP4 | MLX |
| Linux / Windows + NVIDIA | `qwen3.5:4b` | GGUF | llama.cpp + CUDA |
| Linux / Windows + AMD | `qwen3.5:4b` | GGUF | llama.cpp + ROCm |

**ข้อควรระวัง**

- `-mlx` ใช้ได้เฉพาะ Apple Silicon เอาไปรันบน CUDA ไม่ได้
- `-nvfp4` สวนทางกับชื่อ — ตอนนี้มีเฉพาะ macOS version ยังไม่รองรับ Linux/Windows แม้จะเป็น format ของ NVIDIA เหตุผลที่เอามาใช้บน Mac คือลด memory bandwidth และขนาดโมเดล ไม่ใช่เพราะ Mac รัน FP4 native แบบ Blackwell

### ถ้าไม่ได้ใช้ Ollama บน CUDA

| Stack | Format | หมายเหตุ |
|---|---|---|
| llama.cpp / Ollama / LM Studio | GGUF | ไฟล์เดียว cross-platform |
| vLLM / transformers | safetensors | bf16/fp16 หรือ quantized (AWQ, GPTQ, NVFP4) |
| TensorRT-LLM | engine file ที่ build เอง | compile เจาะจงต่อ GPU รุ่นนั้น |

### หลักการเดียวที่ต้องจำ

> Format ไม่ได้ผูกกับยี่ห้อ GPU แต่ผูกกับ **engine**
>
> GGUF คู่กับ llama.cpp · safetensors คู่กับ MLX / vLLM / transformers
>
> ส่วนจะรันบน CUDA หรือ Metal เป็นเรื่องที่ engine จัดการให้ทีหลัง
