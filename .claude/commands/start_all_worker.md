---
description: Start all configured worker tmux sessions only. Resume Codex by default.
argument-hint: "[resume|fresh]"
---

# /start_all_worker — Start all configured worker tmux sessions

Use this command when the owner wants only the worker fleet brought up.

This is agent-manager meta-work. Do not delegate it.

## Input

`$ARGUMENTS` — Optional worker launch mode:

- empty or `resume` — try `codex ... resume` first and fall back once to a fresh launch if resume fails
- `fresh` — launch fresh instead of trying resume first

If `$ARGUMENTS` is provided, accept only `resume` or `fresh`. If empty, default to `resume`.

## Goal

Bring up every configured worker from `config.json` while preserving the original worker settings:

- `name`
- `session`
- `working_dir`
- `send_method`

## Procedure

### Step 1: Read the worker registry

```bash
python3 -c 'import json, pathlib; c=json.loads(pathlib.Path("config.json").read_text()); print(json.dumps({"workers": c.get("workers"), "worker": c.get("worker"), "team_roles": c.get("team", {}).get("roles", {})}, indent=2))'
```

Use `workers[]` if present. If `workers[]` is missing, use the legacy top-level `worker` object as a one-item list.

Process workers in the order they appear in `config.json`.

### Step 2: Verify live tmux state before acting

Run live checks first:

```bash
tmux ls 2>&1 || true
```

For each worker session:

```bash
tmux has-session -t <session> 2>/dev/null && echo "SESSION EXISTS" || echo "SESSION NOT FOUND"
tmux display-message -p -t <session> 'cmd=#{pane_current_command} dead=#{pane_dead} in_mode=#{pane_in_mode} alt=#{alternate_on} path=#{pane_current_path} cursor=#{cursor_x},#{cursor_y} size=#{pane_width}x#{pane_height}' 2>/dev/null || true
tmux capture-pane -t <session> -p -S -20 2>/dev/null || true
```

Use small captures first. Escalate only if the state is unclear.

Classify workers as:

- `session_missing`
- `shell_prompt`
- `worker_running`
- `resume_hint_visible`
- `ambiguous`

### Step 3: Start all workers

For each worker:

1. If the tmux session is missing, recreate that exact session:
   ```bash
   tmux new-session -d -s <session> -c <working_dir>
   tmux has-session -t <session> 2>/dev/null && echo "SESSION EXISTS" || echo "SESSION NOT FOUND"
   tmux capture-pane -t <session> -p -S -20
   ```
2. If Codex is already clearly running in that session, leave it alone and report `already running`.
3. If the pane is at a shell prompt, clear stale input:
   ```bash
   tmux send-keys -t <session> C-u
   ```
4. Launch Codex from the worker's configured `working_dir`.
   If worker mode is `resume`:
   ```bash
   tmux send-keys -t <session> "cd <working_dir> && codex --dangerously-bypass-approvals-and-sandbox resume"
   ```
   If worker mode is `fresh`:
   ```bash
   tmux send-keys -t <session> "cd <working_dir> && codex --dangerously-bypass-approvals-and-sandbox"
   ```
5. Submit using the worker's original `send_method`:
   If `send_method` is `two-line`:
   ```bash
   tmux send-keys -t <session> C-m
   ```
   If `send_method` is `enter`:
   ```bash
   tmux send-keys -t <session> Enter
   ```
6. Wait and inspect:
   ```bash
   sleep 5
   tmux display-message -p -t <session> 'cmd=#{pane_current_command} dead=#{pane_dead} in_mode=#{pane_in_mode} alt=#{alternate_on} path=#{pane_current_path} cursor=#{cursor_x},#{cursor_y} size=#{pane_width}x#{pane_height}'
   tmux capture-pane -t <session> -p -S -30
   ```
7. If worker mode is `resume` and the pane clearly shows resume failure or is still sitting at a shell prompt, fall back once to a fresh launch:
   ```bash
   tmux send-keys -t <session> C-u
   tmux send-keys -t <session> "cd <working_dir> && codex --dangerously-bypass-approvals-and-sandbox"
   ```
   Submit with the same `send_method`, then wait and inspect again:
   ```bash
   sleep 5
   tmux capture-pane -t <session> -p -S -30
   ```

### Step 4: Report

Report in this format:

```md
## Worker Start Complete

- Mode: resume / fresh
- <worker name 1>: ready / already running / failed / ambiguous
- <worker name 2>: ready / already running / failed / ambiguous
- <worker name 3>: ready / already running / failed / ambiguous
- Active tmux sessions after start:
  <output of tmux ls>
```

## Important rules

- **Always read `config.json`** — never hardcode worker `working_dir`, `session`, or `send_method`
- **Do not ask for confirmation** — start immediately when the owner invokes this command
- **Preserve every worker's original settings**
- **Never use `C-c`** on workers — if you need worker recovery, use the worker-safe flow
- **If one worker fails, continue with the rest** and report the failure clearly
