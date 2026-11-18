# input contract

Capability: `/pmcro:input`.

Validate and correlate newly received input before it enters reasoning or dispatch.

Require the exact event name `input` in LifecycleContext version 1. See the [shared lifecycle contract](../../pmcro/references/lifecycle.md) for typed fields and evidence rules. Resolve only this boundary, never a different event.
