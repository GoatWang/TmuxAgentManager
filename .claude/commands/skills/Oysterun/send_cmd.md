---
description: Send a command or question into an Oysterun session using a direct Host API call.
argument-hint: "[optional target] <message>"
disable-model-invocation: true
---

# /skills/Oysterun/send_cmd

Queue a message into an Oysterun session without using tmux.

## Target resolution

The first argument may be:

- a configured team role such as `team_lead`
- a concrete `sessionName`
- a concrete `session_id`
- a concrete legacy `agent_id`

If no target is supplied, default to the `team_lead` role from `config.json`.

For persistent team roles in `config.json`, prefer stable `session_name` binding.
Do not persist live `session_id`, and treat `agent_id` as legacy compatibility only.

## Examples

- `/skills/Oysterun/send_cmd team_lead give me progress report`
- `/skills/Oysterun/send_cmd oysterun-chat-telegram-refactor-v2-025fc give me progress report`
- `/skills/Oysterun/send_cmd 0a02921a-185b-42e7-8109-33be12f32ecf give me progress report`

## Procedure

1. Parse `$ARGUMENTS`.
2. If the first token is a role/session selector, use it as `--target`.
3. Otherwise, treat the whole argument string as the message and default the target to `team_lead`.
4. Before sending to `team_lead`, run `/skills/Oysterun/read_status` for the same target. Send only if it reports `Ready to send: yes`.

Run one of:

```bash
python3 tool_scripts/oysterun_control.py send --target "<target>" "<message>"
```

or

```bash
python3 tool_scripts/oysterun_control.py send "<message>"
```

## If target resolution fails

Do not guess.

Instead:

1. Run `/skills/Oysterun/list_session`
2. Use the live choices only to diagnose the routing problem
3. If the role is legacy agent-bound but multiple live sessions match, stop and report a session-binding blocker
4. If the role is unbound or no live session exists, stop and report that `config.json` must be fixed before routing work

## What to report

Report:

- the resolved target label
- the resolved `sessionName` and `sessionId`
- the queued `message_id`
- the returned delivery state

## Rules

- This is agent-manager meta-work. Do not delegate it.
- Never silently switch from one Oysterun session to another.
- If `team_lead` is unresolved or ambiguous, stop and report the live session list as a configuration blocker; do not ask the owner to choose a task-routing target.
- Do not queue a new TL message when `read_status` shows active, queued, or cancelable work. Defer to the next tick and check again.
