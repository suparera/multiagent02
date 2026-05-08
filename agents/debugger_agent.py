from agents.ResilientClaudeAgent import ResilientClaudeAgent
from agents.base import Agent


class DebuggerAgent(Agent):
    """Analyzes runtime output against source code and produces targeted fixes.

    Returns "LGTM" if behavior is correct.
    Returns "RESEARCH: <question>" on the first line if library docs are needed,
    followed by whatever partial fixes it can make.
    Otherwise returns ### File: blocks with fixes.
    """

    def __init__(self):
        self._agent = ResilientClaudeAgent()

    def run(self, prompt: str) -> str:
        return self._agent.run(prompt)
