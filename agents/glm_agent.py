import os

import anthropic
from dotenv import load_dotenv

load_dotenv()


class GLMAgent:
    def __init__(self, temperature=0.2):
        self.temperature = temperature
        api_key = os.getenv("ZAI_API_KEY")

        if not api_key:
            raise ValueError("ZAI_API_KEY not found")

        self.client = anthropic.Anthropic(
            api_key=api_key,
            base_url="https://api.z.ai/api/anthropic",
        )

    def run(self, prompt: str) -> str:

        message = self.client.messages.create(
            model="glm-5.1",
            max_tokens=2048,
            temperature=self.temperature,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )

        return message.content[0].text
