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
For unused custom property definitions, `remove_case_properties` checks app
references and saved values. If saved values prevent removal, preserve them and
report the need for a reviewed migration.

Look for relevant retained work with `list_work` filtered by the app; inspect it
with `get_work` before resuming. Otherwise call `begin_work` with
`{ app_id: "$0", request_id: "unique-request-id" }`. Keep the returned `work_id`.
Shared edits use that ID and a unique `request_id`; shared reads choose exactly
one of `work_id` for the candidate or `app_id` for the saved app.
`get_authoring_guide` explains features and expressions against that target.

Refine the app privately, using focused operations rather than nested creation.
Save complete progress with `save_work`: pass `work_id`, a unique `request_id`,
and `expected_revision` copied from the latest candidate result. Validation
refusals retain the candidate for correction. If the saved app changed during
your work, inspect both versions and discuss the conflict; do not silently
merge or discard the candidate. `discard_work` requires the same revision-bound
envelope, abandons pending changes and keeps the work ID. The next edit starts
from current saved state. Earlier checkpoints remain saved. Reuse a request ID
only for an exact retry, including after a lost response.

After saving, use the isolated app-test tools to exercise affected journeys from app
entry through record details, submission and the next task. Start and continue
calls take a unique `request_id` and exactly one of `app_id` or `work_id`; both
target the saved checkpoint, never the pending candidate. `read_app_test` is a
shared read and takes no request ID. Follow the offered
Continue action from Details, and use Back when inspecting the return path.
Use the offered `section` action to check form pages and forward validation.
Read retained observations with their revision and identity; omit `testId` from `read_app_test` to discover recent
tests when needed. Changed behavior needs a fresh test of the saved app. Keep fictional records and assignments inside the test session.

Only a successful save changes the app. Report saved changes, any remaining
private work with its work ID, and material limitations. Describe
verification and deployment only when you have evidence for them. Publishing
and changes to shared Project data need authorization from the user's request.
Project data, real organization records, media service writes and deployment
have separate immediate effects; discarding app work does not undo them.


Journey tests accept a configured worker language at start and a `language`
action without clearing answers or repeat rows. Use the structured language
identity (for example `{language: "spa"}`); observations report platform fallback.
Results and Details include formatted values and route context. Up to eight
ordered `actions: [{action, expect?}, ...]` can share one continuation request.
Each retains its own step; a refusal or unmet screen/module/form/submission
expectation stops with the completed prefix. An already completed submission
stays completed. Exact retries replay the entire response. The 200-action bound
still counts individual actions.
Read evidence by following `nextCursor` with its fixed `throughStep`. Large
steps offer explicit `inspect` paths and offsets so all retained evidence remains
accessible. Case transaction evidence does not establish serialized submission,
retained report, native-device or deployment behavior.
