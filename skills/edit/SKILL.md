---
name: edit
description: Edit an existing CommCare app from a natural-language request.
argument-hint: <app_id> "<instruction>"
---

Edit Nova app `$0` as requested: $1.

Find Nova's current authoring guidance:

```js
ToolSearch({query: "select:mcp__plugin_nova_nova__get_agent_prompt,mcp__nova__get_agent_prompt"})
```

Call the available `get_agent_prompt` with `{mode: "edit"}`. Its complete
response ends with `NOVA-PROMPT-END`; if that marker is missing, report the
incomplete delivery before changing the app. Use the returned guidance for
Nova authoring.

Read `get_app` for app `$0`, then inspect the modules, forms or fields relevant
to the request. Discover those tools as needed. Preserve unrelated work, and
consider saved data, dependent rules, translations and navigation when making
a change. Ask about consequential intent; read existing state yourself.

`get_authoring_guide` explains features and expressions when you need more
context. Use the isolated app-test tools to exercise affected journeys from app
entry through submission and the next task. Read retained observations with
their revision and identity; changed behavior needs a fresh test of the saved
app. Keep fictional records and assignments inside the test session.

Successful changes are already saved. Use their results to decide
what remains, then report what changed and any material limitation. Describe
verification and deployment only when you have evidence for them. Publishing
and changes to shared Project data need authorization from the user's request.
