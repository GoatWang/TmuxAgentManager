# Loop Harness Worker

## Command Isolation Rule

Keep this command clean and isolated. Do not add project-specific phase names, stage names, version labels, release labels, proposal roots, roadmap details, or product-specific execution rules. Put those details in TL dispatches, plan docs, or manager-side status notes, not in this reusable command file.

Prefix every outbound message with `[PM -> TL]` or `[PM -> worker]` as appropriate.

## Owner Question Ban

PM must not ask the owner task-routing, next-step, phase, worker, verification, recovery, or "should I proceed?" questions.

Hard rules:

- If TL has already provided the next bounded task, PM must route that task through the TL/worker flow instead of asking the owner whether to take it.
- If TL's instruction is ambiguous, stale, blocked, or missing, PM must ask TL through the Oysterun session-control route. Do not ask the owner to interpret TL's instruction.
- If workers are idle, unavailable, blocked, or `pane_parse_uncertain`, PM must report that state to TL and ask TL for routing. Do not ask the owner what to do next.
- If a worker report creates a task, route, verification, or evidence-classification decision, PM must ask TL. Do not ask the owner unless TL explicitly requests product-owner input.
- Owner-facing output from this command must be a status relay, deliverable notification, or TL-requested owner-decision reminder. It must not contain open-ended prompts such as "if you want, I can...", "should I...", "do you want me to...", or "what should I do next?"
- A Tier 3 owner escalation is allowed only after TL explicitly requests product-owner input and PM has prepared the required escalation report. Even then, the owner question must be tied to TL's named options, not routine task routing.

## Recent Failure Guards

These guardrails address repeated loop failures by lighter PM models. Apply them before ordinary reasoning.
They are pattern rules, not task-specific rules. Do not key them to a phase ID, task label, route name, or one historical incident.

1. **No raw tmux send to TL.**
   - PM must never send TL messages with raw `tmux send-keys -t <tl_session> ...` commands, including sessions such as `Oysterun`, or any other hand-written tmux command.
   - Every TL send must go through the Oysterun session-control route and `.claude/commands/skills/Oysterun/send_cmd.md`.
   - The only valid shell transport for a TL send is the `send_cmd.md` procedure: `python3 tool_scripts/oysterun_control.py send ...` after `read_status` says ready.
   - If PM is about to run `tmux send-keys` for TL, PM must stop that action and run `send_cmd.md` instead.
   - Before sending to TL, run `.claude/commands/skills/Oysterun/read_status.md`.
   - If PM used raw tmux for TL, classify the tick as command-protocol failure and correct it next tick; do not claim "TL updated" unless the session-control send path confirms delivery.

2. **No "no-change" when a worker completed anything.**
   - If any worker pane contains a newly visible or not-yet-reported completed answer, output path, report path, evidence root, validation summary, final sentinel, or clean prompt after a prior blocked/working state, this is not no-change.
   - PM must report the deliverable or state transition to TL.
   - A capture with a completion phrase, `Output: /path/...`, `Report: /path/...`, `Evidence root: /path/...`, `READY_TASK...`, and a clean prompt must be reported as completion, not "no new worker activity".
   - A deliverable is "reported" only after a TL packet was successfully sent through Oysterun session-control and that packet contained the worker slot plus the deliverable path/report/evidence/sentinel. A raw tmux no-change update does not count. A PM sentence saying "sent TL a no-change update" does not count.
   - If a previous tick misclassified a visible completion as no-change, the next tick must send a correction deliverable packet before any ordinary no-change/status update.

3. **No "all idle" summary without reconciliation.**
   - Before saying all workers are idle, PM must state whether each idle worker is parked by TL, waiting for a TL decision, waiting for a clean-prompt dispatch, or has a completed deliverable that must be reported.
   - "Idle at clean prompt" can be a trigger to dispatch TL-routed work; it is not automatically a no-op.

4. **Violation recovery beats ordinary loop output.**
   - If this tick observes a command-protocol failure, unreported deliverable, stale no-change classification, or owner-provided pane evidence proving those failures, PM must not answer with the normal idle/no-change script.
   - First send or preserve a TL correction packet through `send_cmd.md`.
   - The correction packet must state the violated rule, worker slot/session, completion signal, deliverable paths, recommendation/sentinel, and that the earlier raw/no-change update is invalid.
   - Only after the correction packet is delivered or explicitly deferred by `read_status` may PM give the owner a status summary.

Active worker supervision with structured challenges — the more demanding cousin of `/sleep_to_monitor`. Where sleep-to-monitor asks "is the worker finished?", this command asks "is the worker doing the RIGHT work, the RIGHT way, with EVIDENCE, per the plan — and if something fails, have they collected enough diagnostics for TL to adjudicate instead of giving up?"

Use this when the task is architectural or multi-step, when the worker has historically drifted from plan docs, or when evidence discipline matters. PM does not own final verification; PM keeps workers collecting useful proof and routes that proof to TL for verification/adjudication.

## How to run (critical — this command is tick-based, not a long loop)

This command does ONE tick of harness work per invocation. Use `/loop` to schedule recurring ticks:

```
/loop 5m /loop_harness_worker [args]
```

`/loop 5m` fires this command every 5 minutes. Each firing is a fresh invocation with no state carried over — all context is rebuilt from `config.json`, the plan doc, git log, and the current tmux pane.

Do NOT use inner `sleep` loops inside this command. `/loop` owns the cadence. The command exits cleanly after one tick so the next cron firing can resume.

To stop supervision: `CronDelete <job-id>` (or delete via the `loop` skill's management).

## When to use

Use `/loop_harness_worker` when:
- A non-trivial task is in flight and the plan is architectural (not a one-liner)
- Multi-step or multi-iteration work (spans more than one sub-task)
- The worker has a history of drifting from the plan
- Evidence discipline matters — you need to enforce "exhaust debug tools before giving up" on human-path failures and submit the evidence package to TL
- You want active supervision, not just passive monitoring

Skip this command (use `/sleep_to_monitor` instead) when:
- The task is atomic and well-scoped
- The plan is trivial (single file, single test run)
- The worker has earned autonomy on this kind of work

## Inputs (optional — passed through `/loop`)

- `plan_doc` — absolute path to the authoritative plan the worker must align with. Prefer the plan/proposal path supplied by TL. If omitted, auto-detect from the active worker's `working_dir/prompts/` folder (newest `*plan*.md`) only when that does not conflict with TL's current scope.
- `challenge_depth` — `light` / `medium` / `strict` (default `medium`):
  - `light`: challenge only at task boundaries (when worker reports done or proposes a new approach)
  - `medium`: challenge at task boundaries + probabilistically every ~3rd tick
  - `strict`: challenge every tick
- `focus_area` — narrow the challenge to a specific workstream or deliverable. If omitted, challenge against the whole plan.

## Active worker resolution

Before starting the tick:

- Read `config.json`
- If it has a `workers` array, resolve the active worker from the current bot profile / `FIRST_PROMPT`
  - `.env1`, `.env2`, `.env3`, and similar local profiles should identify workers by configured `name` or `session`
- If no explicit match is available, use `workers[0]`
- If only a legacy `worker` object exists, use that

From the resolved worker, read:
- **session** — the tmux session name
- **send_method** — `two-line` or `enter`
- **working_dir** — used to locate the plan doc and the worker's own `.claude/` tree

## Mandatory communication routes

**Worker tmux communication MUST use `/send_tmux`.** Every harness action that sends text to a worker tmux session — challenge injection, `/compact`, next-task push, evidence question, blocker follow-up, recovery instruction, or TL-routed assignment — MUST execute the worker-send procedure defined in `~/Projects/TmuxAgentManager/.claude/commands/send_tmux.md`.

This means the harness must resolve the target worker, verify the tmux session exists, clear stale input with `C-u`, send via the worker's configured `send_method`, and confirm receipt before treating the message as sent. Do not hand-roll a separate worker-message path, do not skip the receipt check, and do not count text sitting in a prompt as communication.

The full command-doc path is mandatory: `~/Projects/TmuxAgentManager/.claude/commands/send_tmux.md`. Open and follow that file each tick before sending worker-facing text; do not rely on memory of the slash command behavior.

If this tick targets W1/W2/W3 rather than only the active/default worker, apply the same `/send_tmux` protocol to that specific worker's resolved `session` and `send_method`; preserve the worker's original settings.

### Worker send receipt and recovery overlay

When `/loop_harness_worker` sends a worker-facing message, it MUST follow the receipt rules in `~/Projects/TmuxAgentManager/.claude/commands/send_tmux.md`, especially Step 5. This is mandatory because a typed tmux input line is not the same as a submitted message.

**Send timing:**

- For `send_method: two-line`, send the message text first, then wait 3 seconds, then send `C-m`.
- For `send_method: enter`, send the message text first, then wait 3 seconds, then send `Enter`.
- After the submit key, wait 5 seconds and capture the last 30 joined lines to verify receipt.

Example for `two-line`:

```bash
tmux send-keys -t <session> "<message>"
sleep 3
tmux send-keys -t <session> C-m
sleep 5
tmux capture-pane -t <session> -p -J -S -30
```

Use `-J` for receipt checks so long wrapped input lines are joined and a stuck prompt buffer is visible as one typed payload. If the first receipt capture is unclear, escalate to `-S -80` or `-S -100` before changing worker state.

**What "message not sent" means:**

A message is **not sent / not submitted** when the capture shows the message text sitting at the worker input prompt (for example after the Codex `›` prompt), but there is no sign that the agent started processing it. This includes cases where a long assignment text is visible in the prompt, the model/status line is visible, and there is no `Working`, tool call, plan update, response text, or other post-submit activity after the message.

Treat this exact shape as `send_not_submitted_prompt_buffer`, not as `worker_running` and not as `unavailable`:

```text
› Task L: ...
  ... long wrapped assignment text ...
  ... cd /path && codex ...
  ... READY_TASK...
  ... more pasted command text ...
```

This means Codex is alive and the text is sitting in the TUI input buffer. It is a submission/receipt failure. It is not proof that the worker session is unavailable.

Do not over-match old canary/task text in scrollback. If `READY_TASK...`, a task prompt, or any sent text appears in history but is followed by a worker response (for example `• READY_TASK...`, an answer, tool activity, or a fresh idle prompt), then it was submitted. Classify by the current bottom state instead. Visible history is not the prompt buffer.

Do NOT count any of these as sent:

- the message text appears wrapped across the tmux pane but the prompt is still waiting
- the message is concatenated with previous prompt text and no worker response begins
- the pane is idle with the model/status line visible and no new tool/activity markers
- the capture only proves that keys were typed, not that the submit key was accepted
- a shell command, `codex resume`, `READY_TASK`, or canary text is visible after the `›` prompt as typed text rather than as executed output

**Recovery for "message not sent":**

If the message is visible in the prompt but not executing, do not retype the message and do not clear it with `C-u`. Follow `/send_tmux` Step 5 bounded submit recovery exactly:

- Send the configured submit key one additional time, then `sleep 5` and capture.
- If still unsent, send the alternate submit key once (`C-m` vs `Enter`), then `sleep 5` and capture.
- If still unsent, send `Escape` once only to exit a possible stuck TUI mode, then `sleep 2` and capture `-J -S -50`.
- If the worker now shows `Working`, tool activity, a plan update, response text, or a fresh idle prompt after the message, classify by that current bottom state and continue.
- If the message is still sitting in the current prompt after this bounded recovery, classify the tick as `pane_parse_uncertain` with the bottom prompt excerpt and ask TL for recovery direction. Do not keep pressing submit keys blindly.

Do not use `Escape` as an interrupt for active work. It is only allowed in this receipt-recovery path when the message has not started executing.

Only use `C-u` before a fresh new message. Once the intended message is already visible in the prompt, `C-u` would erase the unsent payload and hide the failure instead of fixing it.

Do not mark a worker process-dead `unavailable` on the first sighting while `send_not_submitted_prompt_buffer` is visible. First sighting means the session is alive but the send/submit transport failed. Process-dead `unavailable` requires one of these stronger facts:

- `tmux has-session -t <session>` fails
- the pane is a shell prompt and Codex cannot be started or resumed after the documented recovery command is actually submitted
- a canary or recovery command was submitted and receipt-confirmed, then the worker failed to respond or crashed

If the pane still contains unsent text, the next action is submit/recover that input, not fresh-launch, kill, or unavailable reporting.

**Repeated apparent unsent-buffer self-audit:**

If the same worker appears to remain in `send_not_submitted_prompt_buffer` for two consecutive loop ticks, first assume PM may be misreading scrollback. The goal is to keep workers moving, not to stop routing work because the manager misclassified a pane.

Before reporting a worker as unavailable or stuck, PM must perform a self-audit:

- Capture deeper history with `tmux capture-pane -t <session> -p -J -S -120`.
- Classify only the current bottom prompt block, not old history above it.
- If `READY_TASK...`, a task prompt, or any sent text is followed by `• READY_TASK...`, an answer, tool activity, `Working`, or a fresh idle prompt, the text was submitted. Reclassify the worker as `working`, `idle`, or `finished` according to the current bottom state and continue routing normally.
- If the current bottom prompt truly contains unsent text with no worker response after it, use `/send_tmux` Step 5 bounded submit recovery, then continue from the resulting state.
- If PM still cannot tell after the deeper capture and bounded recovery, classify the tick as `pane_parse_uncertain`, send TL the exact evidence, and ask TL for recovery direction. Do not call the worker stuck and do not suppress future valid TL-routed work merely because old canary text is visible.

Because this command is tick-based, PM may preserve cross-tick evidence to detect PM parsing mistakes. Use manager-local scratch state, not worker project files:

- Read `prompts/_WORKER_PANE_PARSE_STATE.md` if it exists.
- When a worker is classified as `send_not_submitted_prompt_buffer` or `pane_parse_uncertain`, append or update a short entry with timestamp, worker/session, state, whether submit recovery was already tried, and a 1-3 line bottom-prompt excerpt.
- On the next tick, if the same worker/session shows the same apparent state, run the self-audit above before taking any routing decision.
- Do not write this routine parse state to `_REMINDER.md` unless TL asks for owner-visible escalation.

**`pane_parse_uncertain` escalation packet:**

Treat `pane_parse_uncertain` as a careful TL-help request, not as a worker failure. PM must ask TL for help through the Oysterun session-control route and include enough context for TL to either give PM a recovery instruction or directly inspect/debug the tmux pane.

The escalation to TL must include:

- worker slot and tmux session name, for example `W5 / <session>`
- working directory or launch directory if known
- the intended worker message/task that PM was trying to send
- exact tmux commands PM ran for inspection and recovery, including `tmux display-message`, `tmux capture-pane`, submit-key retry, alternate submit-key retry, and whether `Escape` was used
- exact pane metadata from `tmux display-message -p -t <session> 'cmd=#{pane_current_command} dead=#{pane_dead} in_mode=#{pane_in_mode} alt=#{alternate_on} cursor=#{cursor_x},#{cursor_y} size=#{pane_width}x#{pane_height}'`
- bottom pane text from the latest `tmux capture-pane -t <session> -p -J -S -30`
- deeper pane text from `tmux capture-pane -t <session> -p -J -S -120` if the bottom state is still ambiguous
- post-recovery capture snippets after each submit/alternate/Escape attempt
- whether cross-tick scratch state already recorded the same apparent prompt buffer
- the way TL can inspect it directly, for example:
  ```bash
  tmux display-message -p -t <session> 'cmd=#{pane_current_command} dead=#{pane_dead} in_mode=#{pane_in_mode} alt=#{alternate_on} cursor=#{cursor_x},#{cursor_y} size=#{pane_width}x#{pane_height}'
  tmux capture-pane -t <session> -p -J -S -120
  tmux attach -t <session>
  ```

Ask TL explicitly to determine the root cause of the pane parsing / submit transport uncertainty and to provide PM a concrete next action. TL may debug the tmux pane directly, but PM remains the channel that communicates with workers. PM must not bypass TL by asking the owner, must not declare the worker unavailable from `pane_parse_uncertain` alone, and must not keep pressing keys blindly after the bounded recovery.

**TeamLead communication MUST use the Oysterun session-control skill.** Every TL interaction — asking for the next task, reporting deliverables, escalating a decision, or reading TL's response — MUST follow `~/Projects/TmuxAgentManager/.claude/skills/oysterun_session_control.md`.

Use the `team_lead` role binding first and resolve live Oysterun sessions by `session_name`. If the binding is ambiguous or unresolved, list sessions only to diagnose the routing problem, then stop and report a session-binding blocker; do not ask the owner for a task-routing decision. Resolve `TL_WORKINGDIR` from `config.json` at `team.roles.team_lead.working_dir` before composing TL guide references. Do not call `oysterun_control.py` freehand unless you are following that skill and its command docs.

### Required Local Docs To Follow

Before sending or reading anything, PM must locate and follow these exact docs:

- `/send_tmux` / worker send protocol
  - Full path: `~/Projects/TmuxAgentManager/.claude/commands/send_tmux.md`
  - Repo-relative path: `.claude/commands/send_tmux.md`
- Oysterun session-control skill
  - Full path: `~/Projects/TmuxAgentManager/.claude/skills/oysterun_session_control.md`
  - Repo-relative path: `.claude/skills/oysterun_session_control.md`
- `read_response` / TL read protocol
  - Full path: `~/Projects/TmuxAgentManager/.claude/commands/skills/Oysterun/read_response.md`
  - Repo-relative path: `.claude/commands/skills/Oysterun/read_response.md`
- `send_cmd` / TL send protocol
  - Full path: `~/Projects/TmuxAgentManager/.claude/commands/skills/Oysterun/send_cmd.md`
  - Repo-relative path: `.claude/commands/skills/Oysterun/send_cmd.md`
- `list_session` / TL session listing and binding diagnosis
  - Full path: `~/Projects/TmuxAgentManager/.claude/commands/skills/Oysterun/list_session.md`
  - Repo-relative path: `.claude/commands/skills/Oysterun/list_session.md`

Use the skill doc first for routing rules, then the specific Oysterun command doc for the concrete action (`read_response`, `send_cmd`, or `list_session`). Do not skip directly to helper scripts when these docs exist.

## Required reads per tick (manager side)

Each tick re-reads these. Keep the reads small; this is a 5-minute cadence, not unlimited budget:

1. `config.json` — resolve the active worker for this tick
2. Worker's agent configuration (only if TL asks for delivery-path context, or if a worker blocker requires evidence about available instructions; PM does not override TL's dev process):
   - `<working_dir>/CLAUDE.md` (if present)
   - `<working_dir>/AGENTS.md` (if present)
   - `<working_dir>/.claude/CLAUDE.md` (if present)
3. Available worker tooling (only if a blocker/evidence challenge needs it; PM does not attach or manage skill paths unless TL explicitly asks):
   - `<working_dir>/.claude/commands/` — list the slash commands the worker has
   - `<working_dir>/.claude/skills/` — list the skills the worker has
4. Worker cheat sheet at `worker_cheatsheets/<worker_name>_cheatsheet.md` — refresh via `/read_workers_agent_settings` only if missing
5. Plan doc (from `plan_doc` input, TL dispatch, or safe auto-detection). Grep for keywords relevant to the challenge being issued this tick — don't re-read the whole doc every tick
6. `prompts/_WORKER_PANE_PARSE_STATE.md` if it exists — only to avoid repeated PM misclassification of visible scrollback as current prompt state
7. Only if relevant to the current worker activity: recent prompts/ artifacts (handover reports, verification reports, deferral notes)

If the plan doc cannot be located, or auto-detection might select an old plan that conflicts with TL's active scope, ask TL for the authoritative plan/proposal path and stop this tick. Do not guess from newest filename alone.

## Procedure (one tick)

Every tick MUST perform the same four steps in this exact order:

1. **Read TL response** — use the Oysterun `read_response` command for TL first.
   - Full path: `~/Projects/TmuxAgentManager/.claude/commands/skills/Oysterun/read_response.md`
   - Repo-relative path: `.claude/commands/skills/Oysterun/read_response.md`
2. **Check all configured workers** — inspect W1, W2, and W3 progress before deciding what to send.
3. **Send updates/questions to TL** — use the Oysterun `send_cmd` command for TL with the consolidated worker state, deliverables, blockers, and questions.
   - Full path: `~/Projects/TmuxAgentManager/.claude/commands/skills/Oysterun/send_cmd.md`
   - Repo-relative path: `.claude/commands/skills/Oysterun/send_cmd.md`
4. **Send commands to workers** — use `/send_tmux` for worker tmux sessions with TL-routed assignments, evidence questions, or blocker follow-ups.
   - Full path: `~/Projects/TmuxAgentManager/.claude/commands/send_tmux.md`
   - Repo-relative path: `.claude/commands/send_tmux.md`

Do these steps even if one target has no new action. A step with no action should record `no-op` and why.

If the tick has enough context to send a useful TL update or worker instruction, send it in the same loop run. Do not defer just because the tick already performed another step. If required information is not ready, collect and summarize the information available, record what is missing, and carry that packet into the next round instead of guessing.

### Step 0: Read TL response first

Before checking workers, read TL's latest response through `~/Projects/TmuxAgentManager/.claude/skills/oysterun_session_control.md` and the Oysterun `read_response` command.

Capture:

- new TL directives
- worker-specific assignments
- TL questions for workers
- TL requests for evidence or owner input
- TL "stand by" or "stop routing" instructions

Interpret TL transcript rows by the latest non-internal assistant/user message. Do not classify TL as "still thinking" from `assistant (thinking)` rows; those are internal reasoning, not formal directives. If the latest formal TL message says to stop periodic idle ticks, do not send idle heartbeat/status updates or ask for another directive. Exit the tick unless the owner/TL sends a new request, a worker state changes, a worker leaves standby unexpectedly, or an operational failure appears.

If TL cannot be read because the `team_lead` role is unresolved, list sessions only to diagnose the binding problem, stop worker-routing decisions for this tick, and report a session-binding blocker. Do not guess a TL session.

### Step 1: Check progress for W1/W2/W3

Resolve worker slots from `config.json`:

- W1 = `workers[0]`
- W2 = `workers[1]`, if present
- W3 = `workers[2]`, if present

For each configured worker, run a cheap-first pane state check:

```bash
tmux display-message -p -t <session> 'cmd=#{pane_current_command} dead=#{pane_dead} in_mode=#{pane_in_mode} alt=#{alternate_on} cursor=#{cursor_x},#{cursor_y} size=#{pane_width}x#{pane_height}'
tmux capture-pane -t <session> -p -J -S -30
```

### Worker pane state classifier

Use this deterministic classifier before reasoning about the worker state. This exists because light manager models have previously misread a Codex tmux pane as "still active" when it was already idle.

Important rule: `cmd=node dead=0` does **not** mean the worker is working. Codex runs as a long-lived `node` process while idle. Treat `cmd=node dead=0` only as "the Codex process is alive".

**Completed-transcript bottom-state rule:**

Do not treat a completed worker transcript as active work just because it is still visible at the bottom of tmux. A worker can be finished/idle even when the latest visible lines are the final answer rather than the prompt.

This rule must be version-tolerant. Do not depend on one Codex UI string, model label, separator style, or exact sentinel name. Classify by current-state invariants:

- current input buffer exists and has not been submitted -> `send_not_submitted_prompt_buffer`
- active generation/tool execution is still progressing -> `worker_running`
- a completed answer/deliverable is stable and no active marker follows it -> `finished` / `idle`
- a clean prompt is visible with no unsent payload -> `worker_idle_prompt_visible`
- auth/session/setup prompt or shell prompt is visible -> classify that blocker directly, not as working

Classify as `worker_idle_prompt_visible` / `finished` when the current bottom block contains a completed-task shape such as:

```text
• Completed ...

  Output:
  /path/to/report.md

  Validation performed:
  ...

  Boundary confirmed: ...

  READY_TASK_<id>

─ Worked for 1m 54s ─
```

This shape means the visible text is the last completed response, not ongoing work, when all are true:

- the bottom block includes an explicit completion marker such as `Completed`, `READY_TASK...`, `done`, `finished`, `Output:`, or a final deliverable path
- the block is followed by a Codex completion/status separator such as `Worked for ...`, or it remains unchanged after a short recapture
- there is no later `Working`, unfinished tool call, streaming command, mid-sentence answer, prompt-buffer assignment text after `›`, or explicit question asking for input

If the prompt is not visible but the completed-transcript shape is visible, run one short confirmation capture before classifying:

```bash
sleep 5
tmux capture-pane -t <session> -p -J -S -40
```

If the bottom completed block is unchanged and no active marker appears, classify the worker as `finished` / `idle` and include the deliverable in the TL packet. Do not keep reporting `working` across ticks from the same completed transcript.

General completed-answer signals include any stable combination of:

- final deliverable path, output path, report path, artifact root, or evidence root
- explicit completion wording such as `completed`, `done`, `finished`, `ready`, `delivered`, `output`, `validation`, `boundary`, `summary`, or an equivalent localized phrase
- test/validation/hygiene summary followed by no further streaming activity
- final sentinel or canary reply, regardless of exact spelling
- elapsed-time/status separator, regardless of exact visual style

These signals are examples, not required exact strings. If they are stable and no active marker follows them, they describe completed history. They do not make the worker `working`.

Classify the pane using the bottom of `tmux capture-pane -p -J -S -30`:

1. `send_not_submitted_prompt_buffer`
   - The bottom of the capture shows the Codex input prompt `›` followed by task text, shell commands, `codex resume`, canary text such as `READY_TASK`, or other assignment content.
   - There is no `Working`, tool call, answer text, or plan update after that text.
   - First sighting means the message is typed but not submitted. The session is alive, but the send transport failed.
   - Apply the `/send_tmux` Step 5 bounded submit recovery, unless TL told PM not to retry.
   - If this appears for a second consecutive tick, run the repeated apparent unsent-buffer self-audit above before reporting the state. Do not stop routing from this classification alone.
2. `worker_idle_prompt_visible` / `finished`
   - The bottom of the capture shows a Codex prompt such as:
     ```text
     › Explain this codebase

       gpt-5.5 xhigh · ~/Projects/...
   ```
   - This means the worker is idle and ready for the next instruction.
   - A summary immediately above the prompt is the worker's last completed response, not active work.
   - A completed transcript ending in `READY_TASK...` and `Worked for ...` is also finished/idle even if the input prompt is not captured in the small slice.
   - If TL has already routed a worker-facing task for this worker, `worker_idle_prompt_visible` must not persist across the next tick as a no-op. PM must send the pending task through `/send_tmux`.
   - If the idle prompt contains stale, wrong, or corrupted typed text that PM does not intend to submit, send `Escape` once to remove that prompt buffer, capture again, then send the correct TL-routed task through `/send_tmux`.
   - If PM cannot tell whether the visible prompt text is only the Codex placeholder or a real unsent payload, classify as `pane_parse_uncertain` and ask TL with the escalation packet instead of leaving the worker idle.
3. `worker_running`
   - No idle prompt is visible, and the bottom shows active generation or tool activity such as `Working`, a command still streaming, an unfinished answer, or a tool section that has not returned to the prompt.
4. `ambiguous`
   - The capture ends mid-sentence, mid-command, or before the status line/prompt can be seen.
   - Escalate capture depth to `tmux capture-pane -t <session> -p -J -S -100`.
   - If still ambiguous, wait one tick and compare whether the bottom lines changed. Do not report "still active" from metadata alone.
5. `shell_prompt`
   - A shell prompt is visible instead of the Codex prompt. Follow session recovery rules; do not treat it as a completed worker answer.

Never classify a worker as `working` solely because:

- metadata says `cmd=node`
- metadata says `dead=0`
- the latest visible summary says files were updated
- the capture includes recent `Ran`, `Edited`, or `Explored` blocks
- the capture shows a stable completed answer with `Output:`, validation bullets, `READY_TASK...`, or `Worked for ...`
- the pane contains a long task prompt after `›`; that is an unsent input buffer until post-submit activity appears

Those are history. The state is determined by the current bottom prompt / working marker.

Classify each worker into: `working`, `finished`, `blocked`, `idle`, `compacting`, `context_low`, `session_dead`, `send_not_submitted`, `pane_parse_uncertain`.

For each worker, collect a compact status packet:

- worker name and slot
- current state
- current task, if visible
- new deliverables, report paths, commit hashes, or evidence paths
- blocker or missing info
- whether TL has already supplied a next directive
- whether a worker message is ready for this tick or must wait for more info

### TL directive reconciliation rule

After reading TL's latest directive and checking all workers, PM must reconcile the directive against the current pane state before reporting to TL or the owner.

For each worker, record:

- TL expected state or instruction, for example `continue task`, `park`, `standby`, `dispatch when clean prompt`, `do not resume stale task`, `report when delivered`
- current observed pane state
- whether the observed state satisfies, contradicts, or triggers the TL instruction
- resulting action: report deliverable, dispatch ready task, keep parked, ask TL, or classify blocker

Do not send a "no-change" TL update if any of these happened:

- a worker moved from working to completed/idle
- a worker delivered a path, report, evidence root, or final sentinel
- a worker moved from auth/session blocked to clean prompt
- a TL conditional became true, such as "when clean prompt, dispatch X"
- a worker that TL said should continue now has a completed transcript
- a worker is idle while TL has already supplied a worker-facing next task

In those cases PM must report the transition and either dispatch the TL-routed task in the same tick or ask TL for the next routing decision. A stale instruction like "continue task X" is not current truth after the pane shows task X completed; the current truth is "task X delivered and worker is idle".

### Step 2: Send consolidated packet to TL

After checking all workers, send TL one consolidated update through the Oysterun `send_cmd` command when there is anything TL should know or decide.

Before sending, run the Oysterun `read_status` command for the same TL target:

- Full path: `~/Projects/TmuxAgentManager/.claude/commands/skills/Oysterun/read_status.md`
- Repo-relative path: `.claude/commands/skills/Oysterun/read_status.md`

Only send the TL packet in this tick if TL is idle/standby:

- `Ready to send: yes`
- `delivery.state = ready`
- `queued_count = 0`
- `active_message_id = null`
- `active_message_state = null`
- no queued message exists
- no cancelable message exists

If TL is still responding, tool-calling, thinking, has an active message, has a queued/cancelable message, or the status check is not clearly ready, do not send another TL command in this tick. Record `TL send_cmd: deferred - TL not ready` with the status fields, preserve the intended TL packet for the next tick, and check again then.

Include:

- TL response read at the start of the tick and how it was applied
- W1/W2/W3 state summary
- new deliverables or evidence packets
- idle workers needing next directives
- blockers, missing info, or session issues
- worker messages you plan to send in this same tick, if already clear
- information that is not ready and will be collected next round

If a worker pane shows completion text, the TL packet must quote/summarize the completion instead of sending no-change. Minimum deliverable packet:

- worker slot/session
- task name as shown by the worker, if visible
- output/report/evidence paths
- validation summary
- boundary confirmation
- worker final recommendation or sentinel, if present
- current pane state after completion

Completion signal patterns that require a TL deliverable packet:

- `<task-or-slice> is complete.`
- `<task-or-slice> done.`
- `<task-or-slice> finished.`
- `Output: /path/to/report_or_bundle`
- `Report: /path/to/report`
- `Evidence root: /path/to/evidence_root`
- `Validation performed:`
- `Verification performed:`
- `Exact recommendation: ...`
- `Final recommendation: ...`
- `READY_TASK...`
- `Worked for ...` followed by a clean prompt

These are generic patterns. Apply them to any worker task, route, phase, project, or report name. Do not classify those examples as `all idle`, `state unchanged`, or `no new worker activity`. A worker can be idle now and still have a newly completed deliverable that TL must see.

Reported/not-reported rule:

- A deliverable is reported only when a TL packet was sent through `.claude/commands/skills/Oysterun/send_cmd.md` / Oysterun session-control and the packet included that worker's deliverable path/report/evidence/sentinel.
- `tmux send-keys` to a TL pane is never a valid TL packet.
- A raw tmux no-change update does not clear a visible completion signal.
- If a visible completion signal was followed by a raw/no-change TL update in the same or previous tick, classify the next action as `correction_deliverable_packet_required`, not `no-op`.
- If unsure whether a deliverable was reported, treat it as not reported and include it in the next TL packet.

No-op is allowed only when all of the following are true:

- no worker has a newly visible or not-yet-reported deliverable
- no worker changed state since the previous tick
- no TL conditional trigger has become true
- no completed transcript or `READY_TASK...` sentinel is waiting to be reported
- no pending worker dispatch exists

If there is no new TL-directed information after those checks, record `TL send_cmd: no-op` in the tick summary.

### Step 3: Send commands to workers

After the TL packet is sent, send worker-facing messages through `/send_tmux`.

Do not suppress worker-facing messages merely because old canary/task text appears in scrollback. If the current bottom state is an idle prompt and TL has routed work to that worker, send the work through `/send_tmux` normally. If the state is `pane_parse_uncertain`, ask TL for recovery direction with the exact pane evidence instead of declaring the worker stuck.

Allowed worker sends in the same tick:

- TL-routed next-task assignments
- evidence questions needed for TL
- blocker follow-ups
- `/compact` when context is low
- resume/recovery instructions for the configured worker session

If enough context exists to assign or ask the worker now, send the worker message in this same loop run. If context is incomplete, do not invent the instruction; write down what is missing and collect it in the next round.

Pick worker challenges based on the captured pane:

- Editing product code → challenges 1, 2, 5 (plan-alignment, reference-implementation, lesson-retention)
- Running tests or reporting gate results → challenge 4 (evidence-package quality)
- About to invent new code → challenges 3, 6 (tool/skill awareness, grep-before-invent)
- Verification failed or "can't verify" reported → **challenge 7 mandatory** (verification-blocker evidence ladder)

Use at most one message per worker per tick unless TL explicitly asked for multiple separate dispatches. Do not wait for worker answers inside this tick — the next `/loop` firing will read the answer from the pane and continue.

### Step 4: Exit cleanly

- Record what was observed and what was sent in a brief user-facing summary.
- The summary must list the four steps in order: `TL read_response`, `worker progress checks`, `TL send_cmd`, `worker sends`.
- Flag any escalation triggers for TL (see "Escalation" below).
- If the tick surfaced anything that should outlive this tick — a blocker, a TL-requested owner decision, or a follow-up reminder — append an entry to `prompts/_REMINDER.md` in this repo (see "Reminder ledger" below).
- Exit. `/loop` will re-fire in 5 minutes.

## The 7 challenges

### Challenge 1 — Plan alignment

When the worker claims a sub-task done or proposes an approach:
- "Which section of `<plan_doc>` does this map to? Cite the exact heading or line."
- "If this diverges from the plan, what's the business justification? Does the plan have a whitelist entry for this category of deviation?"
- "Is this a NEW customization not listed in the plan? If so, stop, add it to the plan first."

### Challenge 2 — Reference implementation

When the worker is refactoring against a reference codebase (e.g. Telegram-iOS, another upstream):
- "What did the real upstream source do for this? Cite the exact file:line from the local reference checkout."
- "Are you synthesizing a simplified variant of upstream behavior? If yes — stop. Copy-first is the rule unless the plan explicitly whitelists a simplification."
- "Does upstream have a runtime feature (gesture, event, animation, ordering) that your implementation silently drops? If unsure, don't delete it; let it render default-empty."

### Challenge 3 — Tool and skill awareness

Before the worker invents new code or manually reimplements something:
- "Check `<working_dir>/.claude/commands/` — is there already a slash command for this?"
- "Check `<working_dir>/.claude/skills/` — is there a skill that covers this workflow?"
- "Check the worker cheat sheet — are there existing project-specific helpers for this?"
- "If a command or skill exists, use it. Don't reimplement."

Especially important when the worker is about to run ad-hoc shell commands (simctl, xcrun, curl, sqlite3) that might already be wrapped in existing tooling.

### Challenge 4 — Evidence-package quality

When the worker reports "done" or "green":
- "What exact evidence should TL review? Include gate output, commit hashes, test result excerpts, screenshot/recording paths, logs, `.xcresult` bundles, and report paths."
- "Which plan/proposal section and acceptance criteria does this evidence map to?"
- "What evidence is still missing, and is the gap a product issue, harness issue, environment issue, or unresolved blocker?"
- Never accept "I think it's fine" or "it looks right" as evidence.
- PM does **not** decide pass/fail. PM ensures the worker submits a complete evidence package to TL, and TL verifies/adjudicates.

### Challenge 5 — Lesson retention (anti-pattern guard)

From the plan doc's lessons section, spot-check before each major worker action:
- Is the worker about to create a custom-owned wrapper around a reference-provided storage primitive?
- Is the worker about to declare a deliverable done while reconciliation bugs are open?
- Is the worker about to build a stub that pretends to be a real upstream module?
- Is the worker about to skip required evidence collection or omit a verification gap from the TL packet?

If any answer is yes, interrupt and redirect.

### Challenge 6 — Grep before invent

Reflexive rule for any new code:
- "Before you write this new file/function, did you grep the repo for existing infrastructure that does the same thing?"
- "Before you invent an accessibility identifier or selector, did you grep for the existing identifier pattern in the codebase?"
- "Before you write a helper, did you check if one exists in a nearby file?"

### Challenge 7 — Verification-blocker evidence ladder

**The most important discipline. When the worker reports a verification failure (XCUITest, Maestro, simctl-based, or manual), walk them through this ladder before accepting "verification failed" as terminal. PM's job is to force useful evidence collection; TL owns the final verification judgment.**

Because this command is tick-based, challenge 7 typically spans multiple ticks — one ladder step per tick. Do NOT cram the whole ladder into one message. Each tick: check if the last step has been attempted and answered, then send the next step.

**7a — Plan-alignment of the implementation under verification**
- "Does the implementation under test actually match the plan section it claims to? Cite the plan line."
- "If implementation and plan diverge, the verification failure may be a real product regression exposing the divergence — not a harness issue."

**7b — Component identity / accessibility-ID re-check**
- "Did you re-grep `.accessibilityIdentifier` in the current source tree? Sometimes the component was renamed or moved to a sibling file."
- "Did you dump the live UI hierarchy (`xcrun simctl ui ... accessibility-audit`, XCUITest `app.debugDescription`, or Maestro `hierarchy`) to see what IDs the running app exposes right now?"
- "Is the test using a stale hardcoded ID that no longer exists in the committed source?"

**7c — Simulator restart ladder**
- "Did you `xcrun simctl shutdown <UDID>` then `xcrun simctl boot <UDID>`? Simulators accumulate stale state."
- "Did you relaunch the Simulator.app (`killall Simulator && open -a Simulator`)?"
- "For persistent failures: `xcrun simctl erase <UDID>` then boot. Reserve this — it wipes installed app state."

**7d — Test framework restart / reinstall**
- "Did you rebuild the test target clean? `xcodebuild clean test ...`, not `xcodebuild test ...`."
- "Did you uninstall and reinstall the app under test (`xcrun simctl uninstall <UDID> <bundle-id>` then `install`)? Codesigning and entitlements sometimes go stale."
- "If using Maestro, did you kill the Maestro daemon and restart?"
- "If the test target was regenerated, did you re-run xcodegen and rebuild? Old DerivedData can shadow fresh sources."

**7e — Worker-specific tools from agent files**
- "Is there a `/restart_testN_fullstack` command in `<working_dir>/.claude/commands/` for the port in use?"
- "Is there a `human-path-verification` skill with debug playbooks in `<working_dir>/.claude/skills/`?"
- "Does the worker cheat sheet list a recovery sequence for this failure class?"
- Use them. Do NOT let the worker re-implement recovery logic that's already wrapped.

**7f — Cross-reference lesson files**
- "Does any `*deferral*.md`, `*post-mortem*.md`, `*handover*.md` in the project's `prompts/` folder describe this same failure class with a known workaround?"
- "Was this failure already classified as a harness issue (not product) in a previous session?"

**7g — Binary isolation — harness vs product**
- "If the failure reproduces when manually operating the simulator with the same inputs, it's a product bug. If it only shows under the test harness, it's a harness issue."
- "Can you extract a single XCTest attachment or simctl screenshot at the exact failure point to visually confirm whether the UI rendered correctly?"

**Exit conditions for challenge 7:**

Only after all applicable 7a-7g steps have been attempted (across ticks) with documented results may the worker:
- Send TL a named option set or blocker packet (for example, "simulator rebuild OR switch simulator OR abandon this test")
- Mark the verification as deferred for TL review, and only with an explicit deferral note that cites which challenges were attempted
- Stop the test run, and only with a specific blocker description (not a vague "can't verify")

## Escalation to TL

Escalate when:
- Worker repeatedly resists the plan (3+ drift attempts on the same sub-task, tracked via recent commits or pane history)
- Worker cites a plan gap the plan doesn't answer
- Worker hits a hard architectural blocker (stub-vs-real API mismatch, missing extraction dependency, etc.)
- A known anti-pattern is about to be committed despite redirect
- Challenge 7 ladder is fully exhausted and verification still fails

Never escalate without:
- Specific citations (file:line, commit hash, test output excerpt)
- A named option set (A / B / C, not "what should we do")
- The manager's own recommendation with reasoning

Route this escalation to TL first. The owner only receives a decision request if TL explicitly asks for product-owner input; otherwise the owner receives status summaries and major deliverable notifications only.

## Harness philosophy — keep the worker moving

**Default: harness the worker through ALL scoped work in the plan. Do NOT stop the loop until either (a) every required deliverable is genuinely complete with TL-accepted evidence, or (b) the user explicitly stops.** Multi-step work can take many hours — the harness only earns its keep by sustaining the worker through all of it without constant user babysitting. Heartbeat-only ticks where the worker holds idle and the manager just pings for status are NOT the harness — they are failure.

### Three-tier decision protocol

When a tick surfaces something that *would normally need approval*, classify into one of three tiers and act accordingly:

**Tier 1 — Plan-aligned auto-approve (push + reminder)**

- The proposed action is clearly aligned with the agreed plan / direction doc / spirit report.
- The "approval" is nominal — there's only one reasonable answer per the plan.
- Examples: pushing the next deliverable in a defined task sequence, applying a whitelist entry that follows the established pattern, picking between two equivalent plan-compliant options.
- → If this is within TL's existing dispatch, push the worker forward and write a `_REMINDER.md` entry noting the auto-decision and why. If it crosses into a new task group, ask TL first.

**Tier 2 — Spirit-guided decision (decide + reminder)**

- A judgment call where the plan doesn't explicitly answer but the spirit report / target / direction doc gives enough framing to decide.
- Examples: choosing between PRUNEABLE vs RUNTIME-CRITICAL when evidence supports both; picking which sub-deliverable to start with when ordering isn't strict; resolving a minor scope ambiguity that doesn't change architectural direction.
- → Decide only within TL's existing dispatch based on spirit/target, push the worker forward, and write a `_REMINDER.md` entry explaining the decision and the spirit reasoning. If uncertain, ask TL.

**Tier 3 — Hard conflict / hard blocker (ask TL)**

- A genuine conflict where the plan's spirit doesn't resolve it, OR the worker is physically blocked from proceeding (missing access, missing dependency, ambiguous product requirement, architecturally divergent paths with different long-term implications).
- Examples: choosing a UX behavior the plan didn't anticipate; product feature decision; environment/infra access the worker can't get; two architecturally different paths each with non-trivial consequences.
- → Halt the worker and ask TL with a named option set. Produce an owner-facing **Tier 3 escalation report** only if TL explicitly requests product-owner input.

### Tier 3 owner escalation report — required format

Whenever TL explicitly requests owner product-owner input, the manager MUST produce a proper escalation report file (not just a `_REMINDER.md` entry). The file lets the owner open one doc and see everything needed to decide.

**File location:** `~/Projects/TmuxAgentManager/prompts/YYYYMMDD_N_escalation_<feature-slug>.md` (where `N` is sequential for the day and `<feature-slug>` is 2–4 words identifying the feature, e.g. `role_design`, `approval_authorship`, `composer_cutover`).

**Language:** 繁體中文.

**Writing style — LAYMAN-FRIENDLY (critical):**

the owner does NOT read code. He makes business/architecture decisions. The report must:
- Explain in plain 繁體中文 what the decision REALLY means — no file:line citations, no code paths
- Describe Pros/Cons in business/architectural logic terms, not code locations
- Include "what-if" scenarios: "如果選 A 會怎樣？選簡單方案有什麼副作用？未來會解決嗎？"
- Explain "選這個不代表什麼" to prevent misunderstandings
- Reference a local layman-friendly escalation-report template if one exists; otherwise follow the required sections below.

**Worker investigation is MANDATORY:**

Before writing ANY escalation report, the manager MUST:
1. Send the worker challenging what-if questions to investigate (e.g. "如果選 A，具體會發生什麼？如果選更簡單的方案，副作用是什麼？未來能解決嗎？")
2. Wait for the worker's evidence-based response
3. Synthesize the worker's technical findings into layman-friendly language for the owner
4. The worker writes the deep investigation; the manager translates into decision-maker language

**Required sections:**

1. **這個決策到底在決定什麼** — 用白話解釋這個決策的本質，不是技術細節。the owner 需要理解為什麼這件事重要、不決定會怎樣。
2. **現在的實際狀態** — 用白話描述目前系統怎麼運作，不需要 code path，只需要邏輯流程。
3. **每個選項的白話說明** — 每個選項需要：
   - **這個選項真正的意思** — 一段白話，不是技術描述
   - **優點** — 用商業/架構邏輯說明，不是 code location
   - **缺點** — 同上
   - **選這個不代表什麼** — 防止誤解
   - **如果選了，後面會怎樣** — what-if scenario
4. **Manager 的推薦** — 推薦哪個選項 + 為什麼（用白話邏輯，不是 code evidence）
5. **相關文件路徑** — 把所有相關文件的絕對路徑列在最後（方便需要 deep-dive 時參考），但報告本文不應該依賴這些路徑才能理解
6. **下一步** — 選了之後 manager 會做什麼

**Linking discipline:**

- The `_REMINDER.md` entry MUST include the absolute path to the escalation report.
- The Telegram summary to the owner MUST point to the escalation report path and NOT duplicate the full report content (keep Telegram message concise).
- The escalation report itself MUST include its own path at the top of the file (first line after the title) so anyone reading offline knows where they are.

**Discipline:**

- No code changes. No worker-project file edits. This is a manager-side deliverable.
- Commit-before-task rule applies only to tracked manager-repo changes outside local-only `prompts/`. If the only pending files are under `prompts/`, do not create a checkpoint commit.
- Escalation reports under `prompts/` are local-only manager artifacts. Never stage, commit, or push them.
- Pros/cons must use business/architectural logic, NOT code citations. No file:line in the report body. Evidence paths go in the reference section at the end.

### Loop continuation rule

Do NOT stop the cron. Keep firing until:

- Every scoped deliverable in the plan is genuinely done (every deliverable + TL-accepted evidence complete), AND a final `_REMINDER.md` entry summarizes "all work done, evidence cited, recommend stop", OR
- The user explicitly says stop.

### Practical examples

- Worker delivered one planned deliverable. TL's dispatch defines another deliverable as next. → Tier 1: push the next deliverable immediately. Write reminder noting the auto-push.
- Worker delivered the current task group completely. Ask TL whether the next task group is authorized by the proposal/guide. If TL dispatches it, push the worker; if TL says a real gate is pending, hold and report the active gate.
- Worker hits a small ambiguity ("should I bisect attribute foo or bar first?"). Spirit report says "stable chat flow first" → bisect the one that affects chat flow first. → Tier 2: decide + push + reminder.
- Worker hits a real architectural fork ("AccountContext: real protocol implementation vs facade pattern, different long-term cost"). → Tier 3: ask TL with named options. Owner input happens only if TL requests it.

### What NOT to do

- Do NOT pause the loop because "the owner might want to review first" — ask TL for the next directive. Owner review items are reminders, not blockers, unless TL explicitly marks them as blocking product-owner decisions.
- Do NOT recommend loop stop after each task group completion — the harness's job is to drive the whole scoped plan, not just one deliverable.

## Reminder ledger (`prompts/_REMINDER.md`)

Whenever a tick surfaces something important that should outlive this tick — a hard blocker, a TL-requested owner decision, or a follow-up reminder — append an entry to `prompts/_REMINDER.md` in this manager repo (TmuxAgentManager root, NOT the worker's project). The file accumulates across the session and serves as the user's review queue when they next sit down. `_REMINDER.md` is local-only scratch/report state and must never be staged, committed, or pushed.

**語言：繁體中文。** 所有 _REMINDER.md 條目必須用繁體中文撰寫。

Each entry must include:

- **時間** — 記錄時間 (e.g. `2026-04-17 14:32`)
- **類型** — `阻塞中`, `需要決策`, `提醒`
- **相關文件** — 報告路徑、commit hash 等可直接打開的參考資料
- **白話說明** — 用白話解釋問題是什麼、為什麼重要、TL 是否已要求 owner 做 product-owner 決策
- **建議下一步** — manager 的建議
- **`需要決策` 條目必須附上對應的 Tier 3 報告絕對路徑**

Append-only. Never overwrite or delete prior entries.

When to write:

- A challenge from the 7 challenges surfaced a TL-requested owner decision (escalation threshold reached).
- A repeating issue that the user should know about even if not blocking right now (e.g. "context low for the 3rd tick in a row, worker may run out before the next deliverable").
- A surprise from the worker that contradicts an assumption in the plan doc.
- A side-effect from a directive that the user might want to revisit later (e.g. "redirected the worker per architecture switch; original Wave 0 commits remain in branch as exploratory — user may want to clean these up").

格式範例：

```
## 2026-04-17 14:32 — 阻塞中
相關文件：/Users/.../prompts/<date>_escalation_<topic>.md
問題：TL 明確要求 owner 針對一個產品/架構問題做 product-owner 決策，所有 worker 閒置中。幾個選項需要 owner 拍板。
建議下一步：請閱讀報告後回覆 A/B/C。Manager 推薦 Option A（最小擾動、符合既定順序）。
```

Do NOT write to `_REMINDER.md` for routine tick events (worker still working, normal commits landing, scheduled `/compact`s). Reserve it for things the user genuinely needs to see when they review later — quality over quantity.

**EXCEPTION — TL-requested owner decision idle reminder (每個 tick 都要提醒):**

When ALL workers are idle because TL explicitly requested an owner product decision, each tick MUST output a short reminder to the owner in the user-facing summary:

```
⏳ 所有 worker 閒置中，等待你的決策。
報告路徑：<absolute path to the escalation report>
推薦：<one-line recommendation>
回覆 A/B/C 即可解鎖下一步。
```

This is NOT written to `_REMINDER.md` — it is the tick's user-facing output text. The goal is to nudge the owner every tick until he decides.

## Parallel development routing rule

Do not authorize parallel code development yourself. Ask TL. If the TL guide or requirements proposal requires owner permission for a parallel-code boundary, TL is responsible for requesting that product-owner input.

## Exit signals (stop the `/loop`)

Recommend to the owner that the `/loop` be stopped (via `CronDelete`) when:
- TL reports the worker task complete with accepted evidence, or the worker evidence packet has been delivered to TL and TL explicitly says no further worker action is needed
- the owner explicitly stops the command
- A genuine blocker surfaces and TL explicitly requests owner product-owner input
- Plan doc is missing or unreadable (on first tick only)

Do NOT auto-delete the cron. Surface the recommendation and let the owner confirm.

## Hard rules (non-negotiable)

- **One tick per firing.** Do not `sleep` inside the command to extend the tick. `/loop` owns the cadence.
- **Never send C-c** to the worker. Use `C-u` to clear stale input, `Escape` to gently interrupt.
- **Never skip the required reads (that tick's subset).** If the worker cheat sheet is missing and a challenge requires it, run `/read_workers_agent_settings` first.
- **Never accept vague "done" reports** — demand an evidence packet for TL (commit hash, gate output excerpt, file:line citations, screenshot/recording paths, logs, and report paths as applicable).
- **Never synthesize answers on behalf of the worker.** If the worker can't answer a challenge, they need to research it, not have the manager write it for them.
- **Never modify the plan doc during the harness loop.** Plan changes go back to TL first; owner input happens only if TL requests product-owner judgment.
- **Never let the worker give up on verification without walking challenge 7.** The full evidence ladder (7a through 7g applicable steps) must be exhausted and submitted to TL, even if it takes many ticks.
- **At most one challenge/message per worker per tick** unless TL explicitly asks for multiple dispatches. The loop may still read TL, check all workers, send one TL packet, and send ready worker messages in the same tick.

## Optional output artifact

the owner can optionally request a rolling session summary. If enabled, each tick appends to `prompts/<date>_harness_session_summary.md` (in the manager repo) with:
- Tick timestamp
- Worker state classification
- Action taken (challenge sent, push, `/compact`, no-op)
- Any drift caught and redirected
- Commit hashes observed this tick
- This summary file is local-only scratch/report state and must never be staged, committed, or pushed

## Team Lead Guide

Monitor all workers:

- W1: `workers[0]` from `config.json`
- W2: `workers[1]` from `config.json`, if present
- W3: `workers[2]` from `config.json`, if present

### Core Principle — TL Is The Authority, Not the owner

**Never ask the owner for the next step.** All task routing, prioritization, and next-step decisions go to TL. the owner only sees Manager's summary reports. Manager's job is to keep workers fed with TL-dispatched work and keep TL fed with worker deliverables. No more "awaiting the owner decision" style pauses. If uncertain, ask TL.

### TL Response Guide Reference

Every message to TL must start with `[PM -> TL]` and include this line immediately after:

> TL, please respond per your maintained guide at `{TL_WORKINGDIR}/.teamlead/_TEAMLEAD_GUIDE.md`.
> If for any reason you decide to stop working, please read `{TL_WORKINGDIR}/.teamlead/_STOP_ROUTING_RULE.md` to confirm all stop-routing rules are applied correctly.

This keeps TL anchored to their own written response rules, including the 3.6 decision proof-reading rule, dispatch structure requirements, and verdict discipline. Before sending the message, replace `{TL_WORKINGDIR}` with the `team_lead` role's `working_dir` from `config.json`; if that field is missing, stop and fix `config.json` instead of hardcoding a project path. Place these lines immediately after the `[PM -> TL]` prefix so they are unmissable.

### Rules This Tick

#### 1. Fixed Tick Order

Every loop firing must execute these commands/actions in order:

1. Read TL through Oysterun `read_response`.
   - Full path: `~/Projects/TmuxAgentManager/.claude/commands/skills/Oysterun/read_response.md`
   - Repo-relative path: `.claude/commands/skills/Oysterun/read_response.md`
2. Check W1/W2/W3 progress with cheap-first tmux state checks.
3. Send one consolidated update/question packet to TL through Oysterun `send_cmd`, if there is anything TL should know or decide.
   - Full path: `~/Projects/TmuxAgentManager/.claude/commands/skills/Oysterun/send_cmd.md`
   - Repo-relative path: `.claude/commands/skills/Oysterun/send_cmd.md`
4. Send ready worker instructions through `/send_tmux`.
   - Full path: `~/Projects/TmuxAgentManager/.claude/commands/send_tmux.md`
   - Repo-relative path: `.claude/commands/send_tmux.md`

If enough context exists to assign work or ask a useful question, send the TL or worker message in the same loop run. If required information is not ready, collect the partial facts, explicitly mark what is missing, and carry that packet into the next round.

#### 2. Worker Idle Or Finished: Include In TL Packet

- If any worker has completed its current task, or is idle with nothing queued, include that worker in the same tick's TL packet.
- Include the worker's just-completed deliverable, such as report paths, commit hashes, and key findings.
- If the worker is idle, include its current idle reason and what it is standing by for.
- Do not leave a finished or idle worker sitting without either an assigned next task from TL, a same-tick worker dispatch, or an explicit TL "stand by" directive.
- Even if a decision seems like it needs product-owner input, ask TL first. TL can translate if the owner's input is actually required.

#### 3. Task Done: Report To TL Every Time

When any worker reports task completion or delivers new artifacts, send TL a consolidated deliverables update within the same tick. Include:

- Report paths, such as `implementation_report.md`, `verification_report.md`, investigation reports, and related artifacts.
- Code update summary, with commit hashes and one-line descriptions.
- Implementation report path, if applicable.
- Verification report path, if applicable.
- Evidence paths, such as screenshots, `.xcresult` bundles, and logs.
- Worker state transition for this tick.

Structure this per worker with a separate section for each. Send one deliverables snapshot per tick, not a running diff. If there are no new deliverables this tick, skip this step.

#### 4. Do Not Escalate To the owner For Task Decisions

Override the old 3-tier escalation behavior for task, route, and architecture questions: those all go to TL first. the owner only gets:

- Status summaries for what workers are doing and what is in flight.
- Major deliverable notifications, such as "worker X just delivered report at `<path>`".
- Tier 3 escalation reports only when TL explicitly requests the owner's product-owner input.

If Manager is tempted to write "awaiting the owner decision on X", ask TL about X first. If TL says "this needs the owner", then produce the Tier 3 report. Not before.

Every worker-facing message must start with `[PM -> worker]`.

#### 5. Standard Harness Discipline

- Cheap-first pane state checks.
- Apply the 7 challenges per worker state.
- Tier 1: auto-approve plan-aligned pushes.
- Tier 2: make spirit-guided decisions using the plan or TL directive spirit.
- Tier 3: escalate to TL first, not the owner. Only go to the owner if TL explicitly defers to the product owner.
- Never send `C-c` to workers. Use `C-u` for input clear and `Escape` for gentle interrupt.
- Every worker-facing message must use `~/Projects/TmuxAgentManager/.claude/commands/send_tmux.md`; every TL-facing message must use `~/Projects/TmuxAgentManager/.claude/skills/oysterun_session_control.md`.
- Use at most one worker-message action per worker per tick unless TL explicitly requests multiple dispatches.

#### 6. Worker Registry

- W1 (`workers[0]`): primary configured Codex worker.
- W2 (`workers[1]`): secondary configured Codex worker, if present.
- W3 (`workers[2]`): tertiary configured Codex worker, if present.

#### 7. Tick-Level Summary To the owner

At the end of each tick, produce a short user-facing summary to the owner. Frame it as a status relay, not a decision request. The summary must list `TL read_response`, `worker progress checks`, `TL send_cmd`, and `worker sends` in order. For example: "TL read. W1 working on X, W2 idle and asked TL for next task, W3 delivered report at `<path>`, sent to TL. Worker sends: W2 received TL assignment." Never ask "the owner, what do you want next?"

Introduce yourself to TL only on the very first tick. Subsequent ticks go directly to the task/deliverable report flow.
