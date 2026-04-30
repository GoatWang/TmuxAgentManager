---
description: Start all three manager Telegram bot tmux sessions only.
argument-hint: ""
---

# /start_all_manager — Start all manager tmux sessions

Use this command when the owner wants only the three Telegram bot manager sessions brought up.

This is agent-manager meta-work. Do not delegate it.

## Input

`$ARGUMENTS` — none expected. Ignore extra arguments unless the owner explicitly asks for a narrower manager target.

## Goal

Bring up:

- Manager `TmuxAgentManager` using `.env1`
- Manager `TmuxAgentManager2` using `.env2`
- Manager `TmuxAgentManager3` using `.env3`

Treat `TmuxAgentManager3Fast` as a legacy alias only. Do not create it.

## Procedure

### Step 1: Resolve the fixed manager mapping

Use this fixed mapping:

- `TmuxAgentManager` -> `.env1`
- `TmuxAgentManager2` -> `.env2`
- `TmuxAgentManager3` -> `.env3`

Use the repo root as the manager launch directory:

```bash
pwd
```

### Step 2: Verify live tmux state before acting

Run live checks first:

```bash
tmux ls 2>&1 || true
```

For each manager session:

```bash
tmux has-session -t <session_name> 2>/dev/null && echo "SESSION EXISTS" || echo "SESSION NOT FOUND"
tmux display-message -p -t <session_name> 'cmd=#{pane_current_command} dead=#{pane_dead} in_mode=#{pane_in_mode} alt=#{alternate_on} path=#{pane_current_path} cursor=#{cursor_x},#{cursor_y} size=#{pane_width}x#{pane_height}' 2>/dev/null || true
tmux capture-pane -t <session_name> -p -S -20 2>/dev/null || true
```

Use small captures first. Escalate only if the state is unclear.

Classify each manager as:

- `session_missing`
- `shell_prompt`
- `manager_running`
- `startup_failed`
- `ambiguous`

### Step 3: Start all managers

For each fixed manager mapping:

1. If the tmux session is missing, create it with a shell that exports the env file line-by-line before launching `ctb`:
   ```bash
   tmux new-session -d -s <session_name> -c "$(pwd)" 'while IFS= read -r line; do [[ -z "$line" || "$line" == \#* ]] && continue; export "$line"; done < <env_file>; ./tool_scripts/ctb_local.sh --chrome; exec $SHELL'
   ```
2. If the session already exists and the pane shows a live manager UI, leave it alone and report `already running`.
3. If the pane is at a shell prompt, clear stale input:
   ```bash
   tmux send-keys -t <session_name> C-u
   ```
4. Start the manager in-place using the same env-file loader:
   ```bash
   tmux send-keys -t <session_name> 'while IFS= read -r line; do [[ -z "$line" || "$line" == \#* ]] && continue; export "$line"; done < <env_file>; ./tool_scripts/ctb_local.sh --chrome'
   tmux send-keys -t <session_name> Enter
   ```
5. Wait and inspect:
   ```bash
   sleep 5
   tmux display-message -p -t <session_name> 'cmd=#{pane_current_command} dead=#{pane_dead} in_mode=#{pane_in_mode} alt=#{alternate_on} path=#{pane_current_path} cursor=#{cursor_x},#{cursor_y} size=#{pane_width}x#{pane_height}'
   tmux capture-pane -t <session_name> -p -S -30
   ```
6. If the pane shows startup errors such as `No .env found`, unsupported-flag errors, or `ENOSPC`, report the session as failed instead of claiming success.

### Step 4: Report

Report in this format:

```md
## Manager Start Complete

- TmuxAgentManager (`.env1`): ready / already running / failed / ambiguous
- TmuxAgentManager2 (`.env2`): ready / already running / failed / ambiguous
- TmuxAgentManager3 (`.env3`): ready / already running / failed / ambiguous
- Active tmux sessions after start:
  <output of tmux ls>
```

## Important rules

- **Do not ask for confirmation** — start immediately when the owner invokes this command
- **Preserve the fixed manager mapping** — `.env1` -> `TmuxAgentManager`, `.env2` -> `TmuxAgentManager2`, `.env3` -> `TmuxAgentManager3`
- **Do not create `TmuxAgentManager3Fast`** — that is a legacy alias only
- **Do not use unsupported `ctb` flags** such as `--env`
- **If one manager fails, continue with the rest** and report the failure clearly
