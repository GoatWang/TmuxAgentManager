---
description: Read Oysterun session delivery and outbox status before sending a new command.
argument-hint: "[optional target]"
disable-model-invocation: true
---

# /skills/Oysterun/read_status

Read whether an Oysterun session is idle enough to receive a new message.

## Target resolution

The target rules are the same as `/skills/Oysterun/send_cmd`:

- role like `team_lead`
- `sessionName`
- `session_id`
- legacy `agent_id`

If omitted, default to the `team_lead` role.

## Examples

- `/skills/Oysterun/read_status`
- `/skills/Oysterun/read_status team_lead`
- `/skills/Oysterun/read_status <oysterun_session_name>`

## Procedure

Run:

```bash
python3 tool_scripts/oysterun_control.py status --target "<target>"
```

or, for the default `team_lead` target:

```bash
python3 tool_scripts/oysterun_control.py status
```

Use the JSON form when another command or report needs structured fields:

```bash
python3 tool_scripts/oysterun_control.py status --target "<target>" --json
```

## Send readiness rule

Treat the session as ready for a new command only when the status output says:

- `Ready to send: yes`
- `delivery.state = ready`
- `queued_count = 0`
- `active_message_id = null`
- `active_message_state = null`
- `Queued messages: 0`
- `Cancelable messages: 0`

If any queued or cancelable message exists, do not send another command in the same tick. Wait until the next tick and read status again.

If an active message exists, treat the target as still responding or processing. Do not stack another command behind it unless TL explicitly instructs a queueing behavior.

## What to report

Report:

- the resolved target
- `Ready to send`
- delivery state, queued count, active message id/state
- queued/cancelable message count
- whether the next message was sent or deferred to the next tick

Do not treat transcript text alone as proof that the session is idle. Transcript rows show what has been written; `/session/snapshot` delivery/outbox state shows whether the Host still has active or queued work.
