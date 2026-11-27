# PMCR-O Protocol

PMCR-O roles:
`interpret`, `orchestrate`, `plan`, `make`, `check`, `reflect`.

Hook Agent is separate:
plugin `hook`, skill/subagent `hook`.

Lifecycle functions resolve through Hook Agent:
`/agent-startup`, `/input`, `/pre-model-call`, `/post-model-call`,
`/pre-tool-call`, `/post-tool-call`, `/handoff`, `/output`, `/error`, `/agent-shutdown`.
