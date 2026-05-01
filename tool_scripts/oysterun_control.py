#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib import error, parse, request


REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO_ROOT / "config.json"


class ConfigError(RuntimeError):
    pass


class HostRequestError(RuntimeError):
    def __init__(self, status: int, payload: Any):
        self.status = status
        self.payload = payload
        detail = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False)
        super().__init__(f"Host request failed ({status}): {detail}")


@dataclass
class OysterunConfig:
    base_url: str
    dashboard_user: str
    dashboard_password: str
    default_nickname: str
    default_transcript_limit: int
    team_roles: dict[str, dict[str, Any]]


def load_config() -> OysterunConfig:
    if not CONFIG_PATH.exists():
        raise ConfigError(
            f"Missing local config: {CONFIG_PATH}\n"
            "Create it from config.example.json before using Oysterun control commands."
        )

    try:
        raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Invalid JSON in {CONFIG_PATH}: {exc}") from exc

    oyster = raw.get("oysterun") or {}
    team = raw.get("team") or {}
    roles = team.get("roles") or {}

    base_url = str(oyster.get("base_url") or "").strip().rstrip("/")
    dashboard_user = str(oyster.get("dashboard_user") or "").strip()
    dashboard_password = str(oyster.get("dashboard_password") or "").strip()
    default_nickname = str(oyster.get("default_nickname") or "Manager").strip() or "Manager"
    default_transcript_limit = int(oyster.get("default_transcript_limit") or 12)

    missing = [
        name
        for name, value in (
            ("oysterun.base_url", base_url),
            ("oysterun.dashboard_user", dashboard_user),
            ("oysterun.dashboard_password", dashboard_password),
        )
        if not value
    ]
    if missing:
        raise ConfigError(f"Missing required config values in {CONFIG_PATH}: {', '.join(missing)}")

    return OysterunConfig(
        base_url=base_url,
        dashboard_user=dashboard_user,
        dashboard_password=dashboard_password,
        default_nickname=default_nickname,
        default_transcript_limit=default_transcript_limit,
        team_roles=roles,
    )


def http_json(
    method: str,
    base_url: str,
    path: str,
    *,
    token: str | None = None,
    query: dict[str, Any] | None = None,
    body: dict[str, Any] | None = None,
) -> Any:
    url = f"{base_url}{path}"
    if query:
        url = f"{url}?{parse.urlencode(query)}"

    headers: dict[str, str] = {}
    data: bytes | None = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = request.Request(url, method=method.upper(), headers=headers, data=data)
    try:
        with request.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            payload = json.loads(raw) if raw else {"error": exc.reason}
        except json.JSONDecodeError:
            payload = raw or {"error": exc.reason}
        raise HostRequestError(exc.code, payload) from exc


def login(cfg: OysterunConfig) -> str:
    payload = http_json(
        "POST",
        cfg.base_url,
        "/auth/login",
        body={
            "username": cfg.dashboard_user,
            "password": cfg.dashboard_password,
        },
    )
    token = str(payload.get("token") or "").strip()
    if not token:
        raise ConfigError("Login succeeded without a token in the response payload.")
    return token


def list_sessions(cfg: OysterunConfig, token: str) -> list[dict[str, Any]]:
    payload = http_json("GET", cfg.base_url, "/sessions", token=token)
    sessions = payload.get("sessions")
    if not isinstance(sessions, list):
        raise ConfigError("Unexpected /sessions payload: missing sessions list.")
    return sessions


def role_match_label(role_name: str, role_cfg: dict[str, Any], session: dict[str, Any]) -> str | None:
    session_id = str(session.get("sessionId") or "")
    session_name = str(session.get("sessionName") or "")
    agent_id = str(session.get("agentId") or "")
    configured_session_name = str(role_cfg.get("session_name") or "").strip()
    configured_agent_id = str(role_cfg.get("agent_id") or "").strip()
    configured_session_id = str(role_cfg.get("session_id") or "").strip()

    if configured_session_name:
        return role_name if configured_session_name == session_name else None
    if configured_agent_id:
        return role_name if configured_agent_id == agent_id else None
    if configured_session_id:
        return role_name if configured_session_id == session_id else None
    return None


def get_role_match_candidates(role_name: str, role_cfg: dict[str, Any], sessions: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], str]:
    configured_session_name = str(role_cfg.get("session_name") or "").strip()
    configured_agent_id = str(role_cfg.get("agent_id") or "").strip()
    configured_session_id = str(role_cfg.get("session_id") or "").strip()

    if configured_session_name:
        matches = [
            session
            for session in sessions
            if str(session.get("sessionName") or "").strip() == configured_session_name
        ]
        return matches, f"session_name={configured_session_name}"

    # Backward-compatibility only for older local config files.
    if configured_agent_id:
        matches = [
            session
            for session in sessions
            if str(session.get("agentId") or "").strip() == configured_agent_id
        ]
        return matches, f"legacy agent_id={configured_agent_id}"

    if configured_session_id:
        matches = [
            session
            for session in sessions
            if str(session.get("sessionId") or "").strip() == configured_session_id
        ]
        return matches, f"explicit session_id={configured_session_id}"

    return [], "unbound"


def is_oysterun_role(role_cfg: dict[str, Any]) -> bool:
    role_type = str(role_cfg.get("type") or "Oysterun").strip().lower()
    return role_type in ("", "oysterun", "oysterun_session")


def roles_for_session(cfg: OysterunConfig, session: dict[str, Any]) -> list[str]:
    labels: list[str] = []
    for role_name, role_cfg in cfg.team_roles.items():
        if not isinstance(role_cfg, dict):
            continue
        if not is_oysterun_role(role_cfg):
            continue
        label = role_match_label(role_name, role_cfg, session)
        if label:
            labels.append(label)
    return labels


def resolve_target(cfg: OysterunConfig, sessions: list[dict[str, Any]], target: str | None) -> tuple[dict[str, Any], str]:
    requested = (target or "team_lead").strip()
    role_cfg = cfg.team_roles.get(requested)

    if isinstance(role_cfg, dict) and is_oysterun_role(role_cfg):
        matches, source = get_role_match_candidates(requested, role_cfg, sessions)
        if len(matches) == 1:
            return matches[0], f"role:{requested} ({source})"
        if len(matches) > 1:
            raise ConfigError(
                f"Role '{requested}' matched {len(matches)} live Oysterun sessions via {source}. "
                "Use /skills/Oysterun/list_session, show the owner the matching live sessions, and ask which one to use."
            )
        raise ConfigError(
            f"Role '{requested}' did not resolve to a live Oysterun session ({source}). "
            "Use /skills/Oysterun/list_session, ask the owner to choose an existing live session, or confirm creating a new session."
        )

    direct_lookup_fields = (
        ("session name", "sessionName"),
        ("session id", "sessionId"),
        ("legacy agent id", "agentId"),
    )
    for label, field_name in direct_lookup_fields:
        direct_matches = [
            session
            for session in sessions
            if str(session.get(field_name) or "").strip() == requested
        ]
        if len(direct_matches) == 1:
            return direct_matches[0], f"{label}:{requested}"
        if len(direct_matches) > 1:
            raise ConfigError(
                f"Target '{requested}' matched multiple live sessions by {label}. "
                "Use the concrete session name or session id from /skills/Oysterun/list_session."
            )

    raise ConfigError(
        f"Could not resolve Oysterun target '{requested}'. "
        "Use /skills/Oysterun/list_session to inspect live sessions first."
    )


def format_session_line(cfg: OysterunConfig, session: dict[str, Any]) -> str:
    labels = roles_for_session(cfg, session)
    label_suffix = f" roles={','.join(labels)}" if labels else ""
    return (
        f"- {session.get('sessionName')} | id={session.get('sessionId')} | "
        f"agent={session.get('agentId')} | provider={session.get('provider')} | "
        f"ready={session.get('ready')} | alive={session.get('alive')}{label_suffix}"
    )


def cmd_list_sessions(args: argparse.Namespace) -> int:
    cfg = load_config()
    token = login(cfg)
    sessions = list_sessions(cfg, token)

    print(f"Oysterun sessions at {cfg.base_url}")
    print(f"Count: {len(sessions)}")
    if not sessions:
        return 0

    for session in sessions:
        rendered = format_session_line(cfg, session)
        if args.filter_text and args.filter_text.lower() not in rendered.lower():
            continue
        print(rendered)

    unresolved_roles = []
    for role_name, role_cfg in cfg.team_roles.items():
        if not isinstance(role_cfg, dict):
            continue
        if not is_oysterun_role(role_cfg):
            continue
        if not any(role_match_label(role_name, role_cfg, session) for session in sessions):
            unresolved_roles.append(role_name)
    if unresolved_roles:
        print("")
        print("Unresolved Oysterun team roles:")
        for role_name in unresolved_roles:
            print(f"- {role_name}")

    return 0


def cmd_send(args: argparse.Namespace) -> int:
    cfg = load_config()
    token = login(cfg)
    sessions = list_sessions(cfg, token)
    session, resolution = resolve_target(cfg, sessions, args.target)

    payload = http_json(
        "POST",
        cfg.base_url,
        "/session/send",
        token=token,
        body={
            "session_id": session["sessionId"],
            "text": args.message,
            "nickname": args.nickname or cfg.default_nickname,
        },
    )

    print(f"Resolved target: {resolution}")
    print(format_session_line(cfg, session))
    print(f"Queued message_id: {payload.get('message_id')}")
    print(f"State: {payload.get('state')}")
    return 0


def should_include_message(message: dict[str, Any], include_internal: bool) -> bool:
    if include_internal:
        return True
    message_type = str(message.get("message_type") or "").strip().lower()
    if message_type in ("thinking", "tool_call", "tool_result", "system"):
        return False
    return True


def render_message(message: dict[str, Any]) -> str:
    role = message.get("role") or "unknown"
    created_at = message.get("created_at") or "unknown-time"
    message_type = message.get("message_type")
    header = f"[{created_at}] {role}"
    if message_type:
        header = f"{header} ({message_type})"
    body = str(message.get("content") or "").strip()
    return f"{header}\n{body}\n"


def cmd_read(args: argparse.Namespace) -> int:
    cfg = load_config()
    token = login(cfg)
    sessions = list_sessions(cfg, token)
    session, resolution = resolve_target(cfg, sessions, args.target)

    payload = http_json(
        "GET",
        cfg.base_url,
        "/session/transcript",
        token=token,
        query={
            "session_id": session["sessionId"],
            "agent_id": session["agentId"],
            "limit": args.limit or cfg.default_transcript_limit,
        },
    )
    messages = payload.get("messages")
    if not isinstance(messages, list):
        raise ConfigError("Unexpected /session/transcript payload: missing messages list.")

    print(f"Resolved target: {resolution}")
    print(format_session_line(cfg, session))
    print("")

    visible = [message for message in messages if should_include_message(message, args.include_internal)]
    if not visible:
        print("No matching transcript messages.")
        return 0

    for message in visible:
        print(render_message(message))

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Control Oysterun Host sessions from TmuxAgentManager local config."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list-sessions", help="List live Oysterun sessions.")
    list_parser.add_argument("--filter", dest="filter_text", help="Optional substring filter.")
    list_parser.set_defaults(func=cmd_list_sessions)

    send_parser = subparsers.add_parser("send", help="Queue a message into an Oysterun session.")
    send_parser.add_argument(
        "--target",
        help="Role, session name, session id, or legacy agent id. Defaults to the team_lead role.",
    )
    send_parser.add_argument(
        "--nickname",
        help="Optional nickname shown in Oysterun. Defaults to oysterun.default_nickname.",
    )
    send_parser.add_argument("message", help="Message text to queue.")
    send_parser.set_defaults(func=cmd_send)

    read_parser = subparsers.add_parser("read", help="Read recent Oysterun transcript messages.")
    read_parser.add_argument(
        "--target",
        help="Role, session name, session id, or legacy agent id. Defaults to the team_lead role.",
    )
    read_parser.add_argument(
        "--limit",
        type=int,
        help="Transcript page size. Defaults to oysterun.default_transcript_limit.",
    )
    read_parser.add_argument(
        "--include-internal",
        action="store_true",
        help="Include tool_call/tool_result/system rows instead of only human-facing transcript rows.",
    )
    read_parser.set_defaults(func=cmd_read)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return int(args.func(args) or 0)
    except (ConfigError, HostRequestError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
