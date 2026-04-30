---
description: Start the full fleet by running the split worker and manager start flows in order.
argument-hint: "[resume|fresh]"
---

# /start_all_sessions — Start the full manager and worker fleet

Use this command when the owner wants the full fleet brought up, but keep the operational steps split between the dedicated worker and manager commands.

This is agent-manager meta-work. Do not delegate it.

## Input

`$ARGUMENTS` — Optional worker launch mode passed through to the worker start flow:

- empty or `resume` — for workers, try `codex ... resume` first and fall back once to a fresh launch if resume fails
- `fresh` — for workers, launch fresh instead of trying resume first

Managers always launch with the current local `./tool_scripts/ctb_local.sh --chrome` behavior.

If `$ARGUMENTS` is provided, accept only `resume` or `fresh`. If empty, default to `resume`.

## Goal

Bring up the full fleet by following the split procedures:

1. Run the worker start flow from `/start_all_worker`
2. Run the manager start flow from `/start_all_manager`

## Procedure

### Step 1: Validate the worker mode

Accept only:

- empty
- `resume`
- `fresh`

If empty, default to `resume`.

### Step 2: Start all workers

Follow `.claude/commands/start_all_worker.md` exactly.

Pass the validated worker mode through unchanged:

```text
/start_all_worker
/start_all_worker resume
/start_all_worker fresh
```

### Step 3: Start all managers

Follow `.claude/commands/start_all_manager.md` exactly.

### Step 4: Report

Report in this format:

```md
## Fleet Start Complete

- Worker mode: resume / fresh
- TmuxAgentManager (`.env1`): ready / already running / failed / ambiguous
- TmuxAgentManager2 (`.env2`): ready / already running / failed / ambiguous
- TmuxAgentManager3 (`.env3`): ready / already running / failed / ambiguous
- <worker name 1>: ready / already running / failed / ambiguous
- <worker name 2>: ready / already running / failed / ambiguous
- <worker name 3>: ready / already running / failed / ambiguous
- Active tmux sessions after start:
  <output of tmux ls>
```

## Important rules

- **Do not ask for confirmation** — start immediately when the owner invokes this command
- **Run the worker flow first, then the manager flow**
- **Follow the split command docs exactly** — this wrapper preserves the order, not a separate implementation
- **If one session fails, continue with the rest** and report the failure clearly
