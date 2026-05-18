from providers.base_provider import BaseProvider
import ollama


class TinyProvider(BaseProvider):
    def load(self):
        if not self.loaded:
            # Nothing heavy to load for tiny models, but you can add caching later
            self.loaded = True

    def unload(self):
        # No persistent resources yet, but this keeps the interface clean
        self.loaded = False

    def generate(self, prompt):
        if not self.loaded:
            raise RuntimeError("TinyProvider used before load()")

        response = ollama.generate(model=self.model_name, prompt=prompt)
        return response["response"]
