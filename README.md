# OpenSpace

A self-hosted local AI router that classifies intent, delegates to specialized subagent models, and manages RAM-aware model lifecycle — all on your own hardware, no cloud required.

Rather than sending every request to a single model, OpenSpace routes each request to the right tool: a coder model for programming tasks, a reasoning model for analysis, a lightweight model for everything else. If a model fails or is unavailable, it falls back through a defined chain automatically.

## Why I built this

Running multiple local models (a fast small one, a slower reasoning one, a coding-specific one) means you're constantly choosing which model to ask. The fast model is bad at code. The coding model is slow for simple questions. I wanted to stop choosing manually.

OpenSpace adds a lightweight classifier in front: it reads the request, decides what kind of task it is, and routes to the right model without any input from me. If that model is unavailable or fails, it tries the next one. If available RAM would be exceeded loading a model, the request fails cleanly instead of crashing the machine — something I learned the hard way.

![License](https://img.shields.io/badge/license-MIT-blue?style=flat-square)
![Python](https://img.shields.io/badge/python-3.10%2B-3776ab?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/framework-FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![Ollama](https://img.shields.io/badge/backend-Ollama-black?style=flat-square)
![Providers](https://img.shields.io/badge/providers-Ollama%20%7C%20llama.cpp%20%7C%20MLX-orange?style=flat-square)

---

## What it does

**Intent classification before routing.** Every request is classified by a fast local model before dispatch. You never manually pick a model — OpenSpace reads the request and sends it to the right specialist.

**Subagent delegation with fallback chains.** Each role has a priority list of models. If the primary fails or times out, the next in chain is tried automatically. Your request always gets a response.

**RAM-aware model lifecycle.** Before loading a model, available system RAM is checked against known model costs. If loading would push past your configured limit, the request is rejected cleanly rather than crashing your machine.

**Context-aware token budgeting.** Large-context models receive the full system prompt and personal context. Small models receive a condensed header — preventing context overflow without losing grounding.

**Multiple backend providers.** Ships with adapters for Ollama, llama.cpp, and MLX (Apple Silicon). Add your own by implementing `BaseProvider`.

**OpenAI-compatible API.** `/v1/chat/completions` accepts the standard OpenAI request format — works with any existing client, library, or tool that can hit a local endpoint.

**Rolling memory buffer.** Multi-turn conversations are tracked across requests with a configurable rolling window.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    YOUR REQUEST                     │
└──────────────────────────┬──────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────┐
│               INTENT CLASSIFIER                     │
│               phi3  (fast, local)                   │
│                                                     │
│   "code / debug / bug"      →  coder                │
│   "explain / analyze / why" →  reasoner             │
│   "everything else"         →  tiny                 │
└──────────────────────────┬──────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────┐
│                 SUBAGENT ROUTER                     │
│                                                     │
│  coder    →  deepseek-coder  →  qwen2.5  →  phi3   │
│  reasoner →  gemma2:9b       →  mistral  →  phi3   │
│  tiny     →  phi3                                   │
│                                                     │
│  (fallback chain — tries next model on failure)     │
└──────────────────────────┬──────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────┐
│                  OLLAMA :11434                      │
│                  local inference                    │
│                  Vulkan compute                     │
└─────────────────────────────────────────────────────┘
```

---

## Quick start

```bash
git clone https://github.com/equ1nox-git/openspace.git
cd openspace
pip install -r requirements.txt
python3 api_server.py
```

Test it:
```bash
# List available roles
curl http://localhost:11435/v1/models

# Send a request — intent is classified and routed automatically
curl http://localhost:11435/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"write a python bubble sort"}]}'
```

---

## Configuration

All settings via environment variables or a `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_URL` | `http://localhost:11434` | Ollama backend address |
| `OPENSPACE_HOST` | `127.0.0.1` | Bind address (`0.0.0.0` to expose on LAN) |
| `OPENSPACE_PORT` | `11435` | Listen port |
| `PROMPTS_DIR` | `./prompts` | Directory for prompt files |

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
| `prompts/master_context.md` | Full personal context for large-context models (create locally — excluded from repo) |
| `prompts/context_header.md` | Condensed context summary for small models (create locally — excluded from repo) |

All prompt files are optional. If absent, requests are handled with a minimal default system prompt.

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
| `GET` | `/` | Health check |
| `POST` | `/v1/chat/completions` | Chat with intent classification and subagent routing |
| `GET` | `/v1/models` | List available roles |
| `GET` | `/api/tags` | Ollama-compatible model list |
| `POST` | `/api/generate` | Ollama-compatible generate endpoint |

---

## CLI mode

`router.py` is a standalone interactive CLI — useful for local testing without running the API server:

```bash
python3 router.py
```

Type `/coder`, `/reason`, `/tiny`, or `/voice` to route directly to a role. Type `/exit` to quit.

---

## Requirements

- Python 3.10+
- [Ollama](https://ollama.ai) running on `localhost:11434`
- Dependencies: `pip install -r requirements.txt`

---

## Related projects

- **[Straddle](https://github.com/equ1nox-git/straddle)** — Minimal Ollama bridge: single endpoint, system prompt injection, KV cache tuning. Pairs well with OpenSpace as a frontend proxy.
- **[OpenCode Agentic OS](https://github.com/equ1nox-git/opencode-agentic-os)** — 35 specialist agents for OpenCode. Education tutors, engineers, sales coaches, QA — all domain-specific.

---

## License

MIT
