---
name: autobuild
description: Build a CommCare app autonomously from the user's description.
argument-hint: <description of the app>
allowed-tools: Agent(nova:nova-architect-autonomous)
---

Start `nova:nova-architect-autonomous` with the Agent tool. Pass the user's
request, `$ARGUMENTS`, and relevant context or constraints from this conversation.
The architect owns its Nova startup and completes the build without questions.

Wait for its result, then report the app's name and ID, the resulting workflow,
and any remaining limitations or setup. Preserve its distinction between
saved changes, observed behavior and deployment.
