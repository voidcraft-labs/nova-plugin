---
name: show
description: Show an overview of a Nova app.
argument-hint: <app_id>
---

Call Nova's `get_app` tool with `app_id: "$ARGUMENTS"`. Present its name, Project,
workflows and languages in a readable overview. If `notices` is non-empty,
tell the user what each one says before anything else. Once they have read
them, offer to dismiss them; only on their yes, call `dismiss_app_notice` with
each notice's `id` as `notice_id`. Use scoped reads if the user asks for more
detail.
