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

- Looks like a Firestore id → call `mcp__plugin_nova_nova__get_app({app_id: "$ARGUMENTS"})`.
- Otherwise → call `mcp__plugin_nova_nova__search_apps({query: "$ARGUMENTS"})`.
  - If the response has zero matches: tell the user no app matched and stop.
  - If multiple matches: show them as a numbered list with
    `<N>. **<App Name>** (<app_id>) — <N> modules, <M> forms, updated <date>`
    and ask which one to upload. Wait for their answer before continuing.
  - If exactly one match: use it.

Throughout the rest of the flow, refer to the app as **"App Name" (app_id)**
so the user sees both the human-readable name and the stable identifier.

## 2. Check the HQ connection

Call `mcp__plugin_nova_nova__get_hq_connection` with no arguments.

- `configured: false` → tell the user: "CommCare HQ isn't connected yet. Add
  your HQ API key in Settings before uploading." Stop.
- `configured: true` → remember `domain.name` for the confirmation message.

## 3. Confirm with the user

Show this before uploading (substitute the real values):

> **"App Name"** (app_id) is already saved in Nova — this upload is not what
> keeps it safe, you can edit it here anytime.
>
> Uploading creates a **new** app at `commcarehq.org/a/<domain.name>/` using
> your API key. Your Nova copy stays put.
>
> Proceed?

Wait for their confirmation. If they decline, stop.

## 4. Upload

Call `mcp__plugin_nova_nova__upload_app_to_hq({app_id: "<resolved app_id>"})`.

The tool derives the target domain from the user's stored credentials — do
NOT pass a `domain` argument.

## 5. Report

On success, the response has `{hq_app_id, url, warnings}`. Tell the user:

> Uploaded **"App Name"** → `<url>`
>
> (If `warnings` is non-empty, list them below as a short bullet list.)

On a failed upload, surface `error_type` and `message` from the response so
the user knows whether it's an HQ-side rejection, a connection issue, or a
missing configuration.
