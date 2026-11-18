"""Validate ActivationRequest v1 without invoking any provider or exposing its data."""

import argparse
import json
import re
import sys
from pathlib import Path

CAPABILITY = "/pmcro:activation"
FIELDS = {"kind", "version", "capability", "request_id", "correlation_id", "host", "runtime", "target", "scope", "evidence_refs"}
TARGET_FIELDS = {"agent", "plugin", "skill", "function"}
SCOPE_FIELDS = {"purpose", "max_targets"}
IDENTIFIER = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9._-]{0,126}[A-Za-z0-9])?\Z")


def separate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON keys")
        result[key] = value
    return result


def identifier(value):
    return isinstance(value, str) and IDENTIFIER.fullmatch(value) is not None


def exact_object(value, keys):
    return isinstance(value, dict) and set(value) == keys


def validate(request):
    if not exact_object(request, FIELDS):
        return "Invalid request fields"
    if request["kind"] != "ActivationRequest":
        return "Invalid request kind"
    if type(request["version"]) is not int or request["version"] != 1:
        return "Invalid request version"
    if request["capability"] != CAPABILITY:
        return "Invalid capability address"
    for field in ("request_id", "correlation_id", "host", "runtime"):
        if not identifier(request[field]):
            return f"Invalid {field}"
    target = request["target"]
    if not exact_object(target, TARGET_FIELDS) or not all(identifier(target[key]) for key in TARGET_FIELDS):
        return "Invalid target identity"
    scope = request["scope"]
    if (not exact_object(scope, SCOPE_FIELDS) or scope["purpose"] != "capability-readiness"
            or type(scope["max_targets"]) is not int or scope["max_targets"] != 1):
        return "Invalid readiness scope"
    refs = request["evidence_refs"]
    if (not isinstance(refs, list) or len(refs) > 16
            or not all(identifier(ref) for ref in refs) or len(set(refs)) != len(refs)):
        return "Invalid evidence references"
    return None


def result(status, reason):
    return {"kind": "ActivationResolution", "capability": CAPABILITY,
            "status": status, "activated": False, "readiness": "UNVERIFIED", "reason": reason}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", required=True, type=Path)
    arguments = parser.parse_args()
    try:
        request = json.loads(arguments.request.read_text(encoding="utf-8"), object_pairs_hook=separate_keys)
        reason = validate(request)
    except (OSError, ValueError, TypeError, UnicodeError, RecursionError):
        reason = "Unreadable or malformed JSON request"
    if reason:
        print(json.dumps(result("BLOCKED", reason)))
        return 1
    print(json.dumps(result("NOT_INVOKED", "No authorized activation provider invoked by this resolver.")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
