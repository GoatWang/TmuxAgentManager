# /login_claude — Restart the first worker session and run Claude `/login`

Use the first/default worker session from `config.json` for a Claude login flow.

This command is specifically for the first worker entry:

- `workers[0]` if a `workers` array exists
- otherwise the legacy `worker` object

In the current setup, that is expected to be `.env1` -> `Oysterun`.

## Input

`$ARGUMENTS` — none

## Procedure

### Step 1: Resolve the first worker

Read `config.json` and use the first/default worker exactly as configured.

```bash
python3 -c 'import json, pathlib; c=json.loads(pathlib.Path("config.json").read_text()); print(json.dumps({"workers": c.get("workers"), "worker": c.get("worker"), "team_roles": c.get("team", {}).get("roles", {})}, indent=2))'
```

Read:

- `name`
- `session`
- `working_dir`

Do not switch to another worker. Do not rewrite worker settings.

### Step 2: Verify the current tmux state

Before making any claim about session state, run live checks:

```bash
tmux ls
tmux has-session -t <session> 2>/dev/null && echo "SESSION EXISTS" || echo "SESSION NOT FOUND"
tmux display-message -p -t <session> 'cmd=#{pane_current_command} dead=#{pane_dead} in_mode=#{pane_in_mode} alt=#{alternate_on} cursor=#{cursor_x},#{cursor_y} size=#{pane_width}x#{pane_height}' 2>/dev/null || true
tmux capture-pane -t <session> -p -S -20 2>/dev/null || true
```

### Step 3: Stop and recreate the worker session

Kill the existing session if present, then recreate it in the worker's configured `working_dir`:

```bash
tmux kill-session -t <session> 2>/dev/null || true
tmux new-session -d -s <session> -c <working_dir>
```

Verify the new shell is ready:

```bash
tmux has-session -t <session> 2>/dev/null && echo "SESSION EXISTS" || echo "SESSION NOT FOUND"
tmux capture-pane -t <session> -p -S -20
```

### Step 4: Launch Claude

First confirm the CLI exists:

```bash
command -v claude || which claude
```

If `claude` is not installed, stop and report the failure clearly.

If it exists, launch it in the recreated tmux session:

```bash
tmux send-keys -t <session> C-u
tmux send-keys -t <session> "cd <working_dir> && claude"
tmux send-keys -t <session> C-m
```

Wait briefly, then confirm Claude actually started:

```bash
sleep 3
tmux display-message -p -t <session> 'cmd=#{pane_current_command} dead=#{pane_dead} in_mode=#{pane_in_mode} alt=#{alternate_on} cursor=#{cursor_x},#{cursor_y} size=#{pane_width}x#{pane_height}'
tmux capture-pane -t <session> -p -S -30
```

Only continue once the Claude UI or prompt is visibly running.

### Step 5: Send `/login`

Clear any stale input first, then send the Claude slash command:

```bash
tmux send-keys -t <session> Escape
tmux send-keys -t <session> "/login"
tmux send-keys -t <session> Enter
```

Wait and capture the response:

```bash
sleep 3
tmux capture-pane -t <session> -p -S -60
```

If the login URL is not visible, widen the capture before concluding failure:

```bash
tmux capture-pane -t <session> -p -S -120
```

### Step 6: Paste the login URL to the owner

If a Claude login URL is visible, paste the exact URL to the owner in the chat and say:

> Open this URL, complete the login, and send me the code.

Do not guess the URL. Copy it from the pane output.

### Step 7: Wait for the owner's code, then submit it

When the owner sends the code:

1. Check the session is still alive and waiting for input
   ```bash
   tmux has-session -t <session> 2>/dev/null && echo "SESSION EXISTS" || echo "SESSION NOT FOUND"
   tmux capture-pane -t <session> -p -S -30
   ```

2. Send the code into the same Claude session
   ```bash
   tmux send-keys -t <session> "<code_from_the_owner>"
   tmux send-keys -t <session> Enter
   ```

3. Wait and verify the result
   ```bash
   sleep 3
   tmux capture-pane -t <session> -p -S -60
   ```

If Claude asks for another prompt or confirmation instead of accepting the code immediately, relay that exact next step back to the owner.

### Step 8: Verify login success before claiming completion

Confirm login appears successful from the pane output before reporting success.

Examples of acceptable evidence:

- Claude returns to its normal prompt without another login challenge
- Claude shows a success or authenticated state
- Claude no longer asks for the login code

If the result is ambiguous, capture a slightly larger slice and report the ambiguity instead of guessing:

```bash
tmux capture-pane -t <session> -p -S -120
```

## Output

When the URL is found:

```md
## Claude Login URL

- Worker: <worker_name>
- Session: <session_name>
- Working dir: <working_dir>
- URL: <exact_login_url>
- Next step: the owner should open the URL and send back the code
```

After the code is submitted:

```md
## Claude Login Result

- Worker: <worker_name>
- Session: <session_name>
- Code submitted: yes
- Login status: success / failed / needs another step
- Evidence: <short pane summary>
```

## Important rules

- **Always use the first/default worker** from `config.json` for this command
- **Always verify tmux state live** before reporting that the session exists or does not exist
- **Always stop and recreate the session** before launching Claude
- **Never send `C-c`** to the worker session
- **Do not invent or paraphrase the login URL** — copy it exactly from the Claude pane output
- **Do not claim success until the post-code pane state confirms the login**
