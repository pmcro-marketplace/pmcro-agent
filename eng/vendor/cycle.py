"""Bounded, host-callable PMCR-O phase coordinator; no native host assumed."""
from __future__ import annotations

import argparse
import json
import re
from collections.abc import Mapping
from pathlib import Path

PHASES = ("orchestrate", "plan", "make", "check", "reflect")
ROLES = dict(zip(PHASES, ("orchestrator", "planner", "maker", "checker", "reflector")))
REQUIRED = {"high_level_goal", "current_intent", "actor", "raw_input", "workspace_id", "trail_id", "cycle_id"}
OPTIONAL = {"request_id", "parent_cycle_id", "chain"}
ADDRESS = re.compile(r"^/[a-z0-9][a-z0-9-]*:[a-z0-9][a-z0-9-]*$")
IDENTITY = re.compile(r"^(?:[a-z][a-z0-9-]*:)?[a-z][a-z0-9-]*$")
IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")


def json_copy(value):
    """Validate JSON value and isolate caller-owned data."""
    return json.loads(json.dumps(value, allow_nan=False))


def _json_identity(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def validate_request(request):
    if not isinstance(request, dict) or not REQUIRED <= request.keys() or request.keys() - REQUIRED - OPTIONAL:
        raise ValueError("request fields do not match the contract")
    for name in ("high_level_goal", "current_intent"):
        if not isinstance(request[name], str) or not request[name].strip():
            raise ValueError(f"{name} must be a nonempty string")
    if not isinstance(request["actor"], str) or not IDENTITY.fullmatch(request["actor"]):
        raise ValueError("invalid actor identity")
    for name in ("workspace_id", "trail_id", "cycle_id", "request_id", "parent_cycle_id"):
        if name in request and (not isinstance(request[name], str) or not IDENTIFIER.fullmatch(request[name])):
            raise ValueError(f"invalid {name}")
    if request.get("parent_cycle_id") == request["cycle_id"]:
        raise ValueError("parent cannot be the current cycle")
    chain = request.get("chain", [])
    if not isinstance(chain, list) or len(chain) > 100:
        raise ValueError("chain must be an array of at most 100 calls")
    for call in chain:
        if (not isinstance(call, dict) or set(call) != {"skill", "prompt"}
                or not isinstance(call["skill"], str) or not ADDRESS.fullmatch(call["skill"])):
            raise ValueError("invalid skill chain entry")
    return json_copy(request)


def _correlation(request):
    return {k: request[k] for k in ("workspace_id", "trail_id", "cycle_id", "request_id", "parent_cycle_id") if k in request}


def _frame(request, phase, status, reason=None, **extra):
    frame = {**_correlation(request), "phase": phase, "role": "pmcro:" + ROLES[phase],
             "agent_invocation": "/pmcro:" + ROLES[phase], "cognitive_skill": "/pmcro:" + phase,
             "status": status, **extra}
    if reason:
        frame["reason"] = reason
    return frame


def _validate_result(result, request, phase):
    if not isinstance(result, dict):
        raise ValueError("adapter must return an object")
    base = set(_correlation(request)) | {"phase", "status", "evidence", "output"}
    optional = {"verdict"} if phase == "check" else {"next_intent", "priority"} if phase == "reflect" else set()
    if not base <= result.keys() or result.keys() - base - optional:
        raise ValueError("invalid adapter result fields")
    if any(result.get(k) != v for k, v in _correlation(request).items()) or result["phase"] != phase:
        raise ValueError("adapter result correlation mismatch")
    if result["status"] not in ("COMPLETED", "FAILED"):
        raise ValueError("invalid adapter status")
    if not isinstance(result["evidence"], list) or not all(isinstance(e, str) and e.strip() for e in result["evidence"]):
        raise ValueError("invalid adapter evidence")
    if result["status"] == "COMPLETED" and not result["evidence"]:
        raise ValueError("completed result requires evidence")
    if phase == "check":
        if result["status"] == "COMPLETED" and result.get("verdict") not in ("PASS", "LOOP", "HALT"):
            raise ValueError("Checker must report PASS, LOOP or HALT")
        if result["status"] != "COMPLETED" and "verdict" in result:
            raise ValueError("failed Checker cannot supply a verdict")
    if phase == "reflect":
        if "next_intent" in result and (result["status"] != "COMPLETED" or not isinstance(result["next_intent"], str) or not result["next_intent"].strip()):
            raise ValueError("invalid Reflector next intent")
        if "priority" in result and ("next_intent" not in result or type(result["priority"]) is not int or not 0 <= result["priority"] <= 100):
            raise ValueError("invalid Reflector priority")
    return json_copy(result)


def _authorized(authorize, address, context):
    try:
        return authorize(address, json_copy(context)) is True
    except Exception:
        return False


def _proposal(request, reflection):
    if reflection["status"] != "COMPLETED" or "next_intent" not in reflection:
        return None
    proposal = {
        "kind": "BehavioralIntent",
        "version": 1,
        "from": "pmcro:reflector",
        "to": "pmcro:orchestrator",
        "workspace_id": request["workspace_id"],
        "trail_id": request["trail_id"],
        "parent_cycle_id": request["cycle_id"],
        "high_level_goal": request["high_level_goal"],
        "current_intent": reflection["next_intent"],
        "priority": reflection.get("priority", 50),
        "chain": [{"skill": "/pmcro:orchestrator", "prompt": reflection["next_intent"]}],
        "execution_authorized": False,
    }
    if "request_id" in request:
        proposal["parent_request_id"] = request["request_id"]
    return proposal


def run_cycle(request, adapters, authorize, feedback=None, capabilities=None):
    """Run precisely five phases, using callbacks explicitly supplied by the host."""
    request = validate_request(request)
    if not isinstance(adapters, Mapping) or not callable(authorize):
        raise ValueError("host must supply a phase-adapter mapping and authorizer")
    if feedback is not None and not callable(feedback):
        raise ValueError("feedback must be a registered callable")
    if capabilities is not None and not isinstance(capabilities, Mapping):
        raise ValueError("capabilities must be a registered mapping")
    capabilities = {} if capabilities is None else capabilities
    frames = []
    verdict = "NOT_EVALUATED"
    proposal = None
    domain_receipts = []
    remaining_calls = json_copy(request.get("chain", []))
    maker_active = False

    def invoke_capability(skill, prompt):
        """Resolve the next submitted call only; no shell, unknown routing or replay."""
        if not maker_active:
            return {"status": "DENIED", "reason": "resolver is scoped to the active Maker"}
        if any(r["status"] != "COMPLETED" for r in domain_receipts):
            return {"status": "BLOCKED", "reason": "earlier capability did not complete"}
        try:
            exact_match = bool(remaining_calls) and _json_identity(remaining_calls[0]) == _json_identity({"skill": skill, "prompt": prompt})
        except (TypeError, ValueError):
            exact_match = False
        if not exact_match:
            domain_receipts.append({**_correlation(request), "status": "DENIED", "reason": "not the next submitted call"})
            return {"status": "DENIED", "reason": "not the next submitted call"}
        context = {"request": request, "phase": "make", "skill": skill, "prompt": prompt}
        if not _authorized(authorize, skill, context):
            receipt = {"status": "DENIED", "skill": skill}
        elif not callable(capabilities.get(skill)):
            receipt = {"status": "NOT_AVAILABLE", "skill": skill}
        else:
            remaining_calls.pop(0)
            try:
                payload = capabilities[skill](json_copy(context))
                if (not isinstance(payload, dict) or payload.get("status") not in ("COMPLETED", "FAILED")
                        or any(payload.get(k) != v for k, v in _correlation(request).items())
                        or payload.get("skill") != skill
                        or not isinstance(payload.get("evidence"), list)
                        or not all(isinstance(e, str) and e.strip() for e in payload["evidence"])
                        or (payload["status"] == "COMPLETED" and not payload["evidence"])):
                    raise ValueError("invalid capability receipt")
                receipt = json_copy(payload)
            except Exception as exc:
                receipt = {"status": "FAILED", "skill": skill, "reason": type(exc).__name__}
        receipt = {**receipt, **_correlation(request)}
        domain_receipts.append(receipt)
        return json_copy(receipt)

    for phase in PHASES:
        if phase in ("plan", "make") and any(f["status"] != "COMPLETED" for f in frames):
            frames.append(_frame(request, phase, "BLOCKED", "prerequisite phase did not complete"))
            continue
        adapter = adapters.get(phase)
        if not callable(adapter):
            frames.append(_frame(request, phase, "NOT_AVAILABLE", "phase adapter not registered"))
            continue
        context = {
            "request": request,
            "phase": phase,
            "role": "pmcro:" + ROLES[phase],
            "agent_invocation": "/pmcro:" + ROLES[phase],
            "cognitive_skill": "/pmcro:" + phase,
            "observations": frames,
            "check_verdict": verdict,
        }
        if not _authorized(authorize, context["agent_invocation"], context):
            frames.append(_frame(request, phase, "DENIED", "agent invocation authorization absent or denied"))
            continue
        if not _authorized(authorize, context["cognitive_skill"], context):
            frames.append(_frame(request, phase, "DENIED", "cognitive skill authorization absent or denied"))
            continue
        invocation = json_copy(context)
        if phase == "make":
            invocation["invoke_capability"] = invoke_capability
            maker_active = True
        try:
            result = _validate_result(adapter(invocation), request, phase)
            if phase == "make" and result["status"] == "COMPLETED":
                if remaining_calls or any(r["status"] != "COMPLETED" for r in domain_receipts):
                    raise ValueError("submitted capability chain did not complete")
            if phase == "check" and result.get("verdict") == "PASS" and any(f["status"] != "COMPLETED" for f in frames):
                raise ValueError("cannot PASS an incomplete execution")
        except Exception as exc:
            frame = _frame(request, phase, "FAILED", "adapter or contract fault: " + type(exc).__name__)
        else:
            frame = _frame(request, phase, result["status"], evidence=result["evidence"], output=result["output"])
            if phase == "check" and result["status"] == "COMPLETED":
                verdict = result["verdict"]
                frame["verdict"] = verdict
            if phase == "reflect":
                proposal = _proposal(request, result)
                if proposal is not None:
                    frame["next_intent"] = proposal["current_intent"]
        if phase == "make":
            maker_active = False
            frame["capability_receipts"] = json_copy(domain_receipts)
        frames.append(frame)

    queue = {"status": "NO_PROPOSAL"} if proposal is None else {"status": "PROPOSED_ONLY"}
    if proposal is not None and feedback is not None:
        queue_context = {"request": request, "proposal": proposal, "agent_invocation": "/pmcro:message-queue", "cognitive_skill": "/message:queue"}
        if (not _authorized(authorize, queue_context["agent_invocation"], queue_context)
                or not _authorized(authorize, queue_context["cognitive_skill"], queue_context)):
            queue = {"status": "DENIED"}
        else:
            try:
                receipt = feedback(json_copy(proposal))
                keys = ("workspace_id", "trail_id", "parent_cycle_id", "parent_request_id")
                if (not isinstance(receipt, dict) or receipt.get("status") != "ENQUEUED"
                        or any(receipt.get(k) != proposal[k] for k in keys if k in proposal)
                        or not isinstance(receipt.get("message_id"), str)
                        or not IDENTIFIER.fullmatch(receipt["message_id"])):
                    raise ValueError("invalid queue receipt")
                queue = json_copy(receipt)
            except Exception as exc:
                queue = {"status": "FAILED", "reason": type(exc).__name__}
    return {
        "request": request, "frames": frames, "check_verdict": verdict,
        "continuation": proposal, "feedback": queue, "next_cycle_started": False,
    }


def main():
    parser = argparse.ArgumentParser(description="PMCR-O cycle offline request diagnostic.")
    parser.add_argument("--diagnose", type=Path, required=True, help="JSON request, read only")
    args = parser.parse_args()
    try:
        request = validate_request(json.loads(args.diagnose.read_text(encoding="utf-8")))
    except (OSError, ValueError, TypeError) as exc:
        parser.exit(1, f"Invalid request: {exc}\n")
    print(json.dumps({
        "mode": "OFFLINE_DIAGNOSTIC", "cycle_id": request["cycle_id"],
        "logical_routes": ["/pmcro:" + ROLES[p] for p in PHASES],
        "cognitive_skills": ["/pmcro:" + p for p in PHASES], "executions": 0,
    }, indent=2))


if __name__ == "__main__":
    main()
