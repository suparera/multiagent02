import json
import subprocess
from pathlib import Path

from agents.glm_agent import GLMAgent
from agents.ResilientClaudeAgent import ResilientClaudeAgent
from delta import analyze_delta, print_delta
from github_issues import close_issue, create_issue, ensure_labels, get_repo, sort_by_severity
from prompt_loader import load_prompt
from utils import extract_code_blocks, extract_json, timed

planner = ResilientClaudeAgent()
coder = GLMAgent(temperature=0.3)
reviewer = ResilientClaudeAgent()
fixer = GLMAgent(temperature=0.1)

architect_prompt = load_prompt("architect")
coder_prompt = load_prompt("coder")
reviewer_prompt = load_prompt("reviewer")
fixer_prompt = load_prompt("fixer")

task = """
Design a minimal stock trading REST API.
"""


planner_input = f"""
{architect_prompt}

User Task:
{task}
"""

plan = timed("planner", lambda: planner.run(planner_input))

print("PLAN:")
print(plan)


coder_input = f"""
{coder_prompt}

Architecture:
{plan}
"""

raw_code = timed("coder", lambda: coder.run(coder_input))

code = extract_code_blocks(raw_code)
print("CODE:")
print(code)

review_prompt = f"""
{reviewer_prompt}


Review ONLY this code:

{code[:12000]}
"""

raw_review = timed("reviewer", lambda: reviewer.run(review_prompt))

review = extract_json(raw_review)

print("REVIEW:")
print(review)

### Post findings as GitHub issues
repo = get_repo()
ensure_labels(repo)

sorted_review = sort_by_severity(review)
issue_numbers = []
for finding in sorted_review:
    number = create_issue(repo, finding)
    issue_numbers.append((number, finding))
    print(f"Created issue #{number}: [{finding['severity']}] {finding['type']}")

### Fix issue by issue, HIGH -> MEDIUM -> LOW
current_code = code
for issue_number, finding in issue_numbers:
    print(f"\nFixing issue #{issue_number}: [{finding['severity']}] {finding['type']}")

    fix_input = f"""
{fixer_prompt}

Finding to Fix:
{json.dumps(finding, indent=2)}

Code:
{current_code}
"""

    fixed_raw = timed(f"fixer #{issue_number}", lambda fi=fix_input: fixer.run(fi))
    fixed = extract_code_blocks(fixed_raw)

    if fixed.strip():
        current_code = fixed
        close_issue(repo, issue_number)
        print(f"Closed issue #{issue_number}")
    else:
        print(f"Fixer returned no code for issue #{issue_number}, skipping close")

fixed_code = current_code

### Re-reviewer
re_review_prompt = f"""
{reviewer_prompt}

Review ONLY this code:

{fixed_code[:6000]}
"""
re_review_raw = timed("re-reviewer", lambda: reviewer.run(re_review_prompt))
if "timeout" in re_review_raw.lower():
    print("Reviewer timed out")

    re_review = []

else:
    print(f"""RE-REVIEW RAW:\n {re_review_raw}\nEND-RE-REVIEW""")
    re_review = extract_json(re_review_raw)
    print("RE-REVIEW:")
    print(re_review)


delta = analyze_delta(review, re_review)
print_delta(delta)

delta_output = {
    "fixed": delta.fixed,
    "remaining": delta.remaining,
    "new": delta.new,
}

Path("outputs/plan.txt").write_text(plan)
Path("outputs/raw_code.txt").write_text(raw_code)
Path("outputs/code.txt").write_text(code)
Path("outputs/reviewer.json").write_text(json.dumps(review, indent=2), encoding="utf-8")
Path("outputs/fixed_code.txt").write_text(fixed_code)
Path("outputs/re_review.json").write_text(
    json.dumps(re_review, indent=2), encoding="utf-8"
)
Path("outputs/delta.json").write_text(json.dumps(delta_output, indent=2), encoding="utf-8")

### Commit outputs to the outputs repo
def _git_outputs(*args):
    subprocess.run(["git", "-C", "outputs", *args], check=True)

_git_outputs("add", "-A")
_git_outputs("commit", "--allow-empty", "-m", f"pipeline run: {task.strip()[:72]}")
print("Committed pipeline outputs to outputs/ repo.")
