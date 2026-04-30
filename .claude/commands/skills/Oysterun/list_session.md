---
description: List live Oysterun Host sessions using the repo-local config.json credentials.
argument-hint: "[optional filter text]"
disable-model-invocation: true
---

# /skills/Oysterun/list_session

List the live Oysterun sessions visible to the configured local dashboard account.

## Local config

This command reads the repo-local ignored file:

```bash
config.json
```

If `config.json` is missing, create it from `config.example.json`.

## Procedure

Run:

```bash
python3 tool_scripts/oysterun_control.py list-sessions "$ARGUMENTS"
```

If `$ARGUMENTS` is non-empty, pass it as a filter:

```bash
python3 tool_scripts/oysterun_control.py list-sessions --filter "$ARGUMENTS"
```

## What to report

Report:

- Host base URL
- count of live sessions
- each live session's `sessionName`, `sessionId`, `agentId`, provider, and ready/alive state
- any role labels already bound from `config.json` such as `team_lead`
- any unresolved Oysterun team roles

Persistent role binding should prefer stable `session_name`, not live `session_id`. `agent_id` is legacy compatibility only.

## Rules

- This is agent-manager meta-work. Do not delegate it.
- Do not guess the target session from memory.
- If the owner asks which session should be used for the team lead and the role is unresolved, show the live session list and ask him to choose one.
