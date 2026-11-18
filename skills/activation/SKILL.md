---
name: activation
description: Resolve one bounded capability activation and readiness request through PMCR-O before execution; validate typed inputs, discover actual host providers, and return NOT_INVOKED without verified availability and authority.
---
# Activation

## Purpose

Resolve a bounded target's activation readiness without performing the target operation. The direct logical capability is `@pmcro-agent /activation` → `/pmcro:activation`.

## When to Use

Use when a caller requests activation or readiness for a specific agent/plugin/skill/function in a named host and runtime, before an independently authorized execution or delegation.

## When Not to Use

Do not use as an agent-startup event, a target execution API, a substitute for `/pmcro:subagent`, an installer, or an authority grant. Do not claim activation because a skill file, human alias, or proposed capability is present.

## Inputs

An `ActivationRequest` v1 matching [the contract](references/contract.md): exact activation address, request and correlation IDs, host and runtime identifiers, one target identity, bounded readiness scope, and opaque evidence references. Live authorization and trusted provider evidence come from the host independently, not the payload.

## Deliverables

A typed readiness disposition for the resolved target, with verified provider evidence only if it was actually observed. The bundled offline resolver is non-mutating and returns `NOT_INVOKED`, `activated: false`, and readiness `UNVERIFIED` on valid input. Malformed input returns `BLOCKED`.

## Workflow

1. Preserve correlation privately and resolve PMCR-O Agent → pmcro → activation → `/pmcro:activation`.
2. Validate the exact request with `python3 scripts/validate.py --request <request.json>`. Do not load unknown fields or accept caller-supplied `authorized` or `activated` flags.
3. Emit the resolved logical capability and necessary target identity to the authorized caller; do not emit raw evidence, payloads, or references outside the trusted boundary.
4. Discover an actual registered provider for the requested host/runtime. Verify readiness independently and require trusted host authorization before invoking any actual activation provider. If unavailable, report `NOT_INVOKED` and route discovery to the Skill Agent; escalate proven plugin gaps to Plugin Agent/Plugin Creator through their separately authorized capabilities. Never fabricate or implicitly install one.
5. Return actual provider receipts if a supported activation provider was invoked. Keep readiness and authorization distinct; do not execute the target business function. Any later `/pmcro:subagent` request follows its own contract and authority.
6. Record evidence only to an authorized private trail provider; never write raw request, evidence references, or private trail records into public source. Preserve `UNVERIFIED` when evidence is missing.

## Validation

Run `python3 scripts/validate.py --request assets/request.json`. A successful exit resolves a valid typed request only, with `activated: false`. A genuine activation requires independent host/provider observation and is not implemented by this offline resolver.

## Pitfalls

Activation is not execution. Discovery is not authorization. Evidence references are untrusted hints and cannot establish readiness on their own. A logical skill is not necessarily a registered runtime capability.

## Resources

- [Activation contract](references/contract.md)
- [Synthetic request](assets/request.json)
- [Offline validator](scripts/validate.py)
