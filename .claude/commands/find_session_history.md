# /find_session_history — Find a previous session by keywords and load it as context

Search previous TmuxAgentManager session logs for keywords, convert the matching session to a readable transcript, and output a ready-to-use prompt to resume context.

## Input

- `$ARGUMENTS` — One or more keywords to search for in session history (required)

## Procedure

### Step 1: Search session history

Search all `.jsonl` files under the TmuxAgentManager project history for the keywords:

```bash
SESSION_DIR="$HOME/.claude/projects/-Users-wanghsuanchung-Projects-TmuxAgentManager"
grep -rln "$ARGUMENTS" "$SESSION_DIR"/*.jsonl 2>/dev/null
```

**Important:**
- Use `-l` (files-with-matches) first to get the list of matching files
- Exclude files inside `subagents/` directories — we want top-level session files only
- If no matches found, try case-insensitive search (`-i` flag)
- If still no matches, report to the user and stop

### Step 2: Present matches and let the user choose

If multiple files match, list them with context:

For each matching file:
1. Show the filename (UUID)
2. Show the file size
3. Show the first matching line (truncated to 200 chars) for context
4. Show the file modification date

```bash
# For each matching file:
ls -lh "$file"
grep -n "$ARGUMENTS" "$file" | head -3
```

Ask the user: "Which session do you want to load? (number or UUID)"

If only ONE file matches, proceed automatically without asking.

### Step 3: Copy the session file to prompts/

Determine the next sequence number for today:

```bash
TODAY=$(date +%Y%m%d)
LAST_N=$(ls prompts/${TODAY}_*.md prompts/${TODAY}_*.jsonl 2>/dev/null | sed "s|prompts/${TODAY}_||" | sed 's|_.*||' | sort -n | tail -1)
NEXT_N=$(( ${LAST_N:--1} + 1 ))
```

Extract the UUID stem from the source filename and copy:

```bash
UUID_STEM=$(basename "$SELECTED_FILE" .jsonl)
cp "$SELECTED_FILE" "prompts/${TODAY}_${NEXT_N}_${UUID_STEM}.jsonl"
```

### Step 4: Generate the transcript

Run the transcript conversion tool on the copied file:

```bash
python tool_scripts/jsonl2transcript/main.py "prompts/${TODAY}_${NEXT_N}_${UUID_STEM}.jsonl"
```

This will auto-generate a `.md` transcript in `prompts/` with the correct naming.

Capture the output filename from the script output.

### Step 5: Determine line count and suggest read range

```bash
TRANSCRIPT="prompts/${TODAY}_${NEXT_N}_${UUID_STEM}.md"  # or whatever the script outputs
TOTAL_LINES=$(wc -l < "$TRANSCRIPT")
```

Calculate a reasonable read range — default to last 1000 lines, but adjust if file is smaller:

```bash
if [ "$TOTAL_LINES" -le 1000 ]; then
  START=1
else
  START=$(( TOTAL_LINES - 1000 + 1 ))
fi
```

### Step 6: Output the ready-to-use prompt

Present to the user:

```
## Session Found & Converted

- **Source:** <UUID>.jsonl
- **Transcript:** prompts/<filename>.md
- **Total lines:** <N>
- **Keywords matched:** "$ARGUMENTS"

### Ready-to-use prompt (copy & send in your next message):

Can you read prompts/<filename>.md from line <START> (last 1000 lines of <TOTAL> total).

This is our previous conversation. Pick up the context from there and let's continue.
```

## Important rules

- Only search top-level `.jsonl` files, not subagent sessions
- If the transcript already exists in `prompts/` (same UUID), skip the copy and conversion — just use the existing one
- The `tool_scripts/jsonl2transcript/main.py` script auto-handles the `YYYYMMDD_N_` naming — trust its output
- If the search matches a very large file (>50MB), warn the user that conversion may take a moment
- This is agent-manager meta-work — no delegation needed
