#!/usr/bin/env python3
"""Dependency-free checks for Nova's copied MCP and language contract."""

from __future__ import annotations

import json
import re
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
ENTRY_POINT_TOOLS = (
    "get_entry_points",
    "add_entry_point",
    "update_entry_point",
    "remove_entry_point",
)
ENTRY_POINT_LINK_TOOL = "get_entry_point_link"
ENTRY_POINT_AUTHORING_CONTRACT = (
    "Create the complete destination first",
    "immutable `entryPointUuid`",
    "external `id` stays stable",
    "changing it can break distributed links",
    "Respect display conditions by default",
    "Only a form entry point",
    "`null` restores condition checks",
    "This never grants access",
    "no-matches registration form",
    "`requiredSelections`, including cardinality and maximum",
    "arbitrary session variables",
    "Do not handcraft CommCare wire",
    "separate MCP-only operation",
    "{app_id, server, domain, entry_point_uuid, selections}",
    "{module_uuid, case_ids}",
    "external HQ case IDs, never Nova case row IDs",
    "Each call freshly checks the released build",
    "`/app/v1/` URL is not pinned",
    "recipient latest-build policy",
    "does not simulate HQ claim or sync",
    "opening it can claim cases",
)
CASE_SELECTION_TOOLS = ("configure_case_selection",)
CASE_SELECTION_AUTHORING_CONTRACT = (
    "Several-case selection belongs to a follow-up or close form",
    "For a new module that owns its consuming form",
    '`selection: { kind: "multiple", maximum: N }`',
    "`N` is 1 through 100",
    "starts blank instead of borrowing one case's value",
    "even when the worker selects only one case",
    "Every nonblank shared answer is saved to every selected case",
    "blank preserves each case's existing value",
    "configured starting value or calculation",
    "Never choose a representative case",
    "A new `case-list-only` parent whose same-case child owns the consuming form is the exception",
    "create the parent without selection",
    "create the child atomically with selection and its consuming form",
    "then use `configure_case_selection` on the parent after the child exists",
    "`configure_case_selection` returns an `outcome`",
    "`applied` and `unchanged` are complete",
    '`outcome: "needs_changes"` applies no changes',
    "UUID-located blockers",
    '`needs: "repair"`',
    '`needs: "refresh"`',
    '`needs: "confirmation"`',
    "confirmation values from an older result",
    '`outcome: "unavailable"` also applies no changes',
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
UPLOAD_SKILL = ROOT / "skills" / "upload_to_hq" / "SKILL.md"
LEGACY_FEATURE_TOOL = "get_app_hq_" + "feature_flags"
LEGACY_FEATURE_RESPONSE = "feature_flag_" + "requirements"
RETIRED_FEATURE_CONTRACT_NAMES = (
    LEGACY_FEATURE_TOOL,
    LEGACY_FEATURE_RESPONSE,
    "nova_hq_" + "feature_flag_requirements",
    "nova/" + "featureFlagRequirements",
    "X-Nova-Hq-" + "Feature-Flag-Report",
)
PRIVATE_DEPLOYMENT_TOKENS = (
    "search" + "_claim",
    "SYNC_SEARCH_CASE" + "_CLAIM",
    "case_search" + "_advanced",
    "CASE_SEARCH" + "_ADVANCED",
    "commcare" + "_connect",
    "COMMCARE" + "_CONNECT",
    "mm_case" + "_properties",
    "MM_CASE" + "_PROPERTIES",
    "view_form" + "_attachments",
    "VIEW_FORM" + "_ATTACHMENT",
    "custom" + "_properties",
    "CUSTOM" + "_PROPERTIES",
    "CASE_UPDATES" + "_UCR_FILTERS",
    "RUN_AUTO_CASE_UPDATES" + "_ON_SAVE",
    "cc-index-case-search-" + "results",
    "cc-sync-after-" + "form",
    "NAMESPACE" + "_DOMAIN",
    "TAG" + "_FROZEN",
    "TAG_CONNECT" + "_DIVISION",
    "TAG" + "_DEPRECATED",
    "TAG_GA" + "_PATH",
)

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


def require_case_selection_authoring_contract(prose: str, label: str) -> None:
    for phrase in CASE_SELECTION_AUTHORING_CONTRACT:
        require(
            phrase in prose,
            f"{label} omits several-case authoring contract: {phrase}",
        )


def require_entry_point_contract(text: str, label: str) -> None:
    prose = " ".join(text.split())
    for tool in (*ENTRY_POINT_TOOLS, ENTRY_POINT_LINK_TOOL):
        for namespace in ("mcp__plugin_nova_nova__", "mcp__nova__"):
            require(
                f"{namespace}{tool}" in text,
                f"{label} omits {namespace}{tool}",
            )
    for phrase in ENTRY_POINT_AUTHORING_CONTRACT:
        require(phrase in prose, f"{label} omits deep-link contract: {phrase}")


def main() -> None:
    manifest = json.loads(
        (ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
    )
    require(manifest["name"] == "nova", "plugin name must remain nova")
    require(
        manifest["version"] == "1.32.0",
        "Plugin source contract requires version 1.32.0",
    )

    for path in GUIDANCE_FILES:
        text = path.read_text(encoding="utf-8")
        require_entry_point_contract(text, str(path.relative_to(ROOT)))
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
        for tool in CASE_SELECTION_TOOLS:
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
        require_case_selection_authoring_contract(
            prose, str(path.relative_to(ROOT))
        )
        if path.relative_to(ROOT) in {
            Path("skills/build/SKILL.md"),
            Path("skills/edit/SKILL.md"),
        }:
            require(
                "`confirmedModuleUuids` exactly equal to `requiredConfirmedModuleUuids`"
                in prose
                and "`confirmationToken` unchanged" in prose,
                f"{path.relative_to(ROOT)} omits reviewed several-case confirmation",
            )
        if path.relative_to(ROOT) in {
            Path("skills/build/SKILL.md"),
            Path("skills/autobuild/SKILL.md"),
        }:
            require(
                "parent with its writer form" in prose,
                f"{path.relative_to(ROOT)} omits the new-parent writer bootstrap",
            )
            require(
                "same `create_module` call as its case type, consuming form, fields, and Results columns"
                in prose
                and "The module is born complete" in prose,
                f"{path.relative_to(ROOT)} omits born-valid several-case creation",
            )
        if path.relative_to(ROOT) == Path("skills/edit/SKILL.md"):
            require(
                "create or update the writer form on the new or existing parent"
                in prose,
                "edit skill omits the existing-parent writer bootstrap",
            )
            require(
                "Pass `selection: null` to return to one case at a time" in prose
                and "Do not remove and recreate the module" in prose,
                "edit skill omits in-place several-case selection changes",
            )
            require(
                "changes whether a module opens one case or several, or changes the maximum number of cases"
                in prose,
                "edit skill does not load case selection for maximum-only changes",
            )
            require(
                "same `create_module` call as its case type, consuming form, fields, and Results columns"
                in prose
                and "The module is born complete" in prose,
                "edit skill omits born-valid several-case creation",
            )
        if path.relative_to(ROOT) == Path("skills/autobuild/SKILL.md"):
            require(
                "For `needs: \"confirmation\"`, do not submit confirmation fields"
                in prose
                and "An autonomous run has no person reviewing the current linked-module effects"
                in prose
                and "later interactive edit" in prose,
                "autobuild skill may approve linked changes without human review",
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
    require_entry_point_contract(agent_text, "autonomous agent")
    agent_allowlist = re.search(r"^tools: \[(.+)\]$", agent_text, re.MULTILINE)
    require(agent_allowlist is not None, "autonomous agent has no tool allowlist")
    for tool in (*ENTRY_POINT_TOOLS, ENTRY_POINT_LINK_TOOL):
        for namespace in ("mcp__plugin_nova_nova__", "mcp__nova__"):
            require(
                f"{namespace}{tool}" in agent_allowlist.group(1),
                f"autonomous agent allowlist omits {namespace}{tool}",
            )
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
    for tool in CASE_SELECTION_TOOLS:
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
    require_case_selection_authoring_contract(agent_prose, "autonomous agent")
    require(
        "same `create_module` call as its case type, consuming form, fields, and Results columns"
        in agent_prose
        and "The module is born complete" in agent_prose,
        "autonomous agent omits born-valid several-case creation",
    )
    require(
        "For `needs: \"confirmation\"`, do not submit confirmation fields"
        in agent_prose
        and "An autonomous run has no person reviewing the current linked-module effects"
        in agent_prose
        and "later interactive edit" in agent_prose,
        "autonomous agent may approve linked changes without human review",
    )
    require(
        "create or update the writer form on the new or existing parent"
        in agent_prose,
        "autonomous agent omits the existing-parent writer bootstrap",
    )
    require_prompt_paging_contract(agent_prose, "autonomous agent")

    for path in (*GUIDANCE_FILES, AUTONOMOUS_AGENT):
        text = path.read_text(encoding="utf-8")
        require(
            "check_project_space_compatibility" not in text
            and "project_space_compatibility" not in text
            and LEGACY_FEATURE_TOOL not in text
            and LEGACY_FEATURE_RESPONSE not in text
            and "project-space" not in text.lower()
            and "project space" not in text.lower()
            and "feature flag" not in text.lower()
            and "domain toggle" not in text.lower(),
            f"{path.relative_to(ROOT)} must stay focused on app design, not destination compatibility",
        )

    upload_text = UPLOAD_SKILL.read_text(encoding="utf-8")
    upload_prose = " ".join(upload_text.split())
    require(
        "`check_project_space_compatibility`" in upload_prose
        and "exact project space the user selected" in upload_prose
        and "`project_space_compatibility`" in upload_prose,
        "upload skill omits the explicit-destination compatibility check",
    )
    require(
        '`status: "blocked"' in upload_prose
        and "`missing` or `unverified`" in upload_prose
        and "Name **<target>** in every blocked notice" in upload_prose
        and "always include its `docs_url`" in upload_prose
        and "Nova has not uploaded anything" in upload_prose
        and "do not call `upload_app_to_hq`" in upload_prose,
        "upload skill does not stop before writes when required support is blocked",
    )
    require(
        "an advisory never blocks the upload" in upload_prose
        and "performance guidance" in upload_prose
        and "Success guarantees that `blockers` is empty" in upload_prose,
        "upload skill misstates non-blocking performance advice",
    )
    require(
        "never show capability `id` values" in upload_prose
        and "private project-space setting names" in upload_prose
        and "private setting slugs" in upload_prose,
        "upload skill does not protect the semantic compatibility vocabulary",
    )
    require(
        "`project_space_incompatible`" in upload_prose
        and "`hq_app_state_unknown`" in upload_prose,
        "upload skill omits current pre-write failure handling",
    )
    require(
        "After they choose, run the step 4 compatibility check for that exact space"
        in upload_prose
        and "Upload it to **<target>** now?" in upload_prose,
        "upload recovery or confirmation bypasses the selected destination",
    )
    require(
        LEGACY_FEATURE_TOOL not in upload_text
        and LEGACY_FEATURE_RESPONSE not in upload_text,
        "upload skill still depends on the legacy feature-setting contract",
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
    require(
        "## Project data tables" in readme,
        "README omits the public Project-data contract",
    )
    require(
        "## Several-case forms" in readme,
        "README omits the public several-case contract",
    )
    require(
        "choose up to 100 cases" in readme_prose
        and "follow-up or close form" in readme_prose
        and "one representative case" in readme_prose
        and "Each nonblank answer is saved to every selected case" in readme_prose
        and "leaving it blank preserves each case's existing value" in readme_prose
        and "starting value or calculation" in readme_prose
        and "Shared calculations and conditions cannot read an arbitrary case"
        in readme_prose
        and "applies nothing until the user accepts" in readme_prose
        and "the old review applies nothing" in readme_prose
        and "exact app item to repair" in readme_prose
        and "Preview creates neither" in readme_prose,
        "README omits visible several-case behavior or review safety",
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
    require(
        "`check_project_space_compatibility`" in readme_prose
        and "exact CommCare HQ project space" in readme_prose
        and "Missing or unverified required support blocks" in readme_prose
        and "Performance advice never blocks" in readme_prose,
        "README omits the semantic project-space compatibility contract",
    )
    require(
        LEGACY_FEATURE_TOOL not in readme
        and LEGACY_FEATURE_RESPONSE not in readme,
        "README still publishes the legacy feature-setting contract",
    )
    public_guidance = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (*GUIDANCE_FILES, AUTONOMOUS_AGENT, README, UPLOAD_SKILL)
    )
    for private_name in PRIVATE_DEPLOYMENT_TOKENS:
        require(
            re.search(
                rf"(?<![A-Za-z0-9_]){re.escape(private_name)}(?![A-Za-z0-9_])",
                public_guidance,
            )
            is None,
            f"public plugin guidance exposes private project-space setting: {private_name}",
        )
    for retired_name in RETIRED_FEATURE_CONTRACT_NAMES:
        require(
            retired_name not in public_guidance,
            f"public plugin guidance retains retired compatibility contract: {retired_name}",
        )
    require(
        "feature flag" not in public_guidance.lower()
        and "domain toggle" not in public_guidance.lower()
        and "requires the toggle" not in public_guidance.lower(),
        "public plugin guidance exposes private deployment settings",
    )

    upload_text = UPLOAD_SKILL.read_text(encoding="utf-8")
    upload_prose = " ".join(upload_text.split())
    for namespace in ("mcp__plugin_nova_nova__", "mcp__nova__"):
        require(
            f"{namespace}{ENTRY_POINT_LINK_TOOL}" in upload_text,
            f"upload skill omits {namespace}{ENTRY_POINT_LINK_TOOL}",
        )
    for phrase in (
        "Nova cannot build or release an app through the HQ API",
        "{app_id, server, domain, entry_point_uuid, selections}",
        "{module_uuid, case_ids}",
        "external HQ case IDs, never Nova case row IDs",
        "Call the verifier again after each upload, including a failed or partial upload",
        "recipient latest-build policy",
        "Do not open the link as a verification probe",
    ):
        require(phrase in upload_prose, f"upload skill omits deep-link contract: {phrase}")
    for tool in (*ENTRY_POINT_TOOLS, ENTRY_POINT_LINK_TOOL):
        require(tool in readme, f"README omits {tool}")

    print("Nova plugin source contract passed")


if __name__ == "__main__":
    main()
