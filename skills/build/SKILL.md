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

The Nova mutation tools are deferred — calling one before its schema is loaded fails with a Zod error. Pre-load the build-path set in a single ToolSearch call before continuing:

```
ToolSearch({query: "+nova create_app generate_schema create_module update_app", max_results: 4})
```

Pre-load the complete worker-information, role, and persona family with a separate deterministic exact selection:

```
ToolSearch({query: "select:mcp__plugin_nova_nova__get_users,mcp__plugin_nova_nova__add_user_properties,mcp__plugin_nova_nova__update_user_property,mcp__plugin_nova_nova__remove_user_property,mcp__plugin_nova_nova__add_user_types,mcp__plugin_nova_nova__update_user_type,mcp__plugin_nova_nova__remove_user_type,mcp__plugin_nova_nova__add_personas,mcp__plugin_nova_nova__update_persona,mcp__plugin_nova_nova__remove_persona,mcp__nova__get_users,mcp__nova__add_user_properties,mcp__nova__update_user_property,mcp__nova__remove_user_property,mcp__nova__add_user_types,mcp__nova__update_user_type,mcp__nova__remove_user_type,mcp__nova__add_personas,mcp__nova__update_persona,mcp__nova__remove_persona"})
```

Pre-load the ordered case-operation family the same way when the spec has a form doing more to cases than saving its own answers:

```
ToolSearch({query: "select:mcp__plugin_nova_nova__get_case_operations,mcp__plugin_nova_nova__add_case_operations,mcp__plugin_nova_nova__update_case_operation,mcp__plugin_nova_nova__remove_case_operation,mcp__plugin_nova_nova__move_case_operation,mcp__nova__get_case_operations,mcp__nova__add_case_operations,mcp__nova__update_case_operation,mcp__nova__remove_case_operation,mcp__nova__move_case_operation"})
```

`+nova` keeps the core search namespace-neutral. Each exact family selection lists both supported spellings without ranking: `mcp__plugin_nova_nova__*` for plugin OAuth and `mcp__nova__*` for a user-scope API-key override.

When the spec requests worker information, roles, or personas, call `get_users` before mutating them and target its stable UUIDs. In a build with custom worker properties, make that read and `add_user_properties` the first calls after creating and naming the app. Typed Predicate/ValueExpression inputs and role/persona values use `userPropertyUuid`. In textual XPath, author the property's exact current saved slug as `#user/<slug>`; Nova parses it into UUID-backed identity, so it follows a later slug rename. Never put the UUID after `#user/` — unresolved UUID-spelled XPath remains raw/name-backed and will not follow a rename. Rename the property with `update_user_property` on that same returned UUID. Add roles (`add_user_types`) after the reference-bearing structure and before personas, and link personas with the returned role UUIDs. In updates, omitted fields keep their values; in persona values, an omitted property inherits from the role while an explicitly present `""` overrides it with blank. The server-fetched prompt remains authoritative subject to this ordering; use the loaded schemas for exact arguments.

A case-bound field is still the simplest way for a form to save its own answers, so reach for `add_case_operations` only when one submission carries a further ordered effect: opening another case, updating or closing a known one, linking, renaming or retyping, assigning an owner, or repeating an effect per repeat entry. Every one of these tools names the form it acts on by `moduleUuid` + `formUuid`: take both from `get_module` or `search_blueprint`, and never guess or construct one. Inside the operation, identities stay author identities — the operation's own slug id, and field paths like `visits/outcome`. Within a single `add_case_operations` call a later item may consume an earlier create by its `operationId`, so keep producer before consumer. The server-fetched prompt remains authoritative for each action's exact shape; use the loaded schemas for arguments.

Load any additional read or edit tools (`get_app`, `edit_field`, `move_field`, `remove_field`, etc.) on demand if a follow-up step needs them.

## 2. Resolve ambiguities first

Short or generic specs almost always hide design ambiguities. Don't assume you know what shape the user wants — they often have a specific vision that doesn't match the canonical pattern.

Scan the spec for genuine design ambiguities — places where reasonable defaults diverge enough to produce a meaningfully different app. Common ambiguity vectors:

- **Case type structure** — one entity, or several related ones (e.g. parent + child)?
- **Workflow stages** — what lifecycle does each entity go through (registration only, or also follow-up / close)?
- **Connect type** — is this a CommCare Connect learn or deliver app, or neither?
- **Module surface** — which entities need their own case-list view?

Ask 1-3 questions via AskUserQuestion covering the most material ambiguities and wait for the user's answers before continuing. The only time to skip is when every vector above is already explicitly addressed in the spec — for short, generic specs that's almost never the case.

Don't ask about field-level details (labels, hint text, validation specifics) — those belong to the build itself, not the framing.

## 3. Plan the work

Use TaskCreate to track the build phases:

1. Creating and naming the app, then adding requested custom worker properties
2. Committing the data model
3. Building each module with its forms and fields
4. Configuring requested roles and personas

## 4. Build

Work through each phase per the fetched instructions. Create the app first (`create_app` — pass the app's name there, and its returned `app_id` threads through every other call). If the build requests custom worker properties, immediately call `get_users` and `add_user_properties`; do not call `generate_schema`, create a module or form, or author any condition or calculation that may reference those properties first. Then commit the data model with `generate_schema` (the case-type catalog; modules reference the recorded types by name — the app's name is not its concern), and build each module — with its forms and fields — in one atomic `create_module` call, using `userPropertyUuid` in typed Predicate/ValueExpression inputs and `#user/<slug>` in textual XPath as described above. Configure requested roles and personas afterward in their dependency order. Every call is validated as it lands, so there is no separate validation step: a build whose calls all succeeded is already export-ready. Do not mark the build complete until every requested user-authoring call has succeeded and its returned identities are confirmed. Mark each task `in_progress` when you start it and `completed` when it's done.

If a new ambiguity surfaces mid-build that materially changes the design, ask via AskUserQuestion before committing to it.

## 5. Report

When the build is done, return:

- **"App Name" (app_id)** on its own line
- A summary of modules and forms
- A summary of requested worker properties, roles, and personas
- Any validation notes
