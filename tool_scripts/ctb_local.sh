#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"
bun_bin="$repo_root/vendor/bin/bun-darwin-aarch64/bun"
ctb_entry="$repo_root/vendor/ctb-local/src/cli.ts"

if [[ ! -x "$bun_bin" ]]; then
  echo "ctb local wrapper error: missing Bun runtime at $bun_bin" >&2
  exit 1
fi

if [[ ! -f "$ctb_entry" ]]; then
  echo "ctb local wrapper error: missing ctb entrypoint at $ctb_entry" >&2
  exit 1
fi

exec "$bun_bin" run "$ctb_entry" "$@"
