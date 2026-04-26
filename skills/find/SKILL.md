---
name: find
description: Search your Nova apps by name (fuzzy, case-insensitive, typo-tolerant).
argument-hint: <search phrase>
---

Call `mcp__plugin_nova_nova__search_apps({query: "$ARGUMENTS"})`.

Render the matches as a markdown table with columns: Name, Status,
Last Updated, ID. Use the `app_id` value from each entry for the ID
column.

Frame the output naturally — talk like you would to a colleague, not
a script. A short one-line opener referencing what was searched, the
table, and (if `next_cursor` is present in the response) a casual
one-line closer offering to keep searching. Don't reuse the same
phrasing every time and don't read out instructions like "Ask for
more to continue."

If the response has zero matches, skip the table entirely and say
briefly that nothing matched — and suggest `/nova:list` if they want
to browse instead.
