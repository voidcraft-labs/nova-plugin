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
README = ROOT / "README.md"

NESTED_MENU_CONTRACT = (
    "parentModuleUuid",
    "one submenu tier",
    "Menu parentage",
    "case parentage",
    "canonical owning module",
    "linked- or shadow-form reuse",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    manifest = json.loads(
        (ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
    )
    require(manifest["name"] == "nova", "plugin name must remain nova")
    require(
        manifest["version"] == "1.28.0",
        "Nested-menus release must carry plugin version 1.28.0",
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
            "`{language, script?, region?}`" in prose
            and "never a combined tag" in prose,
            f"{path.relative_to(ROOT)} omits the language identity contract",
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
        for phrase in NESTED_MENU_CONTRACT:
            require(
                phrase in prose,
                f"{path.relative_to(ROOT)} omits nested-menu contract: {phrase}",
            )
        require(
            "`create_module`" in prose
            and "omit `parentModuleUuid` for a top-level module" in prose,
            f"{path.relative_to(ROOT)} omits create_module root placement",
        )
        require(
            "`move_module`" in prose
            and "`after` remains the sibling anchor" in prose
            and "Omit `parentModuleUuid` only to reorder within" in prose
            and "pass `null` to make it top-level" in prose
            and "eligible root UUID" in prose,
            f"{path.relative_to(ROOT)} omits move_module placement semantics",
        )
        require(
            "Use `move_module`, never `update_module`, for menu placement" in prose,
            f"{path.relative_to(ROOT)} permits non-atomic menu placement",
        )
        require(
            "NOVA-PROMPT-END" in prose
            and "missing marker is a transport failure" in prose
            and (
                "don't build" in prose
                or "don't edit" in prose
                or "instead of building" in prose
            ),
            f"{path.relative_to(ROOT)} does not stop on a missing prompt marker",
        )

    for path in GUIDANCE_FILES[:2]:
        text = path.read_text(encoding="utf-8")
        for namespace in ("mcp__plugin_nova_nova__", "mcp__nova__"):
            require(
                f"{namespace}move_module" in text,
                f"{path.relative_to(ROOT)} omits {namespace}move_module",
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
    for namespace in ("mcp__plugin_nova_nova__", "mcp__nova__"):
        require(
            f"{namespace}move_module" in frontmatter,
            f"autonomous agent allowlist omits {namespace}move_module",
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
        "`{language, script?, region?}`" in agent_prose
        and "never a combined tag" in agent_prose,
        "autonomous agent omits the language identity contract",
    )
    require(
        "expectedSourceFingerprint" in agent_prose
        and "expectedValue" in agent_prose
        and "expectedCurrentSourceFingerprint" in agent_prose
        and "concurrency refusal" in agent_prose,
        "autonomous agent omits translation concurrency fencing",
    )
    for phrase in NESTED_MENU_CONTRACT:
        require(
            phrase in agent_prose,
            f"autonomous agent omits nested-menu contract: {phrase}",
        )
    require(
        "`create_module`" in agent_prose
        and "omit `parentModuleUuid` for a top-level module" in agent_prose
        and "`after` remains the sibling anchor" in agent_prose
        and "Omit `parentModuleUuid` only to reorder within" in agent_prose
        and "pass `null` to make it top-level" in agent_prose
        and "eligible root UUID" in agent_prose,
        "autonomous agent omits create/move module placement semantics",
    )
    require(
        "NOVA-PROMPT-END" in agent_prose
        and "missing marker is a transport failure" in agent_prose
        and "Do not build from it" in agent_prose,
        "autonomous agent does not stop on a missing prompt marker",
    )

    readme = README.read_text(encoding="utf-8")
    readme_prose = " ".join(readme.split())
    require(
        "## Languages and translations" in readme,
        "README omits the public language contract",
    )
    require(
        "`{language, script?, region?}`" in readme_prose
        and "Every individual living language" in readme_prose,
        "README must state the identity contract and distinguish language"
        " availability from model capability",
    )
    require(
        "57-language launch set" in readme_prose
        and "no paid automatic MCP action" in readme_prose,
        "README misstates automatic translation",
    )
    require(
        "## Nested menus" in readme,
        "README omits the public nested-menu contract",
    )
    for phrase in NESTED_MENU_CONTRACT:
        require(
            phrase in readme_prose,
            f"README omits nested-menu contract: {phrase}",
        )
    require(
        "`create_module`" in readme_prose
        and "omit it for a top-level module" in readme_prose
        and "`move_module`" in readme_prose
        and "Omit the parent only to reorder inside" in readme_prose
        and "pass `null` to make it top-level" in readme_prose
        and "`after` sibling anchor" in readme_prose,
        "README omits exact create/move placement semantics",
    )

    print("Nova plugin source contract passed")


if __name__ == "__main__":
    main()
