---
description: Stop all three manager Telegram bot tmux sessions only.
argument-hint: ""
---

# /stop_all_manager — Stop all manager tmux sessions

Use this command when the owner wants only the Telegram bot manager sessions shut down.

This is agent-manager meta-work. Do not delegate it.

## Input

`$ARGUMENTS` — none expected. Ignore extra arguments unless the owner explicitly asks for a narrower manager target.

## Goal

Stop:

- `TmuxAgentManager`
- `TmuxAgentManager2`
- `TmuxAgentManager3`

Also check `TmuxAgentManager3Fast` as a legacy session name. Kill it if it exists, but do not recreate it.

## Procedure

### Step 1: Verify live tmux state before acting

Run the live check first:

```bash
tmux ls 2>&1 || true
```

For each target manager session:

```bash
tmux has-session -t <session_name> 2>/dev/null && echo "SESSION EXISTS" || echo "SESSION NOT FOUND"
```

### Step 2: Stop manager sessions

For each manager session that exists:

```bash
tmux kill-session -t <session_name> 2>/dev/null || true
tmux has-session -t <session_name> 2>/dev/null && echo "SESSION STILL EXISTS" || echo "SESSION STOPPED"
```

Process managers in this order:

1. `TmuxAgentManager`
2. `TmuxAgentManager2`
3. `TmuxAgentManager3`
4. `TmuxAgentManager3Fast` if it exists

### Step 3: Report

Report in this format:

```md
## Manager Stop Complete

- TmuxAgentManager: stopped / already missing / failed
- TmuxAgentManager2: stopped / already missing / failed
- TmuxAgentManager3: stopped / already missing / failed
- TmuxAgentManager3Fast: stopped / already missing / failed
- Active tmux sessions after stop:
  <output of tmux ls, or "no server running">
```

## Important rules

- **Do not ask for confirmation** — stop immediately when the owner invokes this command
- **Do not recreate anything** in this command — this command only stops manager sessions
- **If one manager fails to stop, continue with the rest** and report the failure clearly
