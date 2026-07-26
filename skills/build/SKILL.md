---
name: build
description: Generate a CommCare app from a natural-language spec, asking the user clarifying questions when the intent is ambiguous. Use when the user wants a collaborative build.
argument-hint: <spec describing the app>
---

# Task

The user wants to build a CommCare app from this spec: $ARGUMENTS.

## 1. Operating instructions

If you have not already fetched the nova-architect operating instructions in this conversation, call Nova's `get_agent_prompt` tool with `mode: "build"`. Treat the returned text as your operating instructions for this build.

If you already fetched it earlier in this conversation, reuse what you have — don't fetch again.

The Nova mutation tools are deferred — calling one before its schema is loaded fails with a Zod error. Pre-load the build-path set in a single ToolSearch call before continuing:

```
ToolSearch({query: "+nova create_app generate_schema create_module update_app", max_results: 4})
```

Pre-load the complete worker-information, role, and persona family in a separate search with enough capacity for every schema:

```
ToolSearch({query: "+nova get_users add_user_properties update_user_property remove_user_property add_user_types update_user_type remove_user_type add_personas update_persona remove_persona", max_results: 10})
```

The `+nova` filter matches whichever Nova namespace is live (`mcp__plugin_nova_nova__*` when using the plugin's OAuth, `mcp__nova__*` when an API-key override is in user-scope).

When the spec requests worker information, roles, or personas, call `get_users` before mutating them and target its stable UUIDs. Add properties first and use their returned UUIDs as role/persona value keys; add roles (`add_user_types`) before personas and link personas with the returned role UUIDs. Rename a property with `update_user_property` on that same UUID. In updates, omitted fields keep their values; in persona values, an omitted property inherits from the role while an explicitly present `""` overrides it with blank. The server-fetched prompt remains authoritative; use the loaded schemas for exact arguments.

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

1. Committing the data model
2. Building each module with its forms and fields
3. Configuring requested worker properties, roles, and personas

## 4. Build

Work through each phase per the fetched instructions. Create the app first (`create_app` — pass the app's name there, and its returned `app_id` threads through every other call), commit the data model with `generate_schema` (the case-type catalog; modules reference the recorded types by name — the app's name is not its concern), then build each module — with its forms and their fields — in one atomic `create_module` call. Configure any requested worker properties, roles, and personas in the dependency order above. Every call is validated as it lands, so there is no separate validation step: a build whose calls all succeeded is already export-ready. Do not mark the build complete until every requested user-authoring call has succeeded and its returned identities are confirmed. Mark each task `in_progress` when you start it and `completed` when it's done.

If a new ambiguity surfaces mid-build that materially changes the design, ask via AskUserQuestion before committing to it.

## 5. Report

When the build is done, return:

- **"App Name" (app_id)** on its own line
- A summary of modules and forms
- A summary of requested worker properties, roles, and personas
- Any validation notes
