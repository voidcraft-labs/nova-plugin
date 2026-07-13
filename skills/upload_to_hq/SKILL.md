---
name: upload_to_hq
description: Upload an existing Nova app to CommCare HQ using the user's stored API key. Name a project space to upload straight there; otherwise it confirms the target with the user first.
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

## 2. Resolve the argument to exactly one app

The app reference may be an app id or a name search phrase.

- Looks like an app id (a UUID, or a compact ~20-char alphanumeric token) → call Nova's `get_app` tool with `{app_id: "<app>"}`.
- Otherwise → call Nova's `search_apps` tool with `{query: "<app>"}`.
  - Zero matches → tell the user no app matched and stop.
  - Multiple matches → show them as a numbered list with
    `<N>. **<App Name>** (<app_id>) — <N> modules, <M> forms, updated <date>`
    and ask which one. Wait for their answer before continuing.
  - Exactly one → use it.

Throughout, refer to the app as **"App Name" (app_id)** so the user sees both
the friendly name and the stable id.

## 3. Pick the path

- **An explicit target was supplied →** go straight to step 4 and upload to it.
  Naming a space IS the user's confirmation — do NOT ask again, and do NOT call
  `get_hq_connection`. (If the space turns out to be unreachable, step 5's
  `domain_not_authorized` handling recovers it in one turn.)

- **No explicit target →** check the connection and confirm:
  - Call Nova's `get_hq_connection` (no arguments). `configured: false` → tell
    the user "CommCare HQ isn't connected yet. Add your HQ API key in Settings
    (picking the CommCare server your account lives on — US, India, or EU)
    before uploading." and stop.
  - A configured connection also carries `server_url` — which CommCare HQ
    deployment the user's key belongs to (US, India, and EU are separate
    servers). The upload lands there; use its host in the confirmation below.
  - One entry in `available_domains` → that's the target.
  - Multiple entries → the user chooses; never pick for them. Show the spaces as
    a numbered list — `<N>. **<displayName>** (<name>)` — and ask which one. Wait
    for their answer. (There is no stored default — a multi-space key's target is
    a per-upload choice.)
  - Then **confirm** before uploading (substitute real values; `<space>` is the
    chosen `name`, `<host>` is `server_url` without the scheme, e.g.
    `eu.commcarehq.org`):

    > **"App Name"** (app_id) is already saved in Nova and you can keep editing
    > it here anytime — this **also** uploads it as a **new** app to CommCare HQ
    > at `<host>/a/<space>/`, using your API key. Your Nova copy stays put.
    >
    > Proceed?

    Wait for their confirmation. If they decline, stop.

## 4. Upload

Call Nova's `upload_app_to_hq` tool with
`{app_id: "<resolved app_id>", domain: "<target space slug>"}`. Always pass
`domain` explicitly — it's the explicit target, or the space resolved and
confirmed in step 3.

## 5. Report

On success the response has `{hq_app_id, url, warnings}`. Report the same way on
both paths:

> Uploaded **"App Name"** → `<url>`
>
> (If `warnings` is non-empty, list them below as a short bullet list.)

On a failed upload, surface `error_type` and `message` from the response:

- `domain_not_authorized` — the space you passed isn't one the key can reach.
  The `message` already names every space it CAN reach, so relay that in one
  turn rather than making the user re-run the command — e.g. "`<space>` isn't
  connected to your key, but these are: `<list>`. Want me to upload to one of
  those?" — then upload to their pick.
- `domain_ambiguous` — only happens with no `domain`; resolve the target via
  step 3 and retry step 4.
- `hq_not_configured` — the user needs to connect CommCare HQ in Settings
  (pick the server their account lives on and add their API key).
- `hq_upload_failed` — an HQ-side rejection; show the `message` so the user
  knows what HQ rejected.
