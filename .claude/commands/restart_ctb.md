# /restart_ctb — Restart the TmuxAgentManager Telegram bot session (with resume)

Restart the `TmuxAgentManager` tmux session that runs this Telegram bot, resuming the previous Claude conversation.

## Input

`$ARGUMENTS` — Optional env file to restart with (for example `.env1` or `.env2`).

## Procedure

### Step 1: Warn the user

**WARNING:** Restarting `TmuxAgentManager` will kill THIS current Telegram session. The new session will resume the previous conversation.

Tell the user: "This will restart the current Telegram bot session with --resume. You will lose this conversation context but the bot will resume its previous session. Proceed?"

Wait for confirmation before continuing.

### Step 2: Kill and recreate

Determine the env profile to use:

- If `$ARGUMENTS` is provided, use that env file
- Otherwise inspect the current pane / launch command for an existing `--env=...`
- If nothing explicit is found, default to `.env1`

**Note:** The session may be named `TmuxAgentManager` or `CodingTelegram`. Check both.

1. **Kill the existing session:**
   ```bash
   tmux kill-session -t TmuxAgentManager 2>/dev/null
   ```

2. **Recreate it with --resume:**
   ```bash
   tmux new-session -d -s TmuxAgentManager -c "$(pwd)" 'ctb --chrome --resume --env=<env_file>; exec $SHELL'
   ```

3. **Verify it started:**
   ```bash
   tmux has-session -t TmuxAgentManager 2>/dev/null && echo "exists" || echo "not found"
   ```

4. **Wait and confirm initialization:**
   ```bash
   sleep 3
   tmux capture-pane -t TmuxAgentManager -p -S -10
   ```

### Step 3: Report

```md
## CTB Restart Complete (with resume)

- Session restarted: TmuxAgentManager
- Resume: yes
- Status: running / failed
- Active sessions after restart:
  <output of tmux ls>
```

## Important rules

- **Always warn and wait for confirmation** — the user is on Telegram and this kills the current conversation
- **After restarting, verify the session exists** — a silent failure is worse than a reported failure
- **If it fails to start**, report the error clearly and suggest checking the project directory or `ctb` command
- **Fallback name:** If `TmuxAgentManager` does not exist, try `CodingTelegram`
- Prefer restarting with the same env profile the session was already using unless Jeremy explicitly asks to switch
