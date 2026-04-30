---
description: Stop the full fleet by running the split manager and worker stop flows in order.
argument-hint: ""
---

# /stop_all_sessions — Stop the full manager and worker fleet

Use this command when the owner wants the full fleet shut down, but keep the operational steps split between the dedicated manager and worker commands.

This is agent-manager meta-work. Do not delegate it.

## Input

`$ARGUMENTS` — none expected. Ignore extra arguments unless the owner explicitly asks for a narrower target.

## Goal

Stop the full fleet by following the split procedures:

1. Run the manager stop flow from `/stop_all_manager`
2. Run the worker stop flow from `/stop_all_worker`

Stopping managers first prevents a live manager from continuing to talk to workers that are about to be killed.

## Procedure

### Step 1: Stop all managers

Follow `.claude/commands/stop_all_manager.md` exactly.

### Step 2: Stop all workers

Follow `.claude/commands/stop_all_worker.md` exactly.

### Step 3: Report

Report in this format:

```md
## Fleet Stop Complete

- TmuxAgentManager: stopped / already missing / failed
- TmuxAgentManager2: stopped / already missing / failed
- TmuxAgentManager3: stopped / already missing / failed
- TmuxAgentManager3Fast: stopped / already missing / failed
- <worker name 1>: stopped / already missing / failed
- <worker name 2>: stopped / already missing / failed
- <worker name 3>: stopped / already missing / failed
- Active tmux sessions after stop:
  <output of tmux ls, or "no server running">
```

## Important rules

- **Do not ask for confirmation** — stop immediately when the owner invokes this command
- **Stop managers before workers**
- **Follow the split command docs exactly** — this wrapper preserves the order, not a separate implementation
- **If one session fails to stop, continue with the rest** and report the failure clearly
