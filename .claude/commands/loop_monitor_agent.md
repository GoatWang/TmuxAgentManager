# Loop Monitor Agent

Legacy command name only. Do **not** start a recurring loop, cron job, or background monitor.
Use this command to monitor the worker manually in a sleep-and-wait manner from the current session.

## Setup

Read the worker config:

```bash
cat tmux_agents.json
```

Resolve the active worker first:

- If `tmux_agents.json` has a `workers` array, match the worker named in the current bot profile / `FIRST_PROMPT`
- `.env1` maps to `Oysterun`
- `.env2` maps to `OysterunDeploy`
- If no explicit match is available, use `workers[0]`
- If only a legacy `worker` object exists, use that
- Respect the resolved worker's original settings. Do not switch workers during monitoring.

From the resolved active worker entry, read:
- **name** — the worker agent name
- **session** — the tmux session name
- **send_method** — `two-line` (worker) or `enter` (regular)

## Procedure

1. Stay in the current session and monitor manually. Do **not** schedule cron or any recurring job.

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

4. **Wait deliberately**, then capture the pane again to read the status response (or use the existing response from step 3 if already present).

   Use a sleep-and-wait cadence such as:
   ```bash
   sleep 10
   tmux capture-pane -t <session> -p -S -30
   ```

   If the worker is clearly in a long-running active step, use a longer wait such as `sleep 30` before checking again.

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

6. **If the next task requires Jeremy's input** (ambiguous direction, multiple options needing his preference, scope decisions), ask the worker for the clearest options/recommendation first, then report that status and recommendation to Jeremy. Do NOT ask Jeremy a bare question.

7. Repeat the capture → assess → sleep → capture cycle manually for as long as needed. Do not hand this off to cron.

## Important notes

- **Always read `tmux_agents.json`** to get the worker session and send method — never hardcode
- Preserve the active worker and original settings from `FIRST_PROMPT` / `tmux_agents.json`; do not switch workers during monitoring
- Do **not** use cron, `/loop`, or recurring background monitoring for worker supervision
- Use sleep-and-wait supervision instead: capture, assess, sleep, capture again
- For `two-line` send method: text first, then C-m separately — `Enter` does not submit in worker sessions
- For `enter` send method: append Enter to the send-keys command
- Do NOT prefix commands with `/` — the worker does not recognize Claude Code slash commands
- If you find a legacy monitor cron job from older behavior, stop it with `/stop_monitor`
