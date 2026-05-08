import json
import os
import re
import subprocess
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


def run_docker_build(output_dir: str = "outputs") -> tuple[bool, str]:
    """Run mvn compile inside a Maven Docker container. Returns (success, error_output)."""
    abs_output = str(Path(output_dir).resolve())
    m2_cache = str(Path.home() / ".m2")
    cmd = [
        "docker", "run", "--rm",
        "-v", f"{abs_output}:/project",
        "-v", f"{m2_cache}:/root/.m2",
        "maven:3.9-eclipse-temurin-21",
        "mvn", "-f", "/project/pom.xml", "compile", "-q", "--no-transfer-progress",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    combined = (result.stdout + result.stderr).strip()
    return result.returncode == 0, combined


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
