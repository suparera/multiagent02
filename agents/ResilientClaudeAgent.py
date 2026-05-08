from agents.claude_code_agent import ClaudeCodeAgent


class ResilientClaudeAgent:
    def __init__(self):

        self.primary = ClaudeCodeAgent(provider="claude_native")

        self.fallback = ClaudeCodeAgent(provider="claude_glm")

    def run(self, prompt: str):

        result = self.primary.run(prompt)

        if "timeout" in result.lower() or not result.strip():
            print("Fallback -> GLM Claude")

            result = self.fallback.run(prompt)

        return result
