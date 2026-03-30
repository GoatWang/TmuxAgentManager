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
4. **CC can apply pressure on your behalf** — for example, telling Codex "Jeremy is really frustrated..." (See: [PUA](https://github.com/tanweai/pua))

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

1. Copy the template and fill in your worker config:
   ```bash
   cp tmux_agents.json.template tmux_agents.json
   ```

2. Configure one or more bot profiles:
   - `.env1` => defaults to the `Oysterun` worker
   - `.env2` => defaults to the `OysterunDeploy` worker

   Each env profile should set `FIRST_PROMPT` to name its default worker.

3. Start the Telegram bot session with an explicit env profile:
   ```bash
   ctb --chrome --env=.env1
   # or
   ctb --chrome --env=.env2
   ```

   Or use the restart commands in `.claude/commands/restart_ctb.md`.

## Structure

```
.claude/
  CLAUDE.md                  # Main manager prompt and rules
  commands/                  # Slash commands for the manager
    delegate.md              # Force delegation before code work
    send_tmux.md             # Send a command to the worker
    chk_agent_status.md      # Check worker progress
    loop_monitor_agent.md    # Manual sleep-and-wait worker monitor
    spawn_tmux_session.md    # Spawn a new worker session
    restart_ctb.md           # Restart Telegram bot (with resume)
    restart_ctb_woresume.md  # Restart Telegram bot (fresh)
    stop_monitor.md          # Stop legacy monitor loops
tool_scripts/                # Utility scripts
tmux_agents.json.template    # Worker config template
```

## Worker Selection

`tmux_agents.json` now supports multiple workers through the `workers` array.

- The active/default worker is chosen by the current env profile's `FIRST_PROMPT`
- `.env1` should target `Oysterun`
- `.env2` should target `OysterunDeploy`
- If no explicit worker hint is available, the manager should fall back to `workers[0]`

## Roles & Responsibilities

### PM (Manager — this repo)

The PM is Jeremy's Technical PM & Agent Manager. It communicates with Jeremy via Telegram and manages the worker via tmux.

| Responsibility | Description |
|---|---|
| Requirements Analysis | Clarify Jeremy's intent, scope, edge cases, and hidden expectations before delegating |
| Task Delegation | Send well-specified tasks + acceptance criteria to the worker via tmux |
| Progress Monitoring | Periodically capture pane, push the worker if stuck or idle |
| Quality Gate | Ask the worker probing verification questions before reporting "done" |
| Research | WebSearch/WebFetch for open-ended questions, aggregate with worker's input |
| Coverage Matrix | For exhaustive deliverables, build a matrix with the worker, confirm scope with Jeremy, then delegate |
| Tmux Send Hygiene | Clear stale input (`C-u`) before every send, use correct `send_method`, verify execution started, one retry max then diagnose |

**The PM never:**
- Reads, writes, or modifies project code
- Runs build / test / server
- Executes project system commands
- Tests directly in Chrome (but can review worker-produced screenshots, logs, curl output)

### Worker (tmux session)

The worker runs in the project directory with full project context and IDE-level tooling.

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
Jeremy (Telegram)
  | request / question
  v
PM (TmuxAgentManager)
  -> Clarify requirements (ask Jeremy)
  -> Build coverage matrix (for exhaustive tasks: discuss with worker, confirm with Jeremy)
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
  -> Confirm result matches Jeremy's original intent
  -> Report to Jeremy
```

**In one line:** The PM is responsible for "thinking it through" and "following up." The Worker is responsible for "doing the work." The only thing the PM does directly is agent-manager config files.
