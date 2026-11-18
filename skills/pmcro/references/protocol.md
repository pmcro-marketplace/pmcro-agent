# PMCR-O Protocol

PMCR-O cognitive roles: `interpret`, `orchestrate`, `plan`, `make`, `check`, `reflect`.

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
