---
name: orchestrate
description: Own one established high-level goal across bounded PMCR-O cycles and route the next bounded intent.
---
# orchestrate

## Purpose
Maintain the high-level goal, select one current bounded intent, and route the PMCR-O cycle while preserving role boundaries.

## When to Use
Use when this PMCR-O role is the narrowest resolved capability for the current bounded cycle.

## When Not to Use
Do not perform another role's work, broaden scope silently, duplicate an existing validated capability, or claim execution without evidence.

## Inputs
A bounded request, resolved target identity, authorization context, current cycle state, and applicable evidence.

## Deliverables
One concrete role result or a BLOCKED/NOT_INVOKED disposition with evidence.

## Workflow
1. Preserve the established high-level goal.
2. Select the smallest useful current intent.
3. Resolve the next PMCR-O role capability.
4. Delegate planning/making/checking/reflection rather than performing those roles.
5. Decide continue, clarify, or stop from evidence.

## Validation
A PASS requires actual evidence. An emitted invocation, route, plan, or declared path is not proof of execution.

## Pitfalls
Emission is not invocation. The installed Hook Agent may surround this role but does not replace its business function.

## Resources
See `references/contract.md` and `assets/request.json`.


## Script reference

Scripts are not loaded into context. An agent runs one only when a step needs it, and you can run the same command by hand from this skill's folder.

| Script | Purpose | Manual run |
|---|---|---|
| `scripts/validate.py` | Structural self-check: verifies the skill's required files (and request.json contents where applicable). Takes no arguments; prints `PASS: <skill>` and exits 0, or prints `FAIL: ...` and exits 1. | `python scripts/validate.py` |
