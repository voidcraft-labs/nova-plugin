---
name: list
description: Show your 10 most recently updated Nova apps.
---

Call `mcp__plugin_nova_nova__list_apps` with no arguments.

Render the apps as a markdown table with columns: Name, Status, Last
Updated, ID. Use the `app_id` value from each entry for the ID column.

Frame the output naturally — talk like you would to a colleague, not
a script. A short one-line opener before the table, the table itself,
and (if `next_cursor` is present in the response) a casual one-line
closer offering to fetch more. Don't reuse the same phrasing every
time and don't read out instructions like "Ask for more to continue."

If the response has zero apps, skip the table entirely and say
something brief — e.g. that the user doesn't have any Nova apps yet
and could try `/nova:build` to make one.
