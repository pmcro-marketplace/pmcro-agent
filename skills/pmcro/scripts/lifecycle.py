"""Resolve a lifecycle event without pretending a runtime adapter ran."""
import argparse
import json
import sys
from pathlib import Path

EVENTS = ["agent-startup","input","pre-model-call","post-model-call","pre-tool-call","post-tool-call","handoff","output","error","agent-shutdown"]

def nonblank(value):
    return isinstance(value, str) and bool(value.strip())

def validate(context, expected):
    if not isinstance(context, dict) or context.get("kind") != "LifecycleContext" or type(context.get("version")) is not int or context["version"] != 1:
        raise ValueError("Expected LifecycleContext version 1")
    for key in ("run", "target", "event", "governance", "evidence"):
        if not isinstance(context.get(key), dict):
            raise ValueError(f"Invalid {key}")
    run, target = context["run"], context["target"]
    if not nonblank(run.get("id")) or (run.get("parent_id") is not None and not nonblank(run["parent_id"])):
        raise ValueError("Invalid run identity")
    if not all(nonblank(target.get(key)) for key in ("agent", "plugin", "skill", "function")):
        raise ValueError("Invalid target identity")
    if context["event"].get("name") != expected:
        raise ValueError("Event does not match selected capability")
    if context["governance"].get("posture") not in ("observe", "enforce"):
        raise ValueError("Invalid governance posture")
    if not nonblank(context["evidence"].get("correlation_id")):
        raise ValueError("Missing correlation ID")

def main(expected=None):
    parser = argparse.ArgumentParser(description=__doc__)
    if expected is None:
        parser.add_argument("event", choices=EVENTS)
    parser.add_argument("--context", required=True, type=Path)
    args = parser.parse_args()
    event = expected or args.event
    if event not in EVENTS:
        parser.error("Unknown event")
    try:
        context = json.loads(args.context.read_text(encoding="utf-8"))
        validate(context, event)
    except (OSError, ValueError, TypeError, UnicodeError) as error:
        print(json.dumps({"status": "BLOCKED", "invoked": False, "reason": str(error)}))
        return 1
    print(json.dumps({"kind": "LifecycleInvocation", "capability": f"/pmcro:{event}", "event": event, "correlation_id": context["evidence"]["correlation_id"], "status": "NOT_INVOKED", "invoked": False, "reason": "No registered runtime provider invoked by this resolver."}))
    return 0

if __name__ == "__main__":
    sys.exit(main())
