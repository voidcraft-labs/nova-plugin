---
name: edit
description: 'Edit an existing CommCare app with a natural-language instruction. Asks clarifying questions when needed. Usage — quote the instruction: /nova:edit <app_id> "<instruction>"'
argument-hint: <app_id> "<instruction>"
---

# Task

The user wants to edit Nova app `$0` with this instruction: $1.

## 1. Operating instructions

Call Nova's `get_agent_prompt` tool with `mode: "edit"` and `app_id: "$0"`. The server inlines the app's current blueprint summary into the returned text — treat the full text as your operating instructions for this edit.

Always fetch fresh in edit mode — the inlined summary reflects the current blueprint, which may have changed since any earlier fetch in this conversation.

The Nova mutation tools are deferred — their schemas only appear in your context after a ToolSearch call. Don't rely on training memory of these tool shapes; pre-load the edit-path set in one ToolSearch call before continuing:

```
ToolSearch({query: "+nova get_app search_blueprint add_fields edit_field move_field remove_field update_form update_module", max_results: 8})
```

Pre-load the complete worker-information, role, and persona family in a separate search with enough capacity for every schema:

```
ToolSearch({query: "+nova get_users add_user_properties update_user_property remove_user_property add_user_types update_user_type remove_user_type add_personas update_persona remove_persona", max_results: 10})
```

The `+nova` filter matches whichever Nova namespace is live (`mcp__plugin_nova_nova__*` when using the plugin's OAuth, `mcp__nova__*` when an API-key override is in user-scope).

When an edit touches worker information, roles, or personas, call `get_users` first and target its stable UUIDs, never display names. Add properties first and use their returned UUIDs as role/persona value keys; add roles (`add_user_types`) before personas and link personas with the returned role UUIDs. Rename a property with `update_user_property` on that same UUID. In updates, omitted fields keep their values; in persona values, an omitted property inherits from the role while an explicitly present `""` overrides it with blank. The server-fetched prompt remains authoritative; use the loaded schemas for exact arguments.

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
