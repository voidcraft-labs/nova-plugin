---
name: upload_to_hq
description: Upload an existing Nova app to CommCare HQ using the user's stored API key, after checking that the selected project space can run it, along with the lookup tables and places Nova manages for it. Then report what is left to do there and offer to make a mobile worker for each persona. The first upload to a project space creates the HQ app, or updates the HQ app it was brought in from; uploading again updates that same app in place, until publishing there stops, after which an upload makes a new app beside the one that stays. Name a project space to upload straight there; otherwise it confirms the target with the user first.
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

Upload uses the saved app. If this conversation has pending authoring work,
finish and save the intended changes before publishing, or explicitly explain
that the pending changes are excluded. Upload never saves private work for you.

Throughout, refer to the app as **"App Name" (app_id)** so the user sees both
the friendly name and the stable id.

Read `get_app` for the resolved app if you have not already. If its `notices`
is non-empty, tell the user what each one says before the upload, and wait for
their answer before calling `upload_app_to_hq`, even when they named the
project space: a notice can say what the next upload there does. Once they
have read them, offer `dismiss_app_notice` with each notice's `id` as
`notice_id`.

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
- `status: "blocked"` — check the report's top-level `issue` first. When it is
  `not-a-member`, the connected account is no longer a member of that project
  space, so nothing about it can be checked and no upload there can go ahead,
  whatever the app needs; `blockers` can then be empty. Relay its `message`:
  publishing there continues once that account joins the project space again or
  a different account is connected in Settings. Otherwise at least one required
  capability in `blockers` is `missing` or `unverified`. Use each blocker's
  friendly `label`, `description`, and app-specific `reasons` where they help.
  Preserve the distinction: missing support is confirmed unavailable, while
  unverified support could not be confirmed. Name **<target>** in every blocked
  notice, relay the report's `message` and next step, and always include its
  `docs_url`; include `support_email` when useful. Say that Nova has not
  uploaded anything, then stop. Do not ask for upload confirmation and do not
  call `upload_app_to_hq`.

Beside `project_space_compatibility`, at the top level of the same response,
the check says what the upload will ask the user to confirm, because no API
key can read it: `plan_features` (each plan feature the app needs, with
its `plans`, `reasons`, `consequence`, `where_missing` and `state`),
`flat_location_fixture` (whether the project space still sends its location
list, for an app that reads places), `connect_forwarder` (whether it forwards
forms to CommCare Connect, for a Connect app), `form_entry_sync_off`
(whether Sync Cases On Form Entry is turned off, for an app that runs on
Android and has a form that works on a case chosen in a menu with Search) and
`commtrack_off` (whether CommCare Supply is turned off, for an app with an
advanced menu that shows its case list as its own menu item, or a form whose
text names the session's supply point).
Each is `null` when the app needs none, and each carries its own
`where_missing` beside `consequence`: what the user can do where the project
space lacks it, or `null` when Nova has nothing to offer. Relay them with their
reasons before the upload, so the user knows what they will be asked. One
already on record reads `confirmed` with who confirmed it, and the upload does
not ask about it again; one that reads `needs_confirmation` will be asked.
When the Save to Case plan feature reads `needs_confirmation`,
`placement_moves` may carry the case changes Nova can keep elsewhere so the
app no longer needs it; relay them with that plan feature.

If the check's `first_publish` is not null, this upload changes things in
CommCare HQ beyond the user's own edits, and its `lead` says why. In the same
message as the confirmation, before the user says yes, relay `lead`, then
`workers.lines`, then `hq_only.lines`, each `sentence` as written, then
`reassurance` where it is not null, then `note`.

Speak in app capabilities, not implementation settings: never show capability
`id` values, private project-space setting names, or private setting slugs. This
is a destination check, never a Nova authoring constraint. Do not remove, undo,
avoid, or revise requested app functionality because of it. When the project
space's plan lacks Web Apps, the user may choose to set the app to Android
only; never make that change unless they ask for it. The upload repeats
the check immediately before its first remote write, so an earlier ready result
cannot become stale permission to publish.

If the check returns `hq_not_configured`, stop with the Settings guidance from
step 3. If it returns `domain_not_authorized`, refresh the connection, show the
reachable spaces, and ask the user to select one; never silently substitute a
different target. A check that cannot confirm required support returns a
blocked report, not permission to continue.

If the check's `new_app_beside` is not null, Nova stopped publishing this app
to the target, and this upload does not update the app in CommCare HQ: it
makes a new app beside it, and the one there stays as it is. The upload itself
asks nothing about this, so relay `new_app_beside` as written in the
confirmation, and upload only if the user wants a new app there, even when
they named the space. It is null while the app still publishes there and
where it never has. Where the user asks who stopped publishing there and when,
`get_deployment`'s deployment for the target carries it in `ending.message`.

## 5. Confirm and upload

For an explicit target, step 1's named space already confirmed the upload. Show
any non-blocking performance guidance from step 4 and proceed without asking
again, unless the app has notices (step 2), step 4 reported an item that
reads `needs_confirmation`, step 4's `first_publish` is not null, or step 4's
`new_app_beside` is not null. Then relay
them, stop, and wait for the user's answer before calling `upload_app_to_hq`. Send the items they confirmed with
the upload, as `hq_confirmation_needed` below describes.

Otherwise, confirm now. Substitute real values and include any non-blocking
performance guidance from step 4 in the same message; `<host>` is `server_url`
without the scheme:

> **"App Name"** (app_id) is already saved in Nova, and you can keep editing
> it here anytime. This **also** uploads it to CommCare HQ at
> `<host>/a/<target>/`, using your API key: a first upload creates the app
> there, and a later one updates that same HQ app in place. If this app was
> brought in from **<target>**, even the first upload updates the app it came
> from. Project data tables and places that Nova manages go up with it; ones
> CommCare HQ manages are left exactly as they are. Your Nova copy stays put.
>
> Upload it to **<target>** now?

Where step 4's `new_app_beside` is not null, the sentence about a first and a
later upload is not so. Say instead `new_app_beside` as written, and that the
app already in **<target>** stays as it is.

Wait for confirmation. If the user declines, stop. Then call Nova's
`upload_app_to_hq` tool with
`{app_id: "<resolved app_id>", domain: "<target>"}`. Always pass the exact
target explicitly.

The first upload of a case change records where CommCare HQ keeps it, which
changes the saved app. Work begun with `begin_work` before the upload must be
begun again.

## 6. Report

On success the response has
`{hq_app_id, hq_app_action, app_preview_note, logo_step, url, warnings,
project_space_compatibility, deployment_state, deployment, setup_artifact}`.
`hq_app_action` says whether this upload created the HQ app or updated it in
place — say which happened (e.g. "Uploaded" for `created`,
"Updated" for `updated`). `created` also covers an upload that filled the
empty app an earlier, unfinished first upload left there.

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

Then the parts of the answer that are there only sometimes:

- `app_preview_note` — when it is not `null`, relay it as it is. It says what
  this upload means for App Preview in CommCare HQ.
- `logo_step` — the app's logo, which an upload never sends. When its
  `changed` is true, relay its `instructions`: the one step in CommCare HQ
  that puts the logo in apps built there, and the plan that step needs.

If `deployment.left_behind` is non-empty, name each entry. Each one is
`{kind, hq_id, hq_name}`:

- `kind: "app"` — an app an earlier upload left on the project space (uploads
  made before Nova updated apps in place, an app replaced after the mapped
  one was deleted on HQ, or an app Nova stopped publishing to, once a later
  upload made a new app beside it). `hq_id` is how the user finds it there.
- `kind: "lookup-table"` — a table still sitting on the project space that the
  app no longer points at, either because its tag was renamed or because
  nothing in the app reads it any more. `hq_name` is the tag it still carries
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
project space: the ones Nova manages match the Nova copy, and the ones
CommCare HQ manages there are left as they are. `null` means the app has
neither and nothing was sent.

A `retry_from: "resources"` does not mean nothing was created. On a first
upload that got past making a new app there, the app itself is already there,
empty, and the next upload fills it. An app brought in from that project space
makes no new app: the HQ app is the one it came from, with its content. Places go up in groups, one organization level at
a time, and each group either lands whole or not at all, so the levels before
the one that stopped really are on the project space. Lookup tables are the
same: CommCare HQ writes a large table in more than one piece, so a table can
be there even though the upload was refused. Nova
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
CommCare HQ did not answer, or the app has not been published there at all,
or Nova stopped publishing it there, or another Nova app publishes to that HQ
app now.
Relay the message as-is — each one already says what to do — and do not report
the deployment as failed, refused, or moved. Nothing changed on the project
space, and the last state you saw is still the true one.

`get_deployment` reports every project space an app has been published to
without contacting CommCare HQ. Each deployment it lists, and the answer from
`refresh_deployment`, can carry two flags worth saying plainly:

- `hq_app_empty: true` — the app on the project space is the empty one a first
  upload makes before it sends the content. The next upload fills that same
  app.
- `hq_app_gone: true` — CommCare HQ reported the app gone. The next upload
  makes a new one there.

Each deployment can also carry `kept`: the settings that stay as CommCare HQ
holds them on that project space, with the date Nova read them. Say them when
the user asks what Nova leaves alone. `refresh_deployment` with
`kept_values: true` reads them again and answers with a sentence instead of a
state; relay it as it is. Where that sentence says the app changed in CommCare
HQ, it names `read_hq_changes`, which lists what changed (see "Changes made in
CommCare HQ" below).

`brought_in`, where it is not null, says the app came from CommCare HQ on that
project space, when and by whom. If `ending` is not null, say that Nova
stopped publishing there and relay its `message`: the app in CommCare HQ
stays, and the next upload there makes a new app beside it. Where
`ending.held_by_another_app` is true, another Nova app publishes to that HQ
app now, no `hq_app_id` is given, and there is no way back to it to offer.
`nova_revision` is the revision of this app that CommCare HQ's copy was last
known to match, beside `pushed_revision`, the one Nova last sent; after
changes made in CommCare HQ are brought in, only a revision after
`nova_revision` holds something waiting to be published.

The same answers, and an upload's `deployment`, carry `confirmations`: what a
person confirmed about that project space for this app (a plan feature, the
flat location list, a Connect forwarder, Sync Cases On Form Entry turned off,
CommCare Supply turned off),
each with its `label` and who confirmed it when. An upload there does not ask
about them again. If the user says the project space no longer has one, for
example after a plan change, which Nova cannot see, call
`withdraw_deployment_confirmation` with `{app_id, domain, kind, subject}`
(`subject` only for a `plan-feature`), and the next upload there asks again.

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

- `app_not_published` — upload the app to that space first. This also covers
  a space that holds only the empty app an unfinished first upload made, or an
  app CommCare HQ reported gone: the next upload there fills or replaces it.
  It also covers a project space Nova stopped publishing this app to, where
  the `message` says so: publishing there again makes a new app, and workers
  can be added after that.
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
  the user separately asks to change the app itself. When the response carries
  `placement_moves`, the project space drops the link between a new case and
  the case of the same type it came from, or Nova could not check that it
  keeps it, and Nova offers to keep those case changes in Save to Case blocks
  instead. Show each move's `sentence`, which names its change, where it moves
  from and where to, and ask whether to move them; only on a yes, retry with
  `accept_placement_moves` carrying its `reason` and `digest`. Moving them
  changes where CommCare HQ keeps those answers in every project space the app
  is published to, and the plan then needs Save to Case, which the next attempt
  may ask about.
- `hq_app_state_unknown` — Nova could not safely read the current HQ app before
  updating it, so it left the existing app unchanged. Relay the `message` and
  try again only when the user asks. On a first upload it also covers an app
  Nova has just made and then could not read, right after making it or after
  sending the tables and places, or whose CommCare version it could not read.
  In each of those cases the app is then on the project space, empty, and the
  `message` says so. It also covers a linked app in CommCare HQ, which Nova
  never updates; the `message` gives the ways forward.
- `remote_app_missing` — the HQ app this one updates in place was deleted on
  HQ. Nothing was changed; relay the `message` (uploading again creates a
  fresh app there).
- `hq_upload_failed` — an HQ-side rejection; show the `message` so the user
  knows what HQ rejected. This also covers CommCare HQ refusing the app's
  Project data tables or its places. That happens before the app's content is
  sent. On a first upload that makes a new app there, Nova has by then made
  the app on the project space, empty, so `get_deployment` reports
  `hq_app_empty: true` and the next upload fills that same app. An app brought
  in from that project space makes no new app: the HQ app is the one it came
  from, with its content, and `hq_app_empty` stays false. When a deployment comes back with
  `retry_from: "resources"`, say that retrying picks up where it stopped rather
  than starting over: at the app on a first upload that never made it,
  otherwise at the data. CommCare HQ's own sentence about a refused place
  arrives in `message` and names the place by its site code — relay it as it
  is, because it is more specific than anything you could infer.
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
  When a lookup table is among them, the response also carries
  `adoption_note`, what taking a table over does to it; relay it before asking.
  If they approve none, stop: the upload cannot proceed while a clash stands.
  The other way out differs by kind — a table's export tag can be renamed in
  Project data, while a place's site code is set once, so sending a place of
  their own beside it means removing it in Organization and adding it again
  with a code that is free.
- `hq_organization_mismatch` — the app's places do not fit the organization
  levels the project space has, so CommCare HQ would refuse them. **Nothing
  was sent**: the check before the upload finds this. (If Nova stops itself
  during the upload because it cannot tell where a place belongs, the
  `message` says so. A place CommCare HQ itself refuses during the upload
  arrives as `hq_upload_failed`, above.) The `message` names each place and
  what is wrong with it: a level the project space does not have, a place
  whose level is not directly below its parent's, two places under one parent
  sharing a name, or a place Nova moved to the top of the organization that HQ
  still holds under a parent. No approval
  resolves this one — do not offer `adopt_resources`. Relay the message, and say
  the fix is either in Nova's Organization or on CommCare HQ's Organization
  Levels page. Nova cannot create levels there: HQ's API is read-only for them,
  so `setup_artifact` carries every level the app needs, in the order to make
  them.
- `hq_confirmation_needed` — the app needs something of the project space that
  no API key can read, and nobody has confirmed it there. Nothing was sent. The
  response carries `confirmations_needed`, one entry per item as
  `{kind, subject, label, plans, consequence, reasons, where_missing}`: a plan
  feature, the flat location list, for a Connect app the Connect forwarder, or,
  for an app that runs on Android and has a form that works on a case chosen in
  a menu with Search, Sync Cases On Form Entry turned off, or, for an app with
  an advanced menu that shows its case list as its own menu item or a form
  whose text names the session's supply point, CommCare Supply turned off.
  Ask the user about
  each one **one at a time**, with its `label`, `plans`, `consequence` and
  `reasons`, whether the project space has it, exactly as for
  `adopt_resources`. When the user says the project space lacks what was asked
  and `where_missing` is not `null`, relay it: it says what they can do there.
  Never decide for them, and never send them all because they said yes to one.
  Retry with `confirm_plan_features` (the `subject` of each plan feature they
  confirmed), `confirm_flat_location_fixture: true`,
  `confirm_connect_forwarder: true`, `confirm_form_entry_sync_off: true` or
  `confirm_commtrack_off: true`, naming only what they confirmed. A
  confirmation is kept once an upload goes ahead, so resend it with each
  attempt until one does. When `placement_moves` comes with the Save to Case
  plan feature, ask one question with two answers: the plan includes Save to
  Case (confirm it), or move those case changes (`accept_placement_moves` with
  its `reason` and `digest`). Never send both.
- `hq_placement_moves_changed`: the case changes Nova offered to move changed
  since the user agreed. Nothing was sent. Show the new `placement_moves` and
  ask again; send only the new `digest`.
- `app_changed_while_publishing`: the app kept changing while Nova got it
  ready to publish. Nothing was sent. Upload again once the edits settle.
- `hq_web_apps_change` — the app's Web App setting on CommCare HQ differs
  from where the app runs, and every upload writes that setting from where the
  app runs. Nothing was sent. Relay the `message`: it says which way the setting
  would change, whether someone changed it in CommCare HQ, and what workers
  there meet. `web_apps_change` carries `{from, to, changed_in_hq}`. Ask the
  user whether to change it, and only when they say yes, retry with
  `confirm_web_apps` set to `web_apps_change.to`. This answer counts for one
  upload only, so resend it with each retry until an upload goes ahead.
- `hq_plan_lacks_web_apps` — a first upload of an app that runs in Web Apps,
  where CommCare HQ made the new app with Web Apps off, which it does when the
  project space's plan doesn't include Web Apps. Only the empty app was made,
  and the next upload fills that same app. Nova no longer counts on an earlier
  answer that the plan includes Web Apps, so leave `web-apps` out of
  `confirm_plan_features` until the user says the plan now includes it. Relay
  the `message`: it offers setting the app to run on Android only where the
  app's content allows it. Where the app runs is the user's decision; change it
  with `update_app`'s `runs_only_on` only when they ask.
- `hq_app_version_below_floor` — the app on CommCare HQ is set to a CommCare
  version below the one Nova's apps need. Its content was not sent. Relay the
  `message` and its `url`, the app's page in CommCare HQ, where the user raises
  the CommCare version in the app's settings. Then upload again. On a first
  upload that makes a new app there, Nova has made the app there, empty, and
  read the CommCare version CommCare HQ gave it; the next upload fills that
  same app once the version is raised at `url`. For an app brought in from that
  project space, the app there is the one it came from, with its content, and
  the `message` says that saving its settings page can change its other
  settings there too, so the next upload may stop to show what changed.
- `hq_changed` — the app, a lookup table or a place this app publishes changed
  in CommCare HQ since Nova last published it, or, for an app brought in and
  not yet published, since it was brought in, or since Nova last brought in
  changes from it (each entry's `since` says which, and the `message` names
  the day in UTC). Nothing was sent. The response carries `remote_changes`,
  one entry per change as `{kind, nova_resource_id, name, hq_name, parts,
  note, observed_digest, baseline_known, since, can_bring_in}`.
  When the app's change has `can_bring_in` true, read what changed with
  `read_hq_changes` and show the user both lists. Bringing the changes in
  keeps everything when `nova_changes` is empty. When it is not empty, it
  removes every change listed there for good: show that list and ask before
  calling `bring_in_hq_changes` with `discard_nova_changes` true. The user can
  also publish over the change instead. "Changes made in CommCare HQ" below
  has the rest. Where the user would rather leave CommCare HQ's version
  alone, an admin or owner of the Project can stop publishing there: see
  "Stop publishing to a project space" below.
  To publish over a change, list every entry with its `name`, `hq_name` and
  `parts` (when `baseline_known` is false, Nova could not tell what changed;
  say so), relay its `note` when there is one, and ask **one at a time**
  whether to write over it. Retry with
  `discard_hq_changes` carrying `{kind, nova_resource_id, observed_digest}` for
  each entry the user confirmed. Never send a digest the user did not see. When
  `remote_changes` is empty, the change landed in CommCare HQ while this upload
  was sending the Project data: the tables and places are already on the project
  space and the app's content was not sent. On a first upload that makes a new
  app there, the empty app was made too. Relay the `message`, send no `discard_hq_changes`, and upload again.
  That upload normally comes back as an ordinary `hq_changed` with
  `remote_changes` listed, because the change is still in CommCare HQ, and that
  one is confirmed the usual way.
- `hq_table_content_unsupported` — a lookup table in CommCare HQ under one of
  this app's export tags holds what Nova cannot keep yet, so publishing over it
  would remove it. Nothing was sent, and neither `adopt_resources` nor
  `discard_hq_changes` resolves it. The `message` names each table; the way out
  it gives is a new export tag in Project data, so Nova publishes its own table
  and leaves that one alone.
- `hq_managed_data_changed`: a lookup table this app reads is managed in
  CommCare HQ and changed there in a way the app depends on. Nothing was sent.
  Relay the `message`: each line names a table, what changed and what the
  user can do, in CommCare HQ or by managing the table in Nova. Call
  `set_lookup_table_management` only if the user chooses that, after showing
  them what it does. Then upload again.
- `managed_table_handed_back`: a lookup table this app reads was handed back
  to CommCare HQ while this upload was getting ready. Nova stopped before
  sending any lookup table or the app's content. Upload again, and Nova leaves
  that table as it is.
- `hq_build_profile_language_missing`: an application profile of the app on
  CommCare HQ includes a language the app no longer has. Its content was not
  sent. Relay the `message` and its `url`, the app's page in CommCare HQ,
  where the user takes the language out of the profile or removes the profile
  on the Application Profiles tab, or, where the `message` offers it, removes
  the language on the Languages tab. Then upload again.
- `publishing_stopped`: someone stopped publishing this app to that project
  space while this upload was getting ready. Relay the `message`, which says
  whether anything was sent. Uploading again makes a new app there, so ask
  first.

These refusals can come one after another: answering one lets the next check
run, so a retry after `hq_confirmation_needed`, `hq_resource_conflict`,
`hq_changed` or `hq_web_apps_change` can stop at another of them. A refused
attempt stores nothing the user answered. On every retry, resend every answer
they have already given in this upload, `confirm_plan_features`,
`confirm_flat_location_fixture`, `confirm_connect_forwarder`,
`confirm_form_entry_sync_off`, `confirm_commtrack_off`, `confirm_web_apps`,
`accept_placement_moves`, `adopt_resources` and `discard_hq_changes`
together, plus the new one, until an upload goes ahead.
Never ask the user the same question twice.

## Changes made in CommCare HQ

Call Nova's `read_hq_changes` with `{app_id, domain: "<target>"}` after an
`hq_changed` whose app change has `can_bring_in` true, or when the user asks
what changed there. It changes nothing. Relay its `message` and its other
sentences as written: they say what the user can do. By `kind`:

- `changes`: `hq_changes` lists what bringing the changes in changes in this
  app, and `nova_changes` what that removes of the changes made in Nova since
  then; it is empty when nothing would be removed. A review longer than one
  answer comes a page at a time: while `next_page` is not null, call
  `read_hq_changes` again with the same `app_id` and `domain` and `page` set
  to it, until it is null. If an answer has `restarted` true, the lists
  changed: relay `restarted_message` and start them over from that answer.
  The pages hold, in order, the lines of `hq_changes`, then of `nova_changes`,
  then the entries of `renamed_in_nova`, then of `tables`, then the names of
  `made_by`, each page its share. So one page may hold only `hq_changes` lines
  while a later one holds the renames or a table that needs a choice: read
  `nova_changes_total`, `renamed_in_nova_total`, `tables_total` and
  `made_by_total` for how many each holds in all, and read every page before
  you ask the user anything. Show the user every line of both lists, then
  `made_by_line` where present, `case_data`, and `publish_changes_lead` with
  `publish_changes`, what the next upload then changes in CommCare HQ. Where
  `cut_line` is not null, this answer's one line is part `part` of `parts` of
  a line of `cut_line.list` too long for one answer: the next pages hold the
  rest, so join the parts in order and show the whole line. Where a page's
  `renamed_in_nova` is not empty, relay that page's `renamed_in_nova_line`,
  which names the renames on that page: while `renamed_in_nova_total` is not
  0, CommCare HQ's version is not offered until those case properties are
  renamed back in Nova. Each entry of `tables` is a lookup table the changed
  app newly reads: show its `sentence`, or its `choice`: the `title`, the
  `body`, and each answer's `label`, `lines` and, where it is not offered, its
  `reason`. Ask the user for each choice, and never choose one for them.
- `nothing`: there is nothing to bring in. Where `review_digest` is not null,
  CommCare HQ saved the app without a change Nova brings in, and `next` says
  how to record that: it changes nothing in the app, and the next upload no
  longer stops for the app's change (a lookup table or a place changed there
  still stops it).
- `account`: CommCare HQ's version holds something Nova can't hold yet, so
  nothing can come in. Relay `message`, then the findings grouped by `place`
  with each `sentence`, its `named` where present and the label of its
  `standing`, paging by `account.next_page` as above, then `check_again`.
- `held`, `unavailable` or `stop`: Nova can't bring the changes in. Relay
  `message`, or for `stop` its `title`, `body` and `next`. An `unavailable`
  answer whose `reason` is `not-published`, `publishing-stopped` or
  `app-deleted` means nothing in that project space is this app's: there is
  no change there to bring in or to publish over.

Bringing the changes in is the user's choice. Call `bring_in_hq_changes` with
`{app_id, domain, reading_id, review_digest, discard_nova_changes,
table_choices}`, the `reading_id` and `review_digest` of the last answer, and
`table_choices` with one answer per table that has a choice, by `tag` (`{}`
where none has). Send `discard_nova_changes` false when `nova_changes_total`
was 0, and true only after the user has seen every line of `nova_changes` and
agreed to lose them: Nova can't put them back. Nothing is sent to CommCare
HQ. By `kind`:

- `brought-in`: relay `message`. The changes are in the app.
- `recorded`: relay `message`. The app is unchanged.
- `changed`: nothing was brought in. Relay `message`, show `now` as an answer
  of `read_hq_changes`, and ask again; never resend old answers against it.
  Where `next` is not null, `now` holds only the first page: call
  `read_hq_changes` with `page` set to `now.next_page`, page on as above, and
  show every line before you ask again.
- `gate`: nothing was brought in, because it would leave something in the app
  that no longer works. Relay `message`, each of `findings`, and `next`.
- `refused`: relay `message`.

After `brought-in` or `recorded`, `deployment` can be null where Nova couldn't
read the record back; what was brought in still landed, and `get_deployment`
reads it again. Where `deployment.first_publish` is not null, relay it before
the next upload as step 4 does. If this began as an upload, upload again: the
app's change no longer stops it. Otherwise offer the upload, which goes through
step 5's confirmation like any other.

Both tools refuse with `error_type` and `message`:

- `invalid_input` from `read_hq_changes`: the `page` sent is not one Nova
  gave. Call it again without `page` and show the lists from the start.
- `invalid_input` from `bring_in_hq_changes`: `discard_nova_changes` did not
  match what the review lists. Relay the `message`, and never send true
  without the user's yes.
- `not_found`: the app is not one the user can edit. Relay the `message`.
- `scope_missing`: the user's connection to Nova lacks the CommCare HQ access
  this needs. Relay the `message`, which names the access to grant, and stop.
- `hq_not_configured`, `domain_not_authorized` or `domain_ambiguous`: the same
  Settings and reachable-space guidance as an upload (step 3). Never choose a
  project space for the user.

## Stop publishing to a project space

Nova's `stop_publishing` ends this app's publishing to one project space.
Call it only when the user asked for exactly this, after telling them what it
does: the app in CommCare HQ stays exactly as it is, this Nova app stops
publishing to it, and that HQ app can be brought in to Nova again as a new app
(`/nova:bring_in`). A later upload to that project space makes a new app there,
beside the one that stays. Nothing is sent to CommCare HQ, and it cannot be
undone from Nova.

Call it with `{app_id, server, domain}`: `server` is `get_hq_connection`'s
`server`, and `domain` the project space. Only an admin or owner of the app's
Project can stop: an editor gets `permission_denied`, whose `message` names who
can, and someone who cannot edit the app gets `not_found`. Relay either and
stop. Where Nova isn't publishing the app there, the `message` says there is
nothing to stop.

The answer is the deployment, with `state: "ended"`; relay `ending.message`.
`setup_artifact` can be null where Nova couldn't read everything back after
the stop landed. Publishing there has still stopped: never call
`stop_publishing` again for it, and `get_deployment` reads it again.

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
