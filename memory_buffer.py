class MemoryBuffer:
    """
    Simple rolling memory buffer for multi-turn conversations.
    Stores user and assistant messages and can build a prompt
    suitable for LLMs that expect conversational context.
    """

    def __init__(self, max_messages=20):
        self.max_messages = max_messages
        self.messages = []

    def add_user_message(self, text):
        self._add("user", text)

    def add_assistant_message(self, text):
        self._add("assistant", text)

    def _add(self, role, text):
        self.messages.append({"role": role, "text": text})
        if len(self.messages) > self.max_messages:
            self.messages.pop(0)

    def build_prompt(self):
        """
        Converts memory into a single prompt string.
        Providers that support chat-style input can override this.
        """
        lines = []
        for msg in self.messages:
            prefix = "User:" if msg["role"] == "user" else "Assistant:"
            lines.append(f"{prefix} {msg['text']}")
        return "\n".join(lines)
