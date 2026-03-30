# /restart_ctb_woresume — Restart the TmuxAgentManager Telegram bot session (fresh, no resume)

Restart the `TmuxAgentManager` tmux session that runs this Telegram bot, starting a completely fresh conversation with no resume.

## Input

`$ARGUMENTS` — Optional env file to restart with (for example `.env1` or `.env2`).

## Procedure

### Step 1: Warn the user

**WARNING:** Restarting `TmuxAgentManager` will kill THIS current Telegram session. The new session will start completely fresh with no conversation history.

Tell the user: "This will restart the current Telegram bot session WITHOUT resume. You will lose all conversation context and start fresh. Proceed?"

Wait for confirmation before continuing.

### Step 2: Kill and recreate

Determine the env profile to use:

- If `$ARGUMENTS` is provided, use that env file
- Otherwise inspect the current pane / launch command for an existing `--env=...`
- If nothing explicit is found, default to `.env1`
- Preserve the current env profile by default so the original worker selection/settings stay intact. Do not switch envs unless Jeremy explicitly asks.

**Note:** The session may be named `TmuxAgentManager` or `CodingTelegram`. Check both.

1. **Kill the existing session:**
   ```bash
   tmux kill-session -t TmuxAgentManager 2>/dev/null
   ```

2. **Recreate it without resume:**
   ```bash
   tmux new-session -d -s TmuxAgentManager -c "$(pwd)" 'ctb --chrome --env=<env_file>; exec $SHELL'
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
## CTB Restart Complete (fresh, no resume)

- Session restarted: TmuxAgentManager
- Resume: no (fresh start)
- Status: running / failed
- Active sessions after restart:
  <output of tmux ls>
```

## Important rules

- **Always warn and wait for confirmation** — the user is on Telegram and this kills the current conversation
- **After restarting, verify the session exists** — a silent failure is worse than a reported failure
- **If it fails to start**, report the error clearly and suggest checking the project directory or `ctb` command
- **Fallback name:** If `TmuxAgentManager` does not exist, try `CodingTelegram`
- Prefer restarting with the same env profile the session was already using so the original worker selection/settings stay intact unless Jeremy explicitly asks to switch
