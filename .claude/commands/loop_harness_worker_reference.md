# Loop Harness Worker Reference

This file holds detailed guidance extracted from `loop_harness_worker.md`. The main command is authoritative for tick execution. Read this reference only when the main command points here or when a case needs more detail.

## Pane Parse Uncertain Packet

When `pane_parse_uncertain` remains after bounded recovery, ask TL for help through Oysterun session-control. Include:

- worker slot and tmux session
- working directory or launch directory
- intended worker message/task
- exact tmux commands run for inspection and recovery
- pane metadata:
  ```bash
  tmux display-message -p -t <session> 'cmd=#{pane_current_command} dead=#{pane_dead} in_mode=#{pane_in_mode} alt=#{alternate_on} cursor=#{cursor_x},#{cursor_y} size=#{pane_width}x#{pane_height}'
  ```
- bottom pane text:
  ```bash
  tmux capture-pane -t <session> -p -J -S -30
  ```
- deeper pane text:
  ```bash
  tmux capture-pane -t <session> -p -J -S -120
  ```
- post-recovery captures after submit / alternate submit / Escape
- whether scratch state already recorded same prompt buffer
- direct TL debug commands:
  ```bash
  tmux display-message -p -t <session> 'cmd=#{pane_current_command} dead=#{pane_dead} in_mode=#{pane_in_mode} alt=#{alternate_on} cursor=#{cursor_x},#{cursor_y} size=#{pane_width}x#{pane_height}'
  tmux capture-pane -t <session> -p -J -S -120
  tmux attach -t <session>
  ```

Ask TL to determine root cause and provide PM a concrete next action. TL may debug directly, but PM remains the channel communicating with workers.

## Challenge Details

### Challenge 1: Plan Alignment

Ask:

- Which section of `<plan_doc>` does this map to?
- If this diverges from the plan, what is the business justification?
- Is this a new customization not listed in the plan? If yes, stop and ask TL.

### Challenge 2: Reference Implementation

Ask:

- What did the real upstream/source reference do? Cite file/line.
- Are you synthesizing a simplified variant? If yes, stop unless plan whitelists it.
- Does upstream have runtime behavior your implementation drops?

### Challenge 3: Tool And Skill Awareness

Ask:

- Check `<working_dir>/.claude/commands/`: is there an existing slash command?
- Check `<working_dir>/.claude/skills/`: is there a skill for this?
- Check worker cheat sheet.
- If existing tooling covers it, use it.

### Challenge 4: Evidence Package Quality

Ask:

- What exact evidence should TL review?
- Include gate output, commit hashes, test excerpts, screenshot/recording paths, logs, `.xcresult`, report paths.
- Which proposal section and acceptance criteria does this map to?
- What evidence is missing and is the gap product, harness, environment, or unresolved blocker?

### Challenge 5: Lesson Retention

Interrupt if worker is about to:

- create a custom wrapper where reference primitive exists
- declare done while reconciliation bugs remain
- build a stub pretending to be real module
- skip required evidence or omit verification gap from TL packet

### Challenge 6: Grep Before Invent

Ask:

- Did you grep for existing infrastructure?
- Did you grep existing accessibility identifier patterns?
- Did you check nearby files for helper functions?

### Challenge 7: Verification-Blocker Evidence Ladder

When verification fails, walk one ladder step per tick. Do not cram all steps into one worker message.

1. Plan-alignment of implementation under verification.
2. Component identity / accessibility-ID re-check.
3. Simulator restart ladder.
4. Test framework restart / reinstall / clean build.
5. Worker-specific tools from commands/skills/cheat sheet.
6. Cross-reference deferral / post-mortem / handover files.
7. Binary isolation: harness vs product.

Exit only after applicable steps have documented results. Then worker may send TL a named option set, explicit deferral note, or specific blocker.

## Tier 3 Owner Escalation Report

Only when TL explicitly requests owner product-owner input, PM writes an escalation report under:

```text
~/Projects/TmuxAgentManager/prompts/YYYYMMDD_N_escalation_<feature-slug>.md
```

Language: 繁體中文.

The report must be layman-friendly. The owner does not need code details to decide.

Required sections:

1. 這個決策到底在決定什麼
2. 現在的實際狀態
3. 每個選項的白話說明
4. Manager 的推薦
5. 相關文件路徑
6. 下一步

Before writing the report, PM must ask worker challenging what-if questions and synthesize the worker's technical findings into decision-maker language.

Do not stage, commit, or push escalation reports under `prompts/`.

## Reminder Ledger Format

Append only to:

```text
prompts/_REMINDER.md
```

Use this shape:

```text
## YYYY-MM-DD HH:MM — 阻塞中 / 需要決策 / 提醒
相關文件：<path>
問題：<plain-language explanation>
建議下一步：<manager recommendation>
```

Use for durable blockers, TL-requested owner decisions, and reminders the owner genuinely needs later. Do not write routine tick events.

## Practical Examples

- Worker delivered one planned deliverable and TL dispatch defines another deliverable as next: push next deliverable immediately if within TL dispatch.
- Worker delivered current task group completely: ask TL if next task group is authorized by proposal/guide.
- Worker hits small ambiguity and plan spirit resolves it: decide within TL dispatch and record reminder if useful.
- Worker hits architectural fork: ask TL with named options. Owner input only if TL requests it.

## What Not To Do

- Do not pause loop because "owner might want to review first"; ask TL.
- Do not recommend loop stop after each task group completion.
- Do not classify old scrollback as current prompt state.
- Do not clear visible unsent payload with `C-u`; use bounded submit recovery first.
