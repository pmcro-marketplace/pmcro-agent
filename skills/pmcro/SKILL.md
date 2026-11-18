---
name: pmcro
description: Own the PMCR-O protocol contract and coordinate bounded role-agent execution without duplicating role capabilities.
---
# pmcro

## Purpose
Define the PMCR-O protocol and coordinate external role agents while preserving their ownership boundaries.

## When to Use
Use when this PMCR-O role is the narrowest resolved capability for the current bounded cycle.

## When Not to Use
Do not perform another role's work, broaden scope silently, duplicate an existing validated capability, or claim execution without evidence.

## Inputs
A bounded request, resolved target identity, authorization context, current cycle state, and applicable evidence.

## Deliverables
One concrete role result or a BLOCKED/NOT_INVOKED disposition with evidence.

## Workflow
1. Preserve the raw seed and current cycle state.
2. Resolve the appropriate installed role agent.
3. Route Orchestrate -> Plan -> Make -> Check -> Reflect through their actual capabilities.
4. Resolve applicable lifecycle events using the directly named PMCR-O skills in [the lifecycle contract](references/lifecycle.md). Attempt the actual provider only when registered and authorized.
5. Require evidence before advancing or declaring PASS.

## Validation
A PASS requires actual evidence. An emitted invocation, route, plan, or declared path is not proof of execution.

## Pitfalls
Emission is not invocation. Lifecycle routing may surround this role but never replaces its business function; unavailable providers return NOT_INVOKED.

## Resources
See `references/contract.md` and `assets/request.json`.
