# Activation request contract (v1)

Direct logical address: `/pmcro:activation`. Agent: `pmcro-agent`; plugin: `pmcro`; skill: `activation`; function: `activation`.

## Input

UTF-8 JSON object. Every listed key is required and unknown keys, including nested unknown keys or authorization/activation assertions, are forbidden. Duplicate JSON keys are invalid. Identifiers below are 1–128 ASCII letters/digits/dot/underscore/hyphen, starting and ending alphanumeric; they are opaque names, not URLs, paths, commands, or proof of identity.

| Field | Type and rule |
|---|---|
| `kind` | exact string `ActivationRequest` |
| `version` | exact integer `1`; booleans are not integers here |
| `capability` | exact string `/pmcro:activation` |
| `request_id` | identifier |
| `correlation_id` | identifier, carried privately by the host |
| `host` | identifier for requested host |
| `runtime` | identifier for requested runtime |
| `target` | exact object with four identifier strings: `agent`, `plugin`, `skill`, `function` |
| `scope` | exact object with `purpose` equal to `capability-readiness` and `max_targets` equal to integer `1` |
| `evidence_refs` | array of 0–16 unique opaque identifiers; placeholders alone do not establish evidence, authorization, or readiness |

Do not embed evidence contents, credentials, raw seed text, private trail paths, user data, or commands in the request example or repository. Private evidence is correlated in the trusted runtime, independently of the submitted references.

## Resolver output

A valid request returns exit code 0 and the constant non-executing disposition: `kind: ActivationResolution`, `capability: /pmcro:activation`, `status: NOT_INVOKED`, `activated: false`, `readiness: UNVERIFIED`. It does not echo raw request values, IDs, target values, or reference strings. Correlation stays with the trusted caller. Invalid input returns exit code 1, `BLOCKED`, `activated: false`, `readiness: UNVERIFIED`, and a static field-specific reason without including untrusted values. Command-line misuse is exit code 2.

The resolver never invokes providers, activates a capability, executes the target, follows evidence references, or writes files. Host readiness requires separately observed registration and provider evidence; authorization must be checked against trusted host policy, not supplied flags. A live activation provider, if available and authorized, returns its own real receipt. A missing or unready target routes to Skill Agent for discovery and then Plugin Agent/Plugin Creator only when the gap and authority are confirmed. Do not simulate or automatically install a missing capability.

The ten direct lifecycle event skills are unchanged. `/pmcro:subagent` owns separately authorized actual delegation; activation only resolves readiness.
