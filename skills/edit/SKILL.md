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

The returned text can instead be a JSON `nova-agent-prompt-page`. When it is,
assemble the prompt before following any of it:

1. Require `kind` to be `nova-agent-prompt-page`, `protocol_version` to equal
   `1`, and `offset_unit` to equal `unicode-code-points` on every page. Interpret
   `chunk_start`, `chunk_end`, and `prompt_length` as Unicode code-point counts,
   never UTF-16 code units or bytes. Record the first page's `prompt_sha256` and
   `prompt_length`; require both values to remain unchanged on every page. You
   have no shell or hashing tool, so compare the advertised `prompt_sha256`
   values across pages and do not claim to recompute SHA-256.
2. Require the first `chunk_start` to be `0`, every later `chunk_start` to equal
   the preceding `chunk_end`. Nova's deterministic code-point slicer computes
   and cursor-validates these offsets; do not attempt to recount an arbitrary
   `prompt_chunk` yourself or claim that you did. Save each `prompt_chunk`
   exactly as returned, without inserting separators or normalizing it.
3. While `complete` is `false`, require one `next_cursor` and call
   `get_agent_prompt` again with the same `mode` and `app_id` values (`"edit"`
   and `"$0"`) plus that cursor. If Nova refuses because the snapshot changed,
   discard every chunk and restart without a cursor.
4. On the page where `complete` is `true`, require no `next_cursor` and require
   final `chunk_end` to equal `prompt_length`. Concatenate the exact
   `prompt_chunk` values in order, then require the assembled prompt to end with
   the line `NOVA-PROMPT-END` before acting on it. Stop and report a transport
   failure if any check fails.

If the response is ordinary text rather than a prompt page, keep the direct
marker check: a complete prompt ends with the line `NOVA-PROMPT-END`. If it
doesn't, the result was too large to deliver whole. Edit mode is where this
bites hardest: the blueprint summary is appended last, so a short delivery
costs you exactly the picture of the app you're about to change. When the
result names a file it was saved to, read that file and use its contents as the
prompt. If there's no such file, stop and tell the user `get_agent_prompt`
returned a truncated prompt; don't edit the app from a fragment, and don't
substitute a `get_app` call for the missing summary — the rest of the prompt is
missing too. A missing marker is a transport failure, never permission to
continue from partial instructions.

Always fetch fresh in edit mode — the inlined summary reflects the current blueprint, which may have changed since any earlier fetch in this conversation.

The Nova mutation tools are deferred — their schemas only appear in your context after a ToolSearch call. Don't rely on training memory of these tool shapes; pre-load the edit-path set in one ToolSearch call before continuing:

```
ToolSearch({query: "+nova get_app search_blueprint add_fields edit_field move_field remove_field update_form update_module move_module", max_results: 9})
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

When the edit sends a worker to a different form or module after submitting,
pre-load the after-submit link family:

```
ToolSearch({query: "select:mcp__plugin_nova_nova__add_form_links,mcp__plugin_nova_nova__update_form_link,mcp__plugin_nova_nova__remove_form_link,mcp__plugin_nova_nova__move_form_link,mcp__nova__add_form_links,mcp__nova__update_form_link,mcp__nova__remove_form_link,mcp__nova__move_form_link"})
```

When the edit splits a form into pages, moves a question between pages, or
merges pages back together, pre-load the one sections tool:

```
ToolSearch({query: "select:mcp__plugin_nova_nova__set_form_sections,mcp__nova__set_form_sections"})
```

When the edit touches app languages or translated worker content, pre-load the
complete language family:

```
ToolSearch({query: "select:mcp__plugin_nova_nova__get_languages,mcp__plugin_nova_nova__get_translatable_content,mcp__plugin_nova_nova__add_language,mcp__plugin_nova_nova__update_language,mcp__plugin_nova_nova__remove_language,mcp__plugin_nova_nova__update_translations,mcp__nova__get_languages,mcp__nova__get_translatable_content,mcp__nova__add_language,mcp__nova__update_language,mcp__nova__remove_language,mcp__nova__update_translations"})
```

When the edit has a reusable answer list whose saved values and labels should
stay consistent across questions, forms, case lists, or apps in one Project,
pre-load the complete Project-data family:

```
ToolSearch({query: "select:mcp__plugin_nova_nova__get_lookup_tables,mcp__plugin_nova_nova__get_lookup_table_rows,mcp__plugin_nova_nova__create_lookup_table,mcp__plugin_nova_nova__update_lookup_table,mcp__plugin_nova_nova__edit_lookup_columns,mcp__plugin_nova_nova__edit_lookup_rows,mcp__plugin_nova_nova__replace_lookup_rows,mcp__plugin_nova_nova__remove_lookup_table,mcp__plugin_nova_nova__set_field_options_source,mcp__nova__get_lookup_tables,mcp__nova__get_lookup_table_rows,mcp__nova__create_lookup_table,mcp__nova__update_lookup_table,mcp__nova__edit_lookup_columns,mcp__nova__edit_lookup_rows,mcp__nova__replace_lookup_rows,mcp__nova__remove_lookup_table,mcp__nova__set_field_options_source"})
```

A Project data table is Project-scoped, outside the app blueprint, so changing
it affects every app in the Project that uses it. A reusable answer list is a
design signal, not authority to change shared data. Call a Project-data write
only when the user's current request explicitly asks to create, change,
replace, or remove that data. Adding a lookup-backed question or asking to
reuse a list authorizes reading and referencing a matching table, not changing
the underlying table. Before any Project-data write, tell the user that it may
affect every app in the Project. Keep a question-specific list inline.

Read `get_lookup_tables` through `complete: true` before every write. Names,
tags, labels, and wire names support human-readable discovery; they are not
addresses. Keep the returned table and column UUIDs. Read the relevant current
rows with `get_lookup_table_rows` before editing, moving, replacing, or removing
them, and address existing rows only by the returned row UUIDs.

`create_lookup_table` atomically creates the complete initial schema and rows;
its request-local column keys are only handles for that call, while the result
returns the durable UUIDs. Every later write takes `expectedTableRevision`:
chain the returned `revisions.tableRevision`, and re-read after a conflict.
Use `edit_lookup_columns` and `edit_lookup_rows` for bounded atomic changes.
An `edit_lookup_rows` update replaces one complete row: send the complete
desired row, including every cell that must remain. Use `replace_lookup_rows`
only for a deliberate replacement of the table's entire row set, and
`remove_lookup_table` only when the table is unreferenced.

For a new lookup-backed select, pass the table, saved-value column, and display
column UUIDs as its `optionsSource` in the same `create_module`, `create_form`,
or `add_fields` call. When converting a field to a select, pass that
`optionsSource` in the same `edit_field` call. `set_field_options_source` is
only for changing an already-valid select's complete source. Never create a
temporary inline source or duplicate the table rows as inline choices.

`+nova` keeps the core search namespace-neutral. Each exact family selection lists both supported spellings without ranking: `mcp__plugin_nova_nova__*` for plugin OAuth and `mcp__nova__*` for a user-scope API-key override.

Nova supports exactly one submenu tier. Menu parentage organizes navigation;
case parentage is the separate case-type relationship that selects related
records at run time. Never infer `parentModuleUuid` from a case type's parent,
or infer a case relationship from a menu. Every parent and child module must
still have its own valid Form or case-list surface, and every Form has one
canonical owning module. Nested menus do not provide linked- or shadow-form
reuse; use deliberate module composition and case-list filters when several
views of the same data are needed.

A top-level parent and child that show different case types require the parent
to have at least one Form. A case-list-only root is rejected by
`NESTED_MENU_CROSS_TYPE_ROOT_REQUIRES_FORM` because the two selections cannot
otherwise be distinguished.

Read the current module tree and stable UUIDs before changing placement. For
`create_module`, omit `parentModuleUuid` for a top-level module and pass an
eligible root UUID for a child. For `move_module`, `after` remains the sibling
anchor: `null` means first in the effective destination. Omit
`parentModuleUuid` only to reorder within the module's current menu, pass
`null` to make it top-level, or pass an eligible root UUID to move it into that
submenu. An `after` UUID must be a sibling in that effective destination. A
child cannot be a parent, a root with children cannot become a child, and a
parent cannot be empty. Use `move_module`, never `update_module`, for menu
placement, and move or remove children before trying to remove their parent.
There is one construction-order exception: when an edit adds a form or case
change that creates the case type shown by its intended child viewer,
`MISSING_CHILD_CASE_MODULE` requires that viewer first. Create the child viewer
temporarily top-level, create or update the writer form on the new or existing
parent, then use `move_module` to place the viewer under the parent. This
temporary bootstrap changes no final menu or case ancestry.

Reply in the language of the user's latest substantive message. Conversation
language is independent from the app's source, runtime default, and target
worker languages; never switch the conversation merely because an app language
differs.

For every language edit, call `get_languages` first. Treat the canonical source
as the ordinary app content and every other language as an overlay. The source
language's identity can be replaced only while it is the sole language. Add a
target with `add_language` and an explicit existing `copyFrom`; it atomically
copies every effective string and marks the result Needs review, so no target
is born blank. Set the runtime default only after that language exists, and
change it before removing the current default. Never mix several languages
into one source label.

A language is an identity object `{language, script?, region?}`, never a
combined tag. `language` is an ISO 639:2023 Set 3 code for one individual
living language (`cmn`, `spa`, `hin`) — never a macrolanguage such as `zho`
and never a two-letter code. `script` is an ISO 15924 code (`Hans`), required
exactly when the language has more than one customary writing system. `region`
is an ISO 3166-1 alpha-2 code (`MX`), used where a country's conventions
differ and otherwise omitted. A rejected identifier names the identifiers to
use instead — a macrolanguage rejection lists its individual members. The
worker-facing name and text direction derive from the identity rather than
being authored; read identities back from tool results instead of assuming
what you sent.

Every individual living language is available for manual authoring and
copying. `get_languages` separately reports automatic translation for each
source-to-target pair as Available, Not evaluated, or Withheld. Nova's launch
policy marks pairs between distinct members of its 57-language launch set
Available, but the MCP surface has no paid automatic translation action. Never
treat your own language fluency as a substitute or bulk-translate by feeding
self-generated text through
`update_translations`. When the user supplies target text, page
`get_translatable_content` to completion for that target, preserve every typed
`protectedParts` reference, and write at most 50 distinct stable unit IDs per
atomic call. For a set, echo the unit's just-read current `sourceFingerprint`
as `expectedSourceFingerprint`. For a review, echo the explicit entry's
`sourceFingerprint` and exact value as `expectedSourceFingerprint` and
`expectedValue`, plus the unit's current `sourceFingerprint` as
`expectedCurrentSourceFingerprint`. Re-read the target after any concurrency
refusal; never mark copied or machine-authored text reviewed on the user's behalf.
If ordinary source content changed, report target entries that are now Out of
date instead of hiding the fallback.

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
standard closed-parent condition, and server-modified age, but no regex
condition; alerts admit direct-case value comparisons plus portable regex, but
no date, parent/host, closed-parent, or server-modified condition. Both admit at
most one UUID-backed location condition plus its descendant flag; preserve it
and report the returned guide's HQ-administrator application caveat. Names must
be nonblank and already trimmed; equality and update
literals must be exact nonblank/unquoted values. Do not invent a parent index, relationship, or
web-user recipient. Connect content cannot use matched-case, parent-case,
all-child-cases, case-property-email, or case-group recipients. A timed restart
property requires a rule-trigger start. Date conditions compare the current date
directly with the case-property date plus a signed day offset; a datetime
contributes its written calendar date only, discarding its time and explicit
offset. Host-scoped references remain representable only while the app has one
unambiguous canonical extension relation for the automation case type. If an
advanced case operation can add a second extension, Nova refuses host-scoped
criteria, update targets, update sources, and message case-property parts rather
than choose from HQ's unordered extensions; use a non-host scope or remove the
additional link. Every host-scoped reference also requires exactly one live
extension at runtime. Retained extra extension indices make the current-match
count unavailable when a criterion reads the host, and HQ does not define which
extension it chooses as the host. Use Nova standard property names in tool
input; returned guides project
`case_type`/`case_name`/
`date_opened`/`last_modified` to HQ `type`/`name`/`opened_on`/`modified_on`.
`case_id` and `case_type` are read-only. `status` is not representable,
standard datetimes do not accept equality/regex, and restart or event-time
fields accept custom properties only. After trimming, case-property event-time
values must begin with `H:MM` or `HH:MM`, and the whole value must parse as a
time. Suffixes such as AM/PM or seconds are accepted; blank, nonmatching, or
unparseable values use 12:00 PM.
Email content has one `body`. Use `plain-text { message }` for prose and
`rich-text { html }` when the message needs authored HTML. HQ sanitizes and
rewraps rich HTML, then derives its plaintext. Never invent parallel email
bodies or promise byte-exact rich output.
Message fields are structural `parts`: ordinary `text` remains literal even
when it looks like `{case.foo}` and the guide escapes its braces for HQ. An
explicit `case-property` part carries scope plus `(caseType, property)`
identity; a `context-property` part explicitly names a case-owner or recipient
field. Preserve and edit that canonical shape directly; never send or parse
magic token strings. A message `case-property` part cannot use `owner`, `host`,
or `last_modified_by` in any scope because HQ's formatter context shadows
same-named custom case data; rename the custom property, or use
`context-property` for the actual case-owner or recipient context. Registered
custom handler IDs, language codes, and
setup-only instructions are exact trimmed nonblank values, not instructional
placeholders. Preserve each setup-only instruction's `ucr-filter` or
`registered-custom` family and the additional setup in the returned guide.
Recipient-filter values are structural exact
literals or custom case-property references. Empty and whitespace literals are
meaningful; never rewrite a reference as brace-wrapped literal text. Preserve
the requirement that every triggering case contain each referenced property;
HQ raises when a direct lookup is missing. HQ filters only contacts that
resolve to user accounts, so never combine filters with case,
parent/child-case, case-email, case-group, or registered custom recipients;
those contacts bypass the filter or have an unknown runtime type. Preserve
the guide's system-administrator JSON-mode caveat when multiple keys/values or
blank/whitespace values require it. An alert using a registered custom recipient or custom content
handler requires an HQ system administrator to save it; preserve that returned
setup-guide caveat because project-admin access alone is insufficient.
Preserve content-specific guidance returned by Nova. Every resolved Connect
recipient must be a CommCare mobile worker with an active PersonalID link.
Checkbox-style,
case-property, and custom recipient kinds are singletons; list-backed kinds may
use each concrete target only once, and every concrete HQ ID is trimmed and
nonblank. Descendant controls require a location
recipient, location-level filters require descendants, and each worker-property
filter key may appear once.

Before pointing a question's choices at a Project data table, call `get_lookup_tables` — its table and column `id` values are the immutable UUIDs `set_field_options_source` needs, and the names and tags it returns are for explaining the choice, not for addressing it. A lookup source names its table plus the value and label columns (`tableId`, `valueColumnId`, `labelColumnId`), and may carry a row `filter`. That filter reads columns of the same table, fixed values, worker/session values, and answers from earlier in this form; it cannot read case data, a case-search answer, a later answer, or an answer inside a child or sibling repeat. The other source kind is inline choices, and setting either one replaces the field's whole source — nothing is kept in reserve.

Read the current sequence with `get_case_operations` before changing it, then `update_case_operation`, `remove_case_operation`, and `move_case_operation` by the operation's `operationUuid`. A case-bound field is still the simplest way for a form to save its own answers, so reach for `add_case_operations` only when a submission carries a further ordered effect: opening another case, updating or closing a known one, linking, renaming or retyping, assigning an owner, or repeating an effect per repeat entry. Every one of these tools names the form it acts on by `moduleUuid` + `formUuid`: take both from `get_module` or `search_blueprint`, and never guess or construct one. Inside the operation every reference is a UUID: a form answer is `{"kind":"field","uuid":"…"}`, a `forEach` repeat scope is that repeat field's UUID, and an earlier create is targeted as `{"kind":"op","opUuid":"…"}` (its resulting case id, inside a value expression, is `{"kind":"id-of","opUuid":"…"}`). The operation's own `id` stays a readable wire name, never an address. Within a single `add_case_operations` call a later item may consume an earlier create by predeclaring that create's `operationUuid`, so keep producer before consumer. The server-fetched prompt remains authoritative for each action's exact shape.

Load any additional tools (`create_form`, `remove_form`, `create_module`, `move_module`, `remove_module`, `generate_schema`, `get_module`, `get_form`, `get_field`, `get_lookup_tables`, `set_field_options_source`) on demand if a follow-up step needs them. A new case type enters an existing app through `generate_schema` — record it there before creating a module or fields that use it. To reposition an existing field, use `move_field` — it keeps the field's identity and every reference to it; never remove and re-add a field to move it. To change a field's kind, pass a different `kind` to `edit_field` — it converts in place (same identity/reference guarantee); converting to a select needs an `optionsSource` in the same call, and converting to `hidden` needs a `calculate`. On a case-bound field one call is property-wide — it also converts the property's same-kind writers in the app's other forms and updates its declared type, so never issue per-form convert calls for the same property. Never remove and re-add a field to change its kind either — if the target kind isn't a supported conversion (the error names the valid targets), surface the constraint to the user instead. A form's pages are sections: `set_form_sections` takes the complete desired partition of the form's top-level questions (kept pages by `sectionUuid`, new pages unnamed, an empty list un-pages the form) and plans the minimal change itself, so never build pages one `add_fields` or `move_field` call at a time — a half-sectioned form is refused by construction.

## 2. Confirm the change (if unsure)

Most edit instructions are specific enough to act on directly. If the instruction is clear, proceed.

If real ambiguity remains — vague scope ("clean up the registration form"), an unclear target ("the height field" when several exist), or missing details that would shape the change — ask one or two questions via AskUserQuestion before planning. Only ask about the user's *intent*; the blueprint is inlined, so don't ask about what already exists.

## 3. Plan the work

Use TaskCreate to outline the changes needed for this edit. There is no validation task — every mutation is checked as it lands, and a rejected call comes back with the reason so you can fix the input and re-issue it.

## 4. Apply the edits

Work through each task using the Nova tools per the fetched instructions. Mark each task `in_progress` when you start it and `completed` when it's done.

For a language task, keep the read/add/copy/manual-write/review sequence in the
plan and re-read `get_languages` after the final mutation so the handoff names
the actual default, targets, coverage, and remaining review work.

If a new ambiguity surfaces mid-edit, ask via AskUserQuestion before applying it.

## 5. Report

When the edits are done, return:

- **"App Name" (app_id)** on its own line
- The updated blueprint summary
- Any worker-property, role, or persona changes
- Any organization, place, or assignment changes
- Any automation changes, returned matching omissions, and the manual HQ setup boundary
- Any language, runtime-default, translation coverage, or review-state changes
