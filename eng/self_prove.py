#!/usr/bin/env python3
"""Make PMCR-O prove its own marketplace, A2A contracts, and sealed cycle evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "eng"))

import run_cycle
import validate_a2a_contract
import validate_a2a_federation_transport
import validate_marketplace

KIND = "PmcroSelfProof"
VERSION = 1
SUBJECT_REPOSITORY = "pmcro-marketplace/pmcro-agent"
SUBJECT_FILES = (
    "marketplace.yaml",
    "contracts/a2a/role-services.json",
    "contracts/a2a/federation-transport.json",
)
EXPECTED_CLAIMS = {
    "pmcro_cycle": "INVOKED",
    "marketplace_capability": "INVOKED",
    "native_role_agents": "NOT_INVOKED",
    "a2a_role_providers": "NOT_INVOKED",
    "hook_lifecycle": "NOT_INVOKED",
    "approval": "NOT_ISSUED",
}

def require(condition, message):
    if not condition:
        raise ValueError(message)

def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def subject_commit():
    return subprocess.run(
        ["git", "--no-replace-objects", "-C", str(ROOT), "rev-parse", "HEAD"],
        check=True, capture_output=True, text=True, timeout=30
    ).stdout.strip()

def subject_remote():
    remote = subprocess.run(
        ["git", "--no-replace-objects", "-C", str(ROOT), "remote", "get-url", "origin"],
        check=True, capture_output=True, text=True, timeout=30
    ).stdout.strip()
    require(
        remote in {
            "https://github.com/pmcro-marketplace/pmcro-agent",
            "https://github.com/pmcro-marketplace/pmcro-agent.git",
        },
        "Self-proof is not running from the PMCR-O Agent repository",
    )
    return SUBJECT_REPOSITORY

def artifact_digests():
    return {name: sha256_file(ROOT / name) for name in SUBJECT_FILES}

def static_checks(providers):
    with tempfile.TemporaryDirectory(prefix="pmcro-self-static-") as temp:
        canonical, _ = validate_marketplace.load_reviewed(
            providers / "marketplace-agent", Path(temp)
        )
        marketplace = validate_marketplace.validate(ROOT, providers, canonical)
    return {
        "marketplace": marketplace,
        "a2a_contract": validate_a2a_contract.validate(),
        "a2a_transport": validate_a2a_federation_transport.validate(),
    }

def validate_execution_report(report):
    require(report.get("kind") == KIND and report.get("version") == VERSION,
            "Invalid self-proof receipt kind/version")
    require(report.get("status") == "PASS", "Self-proof execution did not pass")
    require(report.get("subject") == SUBJECT_REPOSITORY, "Wrong self-proof subject")
    commit = report.get("subject_commit")
    require(isinstance(commit, str) and len(commit) == 40
            and all(c in "0123456789abcdef" for c in commit),
            "Invalid subject commit")
    digests = report.get("artifact_digests", {})
    require(set(digests) == set(SUBJECT_FILES)
            and all(isinstance(v, str) and len(v) == 64 for v in digests.values()),
            "Incomplete subject artifact digests")

    checks = report.get("self_checks", {})
    marketplace = checks.get("marketplace", {})
    a2a = checks.get("a2a_contract", {})
    transport = checks.get("a2a_transport", {})
    require(
        marketplace.get("catalog_validation") == "PASS"
        and marketplace.get("provider_resolution") == "PASS"
        and marketplace.get("memberships") == 8
        and marketplace.get("skills") == 9
        and marketplace.get("role_invocation") == "NOT_INVOKED",
        "Marketplace self-check failed",
    )
    require(
        a2a.get("status") == "PASS"
        and a2a.get("roles") == 5
        and a2a.get("transport_proofs") == 5
        and a2a.get("provider_execution") == "NOT_INVOKED",
        "A2A contract self-check failed",
    )
    require(
        transport.get("status") == "PASS"
        and transport.get("services") == 5
        and transport.get("provider_execution") == "NOT_INVOKED",
        "A2A federation transport self-check failed",
    )

    cycle = report.get("cycle", {})
    require(
        cycle.get("status") == "PASS"
        and cycle.get("checker") == "PASS"
        and cycle.get("trail_verified") is True
        and cycle.get("disposition") == "accept"
        and cycle.get("frames") == 7
        and cycle.get("native_role_agents") == "NOT_INVOKED"
        and cycle.get("approval") == "NOT_ISSUED"
        and cycle.get("next_cycle_started") is False,
        "PMCR-O cycle self-proof failed",
    )
    require(
        cycle.get("phases") == {
            "orchestrate": "COMPLETED",
            "plan": "COMPLETED",
            "make": "COMPLETED",
            "check": "COMPLETED",
            "reflect": "COMPLETED",
        },
        "Incomplete PMCR-O self-proof phases",
    )
    require(report.get("claims") == EXPECTED_CLAIMS, "Capability claims inflated")
    return True

def execute(providers, project_id):
    subject_remote()
    report = {
        "kind": KIND,
        "version": VERSION,
        "status": "PASS",
        "subject": SUBJECT_REPOSITORY,
        "subject_commit": subject_commit(),
        "artifact_digests": artifact_digests(),
        "self_checks": static_checks(providers),
        "cycle": run_cycle.run(providers, project_id),
        "claims": dict(EXPECTED_CLAIMS),
        "proof_scope": "github-ci-local-deterministic-adapters",
    }
    validate_execution_report(report)
    return report

def verify(providers, project_id, receipt_path):
    report = json.loads(Path(receipt_path).read_text(encoding="utf-8"))
    validate_execution_report(report)
    subject_remote()
    require(subject_commit() == report["subject_commit"], "Subject commit changed")
    require(artifact_digests() == report["artifact_digests"], "Subject artifacts changed")
    checks = static_checks(providers)
    require(checks == report["self_checks"], "Independent static recheck differs")
    cycle = report["cycle"]
    reopened = run_cycle.verify(providers, project_id, cycle["trail_id"])
    require(
        reopened.get("status") == "PASS"
        and reopened.get("trail_verified") is True
        and reopened.get("trail_id") == cycle["trail_id"]
        and reopened.get("cycle_id") == cycle["cycle_id"]
        and reopened.get("checker") == "PASS"
        and reopened.get("frames") == 7
        and reopened.get("invocation") == "NOT_INVOKED",
        "Independent Trail reopen failed",
    )
    return {
        "kind": "PmcroSelfProofVerification",
        "version": 1,
        "status": "PASS",
        "subject": SUBJECT_REPOSITORY,
        "subject_commit": report["subject_commit"],
        "artifact_digests_match": True,
        "static_recheck": "PASS",
        "trail_reopen": reopened,
        "native_role_agents": "NOT_INVOKED",
        "a2a_role_providers": "NOT_INVOKED",
        "hook_lifecycle": "NOT_INVOKED",
        "approval": "NOT_ISSUED",
        "self_proof_verified": True,
    }

def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--providers-dir", type=Path, required=True)
    parser.add_argument("--project-id", required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--execute", action="store_true")
    mode.add_argument("--verify", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        providers = args.providers_dir.resolve(strict=True)
        result = execute(providers, args.project_id) if args.execute else verify(
            providers, args.project_id, args.verify
        )
        text = json.dumps(result, sort_keys=True)
        if args.output:
            args.output.write_text(text + "\n", encoding="utf-8")
        print(text)
        return 0
    except (
        OSError, ValueError, KeyError, TypeError,
        json.JSONDecodeError, subprocess.SubprocessError
    ) as exc:
        print(json.dumps({
            "status": "FAIL",
            "self_proof_verified": False,
            "error": str(exc),
            "native_role_agents": "NOT_INVOKED",
            "approval": "NOT_ISSUED",
        }, sort_keys=True))
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
