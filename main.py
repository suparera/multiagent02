import json
import subprocess
from pathlib import Path

from agents.debugger_agent import DebuggerAgent
from agents.doc_research_agent import DocResearchAgent
from agents.docker_run_agent import DockerRunAgent
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

# ── Agents ──────────────────────────────────────────────────────────────────
planner       = ResilientClaudeAgent()
coder         = GLMAgent(temperature=0.3)
reviewer      = ResilientClaudeAgent()
fixer         = GLMAgent(temperature=0.1)
compile_fixer = GLMAgent(temperature=0.1)
debugger      = DebuggerAgent()
doc_research  = DocResearchAgent()
docker_runner = DockerRunAgent(output_dir="outputs", timeout=30)

# ── Prompts ──────────────────────────────────────────────────────────────────
architect_prompt     = load_prompt("architect")
coder_prompt         = load_prompt("coder")
reviewer_prompt      = load_prompt("reviewer")
fixer_prompt         = load_prompt("fixer")
compile_fixer_prompt = load_prompt("compile_fixer")
debugger_prompt      = load_prompt("debugger")
doc_research_prompt  = load_prompt("doc_research")

# ── Ensure outputs repo has a .gitignore ─────────────────────────────────────
_outputs_gitignore = Path("outputs/.gitignore")
if not _outputs_gitignore.exists():
    _outputs_gitignore.write_text(
        "target/\n*.class\n.quarkus/\n.idea/\n.eclipse/\n*.iml\n.DS_Store\n"
    )

# ── Task ─────────────────────────────────────────────────────────────────────
task = """
Build a Binance USDS-Margined Futures market data stream consumer in Quarkus 3.9 / Java 21.

Requirements:
1. WebSocket connection
   - Connect to wss://fstream.binance.com/ws using bare Vert.x HttpClient.
   - IMPORTANT: obtain the client via vertx.getDelegate().createHttpClient()
     which returns io.vertx.core.http.HttpClient (NOT the Mutiny wrapper).
     The Mutiny wrapper pauses the stream after the first frame and must NOT be used.
   - Subscribe to streams: btcusdt@aggTrade and btcusdt@markPrice@1s
   - Register ws.handler(buffer -> ...) BEFORE calling ws.writeTextMessage()

2. ClickHouse storage (HTTP API)
   - On startup, create these tables if they do not exist using
     POST http://{CLICKHOUSE_HOST}:{CLICKHOUSE_PORT}/?query=<DDL>
   - Table: agg_trades
       symbol String, price Float64, quantity Float64,
       trade_time DateTime64(3), agg_trade_id UInt64
     ENGINE = MergeTree() ORDER BY trade_time
   - Table: mark_prices
       symbol String, mark_price Float64, funding_rate Float64,
       event_time DateTime64(3)
     ENGINE = MergeTree() ORDER BY event_time
   - On each incoming frame, insert one row via
     POST http://{CLICKHOUSE_HOST}:{CLICKHOUSE_PORT}/?query=INSERT+INTO+<table>+FORMAT+JSONEachRow
   - Use java.net.http.HttpClient for the ClickHouse HTTP calls (not Vert.x)

3. Configuration (application.properties, overridable by env var)
   - clickhouse.host=clickhouse   (env: CLICKHOUSE_HOST)
   - clickhouse.port=8123         (env: CLICKHOUSE_PORT)
   - binance.streams=btcusdt@aggTrade,btcusdt@markPrice@1s

4. Logging
   - Print each insert to stdout: [INSERT] table=agg_trades symbol=BTCUSDT price=67432.10
   - Print errors clearly with [ERROR] prefix

5. docker-compose.yml (generate this file)
   - Service: clickhouse using image clickhouse/clickhouse-server:24.3
     ports 8123 and 9000, volume clickhouse_data, healthcheck via clickhouse-client SELECT 1
   - Service: binance-stream using build: .
     depends_on clickhouse (condition: service_healthy)
     environment: CLICKHOUSE_HOST, CLICKHOUSE_PORT, BINANCE_STREAMS
   - Named volume: clickhouse_data
"""

# ════════════════════════════════════════════════════════════════════════════
# STAGE 1 — PLAN
# ════════════════════════════════════════════════════════════════════════════
planner_input = f"""
{architect_prompt}

User Task:
{task}
"""

plan = timed("planner", lambda: planner.run(planner_input))
print("PLAN:\n" + plan)

# ════════════════════════════════════════════════════════════════════════════
# STAGE 2 — CODE
# ════════════════════════════════════════════════════════════════════════════
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

# ════════════════════════════════════════════════════════════════════════════
# STAGE 3 — REVIEW → GITHUB ISSUES
# ════════════════════════════════════════════════════════════════════════════
review_prompt = f"""
{reviewer_prompt}

Review ONLY this code:

{code_text[:12000]}
"""

raw_review = timed("reviewer", lambda: reviewer.run(review_prompt))
review = extract_json(raw_review)
print("REVIEW:\n" + json.dumps(review, indent=2))

repo = get_repo()
ensure_labels(repo)

sorted_review = sort_by_severity(review)
issue_numbers = []
for finding in sorted_review:
    number = create_issue(repo, finding)
    issue_numbers.append((number, finding))
    print(f"Created issue #{number}: [{finding['severity']}] {finding['type']}")

# ════════════════════════════════════════════════════════════════════════════
# STAGE 4 — FIX (issue by issue, HIGH → MEDIUM → LOW)
# ════════════════════════════════════════════════════════════════════════════
current_structure = file_structure
for issue_number, finding in issue_numbers:
    print(f"\nFixing issue #{issue_number}: [{finding['severity']}] {finding['type']}")

    fix_input = f"""
{fixer_prompt}

Finding to Fix:
{json.dumps(finding, indent=2)}

Code:
{format_file_structure(current_structure)}
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

# ════════════════════════════════════════════════════════════════════════════
# STAGE 5 — COMPILE VALIDATION (Docker Maven)
# ════════════════════════════════════════════════════════════════════════════
MAX_COMPILE_ATTEMPTS = 3
print("\n" + "=" * 60)
print("COMPILE VALIDATION (Docker Maven)")
print("=" * 60)

for attempt in range(1, MAX_COMPILE_ATTEMPTS + 1):
    print(f"\nCompile attempt {attempt}/{MAX_COMPILE_ATTEMPTS}...")
    success, build_output = timed(f"compile #{attempt}", lambda: run_docker_build("outputs"))

    if success:
        print("Compile PASSED")
        break

    print(f"Compile FAILED:\n{build_output[:3000]}")
    if attempt == MAX_COMPILE_ATTEMPTS:
        print("Max compile attempts reached — moving on")
        break

    compile_fix_input = f"""
{compile_fixer_prompt}

Compile Error:
{build_output[:3000]}

Code:
{format_file_structure(current_structure)}
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

# ════════════════════════════════════════════════════════════════════════════
# STAGE 6 — RUNTIME VALIDATION (docker compose + DebuggerAgent)
# ════════════════════════════════════════════════════════════════════════════
MAX_RUNTIME_ATTEMPTS = 3
print("\n" + "=" * 60)
print("RUNTIME VALIDATION (docker compose)")
print("=" * 60)

for attempt in range(1, MAX_RUNTIME_ATTEMPTS + 1):
    print(f"\nRuntime attempt {attempt}/{MAX_RUNTIME_ATTEMPTS} — observing for {docker_runner.timeout}s...")

    runtime_output = timed(f"docker-run #{attempt}", lambda: docker_runner.run())

    debug_input = f"""
{debugger_prompt}

Runtime Output:
{runtime_output}

Code:
{format_file_structure(current_structure)[:10000]}
"""

    debug_raw = timed(f"debugger #{attempt}", lambda di=debug_input: debugger.run(di))
    print(f"Debugger says:\n{debug_raw[:400]}")

    # ── Success ──────────────────────────────────────────────────────────────
    if debug_raw.strip().upper() == "LGTM":
        print("Runtime validated by DebuggerAgent")
        break

    # ── Research needed ───────────────────────────────────────────────────────
    if debug_raw.startswith("RESEARCH:"):
        question = debug_raw.splitlines()[0].replace("RESEARCH:", "").strip()
        print(f"DocResearchAgent called: {question}")

        research_input = f"""
{doc_research_prompt}

Question:
{question}
"""
        doc_answer = timed("doc-research", lambda ri=research_input: doc_research.run(ri))
        print(f"DocResearch answer:\n{doc_answer[:400]}")

        # Re-run debugger with doc context included
        debug_input_with_docs = f"""
{debugger_prompt}

Library Documentation Context:
{doc_answer}

Runtime Output:
{runtime_output}

Code:
{format_file_structure(current_structure)[:10000]}
"""
        debug_raw = timed(
            f"debugger-with-docs #{attempt}",
            lambda di=debug_input_with_docs: debugger.run(di),
        )
        print(f"Debugger (with docs) says:\n{debug_raw[:400]}")

        if debug_raw.strip().upper() == "LGTM":
            print("Runtime validated by DebuggerAgent (after research)")
            break

    # ── Apply fixes ───────────────────────────────────────────────────────────
    fixed_files = extract_file_structure(debug_raw)
    if not fixed_files:
        print("DebuggerAgent returned no file fixes — stopping runtime loop")
        break

    current_structure = {**current_structure, **fixed_files}
    write_project_files(fixed_files)
    print(f"Applied debugger fixes to {len(fixed_files)} file(s)")

    if attempt == MAX_RUNTIME_ATTEMPTS:
        print("Max runtime attempts reached")

# ════════════════════════════════════════════════════════════════════════════
# STAGE 7 — RE-REVIEW + DELTA
# ════════════════════════════════════════════════════════════════════════════
final_text = format_file_structure(current_structure)

re_review_prompt = f"""
{reviewer_prompt}

Review ONLY this code:

{final_text[:6000]}
"""
re_review_raw = timed("re-reviewer", lambda: reviewer.run(re_review_prompt))
if "timeout" in re_review_raw.lower():
    print("Re-reviewer timed out")
    re_review = []
else:
    re_review = extract_json(re_review_raw)
    print("RE-REVIEW:\n" + json.dumps(re_review, indent=2))

delta = analyze_delta(review, re_review)
print_delta(delta)

delta_output = {
    "fixed": delta.fixed,
    "remaining": delta.remaining,
    "new": delta.new,
}

# ════════════════════════════════════════════════════════════════════════════
# SAVE + COMMIT
# ════════════════════════════════════════════════════════════════════════════
Path("outputs/plan.txt").write_text(plan)
Path("outputs/raw_code.txt").write_text(raw_code)
Path("outputs/reviewer.json").write_text(json.dumps(review, indent=2), encoding="utf-8")
Path("outputs/re_review.json").write_text(json.dumps(re_review, indent=2), encoding="utf-8")
Path("outputs/delta.json").write_text(json.dumps(delta_output, indent=2), encoding="utf-8")


def _git_outputs(*args):
    subprocess.run(["git", "-C", "outputs", *args], check=True)

_git_outputs("add", "-A")
_git_outputs("commit", "--allow-empty", "-m", f"pipeline run: {task.strip()[:72]}")
print("Committed pipeline outputs to outputs/ repo.")
