from pathlib import Path


def load_prompt(name: str) -> str:

    path = Path("prompts") / f"{name}.txt"

    return path.read_text()
