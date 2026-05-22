class PromptOrchestrator:
    """
    The orchestrator decides how to prepare prompts for each model.
    It can:
      - rewrite prompts
      - add system instructions
      - add memory context
      - route based on role
      - apply model-specific formatting
    """

    def __init__(self, models):
        self.models = models

    def choose_model(self, user_input):
        """
        Basic routing logic:
        - If user explicitly selects a model (/tiny, /coder, etc.), router handles it.
        - Otherwise, choose based on keywords or roles.
        """
        text = user_input.lower()

        if any(k in text for k in ["code", "function", "bug", "error"]):
            return "coder"

        if any(k in text for k in ["why", "explain", "reason", "logic"]):
            return "reasoner"

        if any(k in text for k in ["speak", "voice", "audio"]):
            return "voice"

        return "tiny"

    def build_prompt(self, memory, user_input):
        """
        Combine:
        - system instructions
        - memory context
        - user input
        """
        system = (
            "You are OpenSpace, a local AI assistant. "
            "Be concise, helpful, and avoid hallucinations."
        )

        context = memory.build_prompt()

        return f"{system}\n\n{context}\nUser: {user_input}\nAssistant:"
