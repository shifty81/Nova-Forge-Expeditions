# Local LLM Models for NovaForge Dev AI

All inference runs locally — no cloud API required after the initial download.

---

## Recommended Models (via Ollama)

| Model | Size | Best for | Command |
|-------|------|----------|---------|
| `deepseek-coder:6.7b` | ~4 GB RAM | Fast iteration, C++ code | `ollama pull deepseek-coder` |
| `deepseek-coder:33b` | ~20 GB RAM | High-quality C++ + complex reasoning | `ollama pull deepseek-coder:33b` |
| `codellama:13b` | ~8 GB RAM | General code, Python, C++ | `ollama pull codellama:13b` |
| `qwen2.5-coder:7b` | ~5 GB RAM | Multi-language (C++/Python/Lua) | `ollama pull qwen2.5-coder:7b` |
| `mistral:7b` | ~5 GB RAM | General reasoning + code | `ollama pull mistral:7b` |
| `mixtral:8x7b` | ~26 GB RAM | Best quality for complex tasks | `ollama pull mixtral:8x7b` |

**Minimum recommended:** `deepseek-coder:6.7b` — runs on 8 GB RAM.

---

## Alternative: LM Studio

1. Download [LM Studio](https://lmstudio.ai/)
2. Search for and download a GGUF model (DeepSeek Coder, CodeLlama, etc.)
3. Start the local server on `http://localhost:1234`
4. Set `LLM_BASE_URL=http://localhost:1234/v1` in your environment

---

## Hardware Requirements

| VRAM / RAM | Recommended model |
|-----------|------------------|
| 8 GB | `deepseek-coder:6.7b`, `qwen2.5-coder:7b` |
| 16 GB | `codellama:13b`, `mistral:7b` |
| 24 GB+ | `deepseek-coder:33b` |
| 32 GB+ | `mixtral:8x7b` |

CPU-only inference is supported but slow for models above 7B.

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_BASE_URL` | `http://localhost:11434` | Ollama or LM Studio API endpoint |
| `LLM_MODEL` | `deepseek-coder` | Model name to use |
| `LLM_TIMEOUT` | `120` | Request timeout in seconds |
| `NOVAFORGE_ROOT` | auto-detected | Path to repository root |
