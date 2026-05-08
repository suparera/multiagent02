from agents.claude_code_agent import ClaudeCodeAgent
from agents.glm_agent import GLMAgent

planner = ClaudeCodeAgent()
coder = GLMAgent()

plan = planner.run("""
Reply briefly.

Design a minimal Quarkus trading REST API architecture.
Return only bullet points.
""")

code = coder.run(f"""
Implement this architecture:

{plan}
""")

print(code)
