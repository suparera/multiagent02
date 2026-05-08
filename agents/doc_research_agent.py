from agents.ResilientClaudeAgent import ResilientClaudeAgent
from agents.base import Agent


class DocResearchAgent(Agent):
    """Answers specific questions about library APIs and framework behavior.

    Uses Claude's knowledge to explain exact class/method semantics,
    backpressure models, threading models, and common pitfalls.
    """

    def __init__(self):
        self._agent = ResilientClaudeAgent()

    def run(self, prompt: str) -> str:
        return self._agent.run(prompt)
