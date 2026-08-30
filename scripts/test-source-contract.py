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
LOOKUP_TOOLS = (
    "get_lookup_tables",
    "get_lookup_table_rows",
    "create_lookup_table",
    "update_lookup_table",
    "edit_lookup_columns",
    "edit_lookup_rows",
    "replace_lookup_rows",
    "remove_lookup_table",
    "set_field_options_source",
)
LOOKUP_WORKFLOW_CONTRACT = (
    "current request explicitly asks",
    "affect every app in the Project",
    "complete desired row",
    "`optionsSource` in the same `create_module`, `create_form`, or `add_fields` call",
    "`optionsSource` in the same `edit_field` call",
    "`set_field_options_source` is only for changing an already-valid select",
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
PROMPT_PAGE_FIELDS = (
    "protocol_version",
    "offset_unit",
    "prompt_sha256",
    "prompt_length",
    "prompt_chunk",
    "chunk_start",
    "chunk_end",
    "complete",
    "next_cursor",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def require_prompt_paging_contract(prose: str, label: str) -> None:
    require(
        "nova-agent-prompt-page" in prose,
        f"{label} omits the paged-prompt discriminator",
    )
    for field in PROMPT_PAGE_FIELDS:
        require(field in prose, f"{label} omits paged-prompt field: {field}")
    require(
        "`protocol_version` to equal `1`" in prose,
        f"{label} does not require prompt protocol version 1",
    )
    require(
        "`offset_unit` to equal `unicode-code-points` on every page" in prose
        and "`chunk_start`, `chunk_end`, and `prompt_length` as Unicode code-point counts"
        in prose
        and "never UTF-16 code units or bytes" in prose
        and "Nova's deterministic code-point slicer" in prose
        and "do not attempt to recount" in prose,
        f"{label} does not require portable Unicode code-point offsets",
    )
    require(
        "same `mode` and `app_id` values" in prose,
        f"{label} does not preserve mode/app_id across prompt pages",
    )
    require(
        "remain unchanged on every page" in prose
        and "advertised" in prose
        and "recompute SHA-256" in prose,
        f"{label} misstates paged-prompt digest/length verification",
    )
    require(
        "first `chunk_start` to be `0`" in prose
        and "every later `chunk_start` to equal the preceding `chunk_end`" in prose,
        f"{label} omits adjacent exact prompt offsets",
    )
    require(
        "Save each `prompt_chunk` exactly as returned" in prose
        and "without inserting separators or normalizing it" in prose,
        f"{label} permits prompt chunk rewriting",
    )
    require(
        "`complete` is `false`" in prose
        and "require one `next_cursor`" in prose
        and "`complete` is `true`" in prose
        and "require no `next_cursor`" in prose,
        f"{label} omits continuation/final-page cursor rules",
    )
    require(
        "final `chunk_end` to equal `prompt_length`" in prose
        and "Concatenate the exact `prompt_chunk` values in order" in prose,
        f"{label} omits final length or exact concatenation",
    )
    require(
        "ordinary text rather than a prompt page" in prose
        and "NOVA-PROMPT-END" in prose,
        f"{label} omits the ordinary-text prompt fallback",
    )


def require_nested_menu_construction_contract(prose: str, label: str) -> None:
    require(
        "`MISSING_CHILD_CASE_MODULE`" in prose
        and "child viewer temporarily top-level" in prose
        and "then use `move_module`" in prose,
        f"{label} omits the child-viewer-first construction exception",
    )
    require(
        "different case types require the parent to have at least one Form" in prose
        and "`NESTED_MENU_CROSS_TYPE_ROOT_REQUIRES_FORM`" in prose
        and "case-list-only root" in prose,
        f"{label} omits the cross-type parent-form requirement",
    )


def main() -> None:
    manifest = json.loads(
        (ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
    )
    require(manifest["name"] == "nova", "plugin name must remain nova")
    require(
        manifest["version"] == "1.29.0",
        "Plugin source contract requires version 1.29.0",
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
        for tool in LOOKUP_TOOLS:
            for namespace in ("mcp__plugin_nova_nova__", "mcp__nova__"):
                require(
                    f"{namespace}{tool}" in text,
                    f"{path.relative_to(ROOT)} omits {namespace}{tool}",
                )
        require(
            "reusable answer list" in prose
            and "Project-scoped" in prose
            and "expectedTableRevision" in prose
            and "human-readable discovery" in prose
            and "not addresses" in prose,
            f"{path.relative_to(ROOT)} omits the lookup authoring workflow",
        )
        for phrase in LOOKUP_WORKFLOW_CONTRACT:
            require(
                phrase in prose,
                f"{path.relative_to(ROOT)} omits lookup safety: {phrase}",
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
        require_nested_menu_construction_contract(
            prose, str(path.relative_to(ROOT))
        )
        if path.relative_to(ROOT) in {
            Path("skills/build/SKILL.md"),
            Path("skills/autobuild/SKILL.md"),
        }:
            require(
                "parent with its writer form" in prose,
                f"{path.relative_to(ROOT)} omits the new-parent writer bootstrap",
            )
        if path.relative_to(ROOT) == Path("skills/edit/SKILL.md"):
            require(
                "create or update the writer form on the new or existing parent"
                in prose,
                "edit skill omits the existing-parent writer bootstrap",
            )
        if path.relative_to(ROOT) == Path("skills/build/SKILL.md"):
            require(
                "root module before its children except for the child-viewer-first writer bootstrap above"
                in prose
                and "For ordinary compositions" in prose,
                "build skill contradicts the child-viewer-first construction exception",
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
        require_prompt_paging_contract(prose, str(path.relative_to(ROOT)))

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
    for tool in LOOKUP_TOOLS:
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
    require(
        "reusable answer list" in agent_prose
        and "Project-scoped" in agent_prose
        and "expectedTableRevision" in agent_prose
        and "human-readable discovery" in agent_prose
        and "not addresses" in agent_prose,
        "autonomous agent omits the lookup authoring workflow",
    )
    for phrase in LOOKUP_WORKFLOW_CONTRACT:
        require(
            phrase in agent_prose,
            f"autonomous agent omits lookup safety: {phrase}",
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
    require_nested_menu_construction_contract(agent_prose, "autonomous agent")
    require(
        "create or update the writer form on the new or existing parent"
        in agent_prose,
        "autonomous agent omits the existing-parent writer bootstrap",
    )
    require_prompt_paging_contract(agent_prose, "autonomous agent")

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
    require(
        "## Project data tables" in readme,
        "README omits the public Project-data contract",
    )
    for tool in LOOKUP_TOOLS:
        require(tool in readme, f"README omits lookup tool: {tool}")
    require(
        "reusable answer list" in readme_prose
        and "Project-scoped" in readme_prose
        and "expectedTableRevision" in readme_prose
        and "human-readable discovery" in readme_prose
        and "not addresses" in readme_prose,
        "README omits the lookup authoring workflow",
    )
    for phrase in LOOKUP_WORKFLOW_CONTRACT:
        require(
            phrase in readme_prose,
            f"README omits lookup safety: {phrase}",
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
    require(
        "## Agent prompt delivery" in readme,
        "README omits paged agent-prompt delivery",
    )
    require_nested_menu_construction_contract(readme_prose, "README")
    require(
        "create or update the writer form on the new or existing parent"
        in readme_prose,
        "README omits the existing-parent writer bootstrap",
    )
    for field in PROMPT_PAGE_FIELDS:
        require(field in readme_prose, f"README omits paged-prompt field: {field}")
    require(
        "nova-agent-prompt-page" in readme_prose
        and "`protocol_version: 1`" in readme_prose
        and "`offset_unit: unicode-code-points`" in readme_prose
        and "same `mode` and `app_id`" in readme_prose
        and "unchanged advertised `prompt_sha256` and `prompt_length`" in readme_prose
        and "adjacent `chunk_start`/`chunk_end` offsets" in readme_prose
        and "`complete: true`" in readme_prose
        and "no `next_cursor`" in readme_prose
        and "exact `prompt_chunk` values" in readme_prose
        and "measured in Unicode code points, not UTF-16 code units or bytes"
        in readme_prose
        and "does not claim to recompute SHA-256" in readme_prose
        and "ordinary-text marker" in readme_prose,
        "README omits the complete paged-prompt contract",
    )

    print("Nova plugin source contract passed")


if __name__ == "__main__":
    main()
