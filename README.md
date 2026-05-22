# OpenSpace

A self-hosted local AI router that classifies intent, delegates to specialized subagent models, and manages RAM-aware model lifecycle — all on your own hardware with no cloud dependency.

Rather than sending every request to a single model, OpenSpace routes each request to the right tool: a coder model for programming tasks, a reasoning model for analysis, and a lightweight model for everything else. If a model fails or is unavailable, it falls back through a defined chain automatically.

![License](https://img.shields.io/badge/license-MIT-blue?style=flat-square)
![Python](https://img.shields.io/badge/python-3.10%2B-3776ab?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/framework-FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![Ollama](https://img.shields.io/badge/backend-Ollama-black?style=flat-square)
![Providers](https://img.shields.io/badge/providers-Ollama%20%7C%20llama.cpp%20%7C%20MLX-orange?style=flat-square)

---

## How it works

```
┌─────────────────────────────────────────┐
│              YOUR REQUEST               │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│         INTENT CLASSIFIER               │
│         phi3 (fast, local)              │
│                                         │
│   "code/debug" → coder                 │
│   "explain/analyze" → reason           │
│   "everything else" → tiny             │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│           SUBAGENT ROUTER               │
│                                         │
│  coder  → deepseek-coder → qwen2.5 → phi3  │
│  reason → gemma2:9b → mistral → phi3   │
│  tiny   → phi3                          │
│                                         │
│  (fallback chain — tries next on fail)  │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│           OLLAMA :11434                 │
│           local inference               │
│           Vulkan compute                │
└─────────────────────────────────────────┘
```

---

## Features

**Intent classification before routing.** Each request is classified by a lightweight model before being dispatched. No manual model selection needed.

**Subagent delegation with fallback chains.** Each role has a priority list of models. If the primary model fails or times out, the next in chain is tried automatically.

**Context-aware token budgeting.** Large-context models receive the full system prompt and personal context. Small models receive a condensed header — preventing context overflow without losing grounding.

**RAM-aware model lifecycle.** Before loading a model, available system RAM is checked against known model costs. If loading would exceed the configured limit, the request is rejected cleanly rather than crashing.

**Multiple backend providers.** Ships with provider adapters for Ollama, llama.cpp, and MLX (Apple Silicon). Add your own by implementing `BaseProvider`.

**OpenAI-compatible API.** `/v1/chat/completions` accepts standard OpenAI request format — works with any existing client.

**Rolling memory buffer.** Multi-turn conversations are tracked across requests with a configurable rolling window.

---

## Quick start

```bash
git clone https://github.com/equ1nox-git/openspace.git
cd openspace
pip install -r requirements.txt
python3 api_server.py
```

Test:
```bash
curl http://localhost:11435/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"write a python bubble sort"}]}'
```

---

## Configuration

**Environment variables:**

| Variable | Default | Description |
|----------|---------|-------------|
| `PROMPTS_DIR` | `./prompts` | Directory for `system_prompt.md`, `master_context.md`, `context_header.md` |

**Model config** — edit `config.json` to change which models back each role:

```json
{
  "models": [
    { "name": "coder",    "provider": "ollama", "model_name": "qwen2.5-coder:7b" },
    { "name": "reasoner", "provider": "ollama", "model_name": "mistral:latest" },
    { "name": "tiny",     "provider": "tiny",   "model_name": "phi3:mini" }
  ]
}
```

---

## Prompt files

| File | Purpose |
|------|---------|
| `prompts/system_prompt.md` | Base instructions injected on every request |
| `prompts/master_context.md` | Full personal context for large-context models (excluded from repo) |
| `prompts/context_header.md` | Condensed context summary for small models (excluded from repo) |

All prompt files are optional. If absent, requests are handled with a default system prompt.

---

## Providers

| Provider | File | Use case |
|----------|------|----------|
| `ollama` | `providers/ollama_provider.py` | Ollama-hosted models (default) |
| `llamacpp` | `providers/llamacpp_provider.py` | Direct llama.cpp GGUF inference |
| `mlx` | `providers/mlx_provider.py` | Apple Silicon MLX inference |
| `tiny` | `providers/tiny_provider.py` | Minimal fallback |

---

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/v1/chat/completions` | Chat with intent classification and subagent routing |
| `GET` | `/v1/models` | List available roles |
| `GET` | `/api/tags` | Ollama-compatible model list |
| `POST` | `/api/generate` | Ollama-compatible generate endpoint |

---

## Requirements

- Python 3.10+
- [Ollama](https://ollama.ai) running on `localhost:11434`
- `psutil` for RAM-aware lifecycle management

---

## License

MIT
