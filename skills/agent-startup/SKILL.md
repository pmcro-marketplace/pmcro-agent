---
name: agent-startup
description: "Establish the agent run identity and applicable governance before the first authorized operation. Use for the direct PMCR-O agent-startup lifecycle event."
---
# agent-startup

## Purpose
Establish the agent run identity and applicable governance before the first authorized operation.

## When to Use
When the host or authorized caller emits the exact agent-startup boundary.

## When Not to Use
Do not synthesize an event, replace the target business function, or claim provider execution without evidence.

## Inputs
A typed LifecycleContext matching the selected event; actual authorization comes from the host. See [contract](references/contract.md).

## Deliverables
A resolved `/pmcro:agent-startup` capability and actual provider evidence, or explicit `BLOCKED` or `NOT_INVOKED`.

## Workflow
1. Resolve agent, plugin, skill, and function to `@pmcro-agent -> pmcro -> agent-startup -> /pmcro:agent-startup`.
2. Validate the context using `python3 scripts/dispatch.py --context <context.json>`.
3. Emit the resolved address, target identity, and correlation ID. Do not print sensitive payloads.
4. Invoke the actual authorized provider for this boundary if available; otherwise preserve `NOT_INVOKED`.
5. Verify provider evidence independently of the target result. Return the target unchanged.

## Validation
Invalid context is BLOCKED. Resolver exit 0 does not prove lifecycle execution.

## Pitfalls
A logical address is not a native registered command. Never simulate a provider or infer authorization.

## Resources
- [Event contract](references/contract.md)
- [Example context](assets/request.json)
- [Dispatcher](scripts/dispatch.py)
