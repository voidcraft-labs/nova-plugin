# Nova for Claude Code

Build, edit, compile, and deploy CommCare apps from Claude Code.

## Install

    /plugin marketplace add voidcraft-labs/nova-marketplace
    /plugin install nova@nova-marketplace

## Authenticate

**Browser sign-in (default).** The first time you use a `/nova:*` skill, Claude Code
opens your browser to sign in at commcare.app. Tokens are stored in Claude Code's
credential store; revoke via `/mcp` → nova → Clear authentication.

**API key.** For unattended runs, set `NOVA_API_KEY` in your environment to a
key from [commcare.app/settings](https://commcare.app/settings). The plugin
picks it up automatically — no browser, no extra setup. Unset it to fall back
to browser sign-in.

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

Version 1.34 requires Nova's isolated app-test tools: `start_app_test`,
`continue_app_test` and `read_app_test`. Release this plugin only after the
compatible Nova server is live. Agents can observe entry, saved Preview identities,
selection, answers, isolated submission effects and the next task, with recorded
steps available in Builder. Tests pin the saved app revision and never write their
fictional records or place assignments into the user's live data. They do not
establish native-device, offline-sync or external-service behavior.

Preview uses real Project case data. A saved app is distinct from a tested
workflow or a deployment to CommCare HQ. Publishing checks the selected target;
automations return setup guidance for the remaining work in HQ. Shared Project
data changes and publishing follow the scope authorized by the user's request.
