# PMCR-O Protocol

PMCR-O cognitive roles: `interpret`, `orchestrate`, `plan`, `make`, `check`, `reflect`.

## Activation readiness

`/pmcro:activation` is a distinct direct capability for validating and resolving one requested agent/plugin/skill/function target. Use an [ActivationRequest v1](../../activation/references/contract.md). Resolve provider readiness and authorization independently using observed host evidence. The offline resolver must return `NOT_INVOKED`, `activated: false`, and readiness `UNVERIFIED`; validation is not proof of activation. A capability gap routes to the Skill Agent, then to an authorized Plugin Agent/Creator only if discovery establishes the gap. It does not create or install automatically.

Actual bounded delegation continues through the independently resolved `/pmcro:subagent`. Activation must not duplicate that capability or execute the requested target. Lifecycle event routes remain unchanged.

## Lifecycle events

PMCR-O lifecycle skills use flat addresses:

- `/pmcro:agent-startup`
- `/pmcro:input`
- `/pmcro:pre-model-call`
- `/pmcro:post-model-call`
- `/pmcro:pre-tool-call`
- `/pmcro:post-tool-call`
- `/pmcro:handoff`
- `/pmcro:output`
- `/pmcro:error`
- `/pmcro:agent-shutdown`

See [lifecycle.md](lifecycle.md) for required context, routing, and provider evidence. The logical addresses require actual registered providers for execution.
