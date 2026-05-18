import subprocess

from .base_provider import BaseProvider

class OllamaProvider(BaseProvider):
    def load(self):
        pass  # nothing to load

    def generate(self, prompt):
        if not prompt:
            return "[Ollama] Empty prompt."

        try:
            process = subprocess.Popen(
                ["ollama", "run", self.model_name],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            out, err = process.communicate(prompt)

            if err and not out:
                return f"[Ollama Error] {err.strip()}"

            return out.strip() if out else "[Ollama] No output."
        except Exception as e:
            return f"[Exception] {str(e)}"

    def unload(self):
        pass
