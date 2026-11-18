# Invocation Contract

Human: `@pmcro-agent /<function> [arguments]`.

Direct lifecycle capability: `/pmcro:<event>` maps to plugin `pmcro`, skill `<event>`. No intermediate public namespace.

Core flow:
`RESOLVE -> EMIT APPLICABLE LIFECYCLE -> INVOKE REAL PROVIDER WHEN AVAILABLE -> INVOKE TARGET -> VERIFY -> EVIDENCE`.

Lifecycle routes:
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

The skill resolves and validates its boundary; a registered host/runtime provider must execute it. Return `NOT_INVOKED` when unavailable. Never let the lifecycle capability replace the original business function or grant authority.

**Emission is not invocation.**
