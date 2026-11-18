# pre-model-call contract

Capability: `/pmcro:pre-model-call`.

Check the authorized model-call boundary before a model invocation.

Require the exact event name `pre-model-call` in LifecycleContext version 1. See the [shared lifecycle contract](../../pmcro/references/lifecycle.md) for typed fields and evidence rules. Resolve only this boundary, never a different event.
