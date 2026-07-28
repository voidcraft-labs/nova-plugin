---
name: edit
description: 'Edit an existing CommCare app with a natural-language instruction. Asks clarifying questions when needed. Usage — quote the instruction: /nova:edit <app_id> "<instruction>"'
argument-hint: <app_id> "<instruction>"
---

# Task

The user wants to edit Nova app `$0` with this instruction: $1.

## 1. Operating instructions

First load the deferred prompt tool under both supported MCP spellings:

```
ToolSearch({query: "select:mcp__plugin_nova_nova__get_agent_prompt,mcp__nova__get_agent_prompt"})
```

Then call the loaded Nova `get_agent_prompt` tool with `mode: "edit"` and `app_id: "$0"`. The server inlines the app's current blueprint summary into the returned text — treat the full text as your operating instructions for this edit.

A complete prompt ends with the line `NOVA-PROMPT-END`. If yours doesn't, the result was too large to deliver whole. Edit mode is where this bites hardest: the blueprint summary is appended last, so a short delivery costs you exactly the picture of the app you're about to change. When the result names a file it was saved to, read that file and use its contents as the prompt. If there's no such file, stop and tell the user `get_agent_prompt` returned a truncated prompt; don't edit the app from a fragment, and don't substitute a `get_app` call for the missing summary — the rest of the prompt is missing too.

Always fetch fresh in edit mode — the inlined summary reflects the current blueprint, which may have changed since any earlier fetch in this conversation.

The Nova mutation tools are deferred — their schemas only appear in your context after a ToolSearch call. Don't rely on training memory of these tool shapes; pre-load the edit-path set in one ToolSearch call before continuing:

```
ToolSearch({query: "+nova get_app search_blueprint add_fields edit_field move_field remove_field update_form update_module", max_results: 8})
```

Pre-load the complete worker-information, role, and persona family with a separate deterministic exact selection:

```
ToolSearch({query: "select:mcp__plugin_nova_nova__get_users,mcp__plugin_nova_nova__add_user_properties,mcp__plugin_nova_nova__update_user_property,mcp__plugin_nova_nova__remove_user_property,mcp__plugin_nova_nova__add_user_types,mcp__plugin_nova_nova__update_user_type,mcp__plugin_nova_nova__remove_user_type,mcp__plugin_nova_nova__add_personas,mcp__plugin_nova_nova__update_persona,mcp__plugin_nova_nova__remove_persona,mcp__nova__get_users,mcp__nova__add_user_properties,mcp__nova__update_user_property,mcp__nova__remove_user_property,mcp__nova__add_user_types,mcp__nova__update_user_type,mcp__nova__remove_user_type,mcp__nova__add_personas,mcp__nova__update_persona,mcp__nova__remove_persona"})
```

Pre-load the ordered case-operation family the same way when the edit touches what a form does to cases beyond saving its own answers:

```
ToolSearch({query: "select:mcp__plugin_nova_nova__get_case_operations,mcp__plugin_nova_nova__add_case_operations,mcp__plugin_nova_nova__update_case_operation,mcp__plugin_nova_nova__remove_case_operation,mcp__plugin_nova_nova__move_case_operation,mcp__nova__get_case_operations,mcp__nova__add_case_operations,mcp__nova__update_case_operation,mcp__nova__remove_case_operation,mcp__nova__move_case_operation"})
```

`+nova` keeps the core search namespace-neutral. Each exact family selection lists both supported spellings without ranking: `mcp__plugin_nova_nova__*` for plugin OAuth and `mcp__nova__*` for a user-scope API-key override.

When an edit touches worker information, roles, or personas, call `get_users` first and target its stable UUIDs, never display names. Add properties first and use their returned UUIDs as role/persona value keys; add roles (`add_user_types`) before personas and link personas with the returned role UUIDs. Rename a property with `update_user_property` on that same UUID. In updates, omitted fields keep their values; in persona values, an omitted property inherits from the role while an explicitly present `""` overrides it with blank. The server-fetched prompt remains authoritative; use the loaded schemas for exact arguments.

Read the current sequence with `get_case_operations` before changing it, then `update_case_operation`, `remove_case_operation`, and `move_case_operation` by the operation's slug id. A case-bound field is still the simplest way for a form to save its own answers, so reach for `add_case_operations` only when a submission carries a further ordered effect: opening another case, updating or closing a known one, linking, renaming or retyping, assigning an owner, or repeating an effect per repeat entry. Address everything by author identity — module/form/operation slug ids and field paths like `visits/outcome` — never UUIDs. Within a single `add_case_operations` call a later item may consume an earlier create by its `operationId`, so keep producer before consumer. The server-fetched prompt remains authoritative for each action's exact shape.

Load any additional tools (`create_form`, `remove_form`, `create_module`, `remove_module`, `generate_schema`, `get_module`, `get_form`, `get_field`) on demand if a follow-up step needs them. A new case type enters an existing app through `generate_schema` — record it there before creating a module or fields that use it. To reposition an existing field, use `move_field` — it keeps the field's identity and every reference to it; never remove and re-add a field to move it. To change a field's kind, pass a different `kind` to `edit_field` — it converts in place (same identity/reference guarantee); converting to a select needs `options` in the same call, and converting to `hidden` needs a `calculate`. On a case-bound field one call is property-wide — it also converts the property's same-kind writers in the app's other forms and updates its declared type, so never issue per-form convert calls for the same property. Never remove and re-add a field to change its kind either — if the target kind isn't a supported conversion (the error names the valid targets), surface the constraint to the user instead.

## 2. Confirm the change (if unsure)

Most edit instructions are specific enough to act on directly. If the instruction is clear, proceed.

If real ambiguity remains — vague scope ("clean up the registration form"), an unclear target ("the height field" when several exist), or missing details that would shape the change — ask one or two questions via AskUserQuestion before planning. Only ask about the user's *intent*; the blueprint is inlined, so don't ask about what already exists.

## 3. Plan the work

Use TaskCreate to outline the changes needed for this edit. There is no validation task — every mutation is checked as it lands, and a rejected call comes back with the reason so you can fix the input and re-issue it.

## 4. Apply the edits

Work through each task using the Nova tools per the fetched instructions. Mark each task `in_progress` when you start it and `completed` when it's done.

If a new ambiguity surfaces mid-edit, ask via AskUserQuestion before applying it.

## 5. Report

When the edits are done, return:

- **"App Name" (app_id)** on its own line
- The updated blueprint summary
- Any worker-property, role, or persona changes
