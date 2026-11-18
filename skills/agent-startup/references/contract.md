# agent-startup contract

Capability: `/pmcro:agent-startup`.

Establish the agent run identity and applicable governance before the first authorized operation.

Require the exact event name `agent-startup` in LifecycleContext version 1. See the [shared lifecycle contract](../../pmcro/references/lifecycle.md) for typed fields and evidence rules. Resolve only this boundary, never a different event.
