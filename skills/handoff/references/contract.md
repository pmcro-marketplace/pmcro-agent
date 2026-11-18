# handoff contract

Capability: `/pmcro:handoff`.

Correlate an authorized transfer from a sender to a resolved recipient.

Require the exact event name `handoff` in LifecycleContext version 1. See the [shared lifecycle contract](../../pmcro/references/lifecycle.md) for typed fields and evidence rules. Resolve only this boundary, never a different event.
