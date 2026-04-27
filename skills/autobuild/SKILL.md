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

Follow your bootstrap: call mcp__plugin_nova_nova__get_agent_prompt
with the mode above (no app_id — build modes have no app to read
from). The nova mutation tools are deferred — pre-load their schemas
in one ToolSearch call before your first mutation: select
mcp__plugin_nova_nova__create_app, generate_schema, generate_scaffold,
add_module, add_fields, validate_app (max_results: 6). Then build the
CommCare app matching the task autonomously. Make every design
decision yourself.

When complete, report the app as **"App Name" (app_id)** on its own
line, followed by a summary of modules and forms, any validation
notes, and the design decisions you made.
```

Return the subagent's report, verbatim.
