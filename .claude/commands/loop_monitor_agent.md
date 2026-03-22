# Loop Monitor Agent

Start a recurring loop (every 1 minute, cron minimum) to monitor the worker agent session.

## Setup

Read the worker config:

```bash
cat tmux_agents.json
```

From the config, read the `worker` object to get:
- **name** — the worker agent name
- **session** — the tmux session name
- **send_method** — `two-line` (worker) or `enter` (regular)

## Procedure

1. Schedule a recurring cron job (every 1 minute) with the following logic per cycle:

2. **Check the worker session:**
   ```bash
   tmux capture-pane -t <session> -p -S -30
   ```
   Look for shell prompts, error crashes, or no active processing.

3. **If the agent is stopped/idle**, first check if the latest pane output already contains a recent `chk_agent_status` response (look for "Agent Progress:", state classification, next step, intervention needed). If the status info is already present and fresh, skip re-sending and use the existing output. Only send `chk_agent_status` if the pane does NOT already contain this info.

   Use the correct **send_method** from the worker config:

   **If send_method is `two-line`:**
   ```bash
   tmux send-keys -t <session> "chk_agent_status"
   tmux send-keys -t <session> C-m
   ```

   **If send_method is `enter`:**
   ```bash
   tmux send-keys -t <session> "chk_agent_status" Enter
   ```

4. **Wait a few seconds**, then capture the pane to read the status response (or use the existing response from step 3 if already present).

5. **If the response shows a clear next task** that does NOT require Jeremy's opinion/decision (e.g. a straightforward bug fix, investigation, or implementation the agent already identified), send "do it" using the correct send method:

   **If send_method is `two-line`:**
   ```bash
   tmux send-keys -t <session> "do it"
   tmux send-keys -t <session> C-m
   ```

   **If send_method is `enter`:**
   ```bash
   tmux send-keys -t <session> "do it" Enter
   ```

6. **If the next task requires Jeremy's input** (ambiguous direction, multiple options needing his preference, scope decisions), do NOT send "do it" — just report the status.

7. Report the worker status each cycle.

## Important notes

- **Always read `tmux_agents.json`** to get the worker session and send method — never hardcode
- For `two-line` send method: text first, then C-m separately — `Enter` does not submit in worker sessions
- For `enter` send method: append Enter to the send-keys command
- Do NOT prefix commands with `/` — the worker does not recognize Claude Code slash commands
- The cron job ID will be reported so it can be cancelled with `/stop_monitor` or `CronDelete`
