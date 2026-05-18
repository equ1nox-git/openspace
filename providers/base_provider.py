class BaseProvider:
    """
    Standard interface for all model providers.
    Every provider must implement:
      - load()
      - unload()
      - generate(prompt)
      - model_name (string)
    """

    def __init__(self, model_name):
        self.model_name = model_name
        self.loaded = False

    def load(self):
        """Load model resources into memory."""
        raise NotImplementedError("Provider must implement load()")

    def unload(self):
        """Unload model resources from memory."""
        raise NotImplementedError("Provider must implement unload()")

    def generate(self, prompt):
        """Generate output from the model."""
        raise NotImplementedError("Provider must implement generate()")
