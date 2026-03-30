---
description: Identify the active worker for the current bot profile, including env file, FIRST_PROMPT match, tmux session, and project directory.
argument-hint: ""
disable-model-invocation: true
---

# /who_is_my_worker — Identify the active worker for this bot profile

Use this command when Jeremy asks:

- who is my worker
- which worker this Telegram bot is currently managing
- which env profile is active
- which tmux session / project dir / send method belongs to the current worker
- whether the selected worker session is actually running

This is agent-manager meta-work. Do not delegate it.

## Input

`$ARGUMENTS` — none expected. Ignore extra arguments unless Jeremy explicitly asks for a deeper explanation.

## Goal

Tell Jeremy exactly which worker is active **right now**, **why** that worker was selected, and whether the worker's tmux session is healthy.

Use the live bot profile first. Do not guess from memory.

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
3. If neither is set, inspect the current manager tmux session launch command / recent pane history for `--env=...`
4. If no explicit env file can be found, report that clearly and continue with a low-confidence fallback only

If you have an env file path and it exists, read it:

```bash
sed -n '1,120p' <resolved_env_file>
```

Extract:

- env file path
- env file basename (for example `.env1`, `.env2`, `.env3`)
- `FIRST_PROMPT`

### Step 2: Read the worker registry

```bash
cat tmux_agents.json
```

Use `workers[]` if present.
If `workers[]` is missing, use the legacy top-level `worker` object.

### Step 3: Resolve the active worker

Resolve the worker in this order:

1. **Exact worker-name match in `FIRST_PROMPT`**
   - If the prompt mentions a worker name from `tmux_agents.json`, use that worker.
2. **Exact session-name match in `FIRST_PROMPT`**
   - If the prompt mentions a configured session, use that worker.
3. **Known env-profile fallback**
   - `.env1` => `Oysterun`
   - `.env2` => `OysterunDeploy`
   - `.env3` => `OysterunFast`
4. **Default fallback**
   - `workers[0]`
5. **Legacy fallback**
   - top-level `worker`

Do not switch away from the resolved worker. This command is identification only.

Also record the **reason** for the resolution:

- matched worker name in `FIRST_PROMPT`
- matched session name in `FIRST_PROMPT`
- env basename fallback
- `workers[0]` fallback
- legacy `worker` fallback

### Step 4: Verify the tmux session exists

Run the live tmux checks before claiming anything about session state:

```bash
tmux ls
tmux has-session -t <session> 2>/dev/null && echo "SESSION EXISTS" || echo "SESSION NOT FOUND"
```

If the session exists, capture a small slice of the pane:

```bash
tmux capture-pane -t <session> -p -S -30
```

From that, determine:

- whether the worker session is running
- whether the pane looks idle, active, blocked, or unclear
- any short clue about what the worker is currently doing

### Step 5: Set confidence

Use:

- `high` — exact match from `FIRST_PROMPT`
- `medium` — env basename fallback like `.env2`
- `low` — `workers[0]` or legacy fallback because no live selector was visible

### Step 6: Report

Report in this format:

```md
## Active Worker

- Worker: <worker name>
- Why selected: <exact reason>
- Confidence: high / medium / low
- Env file: <full path or unknown>
- Env profile: <basename or unknown>
- FIRST_PROMPT: <short relevant excerpt or unavailable>
- Session: <session name>
- Send method: <two-line / enter>
- Project dir: <project_dir>
- Tmux status: running / missing
- Current pane clue: <one short line or unavailable>
```

## Rules

- Prefer the **live env variables** (`CTB_ENV`, `CTB_ENV_FILE`, `FIRST_PROMPT`) over static guesses
- Do not claim a session exists or is missing without `tmux has-session` or `tmux ls`
- Do not rewrite worker settings or switch workers during this command
- If the env file cannot be determined, say that explicitly instead of pretending certainty
- This command identifies the current worker; it does not send work, restart sessions, or edit config
