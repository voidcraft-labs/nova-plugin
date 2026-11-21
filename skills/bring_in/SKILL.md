---
name: bring_in
description: Bring an app that already exists in CommCare HQ in to Nova, using the user's stored API key, so they can keep working on it in Nova and publish back to the same HQ app. Nova reads the app first and creates nothing until the user has seen what will come in. If Nova can't hold every part of the app yet, it says exactly what and where, and creates nothing. Name a project space and an app to go straight to them; otherwise it asks.
argument-hint: [project space] [app name]
---

# Task

The user wants to bring an app they already have in CommCare HQ in to Nova.
The input is `$ARGUMENTS`.

## 1. Parse the arguments

`$ARGUMENTS` is optional. When present, it is a project space, optionally
followed by an app name:

- **Project space (optional)**: a CommCare domain slug (lowercase, hyphenated,
  no spaces), given as the FIRST token.
- **App name (optional)**: everything after the project space, which may
  contain spaces. If the user quoted it, the quoted part is the name.

A CommCare HQ **project space** is not a Nova **Project** (the shared
workspace `list_projects` reports). The project space here is always an HQ
domain slug; never pass a Nova Project name or id as the space.

## 2. Check the connection

Call Nova's `get_hq_connection` (no arguments). `configured: false`: tell the
user CommCare HQ isn't connected yet, that they can add their HQ API key at
commcare.app/settings (picking the CommCare server their account lives on: US,
India, or EU), and stop.

A configured connection carries `server_url` and `available_domains`:

- **A project space was named** → match it to an `available_domains.name`. If
  it is not one of them, list the reachable spaces and ask which one they
  meant.
- **None named and one reachable space** → use it, and say which it is.
- **None named and several reachable spaces** → show a numbered list as
  `<N>. **<displayName>** (<name>)`, ask which one, and wait.

Never choose a project space for the user. Every later call takes the space's
`name`, never its display name. Call the chosen name the **space**.

## 3. Choose the app

Call Nova's `list_hq_apps` with `{domain: "<space>"}`. It reads CommCare HQ
with the user's own key and changes nothing. Show the apps' `name`s as a list.

- `in_nova` null: the app is free to bring in.
- `in_nova.kind: "open"`: the app is already in Nova as `app_name`
  (`app_id`). Say so and offer `/nova:show <app_id>`.
- `in_nova.kind: "elsewhere"`: a Nova app the user can't open manages it.
  Relay `next` as written and stop there for that app. Do not try another way
  in. One CommCare HQ app is managed by one Nova app.

If an app name was given and it names exactly one free app, use it. Otherwise
ask which app, and wait. Keep its `hq_app_id`.

## 4. Settle the Nova Project

Call Nova's `list_projects`. The user can edit a Project where their `role` is
`editor`, `admin` or `owner`. Say which Project the app will be added to and
why it matters: an app that reads lookup tables stays in the Project it is
added to. Where the user can edit several, ask which one and never pick for
them. Where they can edit exactly one, say its name and go on: there is
nothing to choose, and the user can still stop you. Where they can edit none,
say so and stop.

## 5. Read

Call Nova's `read_hq_app` with
`{project_id: "<project>", domain: "<space>", hq_app_id: "<hq_app_id>"}`,
once. Tell the user Nova is reading the app and that nothing is being created
or changed. An app with many pictures and sounds can take a few minutes. If
the call ends before an answer comes, the user can read the app in Nova in a
browser.

Keep the `project_id`, `domain` and `hq_app_id` you sent: creating needs the
same three. The answer's `state` is `stop`, `account` or `review`.

## 6. If it stopped

`state: "stop"`: something ended the read before Nova had an app to show, such
as a permission, a plan without API access, or an app already in Nova. Relay
`stop.title`, `stop.body` and `stop.next` as written. Offer to read again
where `next` invites it.

## 7. If Nova can't bring it in yet

`state: "account"`: Nova found parts of the app it can't hold yet. Say plainly
that nothing was created and nothing changed in CommCare HQ.

Give `account.counts`, then the findings grouped by `place`, each with its
`sentence`, its `named` where present, and the label of its `standing` from
`account.labels`. Give each entry of `account.labels` with its `next` once. A
finding with an `hq_url` can be opened there. Where `more` is not null, relay
it.

While `account.next_page` is not null, call `read_hq_app` again with the same
three fields and `page` set to it, or offer the rest where the list is long.
If an answer has `restarted` true, the app changed while you were paging:
relay `message` and start the list over from this answer.

Relay `note` where present, and after the list relay `check_again` as written.
Never tell the user the list is complete: a later check may find more. Never
soften the list, never call it an error, and never offer to bring in part of
the app: Nova brings in an app only when it can hold all of it.

Nova keeps no list. `/nova:bring_in` again reads the app afresh.

## 8. If it is ready

`state: "review"`: keep `reading_id` and `review.review_digest`. Show the
review in this order:

1. **The name**: `review.app_name`, CommCare HQ's name for the app. It is empty
   where CommCare HQ holds none.
2. **What will be created**: `creates` (menus, forms, questions, case types,
   languages, pictures and sounds).
3. **Where it runs**: every entry of `runs_on` with its `label`, `line` and
   `split_line`, and its `recorded_features` where there are any, saying which
   one Nova proposes (`preselected`). `recorded_features` are plan features
   the app already uses on that project space under that choice: Nova records
   them, so publishing asks nothing about them, and the user can withdraw any
   of them later. Then each of `runs_on_notes`, and each
   entry of `cannot_run`: its `sentence`, its `features` as a list, and its
   `files`.
4. **Lookup tables**: each entry of `tables`, with its `sentence`, or its
   `choice`: the `title`, the `body`, and each entry of `answers` with its
   `label`, `lines` and, where its `offered` is false, its `reason`. An answer holds only as many tables
   as fit, and `review.tables_total` says how many there are in all. While
   `review.next_page` is not null, call `read_hq_app` again with the same
   three fields and `page` set to it, and show that page's tables too. Every
   other part of the review is the same on every page. If an answer has
   `restarted` true, the app changed while you were paging: relay `message`
   and show the review again from this answer.
5. **Places and media**: `places.sentence`, `media.sentence` and
   `media.left_out`, each where present.
6. **What stays in CommCare HQ**: `kept.lead`, its `labels`, and `kept.note`.
7. `after`, each sentence as written.
8. **What the first publish changes**: the proposed entry's `first_publish`.
   Relay its `lead`, then `workers.lines` first, then `hq_only.lines`, each
   `sentence` as written, then `reassurance` where it is not null, then
   `note`.

If the user picks another way for the app to run, show that entry's
`first_publish` before you create: the list belongs to the choice.

## 9. Ask, and wait

> Never answer one of these for the user, and never send `bring_in_hq_app`
> until they have answered every one: the Project where they can edit more
> than one, the name, where the app runs, whether date and time questions are
> split, and each lookup table's answer. A table's answer can change what
> other apps of the Project read. If the user says "use the defaults", say
> what the defaults are first and get a yes.

Ask for:

- **The name**: keep CommCare HQ's or use another. Where `review.app_name` is
  empty, ask the user for a name.
- **Where it runs**: one entry of `runs_on`. Its `runs_only_on` and
  `split_datetime` go to the create together.
- **Each table choice**: for each entry of `tables` that has a `choice`, on
  every page of the review, one of its `answers` whose `offered` is true.
  Keep the `answer` of the one the user picks (`use-commcare-hq` or
  `use-project`) by the table's `tag`.

## 10. Create

Call Nova's `bring_in_hq_app` once, with the nine fields:
`{project_id, domain, hq_app_id}` as sent to `read_hq_app`, `reading_id`,
`review_digest` (`review.review_digest`), `app_name`, `runs_only_on` and
`split_datetime` from the chosen `runs_on` entry, and `table_choices`, which
maps each table's `tag` to the `answer` the user picked, never its `label`
(`{}` where no table has a choice). Creating changes nothing in CommCare HQ. If the
call ends before you get an answer, send it again with the same arguments: it
answers the app if it was created, and creates it if it was not.

By `status`:

- `created`: go on to step 11.
- `changed`: something changed in CommCare HQ or the Project since the review,
  and no app was created. Say what `message` says, show `reading` again from
  step 6, 7 or 8, and ask again; never resend old answers against a new
  review. A long `reading` is its first page: read the rest with
  `read_hq_app` and its `next_page`, as in step 7 or 8.
- `read_again`: a lookup table the app reads changed in the Project while Nova
  was creating the app, and no app was created. Relay `message`, call
  `read_hq_app` again, and go on from step 6, 7 or 8 with what it answers. Ask
  again for any choice the new review changed.
- `check_failed`: one of Nova's own checks stopped the create, and no app was
  created. Relay `message` and the finding in `reading`. Do not send it again
  by yourself: nothing the user can change clears it.
- `held`: no app was created. Relay `message` and `stop` (its `title`, `body`
  and `next`), and send the same arguments again only after the user has done
  what `stop.next` says, or, where it says to check again in a while (Nova is
  busy reading other apps), after that wait.

## 11. Report

On `created`: give the app's name (`app_name`) and its `url`. Relay `message`:
the app is in Nova and nothing changed in CommCare HQ, and publishing from
Nova updates the same HQ app. Give the review's `after` sentences once more.
Offer `/nova:show <app_id>` and `/nova:edit <app_id>`.

Do not upload it now unless the user asks. Before its first upload, the
upload relays what that upload changes in CommCare HQ
(`/nova:upload_to_hq`).

## 12. Errors

A refusal comes back with `error_type` and `message`:

- `scope_missing`: the user's connection to Nova lacks the CommCare HQ access
  this needs. Relay `message`, which names the access to grant, and stop.
  Checking the connection needs HQ Read. Listing, reading and bringing in
  apps needs HQ Import (`nova.hq.import`). The user can approve the named
  permission when prompted or sign in again through `/mcp`. For an API key,
  they can select it under the key's scopes in Nova's Settings.
- `hq_not_configured`: the user has not connected CommCare HQ. Point at
  commcare.app/settings and stop, as in step 2.
- `domain_not_authorized`: the key can't reach that project space, or
  CommCare HQ turned the account away there. Relay `message`, `title` and
  `next`. Where the message names project spaces the key reaches, ask whether
  to use one of those.
- `hq_read_stopped`: CommCare HQ ended the read before Nova had anything to
  show. Relay `title`, `message` and `next` as written, and try again only
  where `next` invites it.
- `permission_denied`: the user can't add an app to that Project, or no
  longer can. Relay `message`, and ask which other Project to use where they
  can edit one.
- `invalid_input`: an answer was not one the review offered, a table still
  needs its answer, or the name was missing. Relay `message`, read the review
  again with `read_hq_app`, and ask the user again. Never pick a replacement
  answer. Two `invalid_input` answers are not about the review: where
  `message` says the `domain` isn't the name of a project space, relay it and
  ask which of the spaces it lists to use, then send that space's `name`,
  never the same `domain` again; where it says a page isn't one Nova gave,
  call `read_hq_app` again without `page` and show the account from its
  start.
- `bring_in_refused`: Nova can't create the app as things stand. Relay
  `message` and stop. Do not send `bring_in_hq_app` again until the user asks.
  Where its `refusal` is `publish_in_flight`, a publish to that HQ app is
  still finishing: no app was created and the review stands, so offer to send
  the same call again in a few minutes.
