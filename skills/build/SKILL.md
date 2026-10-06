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

If the user named a Nova Project, resolve it with `list_projects`. Resume work
from an earlier request with `list_work` and `get_work` when relevant. Otherwise
call `begin_work` with a unique `request_id` and
`new_app: { name: "App name", project_id: "resolved-project-id" }`, omitting
`project_id` for the personal Project. Keep the returned `work_id` across saves;
`get_work` reads its current candidate and diagnostics. The app receives its
saved identity at the first valid checkpoint.

Design the records and workflows together. Ask about choices that materially
change the app and fill routine gaps yourself. Build complete workflows, then
refine their wording, layout and behavior. Create the module, then the empty
form, then its questions; configure answer-dependent rules once their questions
exist. Use `work_id` and a unique `request_id` for shared edits. Shared reads
select exactly one of `work_id` for private state or `app_id` for saved state.
Read `get_authoring_guide` against that target when a feature needs explanation; the server owns the current syntax
and domain guidance.

Form and case-operation reads, plus operation edit feedback, include
`operationSemantics`: record targets, condition/value dependencies and possible
read/write overlaps. Read it when designing competing actions. Native conditions
can retain an open form's initialized record view even after another form updates
the same local store; they do not compare-and-set current records at submission.
Preview transaction reads have a separate provenance. An empty overlap inventory
does not establish concurrency protection.

Read the resolved navigation returned by form tools. After a submission,
Previous resumes the preceding task or record selection. That can be the same
form's record picker or a menu for the retained records. Ordinary Back follows
visited screens. Check the actual next task after submitting.

Save meaningful progress with `save_work`, using `work_id`, a unique
`request_id`, and `expected_revision` copied from the latest candidate result.
Staged edits are not saved. If validation refuses, correct the private candidate
and try a new save request. If another editor changed the saved app, preserve
your candidate and discuss the conflicting work before explicitly discarding it.
`discard_work` uses the same revision-bound envelope and keeps the work ID;
subsequent edits start from current saved state. Reuse a request ID only for an
exact retry after a lost response, never for changed input.

After a successful save, exercise representative journeys from app entry with `start_app_test`,
`continue_app_test` and `read_app_test`. Start and continue calls take a unique
`request_id` and exactly one of `app_id` or `work_id`; both exercise the saved
checkpoint. `read_app_test` is a shared read and takes no request ID.
Use the app's saved Preview identities
and fictional records or place assignments within the isolated test session.
Observe selection, record details, answers, submission effects and the next task.
Follow the offered `routeContinue` action from Details; `routeBack` revisits the
prior screen. In a sectioned form, `pageNext` and `pagePrevious` turn form pages;
the offered `section` action also selects a page. Answer the current page before
advancing. Investigate failed behavior through ordinary authoring tools, then
check affected journeys.
To reuse recorded evidence, call `read_app_test` without `testId` to list recent
tests, then read the returned identity for the relevant purpose and revision.
These observations do not establish native-device or deployment behavior.

Finish with the app's name and ID, how to try it, and any work or decision still
needed. Distinguish saved structure, behavior you observed, and deployment to
CommCare HQ. Publishing and changes to shared Project data need authorization
from the user's request. Project data, real organization records, media service
writes and deployment take effect separately; discarding app work does not undo
them. If work remains private, include its work ID and what still needs attention.


Journey tests accept a configured worker language at start and a `language`
action without clearing answers or repeat rows. Use the structured language
identity (for example `{language: "spa"}`); observations report platform fallback.
Results and Details include formatted values and route context. Up to four
named sessions can share disposable records while retaining separate identities,
languages, navigation and open forms. Use `sessions` at start and `sessionId` on
each addressed continuation item; omission selects the primary session. For
competing actions, retain one form while another session submits, then return to
the retained form. Sync refreshes that session's record catalog and keeps its
open-form entry snapshot. Observations identify retained and current-store reads.
Up to eight ordered `actions: [{sessionId?, action, expect?}, ...]` can share one continuation request.
Each retains its own step; a refusal or unmet screen/module/form/submission
expectation stops with the completed prefix. An already completed submission
stays completed. Exact retries replay the entire response. The 200-action bound
still counts individual actions.
Read evidence by following `nextCursor` with its fixed `throughStep`. Large
steps offer explicit `inspect` paths and offsets so all retained evidence remains
accessible. Case transaction evidence does not establish serialized submission,
retained report, native-device or deployment behavior.
