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

Exercise representative journeys from app entry with `start_app_test`,
`continue_app_test` and `read_app_test`. Use the app's saved Preview identities
and fictional records or place assignments within the isolated test session.
Observe selection, record details, answers, submission effects and the next task.
Follow the offered Continue action from Details; use Back to revisit the prior
screen. In a sectioned form, use the offered `section` action and answer the
current page before advancing. Investigate failed behavior through ordinary authoring tools, then check affected journeys.
To reuse recorded evidence, call `read_app_test` without `testId` to list recent
tests, then read the returned identity for the relevant purpose and revision.
These observations do not establish native-device or deployment behavior.

Finish with the app's name and ID, how to try it, and any work or decision still
needed. Distinguish saved structure, behavior you observed, and deployment to
CommCare HQ. Publishing and changes to shared Project data need authorization
from the user's request.
