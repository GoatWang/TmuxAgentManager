# Oysterun Session Control

Use this local skill when the owner wants the manager to talk to an Oysterun Host session directly instead of using tmux.

## Local files

- Ignored runtime config: `config.json`
- Example config: `config.example.json`
- Helper: `tool_scripts/oysterun_control.py`
- Command docs:
  - `.claude/commands/skills/Oysterun/list_session.md`
  - `.claude/commands/skills/Oysterun/send_cmd.md`
  - `.claude/commands/skills/Oysterun/read_response.md`

## Supported actions

- List live Oysterun sessions
- Send a message to a live Oysterun session
- Read recent transcript rows from a live Oysterun session

## Team role rule

`config.json` may bind team roles to Oysterun sessions under:

```json
"team": {
  "roles": {
    "team_lead": {
      "type": "Oysterun",
      "session_name": null,
      "working_dir": "~/Projects/<teamlead_project>",
      "guide_path": "{TL_WORKINGDIR}/.teamlead/_TEAMLEAD_GUIDE.md",
      "stop_routing_rule_path": "{TL_WORKINGDIR}/.teamlead/_STOP_ROUTING_RULE.md"
    }
  }
}
```

Use `session_name` as the persistent identity. A live `session_id` is ephemeral and should not be the default long-term binding. `agent_id` remains legacy compatibility only. Use `working_dir` as `TL_WORKINGDIR` when composing TeamLead guide and stop-routing-rule references; do not hardcode a project path in command docs.

If the owner asks to "ask the team lead" or "get the next task from the team lead":

1. Try the `team_lead` role first.
2. Resolve that role to live sessions by `session_name`.
3. If it resolves to one live Oysterun session, use it.
4. If it resolves to multiple live sessions, treat that as legacy fallback or inconsistent host state, run `/skills/Oysterun/list_session` only to diagnose, then stop and report a session-binding blocker; do not ask the owner to choose a task-routing target.
5. If it is unresolved, run `/skills/Oysterun/list_session`.
6. Report that `config.json` must be fixed before routing work to TL; do not create or bind a replacement TL session by guesswork.
7. Do not guess.

## Boundary

This is agent-manager meta-work in `TmuxAgentManager`, not worker code work.
