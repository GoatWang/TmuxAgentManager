# /restart_ctb — Restart one or all TmuxAgentManager Telegram bot sessions (with resume)

Restart the Telegram bot tmux session(s) for this repo, resuming the previous conversation in each restarted bot.

`all` mode replaces the old `/restart_ctb_all` command.

## Input

`$ARGUMENTS` — Optional target:

- empty — restart the current/default Telegram bot session with `--resume`
- `.env1`, `.env2`, `.env3` — restart the specific Telegram bot session mapped to that env profile
- `TmuxAgentManager`, `TmuxAgentManager2`, `TmuxAgentManager3Fast` — restart that specific Telegram bot session
- `CodingTelegram` — legacy alias for the `.env1` bot session
- `all` — restart all three Telegram bot sessions with `--resume`

## Procedure

### Step 1: Restart immediately

Restart immediately. Do not ask for confirmation.

### Step 2: Resolve the restart target

Use this fixed Telegram bot session mapping:

- `TmuxAgentManager` -> `.env1`
- `TmuxAgentManager2` -> `.env2`
- `TmuxAgentManager3Fast` -> `.env3`
- `CodingTelegram` -> `.env1` (legacy alias for the first bot)

Resolve `$ARGUMENTS` like this:

1. If `$ARGUMENTS` is `all`, target all three fixed mappings above.
2. If `$ARGUMENTS` is one of `.env1`, `.env2`, `.env3`, map it to the corresponding session.
3. If `$ARGUMENTS` is one of the supported session names, map it to the corresponding env file.
4. If `$ARGUMENTS` is empty:
   - inspect `CTB_ENV` / `CTB_ENV_FILE` first
   - if still unknown, inspect the current tmux session launch command or recent pane output for `--env=...`
   - if still unknown, default to `TmuxAgentManager` -> `.env1`
5. If `$ARGUMENTS` is anything else, stop and report the supported values.

Preserve the current env profile by default so the original worker selection/settings stay intact. Do not switch envs unless the owner explicitly asks.

### Step 3: Restart the target session(s)

For each target session:

1. Kill it if it exists:
   ```bash
   tmux kill-session -t <session_name> 2>/dev/null || true
   ```

2. Recreate it with resume:
   ```bash
   tmux new-session -d -s <session_name> -c "$(pwd)" './tool_scripts/ctb_local.sh --chrome --resume --env=<env_file>; exec $SHELL'
   ```

   Keep `; exec $SHELL` at the end. That ensures the tmux session stays alive even if `ctb` is stopped with `C-c`.

3. Verify the session exists:
   ```bash
   tmux has-session -t <session_name> 2>/dev/null && echo "exists" || echo "not found"
   ```

After restarting the selected target(s), wait briefly and capture a small recent slice from each restarted session:

```bash
sleep 3
tmux capture-pane -t <session_name> -p -S -10
```

### Step 4: Report

```md
## CTB Restart Complete (with resume)

- Target: <single session name or all>
- Resume: yes
- TmuxAgentManager (`.env1`): running / failed / not targeted
- TmuxAgentManager2 (`.env2`): running / failed / not targeted
- TmuxAgentManager3Fast (`.env3`): running / failed / not targeted
- Active sessions after restart:
  <output of tmux ls>
```

## Important rules

- **Do not ask for confirmation** — restart immediately when the owner invokes this command
- **`all` replaces the old `/restart_ctb_all` flow** — do not look for a separate bulk CTB command
- **Preserve the fixed env mapping** for the three Telegram bot sessions — do not swap `.env1`, `.env2`, and `.env3`
- **After restarting, verify every targeted session exists** — a silent failure is worse than a reported failure
- **If one session fails, continue restarting the others** and report the failure clearly
- **If it fails to start**, report the error clearly and suggest checking the repo directory or `ctb` command
- **Do not remove `; exec $SHELL`** from the launch command — that is what keeps the tmux session alive after `ctb` exits or is interrupted with `C-c`
