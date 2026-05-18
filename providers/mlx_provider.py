from .base_provider import BaseProvider
import mlx.core as mx
import mlx.nn as nn
from mlx.utils import tree_flatten
import json
import os


class MLXProvider(BaseProvider):
    def load(self):
        if self.loaded:
            return

        model_path = os.path.expanduser(f"~/.mlx/models/{self.model_name}")

        if not os.path.exists(model_path):
            raise RuntimeError(f"MLX model not found at {model_path}")

        # Load model weights
        with open(os.path.join(model_path, "config.json"), "r") as f:
            config = json.load(f)

        self.model = nn.Sequential(
            nn.Embedding(config["vocab_size"], config["hidden_size"]),
            nn.Linear(config["hidden_size"], config["vocab_size"])
        )

        weights = mx.load(os.path.join(model_path, "weights.npz"))
        self.model.update(tree_flatten(weights))

        self.tokenizer = self._load_tokenizer(model_path)
        self.loaded = True

    def _load_tokenizer(self, model_path):
        tok_path = os.path.join(model_path, "tokenizer.json")
        if not os.path.exists(tok_path):
            raise RuntimeError("Tokenizer not found for MLX model")

        with open(tok_path, "r") as f:
            return json.load(f)

    def unload(self):
        self.model = None
        self.tokenizer = None
        self.loaded = False

    def generate(self, prompt):
        if not self.loaded:
            raise RuntimeError("MLXProvider used before load()")

        # Tokenize
        tokens = [self.tokenizer["vocab"].get(c, 0) for c in prompt]

        # Run model
        logits = self.model(mx.array(tokens))
        out_ids = logits.argmax(axis=-1).tolist()

        # Decode
        inv_vocab = {v: k for k, v in self.tokenizer["vocab"].items()}
        return "".join(inv_vocab.get(i, "?") for i in out_ids)
