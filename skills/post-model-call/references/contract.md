# post-model-call contract

Capability: `/pmcro:post-model-call`.

Correlate the observed model result and evidence after a model invocation.

Require the exact event name `post-model-call` in LifecycleContext version 1. See the [shared lifecycle contract](../../pmcro/references/lifecycle.md) for typed fields and evidence rules. Resolve only this boundary, never a different event.
