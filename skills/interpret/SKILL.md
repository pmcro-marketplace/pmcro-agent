---
name: interpret
description: Interpret messy seed intent or BehavioralIntent events before orchestration.
---
# interpret

## Purpose
Preserve the user's raw seed while producing a bounded refined intent for Orchestrator Agent.

## When to Use
Use when this PMCR-O role is the narrowest resolved capability for the current bounded cycle.

## When Not to Use
Do not perform another role's work, broaden scope silently, duplicate an existing validated capability, or claim execution without evidence.

## Inputs
A bounded request, resolved target identity, authorization context, current cycle state, and applicable evidence.

## Deliverables
One concrete role result or a BLOCKED/NOT_INVOKED disposition with evidence.

## Workflow
1. Preserve the raw seed exactly.
2. Repair obvious speech-to-text artifacts without changing intent.
3. Identify goal, constraints, and ambiguity flags.
4. Produce a bounded refined intent.
5. Hand the refined intent to Orchestrator Agent.

## Validation
A PASS requires actual evidence. An emitted invocation, route, plan, or declared path is not proof of execution.

## Pitfalls
Emission is not invocation. Applicable lifecycle events resolve through PMCR-O direct skills and do not replace the interpretation function.

## Resources
See `references/contract.md` and `assets/request.json`.
