---
description: Restart every configured worker tmux session using each worker's original session, working_dir, and send_method. Resume Codex by default.
argument-hint: "[resume|fresh]"
---

# /restart_all_worker — Restart all configured worker tmux sessions

Use this command when the owner wants every worker in `config.json` restarted.

This is agent-manager meta-work. Do not delegate it.

## Input

`$ARGUMENTS` — Optional restart mode:

- empty or `resume` — restart all workers and resume each worker where possible
- `fresh` — restart all workers with a fresh Codex launch instead of resume

## Goal

Restart every configured worker while preserving each worker's original:

- `name`
- `session`
- `working_dir`
- `send_method`

Do not switch workers, rename sessions, or rewrite config.

## Procedure

### Step 1: Restart immediately

Restart immediately. Do not ask for confirmation.

If `$ARGUMENTS` is provided, accept only `resume` or `fresh`. If empty, default to `resume`.

### Step 2: Read the worker registry

```bash
python3 -c 'import json, pathlib; c=json.loads(pathlib.Path("config.json").read_text()); print(json.dumps({"workers": c.get("workers"), "worker": c.get("worker"), "team_roles": c.get("team", {}).get("roles", {})}, indent=2))'
```

Use `workers[]` if present. If `workers[]` is missing, use the legacy top-level `worker` object as a one-item list.

From each worker, record:

- `name`
- `session`
- `working_dir`
- `send_method`

Process workers in the order they appear in `config.json`.

### Step 3: Verify live tmux state before acting

Run the live checks before making any claim about session state:

```bash
tmux ls
tmux has-session -t <session> 2>/dev/null && echo "SESSION EXISTS" || echo "SESSION NOT FOUND"
tmux display-message -p -t <session> 'cmd=#{pane_current_command} dead=#{pane_dead} in_mode=#{pane_in_mode} alt=#{alternate_on} path=#{pane_current_path} cursor=#{cursor_x},#{cursor_y} size=#{pane_width}x#{pane_height}' 2>/dev/null || true
tmux capture-pane -t <session> -p -S -20 2>/dev/null || true
```

Classify each worker as one of:

- `session_missing`
- `shell_prompt`
- `worker_running`
- `resume_hint_visible`
- `ambiguous`

If the state is unclear, widen the capture only as needed:

```bash
tmux capture-pane -t <session> -p -S -80
```

### Step 4: Restart each worker using the original session

For each worker:

1. If the tmux session is missing, recreate that exact session:
   ```bash
   tmux new-session -d -s <session> -c <working_dir>
   tmux has-session -t <session> 2>/dev/null && echo "SESSION EXISTS" || echo "SESSION NOT FOUND"
   tmux capture-pane -t <session> -p -S -20
   ```

2. If Codex is actively responding, wait for it to finish before interrupting:
   ```bash
   tmux capture-pane -t <session> -p -S -20
   sleep 10
   tmux capture-pane -t <session> -p -S -20
   ```

   Repeat until the worker is idle and the prompt is visible.

3. If the pane shows a live Codex UI instead of a plain shell prompt, stop it gently:
   ```bash
   tmux send-keys -t <session> Escape
   sleep 10
   tmux capture-pane -t <session> -p -S -20
   ```

   If the first `Escape` did not stop Codex, send one second `Escape`, wait again, and inspect:

   ```bash
   tmux send-keys -t <session> Escape
   sleep 10
   tmux capture-pane -t <session> -p -S -20
   ```

   Do **not** use `C-c`.

4. Once the shell prompt is visible, clear stale input:
   ```bash
   tmux send-keys -t <session> C-u
   ```

5. Launch Codex again from the worker's configured `working_dir`.

   If restart mode is `resume` and a resume hint is visible, use the exact resume id shown by Codex:

   ```bash
   tmux send-keys -t <session> "cd <working_dir> && codex --dangerously-bypass-approvals-and-sandbox resume <session_id>"
   ```

   Otherwise, if restart mode is `resume`:

   ```bash
   tmux send-keys -t <session> "cd <working_dir> && codex --dangerously-bypass-approvals-and-sandbox resume"
   ```

   If restart mode is `fresh`:

   ```bash
   tmux send-keys -t <session> "cd <working_dir> && codex --dangerously-bypass-approvals-and-sandbox"
   ```

6. Submit using the worker's configured `send_method`:

   If `send_method` is `two-line`:
   ```bash
   tmux send-keys -t <session> C-m
   ```

   If `send_method` is `enter`:
   ```bash
   tmux send-keys -t <session> Enter
   ```

7. Wait and verify that Codex actually started:
   ```bash
   sleep 5
   tmux display-message -p -t <session> 'cmd=#{pane_current_command} dead=#{pane_dead} in_mode=#{pane_in_mode} alt=#{alternate_on} path=#{pane_current_path} cursor=#{cursor_x},#{cursor_y} size=#{pane_width}x#{pane_height}'
   tmux capture-pane -t <session> -p -S -30
   ```

8. If `resume` fails and the pane is still at a shell prompt, fall back once to a fresh launch:
   ```bash
   tmux send-keys -t <session> C-u
   tmux send-keys -t <session> "cd <working_dir> && codex --dangerously-bypass-approvals-and-sandbox"
   ```

   Then submit using the same `send_method`, wait, and capture again:

   ```bash
   sleep 5
   tmux capture-pane -t <session> -p -S -30
   ```

### Step 5: Report

```md
## Worker Restart Complete

- Mode: resume / fresh
- Oysterun: ready / failed / ambiguous
- OysterunDeploy: ready / failed / ambiguous
- OysterunFast: ready / failed / ambiguous
- Active tmux sessions after restart:
  <output of tmux ls>
```

If the configured worker names differ, report the actual names from `config.json`.

## Important rules

- **Always read `config.json`** — never hardcode worker sessions, paths, or send methods
- **Do not ask for confirmation** — restart immediately when the owner invokes this command
- **Preserve every worker's original settings** — `session`, `working_dir`, `send_method`, and worker identity must stay intact
- **Wait for a worker to go idle before interrupting it** — do not send new input while the worker is still generating
- **Never use `C-c`** to stop a worker — use `Escape`, inspect, and only then continue
- **Use the worker's configured `send_method`** when relaunching Codex
- **Prefer resume first** — use fresh launch only when the user explicitly asked for `fresh`, or as a one-time fallback when resume clearly failed
- **If one worker fails, continue with the rest** and report the failure clearly
- **Do not touch Telegram bot sessions here** — this command is only for the worker sessions in `config.json`
