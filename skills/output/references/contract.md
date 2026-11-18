# output contract

Capability: `/pmcro:output`.

Validate the result boundary and evidence before returning an authorized output.

Require the exact event name `output` in LifecycleContext version 1. See the [shared lifecycle contract](../../pmcro/references/lifecycle.md) for typed fields and evidence rules. Resolve only this boundary, never a different event.
