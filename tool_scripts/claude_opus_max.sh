#!/usr/bin/env bash
set -euo pipefail

real_claude="${CLAUDE_REAL_PATH:-${HOME}/.local/bin/claude}"
forced_model="${CLAUDE_DEFAULT_MODEL:-opus}"
forced_effort="${CLAUDE_DEFAULT_EFFORT:-max}"

if [[ ! -x "$real_claude" ]]; then
  echo "Claude wrapper error: real Claude binary is not executable: $real_claude" >&2
  exit 1
fi

forwarded=()
while (($#)); do
  case "$1" in
    --model)
      shift
      if (($# == 0)); then
        echo "Claude wrapper error: --model requires a value" >&2
        exit 1
      fi
      shift
      ;;
    --model=*)
      shift
      ;;
    --effort)
      shift
      if (($# == 0)); then
        echo "Claude wrapper error: --effort requires a value" >&2
        exit 1
      fi
      shift
      ;;
    --effort=*)
      shift
      ;;
    *)
      forwarded+=("$1")
      shift
      ;;
  esac
done

exec "$real_claude" --model "$forced_model" --effort "$forced_effort" "${forwarded[@]}"
