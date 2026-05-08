---
name: edit
description: Edit an existing CommCare app with a natural-language instruction. Asks clarifying questions when needed. Usage — quote the instruction: /nova:edit <app_id> "<instruction>"
argument-hint: <app_id> "<instruction>"
---

# Task

The user wants to edit Nova app `$0` with this instruction: $1.

## 1. Operating instructions

Call Nova's `get_agent_prompt` tool with `mode: "edit"` and `app_id: "$0"`. The server inlines the app's current blueprint summary into the returned text — treat the full text as your operating instructions for this edit.

Always fetch fresh in edit mode — the inlined summary reflects the current blueprint, which may have changed since any earlier fetch in this conversation.

The Nova mutation tools are deferred — their schemas only appear in your context after a ToolSearch call. Don't rely on training memory of these tool shapes; pre-load the edit-path set in one ToolSearch call before continuing:

```
ToolSearch({query: "+nova get_app search_blueprint add_fields add_field edit_field remove_field update_form update_module validate_app", max_results: 9})
```

The `+nova` filter matches whichever Nova namespace is live (`mcp__plugin_nova_nova__*` when using the plugin's OAuth, `mcp__nova__*` when an API-key override is in user-scope).

Load any additional tools (`create_form`, `remove_form`, `create_module`, `remove_module`, `get_module`, `get_form`, `get_field`) on demand if a follow-up step needs them.

## 2. Confirm the change (if unsure)

Most edit instructions are specific enough to act on directly. If the instruction is clear, proceed.

If real ambiguity remains — vague scope ("clean up the registration form"), an unclear target ("the height field" when several exist), or missing details that would shape the change — ask one or two questions via AskUserQuestion before planning. Only ask about the user's *intent*; the blueprint is inlined, so don't ask about what already exists.

## 3. Plan the work

Use TaskCreate to outline the changes needed for this edit. Always include "Validating" as the final task.

## 4. Apply the edits

Work through each task using the Nova tools per the fetched instructions. Mark each task `in_progress` when you start it and `completed` when it's done.

If a new ambiguity surfaces mid-edit, ask via AskUserQuestion before applying it.

## 5. Report

When the edits are done, return:

- **"App Name" (app_id)** on its own line
- The updated blueprint summary
