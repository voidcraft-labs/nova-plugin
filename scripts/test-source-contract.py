#!/usr/bin/env python3
"""Dependency-free checks for Nova's copied MCP and language contract."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LANGUAGE_TOOLS = (
    "get_languages",
    "get_translatable_content",
    "add_language",
    "update_language",
    "remove_language",
    "update_translations",
)
GUIDANCE_FILES = (
    ROOT / "skills" / "build" / "SKILL.md",
    ROOT / "skills" / "autobuild" / "SKILL.md",
    ROOT / "skills" / "edit" / "SKILL.md",
)
AUTONOMOUS_AGENT = ROOT / "agents" / "nova-architect-autonomous.md"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    manifest = json.loads(
        (ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
    )
    require(manifest["name"] == "nova", "plugin name must remain nova")
    require(
        manifest["version"] == "1.19.0",
        "language contract release must carry plugin version 1.19.0",
    )

    for path in GUIDANCE_FILES:
        text = path.read_text(encoding="utf-8")
        prose = " ".join(text.split())
        for tool in LANGUAGE_TOOLS:
            for namespace in ("mcp__plugin_nova_nova__", "mcp__nova__"):
                require(
                    f"{namespace}{tool}" in text,
                    f"{path.relative_to(ROOT)} omits {namespace}{tool}",
                )
        require(
            "latest substantive message" in prose,
            f"{path.relative_to(ROOT)} omits the conversation-language rule",
        )
        require(
            "57-language launch set" in prose
            and "no paid automatic translation action" in prose,
            f"{path.relative_to(ROOT)} misstates automatic translation",
        )
        require(
            "bulk-translate" in prose and "update_translations" in prose,
            f"{path.relative_to(ROOT)} omits the manual-write boundary",
        )
        require(
            "expectedSourceFingerprint" in prose
            and "expectedValue" in prose
            and "expectedCurrentSourceFingerprint" in prose
            and "concurrency refusal" in prose,
            f"{path.relative_to(ROOT)} omits translation concurrency fencing",
        )

    agent_text = AUTONOMOUS_AGENT.read_text(encoding="utf-8")
    agent_prose = " ".join(agent_text.split())
    frontmatter = agent_text.split("---", 2)[1]
    for tool in LANGUAGE_TOOLS:
        for namespace in ("mcp__plugin_nova_nova__", "mcp__nova__"):
            require(
                f"{namespace}{tool}" in frontmatter,
                f"autonomous agent allowlist omits {namespace}{tool}",
            )
    require(
        "latest substantive message" in agent_prose,
        "autonomous agent omits the conversation-language rule",
    )
    require(
        "57-language launch set" in agent_prose
        and "no paid automatic MCP action" in agent_prose,
        "autonomous agent misstates automatic translation",
    )
    require(
        "expectedSourceFingerprint" in agent_prose
        and "expectedValue" in agent_prose
        and "expectedCurrentSourceFingerprint" in agent_prose
        and "concurrency refusal" in agent_prose,
        "autonomous agent omits translation concurrency fencing",
    )

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    readme_prose = " ".join(readme.split())
    require(
        "## Languages and translations" in readme,
        "README omits the public language contract",
    )
    require(
        "Every language code CommCare Classic accepts" in readme_prose,
        "README must distinguish Classic compatibility from model capability",
    )
    require(
        "57-language launch set" in readme_prose
        and "no paid automatic MCP action" in readme_prose,
        "README misstates automatic translation",
    )

    print("Nova plugin source contract passed")


if __name__ == "__main__":
    main()
