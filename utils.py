import json
import re
import time
from pathlib import Path


def extract_file_structure(text: str) -> dict[str, str]:
    """Parse ### File: <path> + fenced code block pairs from LLM output."""
    pattern = r'###\s+File:\s+(\S+)\n```(?:\w+)?\n(.*?)```'
    matches = re.findall(pattern, text, re.DOTALL)
    return {path: content for path, content in matches}


def format_file_structure(files: dict[str, str]) -> str:
    """Serialize a file structure dict back to ### File: format for LLM input."""
    parts = []
    for path, content in files.items():
        ext = path.rsplit('.', 1)[-1] if '.' in path else ''
        parts.append(f"### File: {path}\n```{ext}\n{content}\n```")
    return "\n\n".join(parts)


def write_project_files(files: dict[str, str], output_dir: str = "outputs") -> None:
    """Write parsed file structure to disk under output_dir, creating directories as needed."""
    for path, content in files.items():
        full_path = Path(output_dir) / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")


def extract_code_blocks(text: str) -> str:
    matches = re.findall(r"```(?:\w+)?\n(.*?)```", text, re.DOTALL)
    return "\n\n".join(matches)


def timed(label, fn):
    start = time.time()
    result = fn()
    elapsed = time.time() - start
    print(f"{label}: {elapsed:.2f}s")
    return result


def extract_json(text: str):
    try:
        start = text.find("[")
        end = text.rfind("]") + 1
        if start == -1 or end == 0:
            return []
        return json.loads(text[start:end])
    except Exception as e:
        print("JSON PARSE ERROR")
        print(e)
        return []
