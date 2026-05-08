import json
import subprocess


SEVERITY_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}

_LABELS = {
    "HIGH":   {"color": "d73a4a", "description": "High severity finding"},
    "MEDIUM": {"color": "e4e669", "description": "Medium severity finding"},
    "LOW":    {"color": "0075ca", "description": "Low severity finding"},
}


def _gh(*args) -> str:
    result = subprocess.run(["gh", *args], capture_output=True, text=True, check=True)
    return result.stdout.strip()


def get_repo() -> str:
    return _gh("repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner")


def ensure_labels(repo: str) -> None:
    existing = {l["name"] for l in json.loads(_gh("label", "list", "--repo", repo, "--json", "name"))}
    for severity, props in _LABELS.items():
        if severity not in existing:
            _gh("label", "create", severity,
                "--repo", repo,
                "--color", props["color"],
                "--description", props["description"])


def create_issue(repo: str, finding: dict) -> int:
    body = f"{finding['description']}\n\n**Suggested fix:** {finding['fix']}"
    url = _gh("issue", "create",
              "--repo", repo,
              "--title", f"[{finding['severity']}] {finding['type']}",
              "--body", body,
              "--label", finding["severity"])
    return int(url.rstrip("/").split("/")[-1])


def close_issue(repo: str, issue_number: int) -> None:
    _gh("issue", "close", str(issue_number),
        "--repo", repo,
        "--comment", "Resolved by AI fixer agent.")


def sort_by_severity(findings: list[dict]) -> list[dict]:
    return sorted(findings, key=lambda f: SEVERITY_ORDER.get(f["severity"], 99))
