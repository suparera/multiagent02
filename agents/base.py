# agents/base.py

from abc import ABC, abstractmethod


class Agent(ABC):
    @abstractmethod
    def run(self, prompt: str) -> str:
        pass
