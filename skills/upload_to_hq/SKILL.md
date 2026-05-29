---
name: upload_to_hq
description: Upload an existing Nova app to CommCare HQ using the user's stored API key. Confirms the target domain with the user before uploading.
argument-hint: <app_id or name>
---

# Task

The user wants to upload app "$ARGUMENTS" to CommCare HQ. Follow these steps.

## 1. Resolve the argument to exactly one app

`$ARGUMENTS` may be either a Firestore app id (a short alphanumeric string,
typically ~20 chars) or a search phrase for the app's name.

- Looks like a Firestore id → call Nova's `get_app` tool with `{app_id: "$ARGUMENTS"}`.
- Otherwise → call Nova's `search_apps` tool with `{query: "$ARGUMENTS"}`.
  - If the response has zero matches: tell the user no app matched and stop.
  - If multiple matches: show them as a numbered list with
    `<N>. **<App Name>** (<app_id>) — <N> modules, <M> forms, updated <date>`
    and ask which one to upload. Wait for their answer before continuing.
  - If exactly one match: use it.

Throughout the rest of the flow, refer to the app as **"App Name" (app_id)**
so the user sees both the human-readable name and the stable identifier.

## 2. Check the HQ connection and resolve the target space

Call Nova's `get_hq_connection` tool with no arguments. The response has
`configured` and `available_domains` (every project space this API key can
upload to — an unscoped key reaches several).

- `configured: false` → tell the user: "CommCare HQ isn't connected yet. Add
  your HQ API key in Settings before uploading." Stop.
- `configured: true` → resolve which space to upload to:
  - One entry in `available_domains` → that's the target.
  - Multiple entries → the user chooses; never pick for them. Show the spaces as
    a numbered list — `<N>. **<displayName>** (<name>)` — and ask which one to
    upload to. Wait for their answer before continuing. (There is no stored
    default: a multi-space key's target is a per-upload choice.)

Remember the chosen space's `name` (the slug) for the upload call.

## 3. Confirm with the user

Show this before uploading (substitute the real values; `<space>` is the
chosen space's `name`):

> **"App Name"** (app_id) is already saved in Nova — this upload is not what
> keeps it safe, you can edit it here anytime.
>
> Uploading creates a **new** app at `commcarehq.org/a/<space>/` using your
> API key. Your Nova copy stays put.
>
> Proceed?

Wait for their confirmation. If they decline, stop.

## 4. Upload

Call Nova's `upload_app_to_hq` tool with
`{app_id: "<resolved app_id>", domain: "<chosen space name>"}`.

Always pass `domain` explicitly — it's the space you confirmed in step 3.
(Omitting it works only for a single-space key; for a multi-space key the tool
returns `domain_ambiguous` rather than guessing the target.)

## 5. Report

On success, the response has `{hq_app_id, url, warnings}`. Tell the user:

> Uploaded **"App Name"** → `<url>`
>
> (If `warnings` is non-empty, list them below as a short bullet list.)

On a failed upload, surface `error_type` and `message` from the response:

- `domain_ambiguous` / `domain_not_authorized` → the message names the spaces
  the key reaches; re-confirm the target with the user and retry step 4 with a
  valid `domain`.
- `hq_not_configured` → the user needs to add their key in Settings.
- `hq_upload_failed` → an HQ-side rejection; show the message so the user knows
  what HQ rejected.
