import json
import importlib
import os

from utils.logging import log
from lifecycle import can_load, mark_loaded, mark_unloaded
from memory_buffer import MemoryBuffer
from core.orchestrator import PromptOrchestrator   # ← ADDED

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")


def load_config():
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


COMMANDS = {
    "/tiny": "tiny",
    "/coder": "coder",
    "/reason": "reasoner",
    "/voice": "voice",
}


def select_model(user_input, models):
    for prefix, model_key in COMMANDS.items():
        if user_input.startswith(prefix):
            prompt = user_input[len(prefix):].strip()
            return model_key, prompt
    return "tiny", user_input.strip()


def load_provider(provider_name, model_name):
    module = importlib.import_module(f"providers.{provider_name}_provider")
    class_name = f"{provider_name.capitalize()}Provider"
    provider_class = getattr(module, class_name)
    return provider_class(model_name)


def main():
    config = load_config()
    models = {m["name"]: m for m in config["models"]}
    orchestrator = PromptOrchestrator(models)      # ← ADDED

    log("OpenSpace Router Ready. Type /exit to quit.")

    current_provider = None
    memory = MemoryBuffer()

    while True:
        user_input = input("> ").strip()

        if user_input == "/exit":
            if current_provider:
                mark_unloaded(current_provider.model_name)
                current_provider.unload()
            log("Goodbye.")
            break

        model_name, prompt = select_model(user_input, models)
        model_info = models[model_name]
        provider_name = model_info["provider"]

        if not can_load(model_name):
            print(f"[ERROR] Cannot load model '{model_name}' due to RAM limits.")
            continue

        if current_provider is None or current_provider.model_name != model_name:
            if current_provider:
                mark_unloaded(current_provider.model_name)
                current_provider.unload()

            current_provider = load_provider(provider_name, model_info["model_name"])
            current_provider.load()
            mark_loaded(model_name)

        memory.add_user_message(prompt)

        # NEW: orchestrator builds the final prompt
        final_prompt = orchestrator.build_prompt(memory, prompt)

        try:
            output = current_provider.generate(final_prompt)
        except Exception as e:
            output = f"[ERROR] Provider failed: {str(e)}"

        memory.add_assistant_message(output)
        print(output)


if __name__ == "__main__":
    main()
