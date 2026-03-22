#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "prompts"


@dataclass(frozen=True)
class RenderOptions:
    include_tools: bool
    include_system: bool
    include_progress: bool
    include_thinking: bool


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert a Claude-style JSONL session log into a Markdown transcript."
    )
    parser.add_argument("input", type=Path, help="Path to the source .jsonl file.")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Explicit output Markdown path. Defaults to prompts/YYYYMMDD_N_description.md",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Directory used for the default output path. Defaults to {DEFAULT_OUTPUT_DIR}",
    )
    parser.add_argument(
        "--no-tools",
        action="store_true",
        help="Omit tool use/result blocks from the transcript.",
    )
    parser.add_argument(
        "--no-system",
        action="store_true",
        help="Omit top-level system records.",
    )
    parser.add_argument(
        "--include-progress",
        action="store_true",
        help="Include progress hook records.",
    )
    parser.add_argument(
        "--include-thinking",
        action="store_true",
        help="Include thinking blocks when present.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = args.input.expanduser().resolve()
    if not input_path.is_file():
        print(f"Input file not found: {input_path}", file=sys.stderr)
        return 1

    records = load_jsonl(input_path)
    if not records:
        print(f"No JSON objects found in: {input_path}", file=sys.stderr)
        return 1

    options = RenderOptions(
        include_tools=not args.no_tools,
        include_system=not args.no_system,
        include_progress=args.include_progress,
        include_thinking=args.include_thinking,
    )

    output_path = resolve_output_path(
        input_path=input_path,
        output_path=args.output,
        output_dir=args.output_dir,
        records=records,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rendered_blocks = render_transcript(records, input_path, options)
    output_path.write_text(rendered_blocks, encoding="utf-8")
    print(str(output_path))
    return 0


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number}: {exc}") from exc
            if isinstance(payload, dict):
                records.append(payload)
    return records


def resolve_output_path(
    input_path: Path,
    output_path: Path | None,
    output_dir: Path,
    records: list[dict[str, Any]],
) -> Path:
    if output_path is not None:
        return output_path.expanduser().resolve()

    resolved_output_dir = output_dir.expanduser().resolve()
    date_prefix = "undated"
    timestamp = first_timestamp(records)
    if timestamp is not None:
        date_prefix = timestamp.astimezone(timezone.utc).strftime("%Y%m%d")
    safe_stem = slugify(input_path.stem)
    sequence = next_daily_sequence(resolved_output_dir, date_prefix)
    return resolved_output_dir / f"{date_prefix}_{sequence}_{safe_stem}.md"


def first_timestamp(records: list[dict[str, Any]]) -> datetime | None:
    for record in records:
        parsed = parse_timestamp(record.get("timestamp"))
        if parsed is not None:
            return parsed
    return None


def parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._")
    return slug or "transcript"


def next_daily_sequence(output_dir: Path, date_prefix: str) -> int:
    if not output_dir.exists():
        return 1

    pattern = re.compile(rf"^{re.escape(date_prefix)}_(\d+)_.*\.md$")
    highest = 0
    for path in output_dir.iterdir():
        if not path.is_file():
            continue
        match = pattern.match(path.name)
        if match:
            highest = max(highest, int(match.group(1)))
    return highest + 1


def render_transcript(
    records: list[dict[str, Any]],
    input_path: Path,
    options: RenderOptions,
) -> str:
    blocks: list[str] = []
    rendered_count = 0

    header_lines = [
        "# Transcript",
        "",
        f"- Source: `{input_path}`",
        f"- Generated: `{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}`",
        f"- Records read: `{len(records)}`",
        f"- Tools included: `{'yes' if options.include_tools else 'no'}`",
        f"- Thinking included: `{'yes' if options.include_thinking else 'no'}`",
        f"- Progress included: `{'yes' if options.include_progress else 'no'}`",
        "",
    ]
    blocks.append("\n".join(header_lines))

    for record in records:
        rendered = render_record(record, rendered_count + 1, options)
        if not rendered:
            continue
        rendered_count += 1
        blocks.append(rendered)

    if rendered_count == 0:
        blocks.append("_No renderable records._")

    return "\n\n".join(blocks).rstrip() + "\n"


def render_record(record: dict[str, Any], index: int, options: RenderOptions) -> str | None:
    record_type = record.get("type")
    if record_type in {"user", "assistant"}:
        return render_message_record(record, index, options)
    if record_type == "system" and options.include_system:
        return render_top_level_record(
            index=index,
            label="System",
            timestamp=record.get("timestamp"),
            body=extract_text(record.get("content")) or "_No content._",
        )
    if record_type == "progress" and options.include_progress:
        progress_body = json_dump(record.get("data"))
        return render_top_level_record(
            index=index,
            label="Progress",
            timestamp=record.get("timestamp"),
            body=f"~~~json\n{progress_body}\n~~~",
        )
    return None


def render_message_record(
    record: dict[str, Any],
    index: int,
    options: RenderOptions,
) -> str | None:
    message = record.get("message")
    if not isinstance(message, dict):
        fallback = extract_text(record.get("content"))
        if not fallback:
            return None
        return render_top_level_record(
            index=index,
            label=title_case(record.get("type", "message")),
            timestamp=record.get("timestamp"),
            body=fallback,
        )

    role = title_case(message.get("role") or record.get("type") or "message")
    content = message.get("content")
    parts = render_message_content(content, options)

    if not parts and "toolUseResult" in record and options.include_tools:
        tool_use_result = extract_text(record.get("toolUseResult"))
        if tool_use_result:
            parts.append(render_tool_result_block({"content": tool_use_result}))

    if not parts:
        return None

    return render_top_level_record(
        index=index,
        label=role,
        timestamp=record.get("timestamp"),
        body="\n\n".join(part for part in parts if part.strip()),
    )


def render_message_content(content: Any, options: RenderOptions) -> list[str]:
    if isinstance(content, str):
        stripped = content.strip()
        return [stripped] if stripped else []

    if not isinstance(content, list):
        fallback = extract_text(content)
        return [fallback] if fallback else []

    parts: list[str] = []
    for item in content:
        rendered = render_content_item(item, options)
        if rendered:
            parts.append(rendered)
    return parts


def render_content_item(item: Any, options: RenderOptions) -> str | None:
    if isinstance(item, str):
        stripped = item.strip()
        return stripped or None

    if not isinstance(item, dict):
        return json_dump(item)

    item_type = item.get("type")
    if item_type == "text":
        text = item.get("text", "")
        return text.strip() or None

    if item_type == "thinking":
        if not options.include_thinking:
            return None
        thinking = extract_text(item.get("thinking")) or "_No thinking text._"
        return "### Thinking\n\n" + fence_text(thinking, "text")

    if item_type == "tool_use":
        if not options.include_tools:
            return None
        return render_tool_use_block(item)

    if item_type == "tool_result":
        if not options.include_tools:
            return None
        return render_tool_result_block(item)

    if item_type == "tool_reference":
        tool_name = item.get("tool_name", "unknown")
        return f"`Tool reference:` `{tool_name}`"

    if item_type == "image":
        image_ref = item.get("source") or item.get("url") or item.get("path") or "image"
        return f"`Image:` `{image_ref}`"

    if "text" in item and isinstance(item["text"], str):
        return item["text"].strip() or None

    fallback = extract_text(item)
    return fallback or None


def render_tool_use_block(item: dict[str, Any]) -> str:
    name = item.get("name", "tool")
    tool_id = item.get("id")
    header = f"### Tool Use | {name}"
    if tool_id:
        header += f" | {tool_id}"
    input_block = fence_text(json_dump(item.get("input", {})), "json")
    return f"{header}\n\n{input_block}"


def render_tool_result_block(item: dict[str, Any]) -> str:
    tool_use_id = item.get("tool_use_id")
    suffix = ""
    if item.get("is_error"):
        suffix = " | error"
    header = "### Tool Result"
    if tool_use_id:
        header += f" | {tool_use_id}"
    header += suffix

    body_text = extract_text(item.get("content"))
    if not body_text:
        body_text = json_dump(item)
    return f"{header}\n\n{fence_text(body_text, guess_language(body_text))}"


def render_top_level_record(index: int, label: str, timestamp: Any, body: str) -> str:
    timestamp_text = format_timestamp(timestamp)
    return f"## {index:04d}. {label} | {timestamp_text}\n\n{body.strip()}"


def format_timestamp(value: Any) -> str:
    parsed = parse_timestamp(value)
    if parsed is None:
        return str(value or "unknown")
    return parsed.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def extract_text(value: Any) -> str:
    if value is None:
        return ""

    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return ""
        parsed_json = try_parse_json_string(stripped)
        if parsed_json is not None:
            return json_dump(parsed_json)
        return stripped

    if isinstance(value, (int, float, bool)):
        return json.dumps(value)

    if isinstance(value, list):
        parts = [extract_text(item) for item in value]
        return "\n\n".join(part for part in parts if part)

    if isinstance(value, dict):
        item_type = value.get("type")
        if item_type == "text" and isinstance(value.get("text"), str):
            return value["text"].strip()
        if item_type == "tool_reference" and isinstance(value.get("tool_name"), str):
            return f"Tool reference: {value['tool_name']}"
        if item_type == "thinking" and isinstance(value.get("thinking"), str):
            return value["thinking"].strip()
        if isinstance(value.get("content"), (str, list, dict)):
            nested = extract_text(value["content"])
            if nested:
                return nested
        if isinstance(value.get("text"), str):
            return value["text"].strip()
        if isinstance(value.get("result"), (str, list, dict)):
            nested = extract_text(value["result"])
            if nested:
                return nested
        return json_dump(value)

    return str(value).strip()


def try_parse_json_string(value: str) -> Any | None:
    if not value or value[0] not in "[{":
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return None


def json_dump(value: Any) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True)


def guess_language(text: str) -> str:
    stripped = text.lstrip()
    if stripped.startswith("{") or stripped.startswith("["):
        return "json"
    return "text"


def fence_text(text: str, language: str) -> str:
    return f"~~~{language}\n{text.rstrip()}\n~~~"


def title_case(value: str) -> str:
    return str(value).replace("_", " ").strip().title()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
