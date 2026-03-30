# /spawn_tmux_session — Spawn a new worker tmux session with context

Spawn a new tmux session running the worker in the project directory, using `resume` to carry over context from a previous session.

## Input

`$ARGUMENTS` — Optional. Format: `<session_name> [session_id|--last]`

- If no arguments: uses a generated name and resumes the latest session (`--last`)
- If one argument: uses it as the tmux session name, resumes latest
- If two arguments: first is session name, second is either a worker session UUID or `--last`

Examples:
- `/spawn_tmux_session` — spawn with auto-name, resume latest
- `/spawn_tmux_session feature-auth` — spawn as `feature-auth`, resume latest
- `/spawn_tmux_session bugfix-api 019d05d4-2f66-7bf0-97fe-67c516ccb27a` — spawn and resume specific session

## Active worker resolution

Before Step 1:

- Read `tmux_agents.json`
- If it has a `workers` array, match the worker named in the current bot profile / `FIRST_PROMPT`
- `.env1` maps to `Oysterun`
- `.env2` maps to `OysterunDeploy`
- If no explicit match is available, use `workers[0]`
- If only a legacy `worker` object exists, use that
- Use that resolved worker as the source of truth. Do not replace or rewrite the original worker's settings.

## Procedure

### Step 1: Read the worker config

```bash
cat tmux_agents.json
```

From the resolved active worker entry, read:
- **project_dir** — the directory where the worker should run
- **session** — the existing worker session name (to avoid naming conflicts)

### Step 2: Parse arguments and determine session name

- If `$ARGUMENTS` is empty: generate a name like `worker-spawn-<timestamp>` and set resume mode to `--last`
- If one argument: use it as session name, set resume mode to `--last`
- If two arguments: first is session name, second is resume target (UUID or `--last`)

### Step 3: Check for naming conflicts

```bash
tmux has-session -t <new_session_name> 2>/dev/null && echo "CONFLICT" || echo "OK"
```

If the session name already exists, report the conflict and stop. Do NOT kill existing sessions.

### Step 4: Create the tmux session

Create a new detached tmux session in the worker's project directory:

```bash
tmux new-session -d -s <new_session_name> -c <project_dir>
```

### Step 5: Launch the worker with resume

**If resuming with `--last` (default):**
```bash
tmux send-keys -t <new_session_name> "codex --dangerously-bypass-approvals-and-sandbox resume --last" Enter
```

**If resuming a specific session ID:**
```bash
tmux send-keys -t <new_session_name> "codex --dangerously-bypass-approvals-and-sandbox resume <session_id>" Enter
```

### Step 6: Wait and verify the worker started

```bash
sleep 5
tmux capture-pane -t <new_session_name> -p -S -30
```

Check for signs that the worker started successfully:
- Worker TUI visible
- Session resumed message
- Prompt ready

**If resume fails** (no matching session, error message), fall back to a fresh start:
```bash
tmux send-keys -t <new_session_name> "codex --dangerously-bypass-approvals-and-sandbox" Enter
```

Wait and verify again:
```bash
sleep 5
tmux capture-pane -t <new_session_name> -p -S -30
```

### Step 7: Report

```md
## Tmux Session Spawned

- Session name: <new_session_name>
- Project dir: <project_dir>
- Resume mode: --last / <session_id> / fresh (fallback)
- Worker status: running / failed
- Active sessions:
  <output of tmux ls>

### How to interact

Send commands (two-line method for worker):
  tmux send-keys -t <new_session_name> "<message>"
  tmux send-keys -t <new_session_name> C-m

Capture output:
  tmux capture-pane -t <new_session_name> -p -S -50

Kill when done:
  tmux kill-session -t <new_session_name>
```

## Important rules

- **Always read `tmux_agents.json`** for the worker's `project_dir` — never hardcode paths
- This command is additive only. Do not repoint `FIRST_PROMPT`, overwrite the original worker session, or rewrite worker settings.
- **Never reuse the existing worker session name** — this spawns a NEW session alongside the worker
- **Always try resume first** — fresh start is only a fallback if resume fails
- **Use `--dangerously-bypass-approvals-and-sandbox`** for automation compatibility
- **New sessions use `two-line` send method** (same as the worker)
- **Do NOT kill or interfere with the existing worker session** — this is additive
- **Report the tmux session name clearly** so the user can interact with it later
