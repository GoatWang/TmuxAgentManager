---
description: Ensure the active worker's configured tmux session exists and is running Codex with full access in the worker working_dir.
argument-hint: ""
---

# /setup_worker — Ensure the active worker session is ready

Use this command when the owner asks:

- set up my worker
- start the worker
- make sure the worker session is running
- reopen Codex for the active worker
- use my current env profile's worker and get it ready

This is agent-manager meta-work. Do not delegate it.

## Input

`$ARGUMENTS` — none expected. Ignore extra arguments unless the owner explicitly asks for a different recovery mode.

## Goal

Resolve the active worker from the **current bot profile** and ensure that exact worker's **configured tmux session** is ready to use.

That means:

- use the worker selected by the live env profile / `FIRST_PROMPT`
- use the worker's original `session`, `send_method`, and `working_dir` from `config.json`
- if the tmux session is missing, recreate that exact session
- ensure Codex is running in the worker's `working_dir`
- use full-access launch flags:
  - `codex --dangerously-bypass-approvals-and-sandbox resume <id>`
  - `codex --dangerously-bypass-approvals-and-sandbox resume`
  - `codex --dangerously-bypass-approvals-and-sandbox`

For the current Oysterun workers, the configured `working_dir` should resolve to the Oysterun repo. Do not hardcode it; always read it from `config.json`.

## Procedure

Execute these steps in order.

### Step 1: Read the live bot profile selectors

Inspect the current process environment first:

```bash
printf 'CTB_ENV=%s\nCTB_ENV_FILE=%s\nFIRST_PROMPT=%s\n' "$CTB_ENV" "$CTB_ENV_FILE" "$FIRST_PROMPT"
pwd
```

Resolve the current env file using this precedence:

1. `CTB_ENV` if set
2. `CTB_ENV_FILE` if set
3. If neither is set, inspect the current manager tmux session launch command or recent pane history for `--env=...`
4. If no explicit env file can be found, report that clearly and continue with a fallback only

If you have an env file path and it exists, read it:

```bash
sed -n '1,120p' <resolved_env_file>
```

Extract:

- env file path
- env file basename
- `FIRST_PROMPT`

### Step 2: Read the worker registry

```bash
python3 -c 'import json, pathlib; c=json.loads(pathlib.Path("config.json").read_text()); print(json.dumps({"workers": c.get("workers"), "worker": c.get("worker"), "team_roles": c.get("team", {}).get("roles", {})}, indent=2))'
```

Use `workers[]` if present.
If `workers[]` is missing, use the legacy top-level `worker` object.

### Step 3: Resolve the active worker

Resolve the worker in this order:

1. Exact worker-name match in `FIRST_PROMPT`
2. Exact session-name match in `FIRST_PROMPT`
3. Known env-profile fallback
   - `.env1` => `Oysterun`
   - `.env2` => `OysterunDeploy`
   - `.env3` => `OysterunFast`
4. `workers[0]` fallback
5. legacy `worker` fallback

Record the reason for the selection.

From the resolved worker entry, read:

- `name`
- `session`
- `send_method`
- `working_dir`

Do not switch to a different worker. Do not rewrite worker settings.

### Step 4: Verify live tmux state before acting

Run the live checks before claiming anything about session state:

```bash
tmux ls
tmux has-session -t <session> 2>/dev/null && echo "SESSION EXISTS" || echo "SESSION NOT FOUND"
tmux display-message -p -t <session> 'cmd=#{pane_current_command} dead=#{pane_dead} in_mode=#{pane_in_mode} alt=#{alternate_on} path=#{pane_current_path} cursor=#{cursor_x},#{cursor_y} size=#{pane_width}x#{pane_height}' 2>/dev/null || true
tmux capture-pane -t <session> -p -S -20 2>/dev/null || true
```

Classify the current state as one of:

- `session_missing`
- `shell_prompt`
- `worker_running`
- `resume_hint_visible`
- `ambiguous`

If the state is unclear, widen the capture only as needed:

```bash
tmux capture-pane -t <session> -p -S -80
```

### Step 5: Recreate the worker tmux session only if missing

If the configured tmux session does not exist, recreate that exact session in the worker's configured `working_dir`:

```bash
tmux new-session -d -s <session> -c <working_dir>
tmux has-session -t <session> 2>/dev/null && echo "SESSION EXISTS" || echo "SESSION NOT FOUND"
tmux capture-pane -t <session> -p -S -20
```

Do not create a differently named tmux session. This command must use the worker's original `session`.

### Step 6: Decide whether Codex already needs no action

If the pane already shows a live Codex UI or prompt and it is clearly running in the configured worker session, do **not** interrupt it.

Report that the worker is already ready if:

- the pane shows the Codex UI / prompt
- the session is alive
- there is no indication that it is sitting at a plain shell prompt

If the pane is at a shell prompt, continue to Step 7.

### Step 7: Start or resume Codex in the worker working_dir

Before sending any launch command:

1. confirm the worker is idle and the shell prompt is visible
2. clear stale input

```bash
tmux send-keys -t <session> C-u
```

Launch from the configured `working_dir`.

#### If a resume hint is visible in the pane

Use the exact resume id shown by Codex:

```bash
tmux send-keys -t <session> "cd <working_dir> && codex --dangerously-bypass-approvals-and-sandbox resume <session_id>"
tmux send-keys -t <session> C-m
```

#### Otherwise, first try resume latest

If `send_method` is `two-line`:

```bash
tmux send-keys -t <session> "cd <working_dir> && codex --dangerously-bypass-approvals-and-sandbox resume"
tmux send-keys -t <session> C-m
```

If `send_method` is `enter`:

```bash
tmux send-keys -t <session> "cd <working_dir> && codex --dangerously-bypass-approvals-and-sandbox resume" Enter
```

Wait, then inspect:

```bash
sleep 5
tmux display-message -p -t <session> 'cmd=#{pane_current_command} dead=#{pane_dead} in_mode=#{pane_in_mode} alt=#{alternate_on} path=#{pane_current_path} cursor=#{cursor_x},#{cursor_y} size=#{pane_width}x#{pane_height}'
tmux capture-pane -t <session> -p -S -30
```

#### If resume fails, fall back to a fresh full-access Codex launch

Only if the pane clearly shows resume failure or the shell prompt is still sitting there:

If `send_method` is `two-line`:

```bash
tmux send-keys -t <session> C-u
tmux send-keys -t <session> "cd <working_dir> && codex --dangerously-bypass-approvals-and-sandbox"
tmux send-keys -t <session> C-m
```

If `send_method` is `enter`:

```bash
tmux send-keys -t <session> C-u
tmux send-keys -t <session> "cd <working_dir> && codex --dangerously-bypass-approvals-and-sandbox" Enter
```

Wait and inspect again:

```bash
sleep 5
tmux display-message -p -t <session> 'cmd=#{pane_current_command} dead=#{pane_dead} in_mode=#{pane_in_mode} alt=#{alternate_on} path=#{pane_current_path} cursor=#{cursor_x},#{cursor_y} size=#{pane_width}x#{pane_height}'
tmux capture-pane -t <session> -p -S -30
```

### Step 8: Verify readiness before reporting success

Do not claim the worker is ready until the pane shows evidence that Codex actually started.

Acceptable evidence:

- Codex TUI is visible
- a Codex prompt is visible
- a resume banner / active session message is visible
- the session is no longer sitting at a plain shell prompt

If the state is ambiguous, widen the capture before concluding:

```bash
tmux capture-pane -t <session> -p -S -80
```

### Step 9: Report

Report in this format:

```md
## Worker Setup

- Worker: <worker name>
- Why selected: <exact reason>
- Env file: <full path or unknown>
- Env profile: <basename or unknown>
- Session: <session name>
- Send method: <two-line / enter>
- Working dir: <working_dir>
- Tmux status: existing / recreated
- Action taken: already running / resumed specific session / resumed latest / fresh launch fallback
- Codex status: ready / failed / ambiguous
- Evidence: <short pane summary>
```

## Important rules

- Prefer the live env selectors (`CTB_ENV`, `CTB_ENV_FILE`, `FIRST_PROMPT`) over guesses
- Always use the resolved active worker exactly as configured
- Always use the worker's original tmux `session`; do not spawn a different session name for setup
- Always launch from the worker's configured `working_dir`
- For Oysterun workers, that `working_dir` should resolve to the Oysterun repo; verify from config instead of hardcoding
- Prefer `resume` before a fresh launch
- Use full-access Codex flags: `--dangerously-bypass-approvals-and-sandbox`
- Never send `C-c`
- Use the configured `send_method`
- Do not claim success until the pane proves Codex is actually running
