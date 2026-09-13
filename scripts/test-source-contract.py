#!/usr/bin/env python3
"""Validate plugin entrypoints and autonomous tool access without matching prose."""
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
    raw_tools = agent["tools"]
    require(raw_tools.startswith("[") and raw_tools.endswith("]"), "Expected an explicit tool allowlist")
    tools = [tool.strip() for tool in raw_tools[1:-1].split(",")]
    require(len(tools) == len(set(tools)), "Duplicate autonomous tool permission")
    namespaces = ("mcp__plugin_nova_nova__", "mcp__nova__")
    require("ToolSearch" in tools, "The architect cannot discover tools")
    require(all(tool == "ToolSearch" or tool.startswith(namespaces) for tool in tools), "The autonomous architect may access only Nova and tool discovery")
    available = [{tool.removeprefix(prefix) for tool in tools if tool.startswith(prefix)} for prefix in namespaces]
    require(available[0] == available[1], "Installed and standalone Nova namespaces must expose the same capabilities")
    require({"get_agent_prompt", "get_authoring_guide", "create_app", "get_app"} <= available[0], "The architect cannot reach current guidance and app state")
    print("Plugin entrypoints and autonomous tool permissions passed.")


if __name__ == "__main__":
    main()
