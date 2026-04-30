---
description: Restart the full fleet by running the split manager and worker stop/start flows in order.
argument-hint: "[resume|fresh]"
---

# /restart_all_sessions — Restart the full manager and worker fleet

Use this command when the owner wants the full fleet restarted in one pass, but keep the operational steps split between the dedicated manager and worker commands.

This is agent-manager meta-work. Do not delegate it.

## Input

`$ARGUMENTS` — Optional worker restart mode passed through to the worker start flow:

- empty or `resume` — restart workers and try resume first
- `fresh` — restart workers fresh

Managers always restart with the current local `./tool_scripts/ctb_local.sh --chrome` behavior.

If `$ARGUMENTS` is provided, accept only `resume` or `fresh`. If empty, default to `resume`.

## Goal

Restart the full fleet by following the split procedures:

1. Run the manager stop flow from `/stop_all_manager`
2. Run the worker stop flow from `/stop_all_worker`
3. Run the worker start flow from `/start_all_worker`
4. Run the manager start flow from `/start_all_manager`

## Procedure

### Step 1: Validate the worker mode

Accept only:

- empty
- `resume`
- `fresh`

If empty, default to `resume`.

### Step 2: Stop all managers

Follow `.claude/commands/stop_all_manager.md` exactly.

### Step 3: Stop all workers

Follow `.claude/commands/stop_all_worker.md` exactly.

### Step 4: Start all workers

Follow `.claude/commands/start_all_worker.md` exactly.

Pass the validated worker mode through unchanged:

```text
/start_all_worker
/start_all_worker resume
/start_all_worker fresh
```

### Step 5: Start all managers

Follow `.claude/commands/start_all_manager.md` exactly.

### Step 6: Report

Report in this format:

```md
## Fleet Restart Complete

- Worker mode: resume / fresh
- TmuxAgentManager (`.env1`): ready / failed / ambiguous
- TmuxAgentManager2 (`.env2`): ready / failed / ambiguous
- TmuxAgentManager3 (`.env3`): ready / failed / ambiguous
- <worker name 1>: ready / failed / ambiguous
- <worker name 2>: ready / failed / ambiguous
- <worker name 3>: ready / failed / ambiguous
- Active tmux sessions after restart:
  <output of tmux ls>
```

## Important rules

- **Do not ask for confirmation** — restart immediately when the owner invokes this command
- **Stop managers first, then workers; start workers first, then managers**
- **Follow the split command docs exactly** — this wrapper preserves the order, not a separate implementation
- **If one session fails, continue with the rest** and report the failure clearly
