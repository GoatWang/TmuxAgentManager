# /delegate — Force Delegation Before Code Work

Use this command when Jeremy gives a non-trivial project task. This command exists to prevent you from slipping into direct implementation.

## Input

`$ARGUMENTS` — the task to delegate, including expected outcome and any known constraints.

## Protocol

Execute these steps in order. Do not skip any.

### Step 1: Read the worker config

```bash
cat tmux_agents.json
```

From the config, read the `worker` object to get:
- **name** — the worker agent name
- **session** — the tmux session name
- **send_method** — `two-line` (worker) or `enter` (regular)
- **project_dir** — the project directory

### Step 2: Confirm repo / worktree location

Before delegating, confirm the execution location:

```bash
cd <project_dir> && pwd && git rev-parse --show-toplevel && git status --short
```

State clearly:

- main repo or worktree
- exact path
- whether the task must stay in main or must use a fresh worktree

### Step 3: Clear stale input and send the task

First, clear any leftover text in the prompt:
```bash
tmux send-keys -t <session> C-u
```

Then use the correct **send_method** from the worker config.

**If send_method is `two-line`:**
```bash
tmux send-keys -t <session> "<task>. Constraints: <constraints>. Repo/worktree: <path>. Verify before reporting. Tell me files changed, tests run, and any risks."
tmux send-keys -t <session> C-m
```

**If send_method is `enter`:**
```bash
tmux send-keys -t <session> "<task>. Constraints: <constraints>. Repo/worktree: <path>. Verify before reporting. Tell me files changed, tests run, and any risks." Enter
```

### Step 4: Confirm receipt

Capture the pane:

```bash
sleep 3
tmux capture-pane -t <session> -p -S -100
```

Do not proceed as if the agent is working until you see evidence the message was received and processing started.

### Step 5: Supervise, don't replace

Your next actions should be limited to:

- monitoring progress
- asking follow-up questions
- reviewing diffs
- verifying results in Chrome, tests, curl, or logs

Do not jump into direct implementation unless one of the explicit exceptions applies.

## Allowed exceptions for direct work

Only bypass delegation if one of these is true:

- trivial fix under 5 lines
- emergency hotfix and all relevant agents are busy/unavailable
- agent-manager meta-work only
- delegated agent failed 2+ times and takeover is justified

If you bypass delegation, say which exception applies.

## Output

Report back in this shape:

```md
## Delegation Started

- Worker: <worker name>
- Session: <session>
- Repo/worktree: <path>
- Mode: main repo / fresh worktree / existing worktree
- Task sent: <summary>
- Receipt confirmed: yes/no
- Next supervision step: <what you will check next>
```

## Rules

- **Always read `tmux_agents.json`** to get the worker config — never hardcode session names
- Never start project-code implementation before Step 4 is complete
- Never assume the agent received the task without checking the pane
- Never omit the repo/worktree path from a risky task
- Never report progress as implementation progress if only you have been reading files locally
