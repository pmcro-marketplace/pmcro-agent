# Lifecycle contract

Canonical plugin: `pmcro`. Each event is a directly named skill. The public address is `/pmcro:<event>`.

| Event | Boundary |
|---|---|
| `agent-startup` | Establish the agent run identity and applicable governance before the first authorized operation. |
| `input` | Validate and correlate newly received input before it enters reasoning or dispatch. |
| `pre-model-call` | Check the authorized model-call boundary before a model invocation. |
| `post-model-call` | Correlate the observed model result and evidence after a model invocation. |
| `pre-tool-call` | Check the resolved tool identity and authorization before its invocation. |
| `post-tool-call` | Correlate an observed tool result, status, and evidence after invocation. |
| `handoff` | Correlate an authorized transfer from a sender to a resolved recipient. |
| `output` | Validate the result boundary and evidence before returning an authorized output. |
| `error` | Correlate an observed failure and preserve the original target disposition. |
| `agent-shutdown` | Close an observed agent run boundary and preserve its final disposition. |

Input: a UTF-8 JSON object with kind `LifecycleContext`, integer version 1, `run.id` (nonblank string), optional `run.parent_id` (null or nonblank string), `target.agent`, `target.plugin`, `target.skill`, `target.function` (nonblank strings), `event.name` (exact selected event), `governance.posture` (observe or enforce), and `evidence.correlation_id` (nonblank string). Additional context may be present; never echo raw input or secrets in results.

Authorization is a trusted host decision, not a field in the request. Validate using the event skill's script. Its successful exit indicates valid routing only; it always returns `NOT_INVOKED` and `invoked: false` because it has no runtime adapter. A real registered provider must execute the event and return evidence before any execution claim. Fail closed on malformed context. Preserve the target business invocation and its result separately.
