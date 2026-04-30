---
description: Stop all configured worker tmux sessions only.
argument-hint: ""
---

# /stop_all_worker — Stop all configured worker tmux sessions

Use this command when the owner wants only the worker fleet shut down.

This is agent-manager meta-work. Do not delegate it.

## Input

`$ARGUMENTS` — none expected. Ignore extra arguments unless the owner explicitly asks for a narrower worker target.

## Goal

Stop every configured worker from `config.json`.

## Procedure

### Step 1: Read the worker registry

```bash
python3 -c 'import json, pathlib; c=json.loads(pathlib.Path("config.json").read_text()); print(json.dumps({"workers": c.get("workers"), "worker": c.get("worker"), "team_roles": c.get("team", {}).get("roles", {})}, indent=2))'
```

Use `workers[]` if present. If `workers[]` is missing, use the legacy top-level `worker` object as a one-item list.

### Step 2: Verify live tmux state before acting

Run the live check first:

```bash
tmux ls 2>&1 || true
```

For each configured worker session:

```bash
tmux has-session -t <session> 2>/dev/null && echo "SESSION EXISTS" || echo "SESSION NOT FOUND"
```

### Step 3: Stop worker sessions

For each configured worker session that exists:

```bash
tmux kill-session -t <session> 2>/dev/null || true
tmux has-session -t <session> 2>/dev/null && echo "SESSION STILL EXISTS" || echo "SESSION STOPPED"
```

Process workers in the order they appear in `config.json`.

### Step 4: Report

Report in this format:

```md
## Worker Stop Complete

- <worker name 1>: stopped / already missing / failed
- <worker name 2>: stopped / already missing / failed
- <worker name 3>: stopped / already missing / failed
- Active tmux sessions after stop:
  <output of tmux ls, or "no server running">
```

## Important rules

- **Always read `config.json`** — never hardcode worker sessions
- **Do not ask for confirmation** — stop immediately when the owner invokes this command
- **Do not recreate anything** in this command — this command only stops worker sessions
- **If one worker fails to stop, continue with the rest** and report the failure clearly
