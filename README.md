# TmuxAgentManager

**The Best Agent Configuration for Complex Software Development**

Agent Manager configuration for a PM-style orchestration layer that manages worker agents via tmux.

The manager communicates with users via Telegram (powered by [claude-telegram-bot](https://github.com/GoatWang/claude-telegram-bot)) and delegates all project work to a worker agent running in a tmux session.

p.s. to have a better experience, recomend to use my fork of claude-telegram-bot I have added/fixed several functions e.g. image updoading, session resuming and network error fixing.  

## Why This Configuration?

- I've been running this setup for a week, and it almost never frustrates me. 
- This configuration is genuinely powerful — it lets me use Telegram as my IDE. 
- With this setup, I can develop applications in domains I'm unfamiliar with purely by talking (嘴++).

### The Problem with Using Each Agent Alone

**Claude Code (CC)** is an excellent communicator — great at interaction, understanding user intent, and acting as a PM. But when it comes to writing code, it often goes in circles: fixing one bug introduces an old one, and after two days you start wondering where all that time went.

**Codex** is a brilliant engineer, but its responses are verbose and hard to digest, and its UX is still far behind CC.

For example, I'm often too lazy to read through Codex's lengthy reports. Instead, I have CC read them for me, then walk me through each point interactively so I can confirm my intent and add comments. This way I don't have to read every detail, yet I can still give precise confirmations and corrections. Codex simply can't do that.

But CC frequently breaks my code — new and old bugs keep alternating, and after two days you start questioning what you even accomplished.

### The Solution

Let CC be the PM and send instructions to Codex, with Codex running inside a tmux session. Once the concept is clear, the rest is solving technical problems.

Two critical points to note: you must **strictly prevent CC from trying to write code itself** — only then can it focus on PM tasks. In my first few days I also gave it testing and verification tasks, and it fell apart.

There's also a technical challenge with tmux interaction: CC often forgets to press Enter to submit messages, or accidentally kills the session because the context window runs too short. The solutions are all documented in this repo (see comments below).

### Why This Configuration Is So Powerful

1. **CC focuses on clarifying your intent and requirements.** Every prompt is refined and optimized before it reaches the engineer.
2. **CC automatically tracks execution progress** and pushes the worker to keep going. It only bothers you when something truly needs your input — unlike Codex, which still constantly asks for responses.
3. **CC can check whether the worker is cutting corners** — for example, asking probing questions like "Are you sure this feature is done? Did you run the tests?"
4. **CC can apply pressure on your behalf** — for example, telling Codex "the owner is really frustrated..." (See: [PUA](https://github.com/tanweai/pua))

If you only have a CC subscription and you believe CC can handle your task, using CC as the engineer directly is also fine.

## Architecture

```
User (Telegram)
  |
  v
PM / Manager (this repo)
  |  - clarifies requirements
  |  - delegates tasks
  |  - monitors progress
  |  - verifies results
  |
  v
Worker Agent (tmux session)
  - implements features
  - runs builds/tests
  - reports results
```

## Setup

1. Copy the unified template and fill in local worker + Oysterun settings:
   ```bash
   cp config.example.json config.json
   ```

2. Configure one or more bot profiles:
   - `.env1` => select a default worker defined in `config.json`
   - `.env2` => select a different default worker from `config.json`, if needed
   - `.env3` => select another default worker from `config.json`, if needed

   Each env profile should set `FIRST_PROMPT` to identify its default worker by `name` or `session` from `config.json`.

3. Start the Telegram bot session with an explicit env profile:
   ```bash
   ./tool_scripts/ctb_local.sh --chrome --env=.env1
   # or
   ./tool_scripts/ctb_local.sh --chrome --env=.env2
   # or
   ./tool_scripts/ctb_local.sh --chrome --env=.env3
   ```

   Or use the restart commands in `.claude/commands/restart_ctb.md`.

## Structure

```
.claude/
  CLAUDE.md                  # Main manager prompt and rules
  skills/                    # Project-local skills for the manager
    oysterun_session_control.md
  commands/                  # Slash commands for the manager
    delegate.md              # Force delegation before code work
    send_tmux.md             # Send a command to the worker
    chk_agent_status.md      # Check worker progress
    who_is_my_worker.md      # Resolve the active worker for this env profile
    setup_worker.md          # Ensure the active worker session is running Codex
    start_all_manager.md     # Start all Telegram bot manager sessions
    start_all_worker.md      # Start all configured worker sessions
    start_all_sessions.md    # Full-fleet start wrapper: workers then managers
    stop_all_manager.md      # Stop all Telegram bot manager sessions
    stop_all_worker.md       # Stop all configured worker sessions
    stop_all_sessions.md     # Full-fleet stop wrapper: managers then workers
    restart_all_manager.md   # Restart all Telegram bot manager sessions
    restart_all_worker.md    # Restart all configured worker sessions
    restart_all_sessions.md  # Full-fleet restart wrapper using split commands
    skills/Oysterun/         # Oysterun Host control commands
      list_session.md        # List live Oysterun sessions
      send_cmd.md            # Send a message into an Oysterun session
      read_response.md       # Read recent Oysterun transcript rows
    loop_monitor_agent.md    # Manual sleep-and-wait worker monitor
    spawn_tmux_session.md    # Spawn a new worker session
    restart_ctb.md           # Restart one or all Telegram bots (with resume)
    restart_ctb_woresume.md  # Restart one or all Telegram bots (fresh)
    stop_monitor.md          # Stop legacy monitor loops
tool_scripts/                # Utility scripts
  oysterun_control.py        # Oysterun Host helper (list/send/read)
config.example.json          # Unified worker + Oysterun config template
```

## Local Oysterun Control

This repo now supports direct Oysterun Host control for manager meta-work.

- Local secret config lives in ignored `config.json`
- Example schema lives in `config.example.json`
- The helper script is `tool_scripts/oysterun_control.py`
- Slash commands live under `.claude/commands/skills/Oysterun/`

The intended pattern is:

1. `/skills/Oysterun/list_session` to inspect live sessions
2. `/skills/Oysterun/send_cmd` to queue a question or command
3. `/skills/Oysterun/read_response` to read the latest transcript

`config.json` can bind `team.roles.team_lead` to a stable Oysterun `session_name` and a `working_dir`. The manager should resolve the live session at runtime by session name first. If the binding is missing, no live session exists, or multiple live sessions match, it should list live sessions and ask the owner to choose one instead of guessing. `agent_id` remains a legacy fallback only.

## Worker Selection

`config.json` now supports multiple typed workers through the `workers` array. Tmux workers use `"type": "tmux"` and Oysterun team roles use `"type": "Oysterun"`.

- The active/default worker is chosen by the current env profile's `FIRST_PROMPT`
- `.env1`, `.env2`, `.env3`, and similar local profiles should point to workers defined in `config.json`
- `FIRST_PROMPT` should identify the target worker by configured `name` or `session`
- If no explicit worker hint is available, the manager should fall back to `workers[0]`
- Each worker entry should define `working_dir`; TeamLead messages should use `{TL_WORKINGDIR}` from `team.roles.team_lead.working_dir`

## Roles & Responsibilities

### PM (Manager — this repo)

The PM is the owner's Technical PM & Agent Manager. It communicates with the owner via Telegram and manages the worker via tmux.

| Responsibility | Description |
|---|---|
| Requirements Analysis | Clarify the owner's intent, scope, edge cases, and hidden expectations before delegating |
| Task Delegation | Send well-specified tasks + acceptance criteria to the worker via tmux |
| Progress Monitoring | Periodically capture pane, push the worker if stuck or idle |
| Quality Gate | Ask the worker probing verification questions before reporting "done" |
| Research | WebSearch/WebFetch for open-ended questions, aggregate with worker's input |
| Coverage Matrix | For exhaustive deliverables, build a matrix with the worker, confirm scope with the owner, then delegate |
| Tmux Send Hygiene | Clear stale input (`C-u`) before every send, use correct `send_method`, verify execution started, one retry max then diagnose |

**The PM never:**
- Reads, writes, or modifies project code
- Runs build / test / server
- Executes project system commands
- Tests directly in Chrome (but can review worker-produced screenshots, logs, curl output)

### Worker (tmux session)

The worker runs in its configured `working_dir` with full project context and IDE-level tooling.

| Responsibility | Description |
|---|---|
| Feature Implementation | All features, bug fixes, refactoring |
| Code Read/Write | Read, modify, create files |
| Build / Test | Run compilation, tests, start servers |
| System Commands | Execute curl, git, npm, and other project commands |
| Screenshots / Docs | Capture screens, generate documentation, produce artifacts |
| Technical Knowledge | The PM's first source for architecture and technical context |
| Report Results | Tell the PM what changed, what was tested, and any risks |

## Workflow

```
the owner (Telegram)
  | request / question
  v
PM (TmuxAgentManager)
  -> Clarify requirements (ask the owner)
  -> Build coverage matrix (for exhaustive tasks: discuss with worker, confirm with the owner)
  -> Write clear spec
  -> C-u clear -> send to worker -> verify receipt
  |
  v
Worker (tmux session)
  -> Implement / fix bugs / test
  -> Report results
  |
  v
PM
  -> Verify (what changed? tested? edge cases?)
  -> Confirm result matches the owner's original intent
  -> Report to the owner
```

**In one line:** The PM is responsible for "thinking it through" and "following up." The Worker is responsible for "doing the work." The only thing the PM does directly is agent-manager config files.
