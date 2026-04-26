# Nova for Claude Code

Build, edit, compile, and deploy CommCare apps from Claude Code.

## Install

    /plugin marketplace add voidcraft-labs/nova-marketplace
    /plugin install nova@nova-marketplace

## Authenticate

First use of any `/nova:*` skill opens your browser to sign in at commcare.app.
Tokens are stored in Claude Code's credential store; revoke via `/mcp` → nova → Clear authentication.

## Skills

- `/nova:build <spec>` — interactive build; subagent asks clarifying questions
- `/nova:autobuild <spec>` — autonomous build; subagent commits to defaults
- `/nova:edit <app_id> "<instruction>"` — edit an existing app
- `/nova:list` — list your apps
- `/nova:show <app_id>` — blueprint summary
- `/nova:upload <app_id> <domain> [app_name]` — deploy to CommCare HQ
