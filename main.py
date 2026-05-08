import json
import subprocess
from pathlib import Path

from agents.glm_agent import GLMAgent
from agents.ResilientClaudeAgent import ResilientClaudeAgent
from delta import analyze_delta, print_delta
from github_issues import close_issue, create_issue, ensure_labels, get_repo, sort_by_severity
from prompt_loader import load_prompt
from utils import (
    extract_file_structure,
    format_file_structure,
    write_project_files,
    run_docker_build,
    extract_json,
    timed,
)

planner = ResilientClaudeAgent()
coder = GLMAgent(temperature=0.3)
reviewer = ResilientClaudeAgent()
fixer = GLMAgent(temperature=0.1)
compile_fixer = GLMAgent(temperature=0.1)

architect_prompt = load_prompt("architect")
coder_prompt = load_prompt("coder")
reviewer_prompt = load_prompt("reviewer")
fixer_prompt = load_prompt("fixer")
compile_fixer_prompt = load_prompt("compile_fixer")

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

file_structure = extract_file_structure(raw_code)
if not file_structure:
    print("WARNING: coder returned no structured files — check raw_code.txt")

write_project_files(file_structure)

print("FILES GENERATED:")
for path in file_structure:
    print(f"  outputs/{path}")

code_text = format_file_structure(file_structure)


review_prompt = f"""
{reviewer_prompt}

Review ONLY this code:

{code_text[:12000]}
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
current_structure = file_structure
for issue_number, finding in issue_numbers:
    print(f"\nFixing issue #{issue_number}: [{finding['severity']}] {finding['type']}")

    current_text = format_file_structure(current_structure)
    fix_input = f"""
{fixer_prompt}

Finding to Fix:
{json.dumps(finding, indent=2)}

Code:
{current_text}
"""

    fixed_raw = timed(f"fixer #{issue_number}", lambda fi=fix_input: fixer.run(fi))
    fixed_files = extract_file_structure(fixed_raw)

    if fixed_files:
        current_structure = {**current_structure, **fixed_files}
        write_project_files(fixed_files)
        close_issue(repo, issue_number)
        print(f"Closed issue #{issue_number}")
    else:
        print(f"Fixer returned no files for issue #{issue_number}, skipping close")

### Compile-and-fix loop (Docker Maven build)
MAX_COMPILE_ATTEMPTS = 3
print("\n" + "=" * 60)
print("COMPILE VALIDATION (Docker)")
print("=" * 60)

for attempt in range(1, MAX_COMPILE_ATTEMPTS + 1):
    print(f"\nCompile attempt {attempt}/{MAX_COMPILE_ATTEMPTS}...")
    success, build_output = timed(f"docker build #{attempt}", lambda: run_docker_build("outputs"))

    if success:
        print("Build PASSED")
        break

    print(f"Build FAILED:\n{build_output[:3000]}")

    if attempt == MAX_COMPILE_ATTEMPTS:
        print("Max compile attempts reached — moving on")
        break

    compile_text = format_file_structure(current_structure)
    compile_fix_input = f"""
{compile_fixer_prompt}

Compile Error:
{build_output[:3000]}

Code:
{compile_text}
"""
    fixed_raw = timed(
        f"compile-fixer #{attempt}",
        lambda fi=compile_fix_input: compile_fixer.run(fi),
    )
    fixed_files = extract_file_structure(fixed_raw)
    if fixed_files:
        current_structure = {**current_structure, **fixed_files}
        write_project_files(fixed_files)
        print(f"Compile-fixer updated {len(fixed_files)} file(s)")
    else:
        print("Compile-fixer returned no files")

final_text = format_file_structure(current_structure)


### Re-reviewer
re_review_prompt = f"""
{reviewer_prompt}

Review ONLY this code:

{final_text[:6000]}
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
Path("outputs/reviewer.json").write_text(json.dumps(review, indent=2), encoding="utf-8")
Path("outputs/re_review.json").write_text(json.dumps(re_review, indent=2), encoding="utf-8")
Path("outputs/delta.json").write_text(json.dumps(delta_output, indent=2), encoding="utf-8")


### Commit outputs to the outputs repo
def _git_outputs(*args):
    subprocess.run(["git", "-C", "outputs", *args], check=True)

_git_outputs("add", "-A")
_git_outputs("commit", "--allow-empty", "-m", f"pipeline run: {task.strip()[:72]}")
print("Committed pipeline outputs to outputs/ repo.")
