---
name: make
description: Produce the authorized artifact or state change using the narrowest real creator or provider capability.
---
# make

## Purpose
Execute only the approved Make scope and return actual evidence.

## When to Use
Use when this PMCR-O role is the narrowest resolved capability for the current bounded cycle.

## When Not to Use
Do not perform another role's work, broaden scope silently, duplicate an existing validated capability, or claim execution without evidence.

## Inputs
A bounded request, resolved target identity, authorization context, current cycle state, and applicable evidence.

## Deliverables
One concrete role result or a BLOCKED/NOT_INVOKED disposition with evidence.

## Workflow
1. Resolve the approved plan and exact target capability.
2. Emit the exact functionality before execution.
3. Invoke the narrowest real provider/capability.
4. Capture actual mutation/output evidence.
5. Hand the result to Checker without issuing the final verdict.

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
