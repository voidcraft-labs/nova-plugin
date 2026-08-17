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
deterministic ToolSearch call before your first mutation:

ToolSearch({query: "select:mcp__plugin_nova_nova__create_app,mcp__plugin_nova_nova__generate_schema,mcp__plugin_nova_nova__create_module,mcp__plugin_nova_nova__update_app,mcp__nova__create_app,mcp__nova__generate_schema,mcp__nova__create_module,mcp__nova__update_app"})

When the task names a target Nova Project — a shared workspace whose
members all see the app — resolve it before creating the app: select
`list_projects` by both spellings the same way, call it, match the
named Project, and pass its `project_id` to `create_app`. When no
Project is named, omit `project_id`; the app lands in the user's
personal Project.

Pre-load the complete worker-information, role, and persona family in
a separate deterministic exact selection:

ToolSearch({query: "select:mcp__plugin_nova_nova__get_users,mcp__plugin_nova_nova__add_user_properties,mcp__plugin_nova_nova__update_user_property,mcp__plugin_nova_nova__remove_user_property,mcp__plugin_nova_nova__add_user_types,mcp__plugin_nova_nova__update_user_type,mcp__plugin_nova_nova__remove_user_type,mcp__plugin_nova_nova__add_personas,mcp__plugin_nova_nova__update_persona,mcp__plugin_nova_nova__remove_persona,mcp__nova__get_users,mcp__nova__add_user_properties,mcp__nova__update_user_property,mcp__nova__remove_user_property,mcp__nova__add_user_types,mcp__nova__update_user_type,mcp__nova__remove_user_type,mcp__nova__add_personas,mcp__nova__update_persona,mcp__nova__remove_persona"})

When the task depends on places, pre-load the complete organization
family in a separate deterministic exact selection:

ToolSearch({query: "select:mcp__plugin_nova_nova__get_organization,mcp__plugin_nova_nova__add_organization_levels,mcp__plugin_nova_nova__update_organization_level,mcp__plugin_nova_nova__remove_organization_level,mcp__plugin_nova_nova__add_location_properties,mcp__plugin_nova_nova__update_location_property,mcp__plugin_nova_nova__remove_location_property,mcp__plugin_nova_nova__create_location,mcp__plugin_nova_nova__update_location,mcp__plugin_nova_nova__move_location,mcp__plugin_nova_nova__set_location_archived,mcp__nova__get_organization,mcp__nova__add_organization_levels,mcp__nova__update_organization_level,mcp__nova__remove_organization_level,mcp__nova__add_location_properties,mcp__nova__update_location_property,mcp__nova__remove_location_property,mcp__nova__create_location,mcp__nova__update_location,mcp__nova__move_location,mcp__nova__set_location_archived"})

When the task requests an automatic case update, conditional alert,
reminder, or scheduled message, pre-load the complete automation family:

ToolSearch({query: "select:mcp__plugin_nova_nova__get_automations,mcp__plugin_nova_nova__add_automations,mcp__plugin_nova_nova__update_automation,mcp__plugin_nova_nova__remove_automation,mcp__nova__get_automations,mcp__nova__add_automations,mcp__nova__update_automation,mcp__nova__remove_automation"})

Pre-load the ordered case-operation family the same way when the task
has a form doing more to cases than saving its own answers:

ToolSearch({query: "select:mcp__plugin_nova_nova__get_case_operations,mcp__plugin_nova_nova__add_case_operations,mcp__plugin_nova_nova__update_case_operation,mcp__plugin_nova_nova__remove_case_operation,mcp__plugin_nova_nova__move_case_operation,mcp__nova__get_case_operations,mcp__nova__add_case_operations,mcp__nova__update_case_operation,mcp__nova__remove_case_operation,mcp__nova__move_case_operation"})

When the task requests non-English worker content or multiple app
languages, pre-load the complete language family:

ToolSearch({query: "select:mcp__plugin_nova_nova__get_languages,mcp__plugin_nova_nova__get_translatable_content,mcp__plugin_nova_nova__add_language,mcp__plugin_nova_nova__update_language,mcp__plugin_nova_nova__remove_language,mcp__plugin_nova_nova__update_translations,mcp__nova__get_languages,mcp__nova__get_translatable_content,mcp__nova__add_language,mcp__nova__update_language,mcp__nova__remove_language,mcp__nova__update_translations"})

Each exact selection lists both supported spellings without ranking:
`mcp__plugin_nova_nova__*` for plugin OAuth and `mcp__nova__*` for a
user-scope API-key override; the spelling that isn't connected simply
matches nothing. Every other Nova tool your instructions
send you to — `configure_connect` for a Connect app, `get_lookup_tables`
and `set_field_options_source` for Project data, `rename_case_properties`
for an app-wide rename, and `configure_case_list` or
`set_case_list_tile` for a composed case list — is deferred the same
way; select it by both spellings before its first use. Then build the
CommCare app matching the task autonomously. Make every design decision
yourself.

Reply in the language of the user's latest substantive message. That
conversation language is independent from the app's source, runtime default,
and target worker languages; never switch the conversation merely because an
app language differs.

When the task requests non-English worker content or multiple app languages,
choose the canonical source language, runtime default, ordered targets, and
each target's copy source explicitly. Author every worker-facing name, label,
hint, option, message, and composition string in the canonical source language.
Do not stack multiple languages into one string. Finish every structural and
source-content mutation before the language phase, because only then does the
complete translation inventory exist.

At the language phase, call `get_languages`. If the requested source is a
different language, call `update_language` with `change-identity` while it
remains the sole language. Add targets in dependency order with
`add_language` and an existing `copyFrom`; each target receives a complete
effective projection and starts Needs review rather than blank. Set the
runtime default only after its language exists.

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
treat your own language fluency as a substitute or
bulk-translate self-generated text through `update_translations`. Only save
target text supplied by the user: page `get_translatable_content` to completion,
preserve typed `protectedParts`, and write at most 50 distinct stable unit IDs
per atomic call. For a set, echo the unit's just-read current
`sourceFingerprint` as `expectedSourceFingerprint`. For a review, echo the
explicit entry's `sourceFingerprint` and exact value as
`expectedSourceFingerprint` and `expectedValue`, plus the unit's current
`sourceFingerprint` as `expectedCurrentSourceFingerprint`. Re-read the target
after any concurrency refusal; never mark copied or machine-authored text
reviewed on the user's behalf. Report incomplete, Out of date, and Needs review
coverage.

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

When the task requests automations, add them after their case types, forms,
worker information, and places exist. Predeclare stable UUIDs for the complete
rule and every nested item, and use only the loaded schema's closed vocabulary.
UCR and registered custom criteria are distinct setup-only kinds;
automatic-update server-modified age is a
separate structured field. None executes locally. Builder Preview may count current real open cases, but MCP does not
return that count. `get_automations` and successful add/update results return
the regenerated manual setup guide and locally omitted criteria; remove returns
only its deletion receipt. Nova never updates a case, sends a message, advances
a schedule, or installs the rule in CommCare HQ. Report the returned guide and
omissions after get/add/update; never promise that uploading configures it.
Schedules use one content type, and timed schedules must map to one CommCare HQ
setup form: every event shares one timing mode, and Weekly and Monthly also share content. Obey the loaded schema's
ordering, five-minute separation, random-window, day, offset, survey-expiration,
and partial-submission dependencies.
Weekly event days are offsets from `startDayOfWeek`, not absolute weekday
numbers. Automatic updates admit value/date comparisons against case, parent,
or host properties, at most one standard closed-parent condition, and
server-modified age; they have no regex condition. Alerts admit direct-case
value comparisons plus portable regex, with no date, parent/host,
closed-parent, or server-modified condition. Both admit at most one UUID-backed
location condition plus its descendant flag; preserve it and report the
returned guide's HQ-administrator application caveat. Names must be nonblank
and already trimmed; equality and update literals must be exact
nonblank/unquoted values. Do not invent a parent index, relationship, or web-user
recipient. Connect content cannot use matched-case, parent-case, all-child-cases,
case-property-email, or case-group recipients. A timed restart property requires
a rule-trigger start. Date conditions compare the current date directly with
the case-property date plus a signed day offset; a datetime contributes its
written calendar date only, discarding its time and explicit offset. Host-scoped
references remain representable only while the app has one unambiguous canonical
extension relation for the automation case type. If an advanced case operation
can add a second extension, Nova refuses host-scoped criteria, update targets,
update sources, and message case-property parts rather than choose from HQ's
unordered extensions; use a non-host scope or remove the additional link. Every
host-scoped reference also requires exactly one live extension at runtime.
Retained extra extension indices make the current-match count unavailable when
a criterion reads the host, and HQ does not define which extension it chooses
as the host. Use Nova
standard property names in tool input; returned guides project `case_type`/`case_name`/
`date_opened`/`last_modified` to HQ `type`/`name`/`opened_on`/`modified_on`.
`case_id` and `case_type` are read-only. `status` is not representable,
standard datetimes do not accept equality/regex, and restart or event-time
fields accept custom properties only. After trimming, case-property event-time
values must begin with `H:MM` or `HH:MM`, and the whole value must parse as a
time. Suffixes such as AM/PM or seconds are accepted; blank, nonmatching, or
unparseable values use 12:00 PM.
Email content has one `body`:
`plain-text { message }` targets a domain without Rich text emails, while
`rich-text { html }` requires the toggle and is sanitized/rewrapped by HQ with
plaintext derived from it. Never invent parallel email bodies or promise
byte-exact rich output.
Message fields are structural `parts`: ordinary `text` remains literal even
when it looks like `{case.foo}` and the guide escapes its braces for HQ. An
explicit `case-property` part carries scope plus `(caseType, property)`
identity; a `context-property` part explicitly names a case-owner or recipient
field. Use that canonical shape directly; never send or parse magic token
strings. A message `case-property` part cannot use `owner`, `host`, or
`last_modified_by` in any scope because HQ's formatter context shadows
same-named custom case data; rename the custom property, or use
`context-property` for the actual case-owner or recipient context. Registered
custom handler IDs, language codes, and setup-only
instructions are exact trimmed nonblank values, not instructional placeholders.
Use `ucr-filter` only for a UCR definition and `registered-custom` only for an
instance-registered criterion; the returned guide names the former's
`CASE_UPDATES_UCR_FILTERS` toggle and the latter's system-administrator save
requirement. Recipient-filter values are structural exact literals or custom
case-property references. Empty and whitespace literals are meaningful; never
encode a lookup as a brace-wrapped literal because HQ executes it dynamically.
Every triggering case must contain each referenced property because HQ raises
when its direct lookup is missing. HQ filters only contacts that resolve to
user accounts, so never combine filters with case, parent/child-case,
case-email, case-group, or registered custom recipients; those contacts bypass
the filter or have an unknown runtime type.
The guide emits exact JSON and names the new-alert system-administrator
prerequisite when multiple keys/values or blank/whitespace values require it.
An alert using a registered custom recipient or custom content handler requires
an HQ system administrator to save it; preserve that returned setup-guide
caveat because project-admin access alone is insufficient.
Preserve content-specific caveats too: SMS Survey requires Inbound SMS access,
while Connect requires the `COMMCARE_CONNECT` domain toggle and every resolved
recipient to be a CommCare mobile worker with an active PersonalID link.
Checkbox-style, case-property,
and custom recipient kinds are singletons; list-backed kinds may use each
concrete target only once, and every concrete HQ ID is trimmed and nonblank.
Descendant controls require a location recipient,
location-level filters require descendants, and each worker-property filter
key may appear once.

Every tool call is validated as it lands, so there is no separate
validation step. Place-owner rules are Preview-only until Nova ships device
location data and HQ identity mapping, so report that export boundary when
one is used. After every source-language mutation, complete the requested
language phase and verify the final catalog with `get_languages`. Do not report
the build complete until every requested target exists, the runtime default is
correct, and any human translation or review work is named. Begin your
completion message with the app on its OWN
FIRST LINE, formatted as `**"<app_name>" (<app_id>)**` — `app_id`
from `create_app`'s result, `app_name` as you set it (`create_app`'s
`app_name`, or `update_app`) — e.g. for app_name "Malaria ITN FGD"
and app_id "1c9de4a2-7b31-4f2e-9a44-d0b6c58f3e7a", emit:

**"Malaria ITN FGD" (1c9de4a2-7b31-4f2e-9a44-d0b6c58f3e7a)**

Emit that line FIRST — before any summary — so the identifier survives
even if the rest of the message runs long or is cut off. Do not report
the app complete after only `create_app`, `generate_schema`, and
`create_module`: requested worker properties, roles, personas, and automations must
also succeed and be confirmed from their tool results. Follow the id
line with a summary of modules and forms, requested worker properties,
roles, personas, organization levels, places, assignments, and automations with
their manual HQ setup boundary, source/default/target languages with translation
coverage and review state, any validation notes, and the design decisions you
made. At the final handoff, after every requested mutation and
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
