# /send_tmux — Send a command to the worker agent

Send a message or task to the current active worker agent session. Reads `config.json` to determine the worker session and send method.

## Input

`$ARGUMENTS` — The message to send to the worker.

Examples:
- `/send_tmux Fix the CSS overflow bug on mobile`
- `/send_tmux What cron jobs are running?`

## Active worker resolution

Before Step 1:

- Read `config.json`
- If it has a `workers` array, match the worker named in the current bot profile / `FIRST_PROMPT`
- `.env1` maps to `Oysterun`
- `.env2` maps to `OysterunDeploy`
- If no explicit match is available, use `workers[0]`
- If only a legacy `worker` object exists, use that
- Respect that resolved worker exactly as configured. Do not switch workers or rewrite worker settings unless the owner explicitly asks for agent-manager meta-work.

## Procedure

### Step 1: Read the worker config

```bash
python3 -c 'import json, pathlib; c=json.loads(pathlib.Path("config.json").read_text()); print(json.dumps({"workers": c.get("workers"), "worker": c.get("worker"), "team_roles": c.get("team", {}).get("roles", {})}, indent=2))'
```

From the resolved active worker entry, read:
- **session** — the tmux session name
- **send_method** — `two-line` (worker) or `enter` (regular)

### Step 2: Verify the session exists

```bash
tmux has-session -t <session> 2>/dev/null && echo "exists" || echo "not found"
```

If the session does not exist, report it and stop.
Do not silently send the message to a different worker session.

### Step 3: Clear stale input first

Before sending, clear any leftover text in the prompt to prevent garbled messages:

```bash
tmux send-keys -t <session> C-u
```

### Step 4: Send the command using the correct method

**If send_method is `two-line`** (worker sessions):

```bash
tmux send-keys -t <session> "<message>"
sleep 3
tmux send-keys -t <session> C-m
```

**If send_method is `enter`** (regular sessions):

```bash
tmux send-keys -t <session> "<message>"
sleep 3
tmux send-keys -t <session> Enter
```

The delay between sending text and sending the submit key is mandatory. Do not collapse the text send and submit key into one command for worker sessions; Codex TUI can leave long input sitting in the prompt if the submit key races the paste.

### Step 5: Confirm receipt

Wait 5 seconds, then capture the pane to confirm the message was received and processing started. The 5-second wait is mandatory; do not judge receipt from an immediate capture because Codex TUI may need a short moment to redraw from prompt input to `Working` / response / tool activity.

```bash
sleep 5
tmux capture-pane -t <session> -p -J -S -30
```

Check for evidence that:
1. The message text appears in the pane
2. The agent started processing (look for `Working`, tool use, plan updates, or equivalent)

This is a receipt check, not a full history read. Keep the first capture small.
Only if receipt is unclear should you escalate to a medium capture such as `-80` to `-100`.

If the message is visible in the current prompt buffer but not executing, use this bounded submit recovery. The goal is to keep work moving while avoiding blind repeated sends:

1. Send the configured submit key one additional time only once (`C-m` for two-line, `Enter` for enter method).
2. `sleep 5`, then capture again with `tmux capture-pane -t <session> -p -J -S -30`.
3. If it is still not executing, send the alternate submit key once:
   - configured `C-m` -> try `Enter`
   - configured `Enter` -> try `C-m`
4. `sleep 5`, then capture again with `tmux capture-pane -t <session> -p -J -S -30`.
5. If the current prompt still contains the unsent message and there is no worker response, tool activity, `Working`, plan update, or fresh idle prompt after it, send `Escape` once to exit a possible stuck TUI mode.
6. `sleep 2`, then capture again with `tmux capture-pane -t <session> -p -J -S -50`.
7. After the Escape capture, classify the pane:
   - If the message executed, receipt is confirmed.
   - If the worker is at a fresh idle prompt, the prior prompt buffer is gone; report `receipt confirmed: no`, `agent state: idle`, and send the assignment again only if TL/PM still intends to dispatch it.
   - If the message is still visibly unsent in the current prompt, report `receipt confirmed: no`, `agent state: pane_parse_uncertain`, include the bottom prompt excerpt, and ask TL/manager recovery direction. Do not keep pressing submit keys blindly.

Do not use `Escape` as an interrupt for active work. Use it only in this receipt-recovery path when the message is still sitting in the prompt and has not started executing.

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

- **Always read `config.json`** to get the worker session and send method — never hardcode
- Preserve the original worker settings from `FIRST_PROMPT` / `config.json`; if the target session is broken, recover or report it instead of switching workers
- **Always use the correct send method** from the config — worker may require two-line, regular requires Enter
- **Always confirm receipt** — text in the prompt without execution is NOT a sent command
- **Never skip the session existence check** — sending to a dead session is silent failure
- **Escape special characters** in the message if needed (quotes, backticks, etc.)
