import os
import subprocess


class ClaudeCodeAgent:
    def __init__(self, provider="claude_native"):

        self.provider = provider

    def build_env(self):

        env = os.environ.copy()

        if self.provider == "claude_glm":
            env["ANTHROPIC_BASE_URL"] = "https://api.z.ai/api/anthropic"

            env["ANTHROPIC_AUTH_TOKEN"] = os.getenv("ZAI_API_KEY", "")

            env["ANTHROPIC_MODEL"] = "glm-5.1"

        return env

    def run(self, prompt: str, timeout: int = 600):

        env = self.build_env()

        process = subprocess.Popen(
            ["claude", "--print", prompt],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )

        try:
            stdout, stderr = process.communicate(timeout=timeout)

        except subprocess.TimeoutExpired:
            process.kill()

            return "Claude timeout"

        if stderr:
            print("STDERR:", stderr)

        return stdout
