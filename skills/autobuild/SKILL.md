---
name: autobuild
description: Generate a CommCare app from a natural-language spec, autonomously, without asking the user clarifying questions. Use when the user wants a one-shot build.
argument-hint: <spec describing the app>
allowed-tools: Agent(nova:nova-architect-autonomous)
---

# Task

Invoke the Agent tool with `subagent_type: "nova:nova-architect-autonomous"` and this prompt:

```
{
  "mode": "autonomous_build",
  "task": "$ARGUMENTS"
}

Follow your bootstrap: first load the deferred prompt tool under either
supported MCP namespace:

ToolSearch({query: "select:mcp__plugin_nova_nova__get_agent_prompt,mcp__nova__get_agent_prompt"})

Then call the loaded Nova `get_agent_prompt` tool with the mode above
(no app_id — build modes have no app to read from). Check that the text
ends with `NOVA-PROMPT-END` before using it; if it doesn't, follow your
bootstrap invariant and report the truncation instead of building. The
Nova mutation tools are deferred — pre-load their schemas in one
ToolSearch call before your first mutation:

ToolSearch({query: "+nova create_app generate_schema create_module update_app", max_results: 4})

Pre-load the complete worker-information, role, and persona family in
a separate deterministic exact selection:

ToolSearch({query: "select:mcp__plugin_nova_nova__get_users,mcp__plugin_nova_nova__add_user_properties,mcp__plugin_nova_nova__update_user_property,mcp__plugin_nova_nova__remove_user_property,mcp__plugin_nova_nova__add_user_types,mcp__plugin_nova_nova__update_user_type,mcp__plugin_nova_nova__remove_user_type,mcp__plugin_nova_nova__add_personas,mcp__plugin_nova_nova__update_persona,mcp__plugin_nova_nova__remove_persona,mcp__nova__get_users,mcp__nova__add_user_properties,mcp__nova__update_user_property,mcp__nova__remove_user_property,mcp__nova__add_user_types,mcp__nova__update_user_type,mcp__nova__remove_user_type,mcp__nova__add_personas,mcp__nova__update_persona,mcp__nova__remove_persona"})

When the task depends on places, pre-load the complete organization
family in a separate deterministic exact selection:

ToolSearch({query: "select:mcp__plugin_nova_nova__get_organization,mcp__plugin_nova_nova__add_organization_levels,mcp__plugin_nova_nova__update_organization_level,mcp__plugin_nova_nova__remove_organization_level,mcp__plugin_nova_nova__add_location_properties,mcp__plugin_nova_nova__update_location_property,mcp__plugin_nova_nova__remove_location_property,mcp__plugin_nova_nova__create_location,mcp__plugin_nova_nova__update_location,mcp__plugin_nova_nova__move_location,mcp__plugin_nova_nova__set_location_archived,mcp__nova__get_organization,mcp__nova__add_organization_levels,mcp__nova__update_organization_level,mcp__nova__remove_organization_level,mcp__nova__add_location_properties,mcp__nova__update_location_property,mcp__nova__remove_location_property,mcp__nova__create_location,mcp__nova__update_location,mcp__nova__move_location,mcp__nova__set_location_archived"})

Pre-load the ordered case-operation family the same way when the task
has a form doing more to cases than saving its own answers:

ToolSearch({query: "select:mcp__plugin_nova_nova__get_case_operations,mcp__plugin_nova_nova__add_case_operations,mcp__plugin_nova_nova__update_case_operation,mcp__plugin_nova_nova__remove_case_operation,mcp__plugin_nova_nova__move_case_operation,mcp__nova__get_case_operations,mcp__nova__add_case_operations,mcp__nova__update_case_operation,mcp__nova__remove_case_operation,mcp__nova__move_case_operation"})

`+nova` keeps the core search namespace-neutral. Each exact family
selection lists both supported spellings without ranking:
`mcp__plugin_nova_nova__*` for plugin OAuth and `mcp__nova__*` for a
user-scope API-key override. Every other Nova tool your instructions
send you to — `configure_connect` for a Connect app, `get_lookup_tables`
and `set_field_options_source` for Project data, `rename_case_properties`
— is deferred the same way; select it by both spellings before its
first use. Then build the CommCare app matching the task autonomously.
Make every design decision yourself.

When the task requests custom worker properties, create and name the
app, then immediately call `get_users` and `add_user_properties`.
Do not call `generate_schema`, create modules or forms, or author any
condition or calculation that may reference those properties first.
Typed Predicate/ValueExpression inputs and role/persona values use
`userPropertyUuid`. Expression slots take Nova's typed AST, not an
XPath source string: a worker property is
`{"kind":"user-property-ref","userPropertyUuid":"…"}` in prose and
`{"kind":"session-user-property","userPropertyUuid":"…"}` in a Predicate
or ValueExpression. Do not send `#user/<slug>` text for Nova to
resolve — an unresolved hashtag is refused, not parsed. Rename the
property later with
`update_user_property` on that same returned UUID. Roles may follow the
reference-bearing structure; add roles
(`add_user_types`) before personas and link personas with the returned
role UUIDs. When the task requests only roles or personas, still call
`get_users` before mutating them and target its stable UUIDs. In
updates, omitted fields keep their values, and one role or persona
value changes per call through `valuePatch`: it names one
`userPropertyUuid`, a string sets that value and `null` clears it, and
omitting `valuePatch` leaves every value alone. A persona that carries
no value for a property inherits the role's; an explicit `""` overrides
the role with blank. The server-fetched prompt remains authoritative
subject to this ordering; use the loaded schemas for exact arguments.

When the task depends on districts, facilities, worker assignments, or
place ownership, call `get_organization`, follow its opaque, snapshot-bound
`cursor` pages until `page.complete`, and restart without a cursor if the
snapshot changed. Its one bounded cursor pages across levels, place-information
fields, and matching places, so accumulate every collection. Add levels
parent-first, add place-information fields, then create the places. Read the
complete organization before changing an existing declaration: level case-flow
and address-book objects are complete replacements, so preserve every nested
setting the edit does not change. Keep every returned UUID and treat level codes and site
codes as create-once identities. Case flow controls ownership and delivery
independently from address-book visibility. Chain the exact revision returned
by every create, update, move, archive, and unarchive into the next place
write; re-read after a conflict and use `valuePatch` for exactly one custom
value per call. If a saved reverse-hop owner rule requires a destination below every
new source, pass the complete bounded, structurally nested `descendants` tree
in that source's `create_location` call and keep the final UUIDs from its
compact mirrored receipt; sequential creates are correctly refused.
Create places before modules that name location owners and before
assigning personas through `locationUuids` (main first). Archiving is a
two-call confirmation: fetch the bounded impact and exact token, review it,
then repeat with that unchanged payload and `expectedRevision` set to the
returned `expectedRevisionForConfirmation`; never confirm a blocked preflight.
It removes persona assignments but never reassigns owned cases.

Every tool call is validated as it lands, so there is no separate
validation step. Place-owner rules are Preview-only until Nova ships device
location data and HQ identity mapping, so report that export boundary when
one is used. Begin your completion message with the app on its OWN
FIRST LINE, formatted as `**"<app_name>" (<app_id>)**` — `app_id`
from `create_app`'s result, `app_name` as you set it (`create_app`'s
`app_name`, or `update_app`) — e.g. for app_name "Malaria ITN FGD"
and app_id "1c9de4a2-7b31-4f2e-9a44-d0b6c58f3e7a", emit:

**"Malaria ITN FGD" (1c9de4a2-7b31-4f2e-9a44-d0b6c58f3e7a)**

Emit that line FIRST — before any summary — so the identifier survives
even if the rest of the message runs long or is cut off. Do not report
the app complete after only `create_app`, `generate_schema`, and
`create_module`: requested worker properties, roles, and personas must
also succeed and be confirmed from their tool results. Follow the id
line with a summary of modules and forms, requested worker properties,
roles, personas, organization levels, places, and assignments, any validation notes, and the design decisions
you made. At the final handoff, after every requested mutation and
validation task is complete and no more app edits are planned, call
`get_app_hq_feature_flags` exactly once without a domain, with the app id from
`create_app`. Do not call it after individual mutations, while planning, or
while editing. This is CommCare HQ deployment information, not a Nova
authoring gate. No matter what the response says, do not remove, undo, avoid,
or revise requested functionality, and make no mutation because of it. Do not
infer requirements yourself. If `feature_flag_requirements.required_flags` is
non-empty, add only those returned requirements as a brief note in this same
completion message, preserving that `domain_checked: false` means the
destination has not been checked. If the list is empty, omit the note. If the
read check itself is unavailable, finish normally without retrying, changing
the app, or creating a separate document or communication surface for it.
```

Return the subagent's report, verbatim.
