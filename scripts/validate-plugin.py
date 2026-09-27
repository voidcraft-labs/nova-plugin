#!/usr/bin/env python3
"""Validate shipping plugin artifacts, not a copy of the server tool contract."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    require(text.startswith("---\n"), f"{path} has no frontmatter")
    header, body = text[4:].split("\n---\n", 1)
    require(bool(body.strip()), f"{path} has no instructions")
    fields: dict[str, str] = {}
    for line in header.splitlines():
        key, value = line.split(":", 1)
        require(key not in fields, f"{path} repeats {key}")
        fields[key] = value.strip()
    for key in ("name", "description"):
        require(bool(fields.get(key)), f"{path} lacks {key}")
    return fields


def main() -> None:
    manifest = json.loads((ROOT / ".claude-plugin/plugin.json").read_text())
    require(manifest["name"] == "nova", "Installed namespace must remain nova")
    require(bool(re.fullmatch(r"\d+\.\d+\.\d+", manifest["version"])), "Invalid plugin version")
    skills = {path.parent.name: frontmatter(path) for path in (ROOT / "skills").glob("*/SKILL.md")}
    for folder, fields in skills.items():
        require(fields["name"] == folder, f"Skill {folder} declares a different name")
    agent = frontmatter(ROOT / "agents/nova-architect-autonomous.md")
    target = f"Agent(nova:{agent['name']})"
    require(skills["autobuild"].get("allowed-tools") == target, "Autobuild must invoke its declared architect")
    require(int(agent["maxTurns"]) > 0, "Autonomous runs need a finite turn limit")
    tools = json.loads(agent["tools"])
    require(
        isinstance(tools, list)
        and len(tools) == 3
        and set(tools) == {"ToolSearch", "mcp__plugin_nova_nova__*", "mcp__nova__*"},
        "The architect needs tool discovery and both Nova server patterns only",
    )
    mcp = json.loads((ROOT / ".mcp.json").read_text())
    require(set(mcp["mcpServers"]) == {"nova"}, "The plugin must connect only Nova")
    server = mcp["mcpServers"]["nova"]
    require(server["type"] == "http", "Nova uses the HTTP MCP transport")
    require(
        server["url"] == "https://mcp.commcare.app/mcp",
        "The shipping plugin must pin Nova's production endpoint",
    )
    require(
        not server.get("headersHelper") and not server.get("headers"),
        "The bundled server must leave authentication to Claude Code's OAuth flow",
    )
    print("Plugin packaging and entrypoints passed.")


if __name__ == "__main__":
    main()
