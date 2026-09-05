---
name: upload_to_hq
description: Upload an existing Nova app to CommCare HQ using the user's stored API key, after checking that the selected project space can run it, along with the lookup tables it reads and the places in its organization. Then report what is left to do there and offer to make a mobile worker for each persona. The first upload to a project space creates the HQ app; uploading again updates that same app in place. Name a project space to upload straight there; otherwise it confirms the target with the user first.
argument-hint: <app_id or name> [project space]
---

# Task

The user wants to upload an app to CommCare HQ. The input is `$ARGUMENTS`.

## 1. Parse the arguments

`$ARGUMENTS` is the app to upload, optionally followed by a target project space:

- **App** — an app id (a UUID like `47f25e32-c265-423f-8a10-e341ae82ef2d`;
  some older apps have a compact ~20-char alphanumeric id) or a search
  phrase for the app's name (a name may contain spaces).
- **Project space (optional)** — a CommCare domain slug (lowercase, hyphenated,
  no spaces), given as the FINAL token. Treat a trailing token as the target
  space only when it reads like a domain slug and what precedes it is still a
  complete app reference; otherwise treat the whole of `$ARGUMENTS` as the app
  and leave the space unset. If the user quoted the app (e.g.
  `"Client Registry" connect-ace-prod`), the quoted part is the app and the
  trailing token is the space.

Call the space parsed here the **explicit target** — it may be unset.

A CommCare HQ **project space** is not a Nova **Project** (the shared
workspace `list_projects` reports). The target here is always an HQ
domain slug; never pass a Nova Project name or id as the space.

## 2. Resolve the argument to exactly one app

The app reference may be an app id or a name search phrase.

- Looks like an app id (a UUID, or a compact ~20-char alphanumeric token) → call Nova's `get_app` tool with `{app_id: "<app>"}`.
- Otherwise → call Nova's `search_apps` tool with `{query: "<app>"}`.
  - Zero matches → tell the user no app matched and stop.
  - Multiple matches → show them as a numbered list with
    `<N>. **<App Name>** (<app_id>, in <project_name>) — <N> modules, <M> forms, updated <date>`
    and ask which one. Wait for their answer before continuing. The
    Nova Project tells apart same-named apps living in different
    shared workspaces.
  - Exactly one → use it.

Throughout, refer to the app as **"App Name" (app_id)** so the user sees both
the friendly name and the stable id.

## 3. Resolve the exact HQ target

Call Nova's `get_hq_connection` (no arguments) before the compatibility check
or upload. `configured: false` → tell the user "CommCare HQ isn't connected yet.
Add your HQ API key in Settings (picking the CommCare server your account lives
on — US, India, or EU) before uploading." and stop.

A configured connection carries `server_url` and `available_domains`:

- **An explicit target was supplied →** match it to an `available_domains.name`.
  Naming that reachable space is already the user's upload confirmation, so do
  not ask again. If it is not reachable, list the reachable spaces and ask the
  user which one they intended; do not guess or continue until they choose.
- **No explicit target and one reachable space →** use that space, but the user
  must still confirm the upload in step 5.
- **No explicit target and several reachable spaces →** show a numbered list as
  `<N>. **<displayName>** (<name>)`, ask which one, and wait. There is no stored
  default and the agent must never choose for the user. Their answer selects the
  target, but step 5 still confirms the external upload action.

Call the chosen slug the **target**. The upload lands on `server_url`; US,
India, and EU are separate CommCare HQ deployments.

## 4. Check whether the target can run the app

Call Nova's `check_project_space_compatibility` with
`{app_id: "<resolved app_id>", domain: "<target>"}` before asking for upload
confirmation or invoking the upload. The domain is mandatory here: check the
exact project space the user selected, never an unselected or inferred space.
Read `project_space_compatibility` literally:

- `status: "not_needed"` means the app needs no destination-specific check.
  Proceed quietly.
- `status: "ready"` means every required capability is available. Do not make
  the confirmation noisy by listing available capabilities. If an `advisories`
  entry is `missing` or `unverified`, relay its friendly `title` and `message`
  as performance guidance; an advisory never blocks the upload.
- `status: "blocked"` means at least one required capability in `blockers` is
  `missing` or `unverified`. Use each blocker's friendly `label`, `description`,
  and app-specific `reasons` where they help. Preserve the distinction: missing
  support is confirmed unavailable, while unverified support could not be
  confirmed. Name **<target>** in every blocked notice, relay the report's
  `message` and next step, and always include its `docs_url`; include
  `support_email` when useful. Say that Nova has not uploaded anything, then
  stop. Do not ask for upload confirmation and do not call `upload_app_to_hq`.

Speak in app capabilities, not implementation settings: never show capability
`id` values, private project-space setting names, or private setting slugs. This
is a destination check, never a Nova authoring constraint. Do not remove, undo,
avoid, or revise requested app functionality because of it. The upload repeats
the check immediately before its first remote write, so an earlier ready result
cannot become stale permission to publish.

If the check returns `hq_not_configured`, stop with the Settings guidance from
step 3. If it returns `domain_not_authorized`, refresh the connection, show the
reachable spaces, and ask the user to select one; never silently substitute a
different target. A check that cannot confirm required support returns a
blocked report, not permission to continue.

## 5. Confirm and upload

For an explicit target, step 1's named space already confirmed the upload. Show
any non-blocking performance guidance from step 4 and proceed without asking
again.

Otherwise, confirm now. Substitute real values and include any non-blocking
performance guidance from step 4 in the same message; `<host>` is `server_url`
without the scheme:

> **"App Name"** (app_id) is already saved in Nova, and you can keep editing
> it here anytime. This **also** uploads it to CommCare HQ at
> `<host>/a/<target>/`, using your API key: a first upload creates the app
> there, and a later one updates that same HQ app in place. Any Project data
> tables the app reads and any places in its organization go up with it. Your
> Nova copy stays put.
>
> Upload it to **<target>** now?

Wait for confirmation. If the user declines, stop. Then call Nova's
`upload_app_to_hq` tool with
`{app_id: "<resolved app_id>", domain: "<target>"}`. Always pass the exact
target explicitly.

## 6. Report

On success the response has
`{hq_app_id, hq_app_action, url, warnings, project_space_compatibility,
deployment_state, deployment, setup_artifact}`. `hq_app_action` says whether
this upload created the HQ app or updated it in place — say which happened
(e.g. "Uploaded" for `created`, "Updated" for `updated`).

**Uploading is not releasing.** `deployment_state` is `uploaded`, which means
the app is on the project space and is NOT yet something workers can open.
CommCare HQ accepts an API key for putting an app there but not for making a
version or releasing one, so those steps need a signed-in person. Never say the
app is live, released, deployed to workers, or ready — say it is on CommCare HQ,
then give the two remaining steps:

> Uploaded **"App Name"** → `<url>`
>
> Two steps left, and they have to happen on CommCare HQ. Open the app's
> Releases screen, choose **Make new version**, then star it to release it.
> Tell me when you have, and I'll check it.
>
> (If `warnings` is non-empty, list them below as a short bullet list.)

If `deployment.left_behind` is non-empty, name each entry. Each one is
`{kind, hq_id, hq_name}`:

- `kind: "app"` — an app an earlier upload left on the project space (uploads
  made before Nova updated apps in place, or an app replaced after the mapped
  one was deleted on HQ). `hq_id` is how the user finds it there.
- `kind: "lookup-table"` — a table still sitting on the project space that the
  app no longer points at, either because its tag was renamed or because the
  last question reading it is gone. `hq_name` is the tag it still carries
  there, which is what the user will see on HQ's Lookup Tables screen. A table
  that was simply republished never appears here.
- `kind: "location"` — a place still on the project space that the app
  archived. Nova stops sending an archived place, and CommCare HQ's location
  API offers no way to archive or delete one, so Nova cannot take it down.
  `hq_name` is its site code, which is what the user will see on HQ's Organization
  screen — and that code stays reserved there even if they archive the place,
  so a future place cannot reuse it.
- `kind: "worker"` — a mobile worker Nova made for a persona the app no longer
  has, or under a username the persona no longer uses. `hq_name` is the complete
  username. Nova never deletes or retires a worker, because CommCare HQ's own
  delete also deletes every case that worker owns — so this one is a real
  person's account, and whether to keep it is entirely the user's call.

Nova never deletes anything on CommCare HQ, so say what is there and leave the
decision with the user: they can archive or delete it themselves once they no
longer need it.

`deployment.phases.resources` tells you whether the app's data went up on this
upload. A `succeeded` status means its lookup tables and places are on the
project space and match the Nova copy; `null` means the app has neither and
nothing was sent.

A `retry_from: "resources"` does not mean nothing was created. Places go up in
groups, one organization level at a time, and each group either lands whole or
not at all, so the levels before the one that stopped really are on the project
space. Lookup tables are the same: CommCare HQ writes a large table in more than
one piece, so a table can be there even though the upload was refused. Nova
records whatever it can account for, and uploading again carries on from there
rather than making a second copy. Never tell the user nothing was created; if
you need to be exact, call `get_deployment` and report what the record says.

`setup_artifact.sections` lists what the project space still needs set up by
hand, each with a real URL on that space. Do not paste all of it. Name the
sections and offer the detail, unless the user asked what they have to set up.

When the user says they have made and released the version, call
`refresh_deployment` with the same `app_id`, `server`, and `domain`. It returns
the same shape; report `state`:

- `built` — a version exists but is not released. Tell them to star it.
- `released` — released, and Nova is confirming a device can install it. Call
  `refresh_deployment` once more.
- `runnable` — now it is genuinely ready for workers. This is the only state to
  describe that way.
- `incomplete` — read `retry_from` and the matching entry in `phases` for the
  reason, relay it, and say that retrying picks up from there rather than
  starting over.

`refresh_deployment` can also answer with an ERROR instead of a state, and an
error is never a verdict on the app. It means Nova could not ask: the account
has no CommCare HQ key or the key no longer reaches that project space, or
CommCare HQ did not answer, or the app has not been published there at all.
Relay the message as-is — each one already says what to do — and do not report
the deployment as failed, refused, or moved. Nothing changed on the project
space, and the last state you saw is still the true one.

`get_deployment` reports every project space an app has been published to
without contacting CommCare HQ.

## 7. Offer to make workers

Once the deployment is `runnable`, the app is ready but nobody has an account
to open it with. If the app has personas (`get_users` reports them), offer:

> Want me to make a CommCare mobile worker for each persona on `<target>`?

Only when the user says yes, call `provision_workers` with
`{app_id, server, domain, workers: [{persona_uuid}]}` — one entry per persona
they asked for. Omit `username` to take Nova's suggestion from the persona's
name, or pass one the user gave you.

**Show every password in the answer to the user immediately, and show them all
before anything else.** Each `workers[]` entry carries `password` for an account
this call CREATED, and that value exists only in that answer — Nova stores no
copy and cannot show it again. Show them even when the answer also carries an
`error_type`: a call that stopped partway still made real accounts. An entry
with `action: "updated"` has `password: null`, because that person's password is
untouched.

**An error does not always mean the account was not made.** CommCare HQ saves a
worker before it writes its reply, so a request that breaks off after that point
leaves a real account behind and still answers with an error. That comes back as
`hq_worker_may_exist`, with the account in `unconfirmed_workers` carrying its
`password`. Show it exactly as urgently as any other password: if the account is
there, that password is the only one it will ever have, and Nova cannot look it
up, because CommCare HQ's username search runs on an index that trails a new
account by seconds. Tell the user to look for that username on their project
space. If it is not there, call again to make it. If it IS, wait a moment
before calling again: CommCare HQ's username search runs on an index that
trails its own new account by seconds, so until it catches up a retry still
tries to create and comes back as `hq_rejected_worker` saying the name is
taken. The take-over path is only available once `worker_conflicts` names the
account, and `adopt_personas` does nothing before then.

The refusals. None created an account except where said otherwise, and one
of them (`hq_rejected_worker`) is not always a proven non-event, so relay each
`message` rather than reading the tag alone:

- `app_not_published` — upload the app to that space first.
- `workers_not_provisionable` — the `message` names each reason: a username
  CommCare HQ will not take, worker information the app marks required that a
  persona has no value for, a persona standing in a place the project space
  does not hold yet (upload the app there, which puts the places there), the
  same persona or the same username named twice in one call, or a persona the
  app no longer has. Relay it and stop; nothing was created.
- `hq_worker_conflict` — one or more usernames already belong to accounts Nova
  did not create. `worker_conflicts` carries one entry per clash as
  `{persona_uuid, persona_name, username, hq_user_id}`. A mobile username is
  the whole address, `name@project-space.commcarehq.org`, so the same name is
  free on every other project space and taken only on this one, where it is
  somebody's real account. Ask the user about each one **one at a time**, and
  never decide for them or send them all because they said yes to one. Retry
  with `adopt_personas` set to the `persona_uuid` of each one they approved. The
  other way out is a username nobody has yet — a username is set once when the
  account is made, so giving a persona a new one makes a second account and
  leaves the first alone, and retiring an account never gives its name back.
- `hq_rejected_worker` — CommCare HQ would not complete one of the writes.
  Accounts made before it are real and are in `workers` with their passwords.
  An UPDATE that broke off mid-flight also lands here, and then the `message`
  says the change may or may not have taken; do not report that as "nothing
  changed".
- `hq_worker_state_unknown` — CommCare HQ would not say which usernames it
  holds. Nothing was written; try again.
- `hq_worker_may_exist` — CommCare HQ broke off mid-create and said nothing
  about what it made, as above. This is the one refusal that may have created
  an account; `unconfirmed_workers` carries it with its password.
- `hq_not_configured` / `domain_not_authorized` — the same Settings and
  reachable-space guidance as an upload.

Nova does not create CommCare user roles, and it does not set up the project
space's custom user-data field definitions; both are on the upload's
`setup_artifact` list. Say so if the user expects a worker to arrive with a
role.

On a successful upload, interpret `project_space_compatibility` literally.
Success guarantees that `blockers` is empty. Do not list available required
capabilities. Relay only `advisories` whose state is `missing` or `unverified`,
using each friendly `title` and `message`; these are performance guidance and
the upload has already succeeded. Link to the report's `docs_url` when useful.
Ignore any legacy compatibility projection that may coexist in a rollout
response.

On a failed upload, surface `error_type` and `message` from the response:

- `domain_not_authorized` — the space you passed isn't one the key can reach.
  The `message` already names every space it CAN reach, so relay that in one
  turn rather than making the user re-run the command — e.g. "`<space>` isn't
  connected to your key, but these are: `<list>`. Want me to upload to one of
  those?" After they choose, run the step 4 compatibility check for that exact
  space, then continue through step 5.
- `domain_ambiguous` — only happens with no `domain`; resolve the target via
  step 3, run the step 4 compatibility check for that target, and retry step 5.
- `hq_not_configured` — the user needs to connect CommCare HQ in Settings
  (pick the server their account lives on and add their API key).
- `project_space_incompatible` — the upload's authoritative pre-write check
  found required support missing or unverified after the earlier check. Nothing
  was uploaded in this attempt. Interpret
  `project_space_compatibility.blockers` exactly as in step 4, relay the
  report's next step, and stop. Never work around it by changing the app unless
  the user separately asks to change the app itself.
- `hq_app_state_unknown` — Nova could not safely read the current HQ app before
  updating it, so it left the existing app unchanged. Relay the `message` and
  try again only when the user asks.
- `remote_app_missing` — the HQ app this one updates in place was deleted on
  HQ. Nothing was changed; relay the `message` (uploading again creates a
  fresh app there).
- `hq_upload_failed` — an HQ-side rejection; show the `message` so the user
  knows what HQ rejected. This also covers CommCare HQ refusing the app's
  Project data tables or its places, which happens before the app is sent, so
  the app never went up either. When a deployment comes back with
  `retry_from: "resources"`, say that retrying picks up at the data rather than
  starting over. CommCare HQ's own sentence about a refused place arrives in
  `message` and names the place by its site code — relay it as it is, because it
  is more specific than anything you could infer.
- `hq_resource_conflict` — the project space already holds a lookup table or a
  place under a name one of the app's uses, and Nova will not overwrite
  something it did not put there. **Nothing was uploaded**, not even the app.
  The response carries `resource_conflicts`, one entry per clash as
  `{kind, nova_resource_id, name, hq_name, hq_id}`: `kind` is `lookup-table` or
  `location`, `name` is what the user calls it in Nova, `hq_name` is the name it
  collides with on HQ (a table's tag, or a place's site code). Name every clash
  and ask the user, **one at a time**, whether that HQ resource is theirs to
  take over. A shared name is not evidence that it is — never decide this for
  them, and never send them all because they said yes to one. Retry with
  `adopt_resources` set to the `nova_resource_id` of each one they approved;
  Nova then takes over exactly those and keeps them in step with the Nova copy.
  If they approve none, stop: the upload cannot proceed while a clash stands.
  The other way out differs by kind — a table's export tag can be renamed in
  Project data, while a place's site code is set once, so sending a place of
  their own beside it means removing it in Organization and adding it again
  with a code that is free.
- `hq_organization_mismatch` — the app's places do not fit the organization
  levels the project space has, so CommCare HQ would refuse them. **Nothing was
  uploaded.** The `message` names each place and what is wrong with it: a level
  the project space does not have, a place whose level is not directly below its
  parent's, two places under one parent sharing a name, or a place Nova moved to
  the top of the organization that HQ still holds under a parent. No approval
  resolves this one — do not offer `adopt_resources`. Relay the message, and say
  the fix is either in Nova's Organization or on CommCare HQ's Organization
  Levels page. Nova cannot create levels there: HQ's API is read-only for them,
  so `setup_artifact` carries every level the app needs, in the order to make
  them.

## Deep links after publishing

Uploading is not building or releasing. Nova cannot build or release an app
through the HQ API; follow the returned setup steps and have the user complete
those actions in HQ before asking Nova for a link.

When a user requests a deep link, load `get_entry_points` and the MCP-only
`get_entry_point_link` under both supported spellings:

```
ToolSearch({query: "select:mcp__plugin_nova_nova__get_entry_points,mcp__nova__get_entry_points,mcp__plugin_nova_nova__get_entry_point_link,mcp__nova__get_entry_point_link"})
```

Read `get_entry_points` to choose the authored immutable `entryPointUuid` and
its `requiredSelections`. Call `get_entry_point_link` with
`{app_id, server, domain, entry_point_uuid, selections}`, using the exact
selected server and project space. Each selection is `{module_uuid, case_ids}`;
use external HQ case IDs, never Nova case row IDs. Preserve order and supply
every required selection within its cardinality and maximum.

Call the verifier again after each upload, including a failed or partial
upload. Never reuse earlier verification as evidence for the new publish.
Nova checks the actual released build and required deployment resources before
returning a canonical public `/app/v1/` URL. If it refuses, relay the next step;
do not handcraft the URL or promise readiness from an upload response.
The URL is not pinned to the checked build: HQ's recipient latest-build policy
controls the version subsequently opened. Report the check time and observed
build from the result, keeping that distinction clear. Do not open the link
as a verification probe, because opening it can claim cases.
