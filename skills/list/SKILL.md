---
name: list
description: Show your 10 most recently updated Nova apps.
---

Call `mcp__plugin_nova_nova__list_apps` with no arguments. Render the
response as a markdown table with columns: Name, Status, Last Updated, ID.

If `next_cursor` is present in the response, append a single line after
the table: "Ask for more to continue."
