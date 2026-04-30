# Sleep to Monitor

After delegating a task to the worker, **proactively enter a sleep-and-check monitoring loop** without waiting for the owner to ask. Continue monitoring until the worker finishes, gets stuck, or needs intervention — then report back.

## When to use

Use this command after you have delegated a task and want to actively supervise the worker until completion. This replaces the need for the owner to repeatedly ask "keep tracking" or "what's the status".

## Inputs

- None required. Monitors the active worker from `config.json`.

## Active worker resolution

Before starting:

- Read `config.json`
- If it has a `workers` array, resolve the active worker from the current bot profile / `FIRST_PROMPT`
  - `.env1` maps to `Oysterun`
  - `.env2` maps to `OysterunDeploy`
- If no explicit match is available, use `workers[0]`
- If only a legacy `worker` object exists, use that

From the resolved worker, read:
- **session** — the tmux session name
- **send_method** — `two-line` or `enter`

## Procedure

### Step 0: Confirm the worker is actively working

```bash
tmux display-message -p -t <session> 'cmd=#{pane_current_command} dead=#{pane_dead} in_mode=#{pane_in_mode} alt=#{alternate_on} cursor=#{cursor_x},#{cursor_y} size=#{pane_width}x#{pane_height}'
tmux capture-pane -t <session> -p -S -20
```

If the worker is idle or the session is not running, report that immediately instead of looping.

### Step 1: Enter the sleep-and-check loop

Repeat this cycle until a terminal state is reached:

1. **Sleep** for an interval appropriate to the task:
   - Short tasks (quick fix, small edit): `sleep 15`
   - Medium tasks (feature implementation, investigation): `sleep 30`
   - Long tasks (large refactor, multi-step work): `sleep 45`

2. **Capture and assess:**
   ```bash
   tmux display-message -p -t <session> 'cmd=#{pane_current_command} dead=#{pane_dead} in_mode=#{pane_in_mode} alt=#{alternate_on} cursor=#{cursor_x},#{cursor_y} size=#{pane_width}x#{pane_height}'
   tmux capture-pane -t <session> -p -S -20
   ```

3. **Classify the state** into one of:
   - `working` — active progress, tool use, file edits in progress
   - `finished` — task complete, prompt visible, summary or result shown
   - `blocked` — error, approval request, ambiguity, or repeated failure
   - `idle` — prompt visible but no progress on the assigned task
   - `compacting` — running `/compact`, wait patiently (sleep 30+)
   - `context_low` — context warning visible, send `/compact`
   - `session_dead` — session crashed or shell prompt visible

4. **Act based on state:**

   - **working** → continue the loop (go back to step 1)
   - **finished** → exit the loop, proceed to Step 2 (evidence collection)
   - **blocked** → escalate capture to `-S -60`, diagnose the blocker, push the worker or ask TL when a TL route is active
   - **idle** → push the worker for a progress update using correct send_method
   - **compacting** → sleep 30, check again, do NOT send any commands
   - **context_low** → send `/compact`, then sleep 30 and resume monitoring
   - **session_dead** → attempt recovery per "Always Resume the Worker" rule, then re-send task context if needed

### Step 2: Collect evidence on completion

When the worker reaches `finished`:

1. Escalate capture to see the result:
   ```bash
   tmux capture-pane -t <session> -p -S -60
   ```

2. Ask the worker targeted evidence questions (using correct send_method):
   - "What files changed? Did you test? Any edge cases?"
   - Wait for the response (short sleep-and-check)

3. If a TL route is active, send the evidence packet to TL for verification/adjudication. PM does not decide pass/fail.

4. Report status to the owner with:
   - What was done
   - What was tested
   - Any caveats or follow-ups needed

### Step 3: Handle mid-task events

During the loop, watch for these and act immediately:

- **Worker asks a question** → read it, answer if you can (from prior context or research), or ask TL when a TL route is active
- **Worker goes off-track** → send a redirect message, do NOT send C-c
- **Worker makes repeated errors (3+)** → do web research on the error, bring findings back to the worker
- **Worker context low warning** → send `/compact` and wait patiently

## Important notes

- **Always read `config.json`** — never hardcode session names or send methods
- **Never send C-c** — use C-u to clear input, Escape to gently interrupt
- **Never send commands while the worker is mid-response** — wait for idle prompt
- **Use Adaptive Pane Capture Depth** — start with `-S -20`, escalate only when needed
- **Use Cheap-First Pane State** — read metadata before large captures
- **Do not use `/loop`, cron, or background monitors** — this is manual sleep-and-wait only
- **Report to the owner at natural milestones** — status only; do not ask the owner for task/verification decisions when TL is active
- Before every send, clear stale input: `tmux send-keys -t <session> C-u`
