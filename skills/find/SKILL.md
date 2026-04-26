---
name: find
description: Search your Nova apps by name (fuzzy, case-insensitive, typo-tolerant).
argument-hint: <search phrase>
---

Call `mcp__plugin_nova_nova__search_apps({query: "$ARGUMENTS"})`. Render
the response as a markdown table with columns: Name, Status, Last Updated, ID.

If `next_cursor` is present in the response, append a single line after
the table: "Ask for more to continue."
