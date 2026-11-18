# PMCR-O Agent

Canonical plugin: `pmcro`.
Human handle: `@pmcro-agent`.

## Lifecycle skills

PMCR-O owns the following direct capability addresses:

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

These are logical skills, not a claim of native slash-command registration. A live lifecycle adapter must provide invocation evidence. Existing external consumers should migrate to these addresses; no standalone repository is removed by this change.
