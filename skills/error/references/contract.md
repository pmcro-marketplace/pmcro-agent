# error contract

Capability: `/pmcro:error`.

Correlate an observed failure and preserve the original target disposition.

Require the exact event name `error` in LifecycleContext version 1. See the [shared lifecycle contract](../../pmcro/references/lifecycle.md) for typed fields and evidence rules. Resolve only this boundary, never a different event.
