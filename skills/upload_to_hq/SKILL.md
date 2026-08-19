---
name: upload_to_hq
description: Upload an existing Nova app to CommCare HQ using the user's stored API key, along with the lookup tables it reads and the places in its organization, then report what is left to do there. The first upload to a project space creates the HQ app; uploading again updates that same app in place. Name a project space to upload straight there; otherwise it confirms the target with the user first.
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

Call Nova's `get_hq_connection` (no arguments) before the feature-flag check or
upload. `configured: false` → tell the user "CommCare HQ isn't connected yet.
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

## 4. Check and disclose the target's feature flags

Call Nova's `get_app_hq_feature_flags` with
`{app_id: "<resolved app_id>", domain: "<target>"}` before asking for upload
confirmation or invoking the upload. Read
`feature_flag_requirements` literally:

- `missing_flags` contains only flags Nova confirmed are not enabled on this
  target. Name each label and slug, include its app-specific `reasons`, link its
  `docs_url`, and tell the user to contact the returned `support_email` with the
  target project-space name.
- `unverified_flags` contains required flags whose state HQ's diagnostic could
  not answer. Name them, but say they are **not confirmed missing**.
- `verification: "verified"` means every diagnostic answered; it does **not**
  mean every flag is enabled, so still inspect `missing_flags`.
- `verification: "not_required"` needs only a quiet sentence, or no extra
  feature-flag copy when the surrounding confirmation is already clear.

This is deployment information, never a Nova authoring gate. Do not remove,
undo, avoid, or revise app functionality because of it, and do not block the
upload based on requirements alone. The upload response checks the same target
again after import.

If the check returns `hq_not_configured`, stop with the Settings guidance from
step 3. If it returns `domain_not_authorized`, refresh the connection, show the
reachable spaces, and ask the user to select one; never silently substitute a
different target. If the diagnostic itself is partially unavailable, continue
with its honest `unverified_flags` result.

## 5. Confirm and upload

For an explicit target, step 1's named space already confirmed the upload; show
the step 4 disclosure and proceed without asking again.

Otherwise, confirm now (substitute real values and include the step 4
feature-flag disclosure in the same message; `<host>` is `server_url` without
the scheme):

> **"App Name"** (app_id) is already saved in Nova and you can keep editing
> it here anytime — this **also** uploads it to CommCare HQ at
> `<host>/a/<target>/`, using your API key: a first upload creates the app
> there, and a later one updates that same HQ app in place. Any Project data
> tables the app reads and any places in its organization go up with it. Your
> Nova copy stays put.
>
> Proceed?

Wait for confirmation. If the user declines, stop. Then call Nova's
`upload_app_to_hq` tool with
`{app_id: "<resolved app_id>", domain: "<target>"}`. Always pass the exact
target explicitly.

## 6. Report

On success the response has
`{hq_app_id, hq_app_action, url, warnings, feature_flag_requirements,
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

Nova never deletes anything on CommCare HQ, so say what is there and leave the
decision with the user: they can archive or delete it themselves once they no
longer need it.

`deployment.phases.resources` tells you whether the app's data went up on this
upload. A `succeeded` status means its lookup tables and places are on the
project space and match the Nova copy; `null` means the app has neither and
nothing was sent.

Places go up in groups, one organization level at a time, and each group either
lands whole or not at all. So a `retry_from: "resources"` after some groups
landed is not "nothing happened" — the earlier levels really are on the project
space and Nova recorded them, and uploading again carries on from there rather
than making a second copy. Never tell the user nothing was created; if you need
to be exact, call `get_deployment` and report what the record says.

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

Then interpret `feature_flag_requirements` literally; never infer a flag's
state from the app alone:

- `missing_flags` — Nova checked the target after the successful upload and
  confirmed these flags are not enabled. Name every flag (label and slug), say
  it is confirmed missing for the target project space, and tell the user to
  contact `support@dimagi.com` to enable it for that named space.
- `unverified_flags` — Nova could not determine these flags' state. Name every
  flag (label and slug), make clear they are required but **not confirmed
  missing**, and tell the user to contact `support@dimagi.com` if they need a
  flag enabled for that named space.
- `verification: "verified"` with both lists empty — a short sentence that Nova
  verified all required flags are enabled is enough.
- `verification: "not_required"` — do not add feature-flag noise.

The upload has already succeeded even when flags are missing or could not be
checked. Present this as follow-up information, never as an upload failure.
Link to `https://docs.commcare.app/feature-flags` when useful.

On a failed upload, surface `error_type` and `message` from the response:

- `domain_not_authorized` — the space you passed isn't one the key can reach.
  The `message` already names every space it CAN reach, so relay that in one
  turn rather than making the user re-run the command — e.g. "`<space>` isn't
  connected to your key, but these are: `<list>`. Want me to upload to one of
  those?" — then upload to their pick.
- `domain_ambiguous` — only happens with no `domain`; resolve the target via
  step 3, run the step 4 feature-flag check for that target, and retry step 5.
- `hq_not_configured` — the user needs to connect CommCare HQ in Settings
  (pick the server their account lives on and add their API key).
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
