---
description: Restart all three manager Telegram bot tmux sessions only.
argument-hint: ""
---

# /restart_all_manager — Restart all manager tmux sessions

Use this command when the owner wants only the Telegram bot manager fleet restarted.

This is agent-manager meta-work. Do not delegate it.

## Input

`$ARGUMENTS` — none expected. Ignore extra arguments unless the owner explicitly asks for a narrower manager target.

## Goal

Restart:

- Manager `TmuxAgentManager` using `.env1`
- Manager `TmuxAgentManager2` using `.env2`
- Manager `TmuxAgentManager3` using `.env3`

Use this restart order:

1. Stop managers
2. Start managers

Treat `TmuxAgentManager3Fast` as a legacy alias only. Kill it if it exists, but do not recreate it.

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

```bash
tmux ls 2>&1 || true
```

For each target manager:

```bash
tmux has-session -t <session_name> 2>/dev/null && echo "SESSION EXISTS" || echo "SESSION NOT FOUND"
tmux display-message -p -t <session_name> 'cmd=#{pane_current_command} dead=#{pane_dead} in_mode=#{pane_in_mode} alt=#{alternate_on} path=#{pane_current_path} cursor=#{cursor_x},#{cursor_y} size=#{pane_width}x#{pane_height}' 2>/dev/null || true
tmux capture-pane -t <session_name> -p -S -20 2>/dev/null || true
```

### Step 3: Stop managers

Kill each fixed manager session if it exists:

```bash
tmux kill-session -t <session_name> 2>/dev/null || true
tmux has-session -t <session_name> 2>/dev/null && echo "SESSION STILL EXISTS" || echo "SESSION STOPPED"
```

Process:

1. `TmuxAgentManager`
2. `TmuxAgentManager2`
3. `TmuxAgentManager3`
4. `TmuxAgentManager3Fast` if it exists

### Step 4: Start managers

For each fixed manager mapping:

1. Create the tmux session in the repo root with a shell that exports the env file line-by-line:
   ```bash
   tmux new-session -d -s <session_name> -c "$(pwd)" 'while IFS= read -r line; do [[ -z "$line" || "$line" == \#* ]] && continue; export "$line"; done < <env_file>; ./tool_scripts/ctb_local.sh --chrome; exec $SHELL'
   ```
2. Wait and inspect:
   ```bash
   sleep 5
   tmux display-message -p -t <session_name> 'cmd=#{pane_current_command} dead=#{pane_dead} in_mode=#{pane_in_mode} alt=#{alternate_on} path=#{pane_current_path} cursor=#{cursor_x},#{cursor_y} size=#{pane_width}x#{pane_height}'
   tmux capture-pane -t <session_name> -p -S -30
   ```
3. If the pane shows startup errors such as `No .env found`, unsupported-flag errors, or `ENOSPC`, report failure clearly.

### Step 5: Report

Report in this format:

```md
## Manager Restart Complete

- TmuxAgentManager (`.env1`): ready / failed / ambiguous
- TmuxAgentManager2 (`.env2`): ready / failed / ambiguous
- TmuxAgentManager3 (`.env3`): ready / failed / ambiguous
- Active tmux sessions after restart:
  <output of tmux ls>
```

## Important rules

- **Do not ask for confirmation** — restart immediately when the owner invokes this command
- **Preserve the fixed manager mapping** — `.env1` -> `TmuxAgentManager`, `.env2` -> `TmuxAgentManager2`, `.env3` -> `TmuxAgentManager3`
- **Do not create `TmuxAgentManager3Fast`** — that is a legacy alias only
- **Do not use unsupported `ctb` flags** such as `--env`
- **If one manager fails, continue with the rest** and report the failure clearly
