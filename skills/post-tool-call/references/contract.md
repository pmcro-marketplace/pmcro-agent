# post-tool-call contract

Capability: `/pmcro:post-tool-call`.

Correlate an observed tool result, status, and evidence after invocation.

Require the exact event name `post-tool-call` in LifecycleContext version 1. See the [shared lifecycle contract](../../pmcro/references/lifecycle.md) for typed fields and evidence rules. Resolve only this boundary, never a different event.
