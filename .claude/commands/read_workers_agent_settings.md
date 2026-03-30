# /read_workers_agent_settings — Discover Worker's Setup & Build Delegation Cheat Sheet

Use this command to understand a worker's full development environment — their instructions, commands, workflow, and available tools — so you can delegate effectively.

## Input

`$ARGUMENTS` — (optional) specific aspect to focus on, e.g. "commands only" or "workflow only". If empty, do a full scan.

## Protocol

Execute these steps in order.

## Active worker resolution

If `$ARGUMENTS` names a specific worker, use that worker.
Otherwise, use the active worker from the current bot profile / `FIRST_PROMPT`:

- `.env1` maps to `Oysterun`
- `.env2` maps to `OysterunDeploy`
- If no explicit match is available, use `workers[0]`
- If only a legacy `worker` object exists, use that
- Do not switch away from the active worker unless Jeremy explicitly asked to scan a different worker

### Step 1: Read the worker config

```bash
cat tmux_agents.json
```

Get the resolved worker's `session`, `send_method`, and `project_dir`.

### Step 2: Detect worker agent type

Capture the worker's pane to identify what agent is running:

```bash
tmux capture-pane -t <session> -p -S -50
```

Look for indicators:
- **Codex** — prompt shows `codex>`, or session was started with `codex`
- **Claude Code** — prompt shows `claude>`, or started with `claude`
- **Other** — shell prompt, cursor, or unknown agent

Record the agent type — this affects how commands are invoked:
- **Claude Code** — supports `/command` slash syntax directly
- **Codex / Other agents** — do NOT support `.claude/commands/` slash commands. The PM must read the command file and send the instructions as plain text, or use the phrasing: `"Please now apply the flow in: .claude/commands/<command_name>.md"`

### Step 3: Read the worker's instructions

Ask the worker to print their instruction files. Use the correct send_method.

**Send to worker:**
```
Please print the contents of these files if they exist (cat each one): CLAUDE.md, AGENTS.md, .claude/CLAUDE.md
```

Wait for the response, then capture:
```bash
sleep 15
tmux capture-pane -t <session> -p -S -500
```

Record:
- Key rules and constraints the worker follows
- Coding standards, naming conventions
- Any workflow instructions (branching, testing, PR conventions)
- Which workflow steps the manager must enforce when delegating to this worker
- Any restrictions or safety rules

### Step 4: Read the worker's available commands

Ask the worker to list and briefly describe their commands.

**Send to worker:**
```
Please list all files in .claude/commands/ and give me a one-line description of each command (read the first few lines of each file).
```

Wait and capture:
```bash
sleep 15
tmux capture-pane -t <session> -p -S -500
```

Record each command with:
- Filename (this is the invocable name)
- Full path from project root (e.g. `.claude/commands/write_feature_plan.md`)
- One-line purpose

### Step 5: Read the worker's tool_scripts

Ask the worker to list available tool scripts.

**Send to worker:**
```
Please list all files and folders inside tool_scripts/ (if it exists) with a brief description of what each script/tool does. Just the top-level structure and purpose, no deep dive.
```

Wait and capture:
```bash
sleep 15
tmux capture-pane -t <session> -p -S -500
```

Record each tool with:
- Script name and path
- What it does
- How to invoke it

### Step 6: Build the Delegation Cheat Sheet

Create or update the file `worker_cheatsheets/<worker_name>_cheatsheet.md` with ALL findings structured as follows:

```markdown
# <Worker Name> — Delegation Cheat Sheet

Last updated: <date>

## Worker Info

- **Agent type:** <Codex / Claude Code / Other>
- **Session:** <tmux session name>
- **Send method:** <two-line / enter>
- **Project dir:** <path>

## Key Rules & Constraints

<Summarize the worker's CLAUDE.md/AGENTS.md rules that affect how you delegate>

## Development Workflow

<Summarize the expected workflow: branching strategy, testing requirements, PR conventions, etc.>

## Manager Process Contract

- The manager must follow this worker's development workflow for any relevant task.
- If the workflow requires plans, worktrees, approval pauses, tests, verification, reports, merges, naming rules, or coordination, those steps are mandatory in delegation and sign-off.
- Only Jeremy may explicitly approve deviating from this workflow.

## Available Commands

| Command | Full Path | Purpose |
|---------|-----------|---------|
| /command_name | .claude/commands/command_name.md | One-line description |
| ... | ... | ... |

**How to invoke:** For non-Claude agents, provide the full path:
"Please now apply the flow in: .claude/commands/<command_name>.md"

## Available Tool Scripts

| Tool | Path | Purpose |
|------|------|---------|
| script_name | tool_scripts/script_name | What it does |
| ... | ... | ... |

## Delegation Quick Reference

<Key things to remember when delegating to this worker — constraints, gotchas, preferred patterns>
- Follow the development workflow above as mandatory manager process; do not ask the worker to skip required steps unless Jeremy explicitly approves that deviation
- Respect the worker's original settings from `tmux_agents.json` / `FIRST_PROMPT`
- Discuss project questions with the worker before asking Jeremy
```

### Step 7: Update CLAUDE.md to point to the cheat sheet

Add or update a reference in this project's CLAUDE.md under a "Worker Cheat Sheets" section pointing to the generated file, so it's always discoverable.

## Output

Report back to Jeremy:

```
Worker Setup Scan Complete

- Worker: <name>
- Agent type: <type>
- Commands found: <count>
- Tool scripts found: <count>
- Cheat sheet saved: worker_cheatsheets/<worker_name>_cheatsheet.md
- CLAUDE.md updated: yes/no

Key findings:
- <most important workflow rule>
- <most useful commands for delegation>
- <any surprises or gotchas>
```

## Rules

- **Stay shallow** — you are the manager, not the developer. Do not explore deeply into src/, lib/, or other code folders.
- **Ask the worker** to read their own files — do not read worker project files directly.
- **Use full paths** when recording commands — non-Claude workers need explicit paths to follow commands.
- **Update, don't duplicate** — if a cheat sheet already exists for this worker, update it rather than creating a new one.
- **Always read `tmux_agents.json`** first — never hardcode session names or paths.
- Treat the generated cheat sheet as the manager-facing workflow contract for that worker, not just a reference note.
- Preserve the current worker's original settings unless Jeremy explicitly asks for worker-config meta-work.
- If a follow-up question remains after the scan, ask the worker first before asking Jeremy.
