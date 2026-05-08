# Multi-Agent AI Dev Team — Current State Summary

## Goal

Build a lightweight multi-agent orchestration system using:

* Claude Code subscription (CLI only, no API)
* GLM API (Anthropic-compatible)
* Python orchestrator

Focus:

* AI engineering workflows
* trading backend generation/review
* practical orchestration (not autonomous swarm)

---

# Current Architecture

```text
Planner   -> Claude Code CLI
Coder     -> GLM API
Reviewer  -> Claude Code CLI
```

Pipeline:

```text
Task
 -> Planner
 -> Coder
 -> Normalizer
 -> Reviewer
```

---

# Current Tech Stack

## Models

* Claude Code CLI
* GLM-5.1 via Anthropic SDK compatibility

## Python

* uv
* anthropic SDK
* python-dotenv

## Structure

```text
/project
    main.py
    prompt_loader.py
    utils.py

    /agents
        claude_code_agent.py
        glm_agent.py

    /prompts
        architect.txt
        coder.txt
        reviewer.txt

    /outputs
        plan.txt
        raw_code.txt
        code.txt
        reviewer.txt
```

---

# Important Implementations

## GLM Agent

Uses:

```python
anthropic.Anthropic(
    api_key=...,
    base_url="https://api.z.ai/api/anthropic"
)
```

---

## Claude Code Agent

Uses subprocess:

```python
subprocess.Popen(
    ["claude", "--print", prompt],
    ...
)
```

with timeout handling.

---

## Prompt System

Prompts separated by role:

* architect.txt
* coder.txt
* reviewer.txt

Loaded via:

```python
load_prompt(...)
```

---

## Normalization Layer

Problem:
LLMs return explanations + markdown + code mixed together.

Solution:
Extract code blocks using regex.

```python
extract_code_blocks()
```

This normalized output is passed to reviewer.

---

## Timing System

Implemented:

```python
timed("planner", ...)
```

Measures:

* planner latency
* coder latency
* reviewer latency

---

# Key Learnings

## Claude Code

* Workspace-aware
* Scans directories
* Slower than API models
* Good at:

  * reasoning
  * reviewing
  * architecture
  * hidden bug detection

## GLM

* Fast
* Strong throughput
* Good code generation
* Less safe for concurrency/security

---

# Reviewer Findings Example

Reviewer successfully detected:

* race conditions
* IDOR
* transaction boundary problems
* missing optimistic locking
* outbox pattern absence
* precision issues
* authorization flaws

Meaning:
Reviewer role is functioning correctly.

---

# Sandbox Folder

Not used yet.

Purpose:
Isolated workspace for Claude Code.

Future usage:

```text
sandbox/
    planner/
    reviewer/
    coder/
```

Benefits:

* reduce workspace scanning
* reduce context pollution
* deterministic outputs
* safer autonomous file editing

Currently unnecessary because agents are not editing files yet.

---

# Short-Term Plan (Next Conversation)

## Priority 1 — Structured Reviewer Output

Current reviewer output:
plain text bullets

Target:
JSON output

Example:

```json
[
  {
    "severity": "HIGH",
    "type": "RACE_CONDITION",
    "description": "...",
    "fix": "..."
  }
]
```

Goal:
Machine-readable orchestration.

---

## Priority 2 — JSON Extraction Layer

Add:

```python
extract_json()
```

Parse reviewer responses safely.

---

## Priority 3 — Fixer Agent

Pipeline becomes:

```text
Planner
 -> Coder
 -> Reviewer(JSON)
 -> Fixer
```

Fixer:

* likely GLM
* receives reviewer findings
* patches code

---

## Priority 4 — Output Metadata

Store:

* timestamps
* latency
* model used
* task id

Potential structure:

```text
outputs/run_001/
```

---

# Medium-Term Plan

## Add Patch/Diff Generation

Instead of full rewrites:

```diff
- old code
+ fixed code
```

or git patch format.

---

## Add Parallel Reviewers

Example:

```text
Security Reviewer
Performance Reviewer
Concurrency Reviewer
```

Using asyncio.

---

## Add Local Models

Potential future local agents:

* Qwen
* Gemma
* Llama

Roles:

* log analysis
* quant analysis
* RAG memory
* monitoring

---

# Long-Term Vision

Build:

```text
AI Engineering Platform
```

Capabilities:

* architecture generation
* code generation
* security review
* patch generation
* trading infra review
* autonomous repair loops
* CI/CD integration

Potential future architecture:

```text
Planner
  ↓
Coder
  ↓
Reviewer
  ↓
Fixer
  ↓
Patch Generator
  ↓
Test Runner
  ↓
Deploy Validator
```

---

# Important Design Philosophy

Avoid:

* over-engineering
* Hermes
* heavy frameworks
* autonomous swarms too early

Prefer:

* deterministic pipelines
* simple orchestration
* explicit roles
* normalization layers
* structured outputs
* debuggable systems

Current approach is considered correct for:

* trading systems
* backend engineering
* PCI/security-sensitive workflows
* practical AI infra
