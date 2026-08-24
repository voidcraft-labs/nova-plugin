# Nova for Claude Code

Build, edit, compile, and deploy CommCare apps from Claude Code.

## Install

    /plugin marketplace add voidcraft-labs/nova-marketplace
    /plugin install nova@nova-marketplace

## Authenticate

**Browser sign-in (default).** The first time you use a `/nova:*` skill, Claude Code
opens your browser to sign in at commcare.app. Tokens are stored in Claude Code's
credential store; revoke via `/mcp` → nova → Clear authentication.

**API key.** For unattended runs, set `NOVA_API_KEY` in your environment to a
key from [commcare.app/settings](https://commcare.app/settings). The plugin
picks it up automatically — no browser, no extra setup. Unset it to fall back
to browser sign-in.

**Working as a team?** Don't share one account. Create a shared Nova Project and
invite your teammates — everyone signs in as themselves, and every member sees
the Project's apps, case data, and media. Agents manage this over MCP too:
`list_projects`, `create_project`, `invite_member`, `list_members`,
`update_member_role`, and `move_app`.

Full details: [docs.commcare.app/mcp/api-keys](https://docs.commcare.app/mcp/api-keys)
and [docs.commcare.app/mcp/tools](https://docs.commcare.app/mcp/tools).

## Skills

- `/nova:build <spec>` — interactive build; subagent asks clarifying questions
- `/nova:autobuild <spec>` — autonomous build; subagent commits to defaults
- `/nova:edit <app_id> "<instruction>"` — edit an existing app
- `/nova:list` — list your apps
- `/nova:show <app_id>` — blueprint summary
- `/nova:upload_to_hq <app_id or name> [project space]` — deploy to CommCare HQ (names a space to upload straight there, otherwise confirms the target first; reports required HQ feature flags that are missing or could not be verified)

## Agent prompt delivery

Build and edit skills fetch their current operating prompt from Nova before
changing an app. A prompt that fits arrives as ordinary text ending in
`NOVA-PROMPT-END`. A larger prompt arrives as JSON pages with kind
`nova-agent-prompt-page`, `protocol_version: 1`, and
`offset_unit: unicode-code-points`.

The plugin repeats `get_agent_prompt` with the same `mode` and `app_id` plus
each `next_cursor`. It requires one unchanged advertised `prompt_sha256` and
`prompt_length`, adjacent `chunk_start`/`chunk_end` offsets, and a final page
with `complete: true`, no `next_cursor`, and `chunk_end` equal to
`prompt_length`. All three offset and length fields are measured in Unicode code
points, not UTF-16 code units or bytes. It concatenates the exact
`prompt_chunk` values in order and requires the assembled text to end in
`NOVA-PROMPT-END` before acting. The agent has no shell or hashing tool, so it
compares the advertised digest across pages and does not claim to recompute
SHA-256 or recount arbitrary chunks. Nova's deterministic code-point slicer
computes and cursor-validates the page offsets. A failed check or a missing
ordinary-text marker stops the build or edit as a transport failure.

## Nested menus

`/nova:build`, `/nova:autobuild`, and `/nova:edit` can organize modules under
one submenu tier. A parent menu remains a complete module with its own Form or
case-list surface, and each child is complete too. A child cannot contain
another child, and a parent that already has children cannot itself become a
child.

A top-level parent and child that show different case types require the parent
to have at least one Form. A case-list-only root is rejected by
`NESTED_MENU_CROSS_TYPE_ROOT_REQUIRES_FORM` because the two selections cannot
otherwise be distinguished.

`create_module` accepts an optional `parentModuleUuid`: omit it for a top-level
module or pass an eligible root module's UUID for a child. `move_module` keeps
its `after` sibling anchor and adds optional `parentModuleUuid`. Omit the parent
only to reorder inside the module's current menu, pass `null` to make it
top-level, or pass an eligible root UUID to move it into that submenu. `after`
must name a sibling in the resulting destination, or be `null` for first.

Normally the parent is created before its children. When a parent form creates
the case type shown by its intended child viewer, Nova's
`MISSING_CHILD_CASE_MODULE` gate requires the reverse bootstrap: create the
child viewer temporarily top-level, create the parent with its writer form,
then use `move_module` to place the viewer under the parent. The final app still
has the same one-tier hierarchy.

Menu parentage controls navigation. It is separate from case parentage, which
selects related case records at run time. Nested menus also do not duplicate
forms: every Form has one canonical owning module, with no linked- or
shadow-form reuse. Separate modules and case-list filters can provide different
views of the same data.

## Languages and translations

`/nova:build`, `/nova:autobuild`, and `/nova:edit` understand Nova's app
language catalog. A language is an identity object
`{language, script?, region?}`: one individual living ISO 639 language, its
writing system where the language has more than one, and optional regional
conventions. Every individual living language can be added, copied, edited,
previewed, and exported; that does not imply that Nova can automatically
translate the same language direction. Macrolanguages and two-letter codes
are rejected with the identifiers to use instead, and each language's name
and text direction come from the identity itself.

For an existing app, ask `/nova:edit` to add or manage a language. The agent
first reads the source and runtime-default languages, then adds each target by
copying a complete existing language so the app is never born with blank
worker text. It can page through every contextual string, save translations
you provide, and mark an exact unchanged value reviewed. Copied and
machine-authored values stay **Needs review** until that explicit review step.

`get_languages` reports automatic translation independently for each exact
source-to-target direction as **Available**, **Not evaluated**, or **Withheld**.
Nova's launch policy marks pairs between distinct members of its 57-language
launch set Available. The plugin has no paid automatic MCP action and does not
treat a model's general language fluency as permission to bulk-translate through
the ordinary manual edit tool. It continues with copied content and tells you
what needs human translation and review.

The agent replies in the language of your latest substantive message. That
conversation language is independent from the app's source, default, and
target worker languages.

Agents connected directly over MCP can call `get_app_hq_feature_flags` before
publishing. It returns only the CommCare HQ flags the app uses, why each
applies, inline plain-language descriptions, and public docs links. With no
domain it makes no claim about what is off; with one explicit connected domain
it reports confirmed missing flags separately from checks HQ could not answer.

Build and edit skills also expose automatic case updates and conditional alerts
through `get_automations`, `add_automations`, `update_automation`, and
`remove_automation`. Nova can describe supported matching, but it does not
execute or install the rule. Builder Preview owns the count; MCP
`get_automations` and successful add/update results return the regenerated
manual CommCare HQ setup guidance and locally omitted criteria.
Schedule definitions use one content type and are constrained to one CommCare
HQ setup form, including shared timing/content, event ordering, window, day,
offset, and survey rules.
The shared schema keeps the forms' criteria distinct: automatic updates admit
case/parent/host value and date comparisons, one standard closed-parent
condition, and server-modified age; alerts admit direct-case value comparisons
and portable regex. Both admit at most one UUID-backed location condition and
an explicit descendant flag; HQ executes and form-accepts it even though the
current visible editors hide the picker, so returned guidance names the
administrator application path. Names and literals
are canonical nonblank values. Date conditions compare the current date directly
with the case-property date plus a signed day offset; a datetime contributes its
written calendar date only, discarding its time and explicit offset. The schema
also enforces
recipient compatibility and the rule-trigger requirement for timed restarts.
Host-scoped references remain representable only while the app has one
unambiguous canonical extension relation for the automated case type. If an
advanced case operation can add a second extension, Nova refuses host-scoped
criteria, update targets, update sources, and message case-property parts rather
than choose from HQ's unordered extensions. Every host-scoped reference also
requires exactly one live extension at runtime. Retained extra extension
indices make the current-match count unavailable when a criterion reads the
host, and HQ does not define which extension it chooses as the host.
Automation input uses Nova standard property names and setup guidance projects
them to HQ's automation model-field names, including `case_type` to `type`;
`case_id` and `case_type` are read-only. Divergent `status`, datetime
equality/regex, and every standard scalar in dynamic-only restart/event-time
slots are refused. After trimming, case-property event-time values must begin
with `H:MM` or `HH:MM`, and the whole value must parse as a time. Suffixes such
as AM/PM or seconds are accepted; blank, nonmatching, or unparseable values use
12:00 PM. Email content chooses one plain-text or rich-text body form;
rich HTML requires the domain toggle, is sanitized and rewrapped by HQ, and has
its plaintext derived rather than authored in parallel.
Message fields use canonical structural `parts`: literal `text` never becomes
a reference, even when it looks like `{case.foo}`; the guide escapes literal
braces before HQ's Python Formatter evaluates them. An explicit `case-property`
part carries scope plus the Nova `(caseType, property)` identity, while a
`context-property` part explicitly names a case-owner or recipient field. Both
project to HQ syntax only in the returned guide. A message `case-property` part
cannot use `owner`, `host`, or `last_modified_by` in any scope because HQ's
formatter context shadows same-named custom case data; rename the custom
property, or use `context-property` for the actual case-owner or recipient
context. Registered custom handler IDs and setup-only
instructions must be exact, trimmed, and nonblank; never invent placeholder
values. Setup-only criteria distinguish UCR filters from registered custom
criteria so the guide can name the required `CASE_UPDATES_UCR_FILTERS` toggle
or system-administrator access. HQ requires a system administrator to save an alert that uses a
registered custom recipient or custom content handler; a project administrator
cannot complete that returned setup guide alone.
Preserve content-specific guide caveats too: SMS Survey requires Inbound SMS
access, while Connect requires the `COMMCARE_CONNECT` domain toggle and every
resolved recipient to be a CommCare mobile worker with an active PersonalID link.
Checkbox-style, case-property, and custom recipient kinds are singletons;
list-backed kinds may use a concrete target only once, and concrete HQ IDs must
be trimmed and nonblank. Descendant controls
require a location recipient, level filters require descendants, and each
worker-property filter key may appear once. Its values are structural exact
literals or custom case-property references: empty and whitespace literals are
meaningful, while brace-wrapped literals are refused because HQ executes them
as lookups. Every triggering case must contain each referenced property because
HQ raises when its direct lookup is missing. Filters apply only to contacts
that resolve to user accounts, so the schema refuses filters with case,
parent/child-case, case-email, case-group, or registered custom recipients;
those contacts bypass the filter or have an unknown runtime type. Multiple keys/values or exact blank/whitespace values use HQ's JSON
mode, whose new-alert system-administrator prerequisite appears in the guide.
