# agent-shutdown contract

Capability: `/pmcro:agent-shutdown`.

Close an observed agent run boundary and preserve its final disposition.

Require the exact event name `agent-shutdown` in LifecycleContext version 1. See the [shared lifecycle contract](../../pmcro/references/lifecycle.md) for typed fields and evidence rules. Resolve only this boundary, never a different event.
