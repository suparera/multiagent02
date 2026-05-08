import os

from dotenv import load_dotenv

from agents.glm_agent import GLMAgent

load_dotenv()

print(os.getenv("ZAI_API_KEY"))

agent = GLMAgent()

print(agent.run("Say hello in one sentence"))
