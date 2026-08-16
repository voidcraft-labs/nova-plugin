---
name: build
description: Generate a CommCare app from a natural-language spec, asking the user clarifying questions when the intent is ambiguous. Use when the user wants a collaborative build.
argument-hint: <spec describing the app>
---

# Task

The user wants to build a CommCare app from this spec: $ARGUMENTS.

## 1. Operating instructions

If you have not already fetched the nova-architect operating instructions in this conversation, first load the deferred prompt tool under both supported MCP spellings:

```
ToolSearch({query: "select:mcp__plugin_nova_nova__get_agent_prompt,mcp__nova__get_agent_prompt"})
```

Then call the loaded Nova `get_agent_prompt` tool with `mode: "build"`. Treat the returned text as your operating instructions for this build.

A complete prompt ends with the line `NOVA-PROMPT-END`. If yours doesn't, the result was too large to deliver whole and you're holding its opening — identity and voice, none of the build guidance. When the result names a file it was saved to, read that file and use its contents as the prompt. If there's no such file, stop and tell the user `get_agent_prompt` returned a truncated prompt; don't build from the fragment and don't reconstruct the missing guidance from the tool schemas.

If you already fetched it earlier in this conversation, reuse what you have — don't fetch again.

The Nova mutation tools are deferred — calling one before its schema is loaded fails with a Zod error. Pre-load the build-path set in a single deterministic ToolSearch call before continuing:

```
ToolSearch({query: "select:mcp__plugin_nova_nova__create_app,mcp__plugin_nova_nova__generate_schema,mcp__plugin_nova_nova__create_module,mcp__plugin_nova_nova__update_app,mcp__nova__create_app,mcp__nova__generate_schema,mcp__nova__create_module,mcp__nova__update_app"})
```

When the spec names a target Nova Project — a shared workspace whose members all see the app — resolve it before creating the app. Load `list_projects`:

```
ToolSearch({query: "select:mcp__plugin_nova_nova__list_projects,mcp__nova__list_projects"})
```

Call it, match the named Project, and pass its `project_id` to `create_app`. When no Project is named, omit `project_id`; the app lands in the user's personal Project.

Pre-load the complete worker-information, role, and persona family with a separate deterministic exact selection:

```
ToolSearch({query: "select:mcp__plugin_nova_nova__get_users,mcp__plugin_nova_nova__add_user_properties,mcp__plugin_nova_nova__update_user_property,mcp__plugin_nova_nova__remove_user_property,mcp__plugin_nova_nova__add_user_types,mcp__plugin_nova_nova__update_user_type,mcp__plugin_nova_nova__remove_user_type,mcp__plugin_nova_nova__add_personas,mcp__plugin_nova_nova__update_persona,mcp__plugin_nova_nova__remove_persona,mcp__nova__get_users,mcp__nova__add_user_properties,mcp__nova__update_user_property,mcp__nova__remove_user_property,mcp__nova__add_user_types,mcp__nova__update_user_type,mcp__nova__remove_user_type,mcp__nova__add_personas,mcp__nova__update_persona,mcp__nova__remove_persona"})
```

When the spec depends on districts, facilities, worker assignments, or place ownership, pre-load the complete organization family too:

```
ToolSearch({query: "select:mcp__plugin_nova_nova__get_organization,mcp__plugin_nova_nova__add_organization_levels,mcp__plugin_nova_nova__update_organization_level,mcp__plugin_nova_nova__remove_organization_level,mcp__plugin_nova_nova__add_location_properties,mcp__plugin_nova_nova__update_location_property,mcp__plugin_nova_nova__remove_location_property,mcp__plugin_nova_nova__create_location,mcp__plugin_nova_nova__update_location,mcp__plugin_nova_nova__move_location,mcp__plugin_nova_nova__set_location_archived,mcp__nova__get_organization,mcp__nova__add_organization_levels,mcp__nova__update_organization_level,mcp__nova__remove_organization_level,mcp__nova__add_location_properties,mcp__nova__update_location_property,mcp__nova__remove_location_property,mcp__nova__create_location,mcp__nova__update_location,mcp__nova__move_location,mcp__nova__set_location_archived"})
```

When the spec requests an automatic case update, conditional alert, reminder,
or scheduled message, pre-load the complete automation family:

```
ToolSearch({query: "select:mcp__plugin_nova_nova__get_automations,mcp__plugin_nova_nova__add_automations,mcp__plugin_nova_nova__update_automation,mcp__plugin_nova_nova__remove_automation,mcp__nova__get_automations,mcp__nova__add_automations,mcp__nova__update_automation,mcp__nova__remove_automation"})
```

Pre-load the ordered case-operation family the same way when the spec has a form doing more to cases than saving its own answers:

```
ToolSearch({query: "select:mcp__plugin_nova_nova__get_case_operations,mcp__plugin_nova_nova__add_case_operations,mcp__plugin_nova_nova__update_case_operation,mcp__plugin_nova_nova__remove_case_operation,mcp__plugin_nova_nova__move_case_operation,mcp__nova__get_case_operations,mcp__nova__add_case_operations,mcp__nova__update_case_operation,mcp__nova__remove_case_operation,mcp__nova__move_case_operation"})
```

When the spec requests non-English worker content or multiple app languages,
pre-load the complete language family:

```
ToolSearch({query: "select:mcp__plugin_nova_nova__get_languages,mcp__plugin_nova_nova__get_translatable_content,mcp__plugin_nova_nova__add_language,mcp__plugin_nova_nova__update_language,mcp__plugin_nova_nova__remove_language,mcp__plugin_nova_nova__update_translations,mcp__nova__get_languages,mcp__nova__get_translatable_content,mcp__nova__add_language,mcp__nova__update_language,mcp__nova__remove_language,mcp__nova__update_translations"})
```

Each exact selection lists both supported spellings without ranking: `mcp__plugin_nova_nova__*` for plugin OAuth and `mcp__nova__*` for a user-scope API-key override; the spelling that isn't connected simply matches nothing.

Reply in the language of the user's latest substantive message. That
conversation language is independent from the app's source, runtime default,
and target worker languages; never switch the conversation merely because an
app language differs.

When the spec requests non-English worker content or multiple app languages,
settle the canonical source language, runtime default, and ordered targets
explicitly. Author every worker-facing name, label, hint, option, message, and
composition string in the canonical source language while building the app.
Do not mix stacked translations into one label. Finish every structural and
source-content mutation before the language phase, because only then does the
complete translation inventory exist.

At the language phase, call `get_languages`. A new app starts with one source
language; if the requested source uses another code, call `update_language`
with `relabel-source` while it is still the sole language. Add targets in copy
dependency order with `add_language`, always naming an existing `copyFrom`.
That call copies the complete effective projection and every copied value starts
Needs review, so a target is never created blank. Set the runtime default only
after its language exists.

Every CommCare Classic language code is available for manual authoring and
copying. `get_languages` separately reports automatic translation for each
source-to-target pair as Available, Not evaluated, or Withheld. Nova's launch
policy marks pairs between distinct members of its 57-language launch set
Available, but the MCP surface has no paid automatic translation action. Never
treat your own language fluency as a substitute or bulk-translate by feeding
self-generated text through
`update_translations`. When the user supplies target text, first page
`get_translatable_content` to completion, preserve typed `protectedParts`, and
write at most 50 distinct stable unit IDs per atomic `update_translations`
call. For a set, echo the unit's just-read current `sourceFingerprint` as
`expectedSourceFingerprint`. For a review, echo the explicit entry's
`sourceFingerprint` and exact value as `expectedSourceFingerprint` and
`expectedValue`, plus the unit's current `sourceFingerprint` as
`expectedCurrentSourceFingerprint`. Re-read the target after any concurrency
refusal; never mark copied or machine-authored text reviewed on the user's behalf.
Report incomplete, out-of-date, and Needs review coverage honestly.

When the spec requests worker information, roles, or personas, call `get_users` before mutating them and target its stable UUIDs. In a build with custom worker properties, make that read and `add_user_properties` the first calls after creating and naming the app. Typed Predicate/ValueExpression inputs and role/persona values use `userPropertyUuid`. Expression slots take Nova's typed AST, not an XPath source string: a worker property is `{"kind":"user-property-ref","userPropertyUuid":"…"}` in prose and `{"kind":"session-user-property","userPropertyUuid":"…"}` in a Predicate or ValueExpression. Do not send `#user/<slug>` text for Nova to resolve — an unresolved hashtag is refused, not parsed. Rename the property with `update_user_property` on that same returned UUID. Add roles (`add_user_types`) after the reference-bearing structure and before personas, and link personas with the returned role UUIDs. In updates, omitted fields keep their values, and one role or persona value changes per call through `valuePatch`: it names one `userPropertyUuid`, a string sets that value and `null` clears it, and omitting `valuePatch` leaves every value alone. A persona that carries no value for a property inherits the role's; an explicit `""` overrides the role with blank. The server-fetched prompt remains authoritative subject to this ordering; use the loaded schemas for exact arguments.

When the workflow depends on places, call `get_organization`, page with its opaque, snapshot-bound `cursor` until `page.complete` is true, and restart without a cursor if a later page reports that the snapshot changed (use `query` to narrow large trees and request `includeValues` only when saved custom values matter). The cursor covers one bounded stream across levels, place-information fields, and matching places, so accumulate each collection rather than expecting every page to repeat the complete shape. Add levels parent-first, add place-information fields, then create the actual places. Read the complete organization before changing an existing declaration: level case-flow and address-book objects are complete replacements, so preserve every nested setting the edit does not change. Keep every returned level, property, and location UUID: names are labels, while level codes and location site codes are create-once external identities. Case flow controls ownership and delivery; the address book separately controls visibility. Every create, update, move, archive, or unarchive requires the exact current revision; chain the revision returned by each successful write into the next one and re-read after a conflict. If a saved reverse-hop owner rule requires a destination below every new source, pass the complete bounded, structurally nested `descendants` tree in that source's `create_location` call and keep the final UUIDs from its compact mirrored receipt; do not attempt sequential creates, because the source would be invalid between them. `update_location.valuePatch` edits exactly one UUID-keyed value per call (`null` clears it), while `values` is an explicit complete-bag replacement. Build the places before assigning personas to them through `locationUuids` (first is main) or using a location UUID in a case-owner expression. Archive never means reassign: first call `set_location_archived` with `archived=true` and no confirmation to get a bounded impact and exact confirmation token, review it with the user, then repeat with `confirm=true`, `expectedRevision` set to the returned `expectedRevisionForConfirmation`, and the unchanged `confirmedImpact`; do not confirm a blocked preflight, and the transaction refuses if any consequence changed.

When the workflow requests automations, add them only after their case types,
forms, worker information, and places exist. The `add_automations` input is the
complete canonical rule: predeclare stable UUIDs for the rule and every nested
criterion, setup-only instruction, update, recipient, schedule event, and user
filter. Use only the loaded schema's closed vocabulary. UCR and registered
custom criteria are distinct setup-only kinds; automatic-update server-modified age is its own
structured field. None is locally executed. Builder Preview can count current real open cases, but the MCP
automation tools do not return that count. `get_automations` and successful
add/update results return the regenerated manual guide plus the locally omitted
criteria; remove returns only its deletion receipt. Nova never updates a case,
sends a message, advances a schedule, or installs the rule in CommCare HQ.
Report the returned guide and omissions after get/add/update, and do not promise
that uploading the app configures the automation.
The returned case-update guide targets
`/a/<domain>/data/edit/automatic_updates/`; the conditional-alert guide targets
`/a/<domain>/messaging/conditional/`. HQ's deprecated
`RUN_AUTO_CASE_UPDATES_ON_SAVE` switch is project-wide and can evaluate every
active case-update rule for a saved case type, so treat it as a separate target
deployment caveat and never invent a per-rule field for it.
Schedules use one content type, and timed schedules must map to one CommCare HQ
setup form: every event shares one timing mode, and Weekly and Monthly also share content. Follow the loaded
schema's ordering, five-minute separation, random-window, day, offset,
survey-expiration, and partial-submission dependencies. Weekly and Monthly days
come from closed, unique sets in canonical HQ order. Weekly event days are
offsets from `startDayOfWeek`, not absolute weekday numbers.
The two automation kinds have different criteria. Automatic updates admit
value/date comparisons against case, parent, or host properties, at most one
standard closed-parent condition, and server-modified age; they have no regex
condition. Alerts admit direct-case value comparisons plus portable regex,
with no date, parent/host, closed-parent, or server-modified condition. Both
admit at most one UUID-backed location condition plus its descendant flag;
preserve it and report the returned guide's HQ-administrator application
caveat. Names must be nonblank and already trimmed;
equality and update literals must be exact nonblank/unquoted values. Do not invent a parent index, relationship, or web-user
recipient. Connect content cannot use matched-case, parent-case, all-child-cases,
case-property-email, or case-group recipients. A timed restart property requires
a rule-trigger start. Date conditions compare the current date directly with
the case-property date plus a signed day offset; a datetime contributes its
written calendar date only, discarding its time and explicit offset.
Host-scoped references remain representable only while the app has one unambiguous
canonical extension relation for the automation case type. If an advanced case
operation can add a second extension, Nova refuses host-scoped criteria, update
targets, update sources, and message case-property parts rather than choose
from HQ's unordered extensions; use a non-host scope or remove the additional
link. Every host-scoped reference also requires exactly one live extension at
runtime. Retained extra extension indices make the current-match count
unavailable when a criterion reads the host, and HQ does not define which
extension it chooses as the host. Use Nova
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

A case-bound field is still the simplest way for a form to save its own answers, so reach for `add_case_operations` only when one submission carries a further ordered effect: opening another case, updating or closing a known one, linking, renaming or retyping, assigning an owner, or repeating an effect per repeat entry. Every one of these tools names the form it acts on by `moduleUuid` + `formUuid`: take both from `get_module` or `search_blueprint`, and never guess or construct one. Inside the operation every reference is a UUID: a form answer is `{"kind":"field","uuid":"…"}`, a `forEach` repeat scope is that repeat field's UUID, and an earlier create is targeted as `{"kind":"op","opUuid":"…"}` (its resulting case id, inside a value expression, is `{"kind":"id-of","opUuid":"…"}`). The operation's own `id` stays a readable wire name, never an address. Within a single `add_case_operations` call a later item may consume an earlier create by predeclaring that create's `operationUuid`, so keep producer before consumer. The server-fetched prompt remains authoritative for each action's exact shape; use the loaded schemas for arguments.

Load any additional read or edit tools (`get_app`, `edit_field`, `move_field`, `remove_field`, etc.) on demand if a follow-up step needs them.

## 2. Resolve ambiguities first

Short or generic specs almost always hide design ambiguities. Don't assume you know what shape the user wants — they often have a specific vision that doesn't match the canonical pattern.

Scan the spec for genuine design ambiguities — places where reasonable defaults diverge enough to produce a meaningfully different app. Common ambiguity vectors:

- **Case type structure** — one entity, or several related ones (e.g. parent + child)?
- **Workflow stages** — what lifecycle does each entity go through (registration only, or also follow-up / close)?
- **Connect type** — is this a CommCare Connect learn or deliver app, or neither?
- **Module surface** — which entities need their own case-list view?

Ask 1-3 questions via AskUserQuestion covering the most material ambiguities and wait for the user's answers before continuing. The only time to skip is when every vector above is already explicitly addressed in the spec; for short, generic specs, that's almost never the case.

Don't ask about field-level details (labels, hint text, validation specifics) — those belong to the build itself, not the framing.

## 3. Plan the work

Use TaskCreate to track the build phases:

1. Creating and naming the app, then adding requested custom worker properties
2. Committing the data model
3. Building requested organization levels, place information, and places
4. Building each module with its forms and fields
5. Configuring requested automations
6. Configuring requested roles, personas, and place assignments
7. Adding requested app languages after all source-language content exists

## 4. Build

Work through each phase per the fetched instructions. Create the app first (`create_app`; pass the app's name there, and its returned `app_id` threads through every other call). If the build requests custom worker properties, immediately call `get_users` and `add_user_properties`; do not call `generate_schema`, create a module or form, or author any condition or calculation that may reference those properties first. Then commit the data model with `generate_schema` (the case-type catalog; modules reference the recorded types by name; the app's name is not its concern). Build any requested organization parent-first next, before modules whose case-owner operations need those returned place identities. Then build each module, with its forms and fields, in one atomic `create_module` call, referring to a worker property by its `userPropertyUuid` in every typed slot as described above, never as `#user/<slug>` text. Add requested automations after every identity they reference exists. Configure roles and personas in dependency order after their places exist. Every call is validated as it lands, so there is no separate authoring-validation step. Place-based case-owner rules work in Preview but are deliberately not export-ready until Nova ships the matching device location fixture and HQ identity mapping; report that boundary when such a rule is requested. Do not mark the build complete until every requested user, organization, and automation authoring call has succeeded and its returned identities are confirmed. Mark each task `in_progress` when you start it and `completed` when it's done.

After all source-language content exists, perform the requested language phase
using the source/default/copy/review contract above. Do not mark the build
complete until every requested language exists, the runtime default is correct,
and the remaining human translation or review work is explicit.

If a new ambiguity surfaces mid-build that materially changes the design, ask via AskUserQuestion before committing to it.

## 5. Report

When the build is done, return:

- **"App Name" (app_id)** on its own line
- A summary of modules and forms
- A summary of requested worker properties, roles, and personas
- A summary of requested organization levels, places, and assignments
- A summary of requested automations and the manual HQ setup boundary
- A summary of source, runtime-default, and target languages, with remaining translation and review coverage
- Any validation notes
