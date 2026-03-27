# /send_tmux — Send a command to the worker agent

Send a message or task to the current active worker agent session. Reads `tmux_agents.json` to determine the worker session and send method.

## Input

`$ARGUMENTS` — The message to send to the worker.

Examples:
- `/send_tmux Fix the CSS overflow bug on mobile`
- `/send_tmux What cron jobs are running?`

## Active worker resolution

Before Step 1:

- Read `tmux_agents.json`
- If it has a `workers` array, match the worker named in the current bot profile / `FIRST_PROMPT`
- `.env1` maps to `Oysterun`
- `.env2` maps to `OysterunDeploy`
- If no explicit match is available, use `workers[0]`
- If only a legacy `worker` object exists, use that

## Procedure

### Step 1: Read the worker config

```bash
cat tmux_agents.json
```

From the resolved active worker entry, read:
- **session** — the tmux session name
- **send_method** — `two-line` (worker) or `enter` (regular)

### Step 2: Verify the session exists

```bash
tmux has-session -t <session> 2>/dev/null && echo "exists" || echo "not found"
```

If the session does not exist, report it and stop.

### Step 3: Clear stale input first

Before sending, clear any leftover text in the prompt to prevent garbled messages:

```bash
tmux send-keys -t <session> C-u
```

### Step 4: Send the command using the correct method

**If send_method is `two-line`** (worker sessions):

```bash
tmux send-keys -t <session> "<message>"
tmux send-keys -t <session> C-m
```

**If send_method is `enter`** (regular sessions):

```bash
tmux send-keys -t <session> "<message>" Enter
```

### Step 5: Confirm receipt

Wait a few seconds, then capture the pane to confirm the message was received and processing started:

```bash
sleep 3
tmux capture-pane -t <session> -p -S -20
```

Check for evidence that:
1. The message text appears in the pane
2. The agent started processing (look for `Working`, tool use, plan updates, or equivalent)

If the message is visible but not executing:
1. Send one additional submit key only once (`C-m` for two-line, `Enter` for enter method)
2. `sleep 10`, then capture the pane again
3. If still stuck, stop retrying — diagnose the pane state or recover the session before sending anything else

## Output

Report in this format:

```md
## Command Sent

- Worker: <worker name>
- Session: <session_name>
- Send method: two-line / enter
- Message: <message sent>
- Receipt confirmed: yes / no
- Agent state: working / received / not responding
```

## Important rules

- **Always read `tmux_agents.json`** to get the worker session and send method — never hardcode
- **Always use the correct send method** from the config — worker may require two-line, regular requires Enter
- **Always confirm receipt** — text in the prompt without execution is NOT a sent command
- **Never skip the session existence check** — sending to a dead session is silent failure
- **Escape special characters** in the message if needed (quotes, backticks, etc.)
