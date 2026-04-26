---
name: build
description: Generate a CommCare app from a natural-language spec, asking the user clarifying questions when the intent is ambiguous. Use when the user wants a collaborative build.
argument-hint: <spec describing the app>
allowed-tools: Agent(nova:nova-architect-interactive)
---

# Task

Invoke the Agent tool with `subagent_type: "nova:nova-architect-interactive"` and this prompt:

```
{
  "mode": "build",
  "interactive": true,
  "task": "$ARGUMENTS"
}

Follow your bootstrap: call mcp__plugin_nova_nova__get_agent_prompt with
the mode/interactive above (no app_id in build mode), then build the
CommCare app matching the task.

When complete, report the app as **"App Name" (app_id)** on its own
line, followed by a summary of modules and forms, and any validation
notes.
```

Return whatever the subagent reports, verbatim.
