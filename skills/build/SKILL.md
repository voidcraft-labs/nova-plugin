---
name: build
description: Build a CommCare app from a natural-language description, working with the user on consequential design choices.
argument-hint: <description of the app>
---

Build the app described in `$ARGUMENTS`.

Find Nova's current authoring guidance:

```js
ToolSearch({query: "select:mcp__plugin_nova_nova__get_agent_prompt,mcp__nova__get_agent_prompt"})
```

Call the available `get_agent_prompt` with `{mode: "build"}`. Its complete
response ends with `NOVA-PROMPT-END`; if that marker is missing, report the
incomplete delivery before changing an app. Use the returned guidance for
Nova authoring. Discover further tools as the work calls for them.

If the user named a Nova Project, resolve it with `list_projects` before
creating the app. Pass its `project_id` to `create_app`; otherwise omit that
argument to use the user's personal Project. Keep the returned `app_id` for
subsequent calls.

Design the records and workflows together. Ask about choices that materially
change the app and fill routine gaps yourself. Build complete workflows, then
refine their wording, layout and behavior. Read `get_authoring_guide` when a
feature or expression needs explanation; the server owns the current syntax
and domain guidance.

Finish with the app's name and ID, what it does, and any work or decision still
needed. Distinguish saved structure, behavior you observed, and deployment to
CommCare HQ. Publishing and changes to shared Project data need authorization
from the user's request.
