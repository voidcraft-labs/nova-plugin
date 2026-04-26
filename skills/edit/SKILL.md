---
name: edit
description: Edit an existing CommCare app with a natural-language instruction. Asks clarifying questions when needed. Usage — quote the instruction: /nova:edit <app_id> "<instruction>"
argument-hint: <app_id> "<instruction>"
allowed-tools: Agent(nova:nova-architect-interactive)
---

# Task

Invoke the Agent tool with `subagent_type: "nova:nova-architect-interactive"` and this prompt:

```
{
  "mode": "edit",
  "interactive": true,
  "app_id": "$0",
  "task": "$1"
}

Follow your bootstrap: call mcp__plugin_nova_nova__get_agent_prompt with
the mode/interactive/app_id above. The server inlines the app's
blueprint summary into the returned text so you boot with full edit
context — do NOT call get_app as a separate step. Then apply the
requested edit.

When complete, report the app as **"App Name" (app_id)** on its own
line, followed by the modified blueprint summary.
```

Return the subagent's report, verbatim.
