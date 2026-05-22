#!/usr/bin/env python3
"""
OpenSpace API with master context and system prompt injection.
Reads prompt files at startup; uses Ollama API with `system` parameter.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import json
import sys
import os

app = FastAPI()

OLLAMA_URL  = os.environ.get("OLLAMA_URL",      "http://localhost:11434")
HOST        = os.environ.get("OPENSPACE_HOST",   "127.0.0.1")
PORT        = int(os.environ.get("OPENSPACE_PORT", 11435))
PROMPTS_DIR = os.environ.get("PROMPTS_DIR", os.path.join(os.path.dirname(__file__), "prompts"))

def _read_prompt(name: str, fallback: str = "") -> str:
    path = os.path.join(PROMPTS_DIR, name)
    if os.path.exists(path):
        with open(path) as f:
            return f.read()
    return fallback

MASTER_CONTEXT = _read_prompt("master_context.md")
SYSTEM_PROMPT  = _read_prompt("system_prompt.md", "You are a helpful local AI assistant.")

# Condensed context header for small models — token-efficient summary of master_context
REASON_CONTEXT_HEADER = _read_prompt("context_header.md", "")
if REASON_CONTEXT_HEADER:
    REASON_CONTEXT_HEADER += "\n\n"

# Full combined context — only safe for large-context models (gemma2:9b, mistral:7b)
FULL_SYSTEM = f"{SYSTEM_PROMPT}\n\n# Personal Context\n{MASTER_CONTEXT}" if MASTER_CONTEXT else SYSTEM_PROMPT

# Fallback chains for each subagent
FALLBACKS = {
    "tiny": ["phi3:8k"],
    "coder": ["deepseek-coder:6.7b", "qwen2.5-coder:7b", "phi3:8k"],
    "reason": ["phi3:8k", "gemma2:9b", "mistral:7b"],
    "voice": ["phi3:8k"]
}

ROLE_MAP = {
    "phi3:8k": "tiny",
    "tiny": "tiny",
    "mistral:7b": "reason",
    "reason": "reason",
    "qwen2.5-coder:7b": "coder",
    "coder": "coder",
    "deepseek-coder:6.7b": "coder",
    "gemma2:9b": "reason",
    "llama3.2:latest": "voice",
    "voice": "voice",
    "nova": "master"
}

class ChatRequest(BaseModel):
    model: str = "tiny"
    messages: list
    stream: bool = False

LARGE_CONTEXT_MODELS = {"gemma2:9b", "mistral:7b"}

def call_ollama_api(model: str, user_prompt: str, system: str = None, timeout: int = 180) -> str:
    """Call Ollama's generate endpoint.
    Large-context models get FULL_SYSTEM; small models get SYSTEM_PROMPT only."""
    url = f"{OLLAMA_URL}/api/generate"
    if system is None:
        system = FULL_SYSTEM if model in LARGE_CONTEXT_MODELS else SYSTEM_PROMPT
    payload = {
        "model": model,
        "prompt": user_prompt,
        "system": system,
        "stream": False,
        "options": {"num_predict": 2048, "temperature": 0.7}
    }
    try:
        resp = requests.post(url, json=payload, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        return data.get("response", "").strip()
    except Exception as e:
        print(f"[call_ollama_api] model={model} error={e}", flush=True)
        return None

def classify_intent(prompt: str) -> str:
    """Use phi3:8k to classify intent (coder, reason, tiny). No master context injected."""
    classifier_system = (
        "You are a request classifier. Output exactly one word only: "
        "'coder', 'reason', or 'tiny'. No other output."
    )
    classifier_prompt = (
        f"Classify this request:\n{prompt}\n\n"
        "Output exactly one word — 'coder' (code/programming/debugging), "
        "'reason' (explanation/analysis/step-by-step), or 'tiny' (anything else):"
    )
    resp = call_ollama_api("phi3:8k", classifier_prompt, system=classifier_system, timeout=45)
    if not resp:
        return "tiny"
    intent = resp.strip().lower().split()[0]
    return intent if intent in ("coder", "reason", "tiny") else "tiny"

def call_subagent(role: str, prompt: str) -> str:
    """Call subagent with fallback chain. Reason role prepends context header for small-model fallbacks."""
    models = FALLBACKS.get(role, ["phi3:8k"])
    for model in models:
        effective_prompt = prompt
        if role == "reason" and model not in LARGE_CONTEXT_MODELS:
            effective_prompt = REASON_CONTEXT_HEADER + prompt
        answer = call_ollama_api(model, effective_prompt)
        if answer:
            return answer
    raise HTTPException(status_code=500, detail=f"All models failed for {role}")

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest):
    if not request.messages:
        raise HTTPException(status_code=400, detail="No messages")
    user_content = request.messages[-1].get("content", "")

    role = ROLE_MAP.get(request.model, "tiny")
    if role == "master":
        user_content = REASON_CONTEXT_HEADER + user_content
        intent = classify_intent(user_content)
        answer = call_subagent(intent, user_content)
    else:
        answer = call_subagent(role, user_content)

    return {
        "choices": [{
            "message": {"role": "assistant", "content": answer},
            "index": 0
        }]
    }

@app.get("/v1/models")
async def list_models():
    return {
        "data": [
            {"id": "tiny", "object": "model"},
            {"id": "coder", "object": "model"},
            {"id": "reason", "object": "model"},
            {"id": "voice", "object": "model"},
            {"id": "nova", "object": "model"},
        ]
    }

@app.get("/api/tags")
async def ollama_tags():
    return {
        "models": [
            {"name": m, "model": m, "modified_at": "2026-01-01T00:00:00Z", "size": 0, "digest": m}
            for m in ["tiny", "coder", "reason", "voice", "nova"]
        ]
    }

@app.post("/api/generate")
async def ollama_generate(request: dict):
    model = request.get("model", "tiny")
    prompt = request.get("prompt", "")
    role = ROLE_MAP.get(model, "tiny")
    if role == "master":
        prompt = REASON_CONTEXT_HEADER + prompt
        intent = classify_intent(prompt)
        answer = call_subagent(intent, prompt)
    else:
        answer = call_subagent(role, prompt)
    return {"model": model, "response": answer, "done": True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)
