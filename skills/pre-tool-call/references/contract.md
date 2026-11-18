# pre-tool-call contract

Capability: `/pmcro:pre-tool-call`.

Check the resolved tool identity and authorization before its invocation.

Require the exact event name `pre-tool-call` in LifecycleContext version 1. See the [shared lifecycle contract](../../pmcro/references/lifecycle.md) for typed fields and evidence rules. Resolve only this boundary, never a different event.
