# Nova for Claude Code

Build, edit, compile, and deploy CommCare apps from Claude Code.

## Install

    /plugin marketplace add voidcraft-labs/nova-marketplace
    /plugin install nova@nova-marketplace

## Authenticate

**Browser sign-in (default).** Run `/mcp`, select Nova, and follow the browser
sign-in at commcare.app. Tokens are stored in Claude Code's credential store;
revoke via `/mcp` → nova → Clear authentication.

**API key.** For unattended runs, set `NOVA_API_KEY` in your environment to a
key from [commcare.app/settings](https://commcare.app/settings), then add a
personal server configuration once:

```bash
claude mcp add-json --scope user nova '{"type":"http","url":"https://mcp.commcare.app/mcp","headers":{"Authorization":"Bearer ${NOVA_API_KEY}"}}'
```

The single quotes keep the key out of the saved configuration. Claude Code
reads it from the environment at startup. Keep it set for each unattended run.
Claude Code uses this personal connection in place of the plugin's connection
to the same endpoint; the plugin's skills and autonomous agent support both.
To return to browser sign-in, run `claude mcp remove --scope user nova` and
restart Claude Code. Unsetting the key alone leaves the API-key connection
configured and does not enable browser sign-in.

This uses Claude Code's [server precedence](https://code.claude.com/docs/en/mcp#scope-hierarchy-and-precedence)
and [environment expansion](https://code.claude.com/docs/en/mcp#environment-variable-expansion-in-mcpjson).
Plugin-provided header helpers cannot read credential environment variables.

**Working as a team?** Don't share one account. Create a shared Nova Project and
invite your teammates — everyone signs in as themselves, and every member sees
the Project's apps, case data, and media. Agents manage this over MCP too:
`list_projects`, `create_project`, `invite_member`, `list_members`,
`update_member_role`, and `move_app`.

Full details: [docs.commcare.app/mcp/api-keys](https://docs.commcare.app/mcp/api-keys)
and [docs.commcare.app/mcp/tools](https://docs.commcare.app/mcp/tools).

## Skills

- `/nova:build <spec>` — interactive build in the current conversation
- `/nova:autobuild <spec>` — autonomous build; subagent commits to defaults
- `/nova:edit <app_id> "<instruction>"` — edit an existing app
- `/nova:list` — list your apps
- `/nova:show <app_id>` — app overview
- `/nova:upload_to_hq <app_id or name> [project space]` — deploy to CommCare HQ (names a space to upload straight there, otherwise confirms the target first; checks whether that project space can run the app before sending anything)

## Authoring guidance

Build and edit skills fetch current guidance from Nova. The prompt stays small
because app state and feature references are read separately. Agents write
wording and expressions as text; Nova resolves references and preserves stable
identities when content is renamed.

`get_app` provides an overview. Agents can inspect individual modules, forms,
fields, languages, organization settings and automations as needed. The
[tool reference](https://docs.commcare.app/mcp/tools) describes current
capabilities and input conventions.

Agents build and edit in durable private work. `begin_work` opens it;
`list_work` and `get_work` find and inspect retained work. Focused operations
create modules, forms and questions separately. `save_work` publishes a complete,
valid checkpoint; a refused save leaves private work available for correction.
`discard_work` abandons pending changes while keeping the work ID and earlier
saved checkpoints. A concurrent saved change requires an explicit restart from
current state, never an automatic merge.

A work ID remains stable across checkpoints. Each write has its own request ID,
reused only for an exact retry. Save and discard bind the opaque revision of the
candidate being acted on. Shared reads select the candidate with `work_id` or
the saved app with `app_id`; `get_app` always reads saved state.

The isolated app-test tools exercise saved checkpoints, with steps available in
Builder. A test can retain up to four named worker sessions sharing disposable
records while keeping separate open forms, identities and languages. Page
navigation and task routes have distinct actions. Starting and continuing a journey accepts either saved app or work
identity and requires a request ID; reading retained observations does not. Tests never write their fictional records or place assignments into
the user's live data. They do not establish native-device, offline-sync or
external-service behavior. A submission receipt records case effects and replay
identity; it does not archive a standalone report's answers. Preview uses real
Project case data.

Version 2.1's retained-session and page-action guidance requires the paired Nova
server release. Publish this plugin after that server is live and verified.

A saved app is distinct from a tested workflow or a deployment to CommCare HQ.
Publishing checks the selected target with `check_project_space_compatibility`;
automations return setup guidance for the remaining work in HQ. Project data,
real organization records, media service writes and deployment are separate
immediate effects. Discarding app work cannot undo them; these actions follow
the scope authorized by the user's request.

## Updating to version 2

Version 2 requires the workspace-first Nova server from
[CommCare Nova PR #693](https://github.com/voidcraft-labs/commcare-nova/pull/693).
Release this plugin only after that server is deployed and verified. Earlier
plugin versions must be updated for the new authoring contract; there is no
legacy immediate-save or nested-creation mode.

Update the plugin, then restart Claude Code:

    /plugin update nova

Use current Claude Code with MCP server-pattern support for subagent tools.
The autonomous agent discovers Nova's live tool surface through the two
supported server namespaces. Its permissions contain no copied tool inventory.

## Development checks

    python3 scripts/validate-plugin.py

This checks plugin packaging, entrypoint links, Nova-only autonomous tool access
and the production MCP endpoint. It does not duplicate Nova's tool schemas or
require an artificial version increment. Runtime authoring and schema behavior
are verified in Nova. Test a paired change against the local Nova server using
Nova's dev launcher with `--nova-plugin` pointing to this plugin worktree; the
generated `.dev-plugin` overlay is not authored source.
