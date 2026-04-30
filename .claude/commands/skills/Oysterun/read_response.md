---
description: Read the latest Oysterun transcript messages from a target session.
argument-hint: "[optional target] [optional limit]"
disable-model-invocation: true
---

# /skills/Oysterun/read_response

Read recent transcript rows from an Oysterun session.

## Target resolution

The target rules are the same as `/skills/Oysterun/send_cmd`:

- role like `team_lead`
- `sessionName`
- `session_id`
- legacy `agent_id`

If omitted, default to the `team_lead` role.

For persistent team roles in `config.json`, prefer stable `session_name` binding and let the live session be resolved at runtime. `agent_id` is legacy compatibility only.

## Examples

- `/skills/Oysterun/read_response`
- `/skills/Oysterun/read_response team_lead`
- `/skills/Oysterun/read_response oysterun-chat-telegram-refactor-v2-025fc`
- `/skills/Oysterun/read_response team_lead 20`

## Procedure

If a numeric final token is present, use it as the transcript limit.

Run:

```bash
python3 tool_scripts/oysterun_control.py read --target "<target>" --limit <N>
```

or, for the default `team_lead` target:

```bash
python3 tool_scripts/oysterun_control.py read --limit <N>
```

By default this shows human-facing transcript rows and hides `tool_call` / `tool_result` noise.
If the owner explicitly wants the internal stream, add:

```bash
--include-internal
```

## If target resolution fails

Do not guess.

Run `/skills/Oysterun/list_session`, use the live sessions only to diagnose the routing problem, then stop and report a session-binding blocker. Do not ask the owner to choose a task-routing target or create a replacement TL session by guesswork.

If the role is legacy agent-bound but multiple live sessions match, stop and report the ambiguity as a configuration blocker.

## What to report

Summarize:

- the resolved target
- the latest assistant/user rows that matter
- whether the session appears idle, responding, or blocked from the transcript evidence
