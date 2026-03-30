# chk_agent_status

Purpose: check the **progress of the last task** in the worker agent session.

This is **not** a generic alive/dead status check.
This skill is for answering:

- What is the agent currently doing for the last assigned task?
- Is it progressing, blocked, idle, or finished?
- What did it actually complete so far?
- What is the next concrete step?

## When to use

Use this skill when Jeremy asks for:

- agent progress
- what the agent is doing now
- what has been finished so far
- whether the last delegated task is blocked
- whether the agent needs a push

## Inputs

- optional reminder of the last delegated task

The target session is always the **active worker** resolved from `tmux_agents.json`. Do not ask for a session name.
Do not switch to another worker or another session during this command.

## Active worker resolution

Before using the steps below:

- Read `tmux_agents.json`
- If it has a `workers` array, resolve the active worker from the current bot profile / `FIRST_PROMPT`
- `.env1` maps to `Oysterun`
- `.env2` maps to `OysterunDeploy`
- If no explicit match is available, use `workers[0]`
- If only a legacy `worker` object exists, use that
- Respect the resolved worker's original `session`, `send_method`, and `project_dir`. If that worker is unhealthy, report or recover it instead of switching workers.

## Core rule

You are checking **task progress**, not merely process status.

Bad answer:

- "The agent session exists."
- "The pane is running node."

Good answer:

- "The agent is currently verifying Playwright results for the mobile composer task."
- "The agent finished the baseline commit, started the server, and is now blocked on stale session state."

## Procedure

### Step 0: Read the worker config

```bash
cat tmux_agents.json
```

From the resolved active worker entry, read:
- **session** — the tmux session name
- **send_method** — `two-line` (worker) or `enter` (regular)

### Step 1: Capture recent task history

```bash
tmux capture-pane -t <session> -p -S -120
```

If needed, extend to:

```bash
tmux capture-pane -t <session> -p -S -300
```

### Step 2: Identify the last delegated task

From the pane history, determine:

- what task was assigned
- whether it was actually executed
- whether the task text was merely queued or was processed

If the pane only shows queued text with no execution/progress, report that clearly.

### Step 3: Classify the current progress state

Classify into one of these:

- `working`
- `blocked`
- `idle`
- `finished`
- `misdirected`

Definitions:

- `working`: clear evidence of active progress on the assigned task
- `blocked`: agent is stuck on an error, approval, environment issue, or ambiguity
- `idle`: no meaningful progress on the assigned task and no active execution
- `finished`: task outcome has been produced and the agent returned to shell/prompt
- `misdirected`: the agent is active, but on the wrong task, wrong repo, or wrong worktree

### Step 4: Extract concrete evidence

Summarize only the high-signal facts:

- files changed
- commands run
- tests run
- server started/stopped
- screenshots or artifacts created
- explicit errors
- explicit next step in the pane

### Step 5: Decide if the agent needs intervention

If the agent is:

- `blocked`: push for blocker explanation or redirect
- `idle`: ask for immediate progress update
- `misdirected`: correct repo/worktree/task immediately
- `finished`: report results and next recommended task
- `working`: report current step and keep monitoring

### Step 6: If needed, push the agent

Clear any stale input first, then use the correct **send_method** from the worker config.

```bash
tmux send-keys -t <session> C-u
```

**If send_method is `two-line`:**

Progress push:
```bash
tmux send-keys -t <session> "Progress update on the last task: what is done, what is blocked, and what is the next concrete step?"
tmux send-keys -t <session> C-m
```

Redirect push:
```bash
tmux send-keys -t <session> "You are on the wrong repo/worktree/task. Stop and switch to <correct target>. Then continue the assigned task only."
tmux send-keys -t <session> C-m
```

Blocker push:
```bash
tmux send-keys -t <session> "What exactly is blocking the last assigned task? Show the failed command/error and your next attempted fix."
tmux send-keys -t <session> C-m
```

**If send_method is `enter`:**

Progress push:
```bash
tmux send-keys -t <session> "Progress update on the last task: what is done, what is blocked, and what is the next concrete step?" Enter
```

Redirect push:
```bash
tmux send-keys -t <session> "You are on the wrong repo/worktree/task. Stop and switch to <correct target>. Then continue the assigned task only." Enter
```

Blocker push:
```bash
tmux send-keys -t <session> "What exactly is blocking the last assigned task? Show the failed command/error and your next attempted fix." Enter
```

## Output format

```md
## Agent Progress: <worker name>

- Last task: <task summary>
- State: working | blocked | idle | finished | misdirected
- Current step: <what the agent is doing now>
- Completed so far: <high-signal completed work>
- Evidence: <commands/tests/artifacts/errors>
- Next step: <most likely next action>
- Intervention needed: yes/no
```

## Important reminders

- **Always read `tmux_agents.json`** to get the worker session and send method — never hardcode
- Use the resolved active worker exactly as configured; do not substitute another worker to get a status
- Do not confuse "running process" with "task progress"
- Do not report "working" unless the pane shows actual task progress
- Do not report "finished" unless the pane shows an outcome, summary, or return to shell after task completion
- If the agent is on the wrong repo/worktree, call that out immediately
- If the pane shows stale conversation context unrelated to the assigned task, classify as `misdirected` or `idle`
