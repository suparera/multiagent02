# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Setup & Commands

```bash
uv sync          # install dependencies
uv run main.py   # run the full pipeline
```

Requires a `.env` file with:
```
ZAI_API_KEY=<your z.ai key>
```

## Architecture

A deterministic multi-agent pipeline for AI-assisted code generation and review. Agents are composed in `main.py` — there is no framework, just sequential function calls.

**Pipeline:**
```
Task -> Planner (ResilientClaudeAgent) -> Coder (GLMAgent) -> Reviewer (ResilientClaudeAgent) -> Fixer (GLMAgent) -> Re-reviewer
```

**Agent types:**

- `GLMAgent` — calls GLM-5.1 via the Anthropic SDK compatibility layer at `https://api.z.ai/api/anthropic`. Used for fast code generation (coder, fixer).
- `ClaudeCodeAgent` — shells out to the `claude --print` CLI. Supports two providers: `claude_native` (uses local Claude Code auth) and `claude_glm` (overrides env vars to route the CLI to z.ai/GLM).
- `ResilientClaudeAgent` — wraps `ClaudeCodeAgent` with automatic fallback: tries `claude_native`, falls back to `claude_glm` if the result is empty or contains "timeout".

**Normalization layer (`utils.py`):**

- `extract_code_blocks(text)` — strips LLM prose and markdown, returns only code fence contents joined by blank lines. Always applied to coder/fixer output before passing downstream.
- `extract_json(text)` — finds and parses the first JSON array `[...]` in a string. Applied to reviewer output to get structured findings.
- `timed(label, fn)` — wraps any callable and prints its wall-clock latency.

**Prompt system:**

Prompts live in `prompts/` as `.txt` files (`architect`, `coder`, `reviewer`, `fixer`). Loaded with `load_prompt(name)`. Prompts are prepended to the task/context before being sent to each agent.

**Outputs:**

`outputs/` contains one file per pipeline stage: `plan.txt`, `raw_code.txt`, `code.txt`, `reviewer.json`, `fixed_code.txt`, `re_review.json`.

## Design Principles

- Deterministic pipelines over autonomous swarms — each stage has an explicit role and hand-off.
- Normalization between stages — never pass raw LLM output directly to the next agent.
- Structured reviewer output — reviewer must return a JSON array of findings with `severity`, `type`, `description`, `fix` fields.
- GLM for speed (coder/fixer), Claude for reasoning (planner/reviewer).
