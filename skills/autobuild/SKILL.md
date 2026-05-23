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

Follow your bootstrap: call Nova's `get_agent_prompt` tool with the
mode above (no app_id — build modes have no app to read from). The
Nova mutation tools are deferred — pre-load their schemas in one
ToolSearch call before your first mutation:

ToolSearch({query: "+nova create_app generate_schema generate_scaffold create_module add_fields validate_app", max_results: 6})

The `+nova` filter matches whichever Nova namespace is live in this
session (`mcp__plugin_nova_nova__*` for the plugin's OAuth, or
`mcp__nova__*` for a user-scope API-key override). Then build the
CommCare app matching the task autonomously. Make every design
decision yourself.

Your final action is `validate_app`; on success it returns the app's
`app_id` and `app_name`. Begin your completion message with that app on
its OWN FIRST LINE, formatted as `**"<app_name>" (<app_id>)**` with the
two values substituted in — e.g. for app_name "Malaria ITN FGD" and
app_id "w1iDapHbSHFtCVgM2Jm2", emit:

**"Malaria ITN FGD" (w1iDapHbSHFtCVgM2Jm2)**

Emit that line FIRST — before any summary — so the identifier survives
even if the rest of the message runs long or is cut off. Follow it with
a summary of modules and forms, any validation notes, and the design
decisions you made.
```

Return the subagent's report, verbatim.
