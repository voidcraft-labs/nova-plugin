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
(no app_id — build modes have no app to read from). The Nova mutation
tools are deferred — pre-load their schemas in one ToolSearch call
before your first mutation:

ToolSearch({query: "+nova create_app generate_schema create_module update_app", max_results: 4})

Pre-load the complete worker-information, role, and persona family in
a separate deterministic exact selection:

ToolSearch({query: "select:mcp__plugin_nova_nova__get_users,mcp__plugin_nova_nova__add_user_properties,mcp__plugin_nova_nova__update_user_property,mcp__plugin_nova_nova__remove_user_property,mcp__plugin_nova_nova__add_user_types,mcp__plugin_nova_nova__update_user_type,mcp__plugin_nova_nova__remove_user_type,mcp__plugin_nova_nova__add_personas,mcp__plugin_nova_nova__update_persona,mcp__plugin_nova_nova__remove_persona,mcp__nova__get_users,mcp__nova__add_user_properties,mcp__nova__update_user_property,mcp__nova__remove_user_property,mcp__nova__add_user_types,mcp__nova__update_user_type,mcp__nova__remove_user_type,mcp__nova__add_personas,mcp__nova__update_persona,mcp__nova__remove_persona"})

`+nova` keeps the core search namespace-neutral. The exact family
selection lists both supported spellings without ranking:
`mcp__plugin_nova_nova__*` for plugin OAuth and `mcp__nova__*` for a
user-scope API-key override. Then build the CommCare app matching the
task autonomously. Make every design decision yourself.

When the task requests custom worker properties, create and name the
app, then immediately call `get_users` and `add_user_properties`.
Do not call `generate_schema`, create modules or forms, or author any
condition or calculation that may reference those properties first.
Use each returned stable property UUID for every such reference and
as the role/persona value key; rename it later with
`update_user_property` on that same UUID. Roles may follow the
reference-bearing structure; add roles (`add_user_types`) before
personas and link personas with the returned role UUIDs. When the task
requests only roles or personas, still call `get_users` before mutating
them and target its stable UUIDs. In updates, omitted fields keep their
values; in persona values, an omitted property inherits from the role
while an explicitly present `""` overrides it with blank. The
server-fetched prompt remains authoritative subject to this ordering;
use the loaded schemas for exact arguments.

Every tool call is validated as it lands, so there is no separate
validation step — when your last call succeeds, the app is already
export-ready. Begin your completion message with the app on its OWN
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
roles, and personas, any validation notes, and the design decisions
you made.
```

Return the subagent's report, verbatim.
