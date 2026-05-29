# Nova for Claude Code

Build, edit, compile, and deploy CommCare apps from Claude Code.

## Install

    /plugin marketplace add voidcraft-labs/nova-marketplace
    /plugin install nova@nova-marketplace

## Authenticate

**Browser sign-in (default).** The first time you use a `/nova:*` skill, Claude Code
opens your browser to sign in at commcare.app. Tokens are stored in Claude Code's
credential store; revoke via `/mcp` → nova → Clear authentication.

**API key.** For unattended runs, or several agents sharing one account, set
`NOVA_API_KEY` in your environment to a key from
[commcare.app/settings](https://commcare.app/settings). The plugin picks it up
automatically — no browser, no extra setup. Unset it to fall back to browser sign-in.

Full details: [docs.commcare.app/mcp/api-keys](https://docs.commcare.app/mcp/api-keys).

## Skills

- `/nova:build <spec>` — interactive build; subagent asks clarifying questions
- `/nova:autobuild <spec>` — autonomous build; subagent commits to defaults
- `/nova:edit <app_id> "<instruction>"` — edit an existing app
- `/nova:list` — list your apps
- `/nova:show <app_id>` — blueprint summary
- `/nova:upload_to_hq <app_id or name> [project space]` — deploy to CommCare HQ (names a space to upload straight there, otherwise confirms the target first)
