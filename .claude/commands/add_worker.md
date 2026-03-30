---
description: Add a new worker profile by cloning an existing worker entry and creating a matching .envN bot profile. Ask for missing inputs before editing files.
argument-hint: "[worker-name] [telegram-user-id] [telegram-bot-token] [template-worker-name]"
disable-model-invocation: true
---

# /add_worker — Add a new worker profile

Use this command when Jeremy wants a new worker added to this repo's manager configuration.

This is agent-manager meta-work. Do not delegate it.

## Inputs

`$ARGUMENTS` — Optional. Preferred order:

`<worker_name> <telegram_allowed_user_id> <telegram_bot_token> [template_worker_name]`

Examples:

- `/add_worker OysterunQA 7714604497 1234567890:AAExampleToken`
- `/add_worker OysterunQA 7714604497 1234567890:AAExampleToken Oysterun`
- `/add_worker` if you want the command to ask for the missing values interactively

## Goal

Create a new worker by:

1. inspecting the current worker config and env profiles first
2. asking the user for any missing required inputs
3. cloning the relevant fields from an existing worker
4. appending the new worker to `tmux_agents.json`
5. creating the next `.envN` file that points `FIRST_PROMPT` at the new worker

## Required files discovered in this repo

Based on the current repo layout, a new worker profile requires these files:

- `tmux_agents.json` — canonical worker registry
- next available `.envN` file — Telegram bot profile that selects the worker through `FIRST_PROMPT`

Read these files first to confirm the current shape and conventions:

- `tmux_agents.json`
- `tmux_agents.json.template`
- `.env1`, `.env2`, and any other existing `.env*` files
- `README.md`
- `.claude/commands/`

## Protocol

Execute these steps in order.

### Step 1: Explore the current worker setup

Read the current command folder and config files before making assumptions:

```bash
find .claude/commands -maxdepth 1 -type f | sort
cat tmux_agents.json
cat tmux_agents.json.template
ls -1 .env*
```

Then inspect the env profiles and README conventions:

```bash
for f in .env*; do
  echo "===== $f ====="
  cat "$f"
done

sed -n '1,220p' README.md
```

From that scan, confirm these conventions before editing:

- workers live in `tmux_agents.json` under `workers`
- the legacy top-level `worker` object mirrors `workers[0]` only
- env profiles use `TELEGRAM_BOT_TOKEN`, `TELEGRAM_ALLOWED_USERS`, `ALLOWED_PATHS=/`, and `FIRST_PROMPT`
- `FIRST_PROMPT` selects the default worker by name
- existing workers and existing env profiles must keep their original settings unless Jeremy explicitly asks to change them

### Step 2: Parse arguments and collect missing inputs interactively

Map `$ARGUMENTS` like this:

- `$0` => `worker_name`
- `$1` => `telegram_allowed_user_id`
- `$2` => `telegram_bot_token`
- `$3` => `template_worker_name` (optional)

If any required value is missing, stop and ask the user before editing files.

Ask one concise question at a time. Start with the bot credential if it is missing.

Required values:

- `worker_name` — also used as the tmux `session` name unless Jeremy explicitly asks for something different
- `telegram_allowed_user_id` — numeric Telegram user ID allowed to talk to the bot
- `telegram_bot_token` — full BotFather token, not only the numeric bot ID

Optional value:

- `template_worker_name` — existing worker to clone from; default to `workers[0]` if not provided

If the user gives only a numeric bot ID without the secret token, ask again for the full `TELEGRAM_BOT_TOKEN` because the env file cannot be built from a bare bot ID.

### Step 3: Resolve the template worker

Read `tmux_agents.json` and choose the source worker to clone:

- if `template_worker_name` is provided, match it by `name`
- otherwise use `workers[0]`

From the template worker, copy these fields:

- `project`
- `project_dir`
- `send_method`

Also use the template's notes as the pattern for the new `notes` text.

### Step 4: Validate before editing

Before writing anything, verify all of these:

- no existing worker already uses the new `worker_name`
- no existing worker already uses the same `session`
- the chosen template worker exists
- the next `.envN` filename is available

Compute the next env filename by scanning existing `.env*` files and incrementing the highest numeric suffix:

```bash
ls .env* 2>/dev/null | sed 's|.env||' | awk '/^[0-9]+$/ { print $1 }' | sort -n | tail -1
```

If no numbered env files exist, use `.env1`.

### Step 5: Update `tmux_agents.json`

Append a new worker object to the `workers` array.

Use:

- `name`: `<worker_name>`
- `project`: copied from template worker
- `project_dir`: copied from template worker
- `session`: `<worker_name>` unless Jeremy explicitly gave a different session name
- `send_method`: copied from template worker
- `notes`: same style as the template worker, but updated for the new worker name

Important:

- do **not** reorder the existing workers
- do **not** alter the existing workers' `name`, `session`, `send_method`, `project`, or `project_dir`
- do **not** overwrite the legacy top-level `worker` object unless Jeremy explicitly wants the new worker to become the default `workers[0]`
- keep JSON formatting consistent with the existing file

### Step 6: Create the new `.envN` profile

Create the next available `.envN` file with this structure:

```dotenv
TELEGRAM_BOT_TOKEN=<telegram_bot_token>
TELEGRAM_ALLOWED_USERS=<telegram_allowed_user_id>
ALLOWED_PATHS=/
FIRST_PROMPT=Default worker: use the worker named <worker_name> from tmux_agents.json for delegation, monitoring, and status checks. Respect the original worker settings and do not switch workers unless Jeremy explicitly asks for agent-manager meta-work.
```

Do not modify existing env files unless Jeremy explicitly asks to repoint an existing bot profile.

### Step 7: Final verification

After writing the files:

1. read back the new worker entry from `tmux_agents.json`
2. read back the new `.envN` file
3. confirm the new worker name appears in the new env file's `FIRST_PROMPT`

### Step 8: Report

Report back in this shape:

```md
## Worker Added

- Worker: <worker_name>
- Template worker: <template_worker_name or workers[0]>
- Session: <session>
- Added to: tmux_agents.json
- Env profile: <.envN>
- Project dir: <project_dir>
- Send method: <send_method>
- Follow-up needed: none / <anything still missing>
```

## Rules

- Explore the command folder and config files first; do not jump straight into editing
- Ask the user for missing inputs before modifying files
- Treat a bare bot ID as insufficient; the env file needs the full bot token
- Copy only the template fields that should stay aligned across workers: `project`, `project_dir`, and `send_method`
- Preserve every existing worker's original settings; this command appends a worker, it does not switch or rewrite the current one
- Do not change unrelated files
- This command creates config for a new worker profile; it does not automatically restart the Telegram bot or spawn a tmux worker session unless Jeremy asks for that separately
