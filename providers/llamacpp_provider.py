from .base_provider import BaseProvider
from llama_cpp import Llama
import os


class LlamaCPPProvider(BaseProvider):
    def load(self):
        if self.loaded:
            return

        model_path = os.path.expanduser(f"~/.llamacpp/models/{self.model_name}.gguf")

        if not os.path.exists(model_path):
            raise RuntimeError(f"LlamaCPP model not found at {model_path}")

        self.llm = Llama(
            model_path=model_path,
            n_ctx=4096,
            n_threads=4
        )

        self.loaded = True

    def unload(self):
        self.llm = None
        self.loaded = False

    def generate(self, prompt):
        if not self.loaded:
            raise RuntimeError("LlamaCPPProvider used before load()")

        output = self.llm(prompt, max_tokens=256)
        return output["choices"][0]["text"].strip()
