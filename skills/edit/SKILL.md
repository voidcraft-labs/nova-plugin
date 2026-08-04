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

When the edit touches organization levels, places, assignments, or place ownership, pre-load the complete organization family:

```
ToolSearch({query: "select:mcp__plugin_nova_nova__get_organization,mcp__plugin_nova_nova__add_organization_levels,mcp__plugin_nova_nova__update_organization_level,mcp__plugin_nova_nova__remove_organization_level,mcp__plugin_nova_nova__add_location_properties,mcp__plugin_nova_nova__update_location_property,mcp__plugin_nova_nova__remove_location_property,mcp__plugin_nova_nova__create_location,mcp__plugin_nova_nova__update_location,mcp__plugin_nova_nova__move_location,mcp__plugin_nova_nova__set_location_archived,mcp__nova__get_organization,mcp__nova__add_organization_levels,mcp__nova__update_organization_level,mcp__nova__remove_organization_level,mcp__nova__add_location_properties,mcp__nova__update_location_property,mcp__nova__remove_location_property,mcp__nova__create_location,mcp__nova__update_location,mcp__nova__move_location,mcp__nova__set_location_archived"})
```

When the edit touches an automatic case update, conditional alert, reminder,
or scheduled message, pre-load the complete automation family:

```
ToolSearch({query: "select:mcp__plugin_nova_nova__get_automations,mcp__plugin_nova_nova__add_automations,mcp__plugin_nova_nova__update_automation,mcp__plugin_nova_nova__remove_automation,mcp__nova__get_automations,mcp__nova__add_automations,mcp__nova__update_automation,mcp__nova__remove_automation"})
```

Pre-load the ordered case-operation family the same way when the edit touches what a form does to cases beyond saving its own answers:

```
ToolSearch({query: "select:mcp__plugin_nova_nova__get_case_operations,mcp__plugin_nova_nova__add_case_operations,mcp__plugin_nova_nova__update_case_operation,mcp__plugin_nova_nova__remove_case_operation,mcp__plugin_nova_nova__move_case_operation,mcp__nova__get_case_operations,mcp__nova__add_case_operations,mcp__nova__update_case_operation,mcp__nova__remove_case_operation,mcp__nova__move_case_operation"})
```

`+nova` keeps the core search namespace-neutral. Each exact family selection lists both supported spellings without ranking: `mcp__plugin_nova_nova__*` for plugin OAuth and `mcp__nova__*` for a user-scope API-key override.

When an edit touches worker information, roles, or personas, call `get_users` first and target its stable UUIDs, never display names. Add properties first and use their returned UUIDs as role/persona value keys; add roles (`add_user_types`) before personas and link personas with the returned role UUIDs. Rename a property with `update_user_property` on that same UUID. In updates, omitted fields keep their values, and one role or persona value changes per call through `valuePatch`: it names one `userPropertyUuid`, a string sets that value and `null` clears it, and omitting `valuePatch` leaves every value alone — so two values are two calls. A persona that carries no value for a property inherits the role's; an explicit `""` overrides the role with blank. The server-fetched prompt remains authoritative; use the loaded schemas for exact arguments.

For an organization edit, call `get_organization` first, page with its opaque, snapshot-bound `cursor` until `page.complete` is true, and restart without a cursor if a later page reports that the snapshot changed. Its one bounded cursor pages across levels, place-information fields, and matching places, so accumulate every collection rather than expecting the complete shape on each page. Target stable UUIDs, never names. Use `query` for a large tree and request `includeValues` only when needed. Levels are blueprint structure and places are app-scoped rows: add levels parent-first, add place-information declarations before their values, and carry the exact current organization revision into every create, update, move, archive, or unarchive. Level case-flow and address-book objects are complete replacements, so preserve every nested setting the edit does not change. Chain each successful write's returned revision into the next write; re-read after a conflict. If a saved reverse-hop owner rule requires a destination below every new source, pass the complete bounded, structurally nested `descendants` tree in that source's `create_location` call and keep the final UUIDs from its compact mirrored receipt; sequential creates are correctly refused. Use `valuePatch` for exactly one UUID-keyed custom value per call; `values` replaces the whole bag. Level codes and place site codes are create-once identities. Case flow controls ownership and delivery independently from address-book visibility. A persona's `locationUuids` replace its complete assignment in main-first order. Archiving is a confirmed two-call flow: fetch its bounded impact and exact token first, review it, then resend the unchanged payload with `confirm=true` and `expectedRevision` set to the returned `expectedRevisionForConfirmation`; never confirm a blocked preflight. It archives the subtree and removes assignments there, but never reassigns the cases it owns.

For an automation edit, call `get_automations` first and preserve the returned
automation UUID, kind, and every nested UUID that still represents the same
item. `update_automation` takes the complete desired rule, so carry forward all
unrelated criteria, setup-only instructions, updates, recipients, events, and
user filters; omission removes the nested item. Use only the loaded closed
schema. `get_automations` and successful add/update results return regenerated
manual CommCare HQ setup guidance and locally omitted criteria; remove returns
only its deletion receipt. Nova does not execute, install, or remove an HQ
rule. Builder Preview's separate current-match count is read-only; MCP does not
return that count. Never describe either surface as automation execution or a
prediction of the next HQ sweep.
Keep every schedule to one content type and each timed schedule within one HQ
setup form: all events share a timing mode, and Weekly and Monthly also share content. Preserve the loaded schema's
ordering, five-minute separation, random-window, day, offset, survey-expiration,
and partial-submission dependencies.
Weekly event days are offsets from `startDayOfWeek`, not absolute weekday
numbers. The two kinds have different criteria: automatic updates admit
value/date comparisons against case, parent, or host properties, at most one
standard closed-parent condition, and server-modified age, but no regex or
location condition; alerts admit direct-case value comparisons plus portable
regex, but no date, parent/host, closed-parent, location, or server-modified
condition. Names must be nonblank and already trimmed; equality and update
literals must be exact nonblank/unquoted values. Do not invent a parent index, relationship, or
web-user recipient. Connect content cannot use matched-case, parent-case,
all-child-cases, case-property-email, or case-group recipients. A timed restart
property requires a rule-trigger start.

Before pointing a question's choices at a Project data table, call `get_lookup_tables` — its table and column `id` values are the immutable UUIDs `set_field_options_source` needs, and the names and tags it returns are for explaining the choice, not for addressing it. A lookup source names its table plus the value and label columns (`tableId`, `valueColumnId`, `labelColumnId`), and may carry a row `filter`. That filter reads columns of the same table, fixed values, worker/session values, and answers from earlier in this form; it cannot read case data, a case-search answer, a later answer, or an answer inside a child or sibling repeat. The other source kind is inline choices, and setting either one replaces the field's whole source — nothing is kept in reserve.

Read the current sequence with `get_case_operations` before changing it, then `update_case_operation`, `remove_case_operation`, and `move_case_operation` by the operation's `operationUuid`. A case-bound field is still the simplest way for a form to save its own answers, so reach for `add_case_operations` only when a submission carries a further ordered effect: opening another case, updating or closing a known one, linking, renaming or retyping, assigning an owner, or repeating an effect per repeat entry. Every one of these tools names the form it acts on by `moduleUuid` + `formUuid`: take both from `get_module` or `search_blueprint`, and never guess or construct one. Inside the operation every reference is a UUID: a form answer is `{"kind":"field","uuid":"…"}`, a `forEach` repeat scope is that repeat field's UUID, and an earlier create is targeted as `{"kind":"op","opUuid":"…"}` (its resulting case id, inside a value expression, is `{"kind":"id-of","opUuid":"…"}`). The operation's own `id` stays a readable wire name, never an address. Within a single `add_case_operations` call a later item may consume an earlier create by predeclaring that create's `operationUuid`, so keep producer before consumer. The server-fetched prompt remains authoritative for each action's exact shape.

Load any additional tools (`create_form`, `remove_form`, `create_module`, `remove_module`, `generate_schema`, `get_module`, `get_form`, `get_field`, `get_lookup_tables`, `set_field_options_source`) on demand if a follow-up step needs them. A new case type enters an existing app through `generate_schema` — record it there before creating a module or fields that use it. To reposition an existing field, use `move_field` — it keeps the field's identity and every reference to it; never remove and re-add a field to move it. To change a field's kind, pass a different `kind` to `edit_field` — it converts in place (same identity/reference guarantee); converting to a select needs an `optionsSource` in the same call, and converting to `hidden` needs a `calculate`. On a case-bound field one call is property-wide — it also converts the property's same-kind writers in the app's other forms and updates its declared type, so never issue per-form convert calls for the same property. Never remove and re-add a field to change its kind either — if the target kind isn't a supported conversion (the error names the valid targets), surface the constraint to the user instead.

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
- Any organization, place, or assignment changes
- Any automation changes, returned matching omissions, and the manual HQ setup boundary
