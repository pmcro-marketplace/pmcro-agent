"""Execute a bounded federation-proof cycle with real local role adapters."""
import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_marketplace import ROOT, load_reviewed, validate

COORDINATOR_SHA256 = "29ff64b78b1347535167885812a095984954ca810eec2d1743ee1bb21207c3a4"
PHASES = ("orchestrate", "plan", "make", "check", "reflect")
ROLES = dict(zip(PHASES, ("orchestrator", "planner", "maker", "checker", "reflector")))
CAPABILITY = "/marketplace:validate"
PROVIDER_ROUTE = "/marketplace:marketplace:validate"
INTENT = "Produce and independently check a pinned PMCR-O federation proof."
CHAIN = [{"skill": CAPABILITY, "prompt": {"operation": "validate-federation"}}]
GRANTS = frozenset([CAPABILITY] + ["/pmcro:" + name for name in (*PHASES, *ROLES.values())])


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def coordinator():
    path = ROOT / "eng/vendor/cycle.py"
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != COORDINATOR_SHA256:
        raise ValueError("Coordinator integrity mismatch")
    # The fixed reviewed dependency is not a request-provided handler.
    namespace = {"__name__": "reviewed_cycle", "__file__": str(path)}
    exec(compile(data, str(path), "exec"), namespace)
    return namespace["run_cycle"]


class FederationHost:
    """Host-owned, fixed-scope callbacks; not a general model or shell runtime."""
    def __init__(self, providers, canonical, trail, grants):
        self.providers = providers
        self.canonical = canonical
        self.trail = trail
        self.grants = frozenset(grants)
        self.role_frames = {}
        self.maker_parent = None

    def authorize(self, address, context):
        return address in GRANTS and address in self.grants

    def result(self, context, output, evidence, **extra):
        request = context["request"]
        return {**{key: request[key] for key in ("workspace_id", "trail_id", "cycle_id")},
                "phase": context["phase"], "status": "COMPLETED",
                "output": output, "evidence": evidence, **extra}

    def orchestrate(self, context):
        request = context["request"]
        self.canonical.require(request["current_intent"] == INTENT and request["chain"] == CHAIN,
                               "Intent outside bounded federation proof")
        return self.result(context, {"intent": INTENT, "next": "/planner:plan:plan"},
                           ["Admitted fixed federation proof intent"])

    def plan(self, context):
        self.canonical.require(context["observations"][0]["output"]["intent"] == INTENT,
                               "No admitted intent")
        return self.result(context, {"chain": CHAIN, "criteria": {
            "catalog_validation": "PASS", "provider_resolution": "PASS",
            "memberships": 8, "skills": 9, "role_invocation": "NOT_INVOKED"}},
            ["Plan bounded to immutable source verification and independent recheck"])

    def validate_capability(self, context):
        self.canonical.require(context["skill"] == CAPABILITY and context["prompt"] == CHAIN[0]["prompt"],
                               "Unknown provider request")
        span = self.trail.begin("function", {"agent": "marketplace-agent", "plugin": "marketplace",
            "skill": "marketplace", "address": PROVIDER_ROUTE}, INTENT, context["prompt"], self.maker_parent)
        print(PROVIDER_ROUTE, file=sys.stderr, flush=True)
        try:
            result = validate(ROOT, self.providers, self.canonical)
        except Exception:
            self.trail.end(span, "FAIL", {"invocation": "INVOKED"}, {})
            raise
        self.trail.end(span, "PASS", {"invocation": "INVOKED"}, result)
        request = context["request"]
        return {**{key: request[key] for key in ("workspace_id", "trail_id", "cycle_id")},
                "skill": CAPABILITY, "status": "COMPLETED", "evidence": [digest(result)],
                "output": result, "frame_id": span["frame_id"]}

    def make(self, context):
        plan = context["observations"][-1]["output"]
        self.canonical.require(plan["chain"] == CHAIN, "Plan scope changed")
        receipt = context["invoke_capability"](CAPABILITY, CHAIN[0]["prompt"])
        self.canonical.require(receipt["status"] == "COMPLETED", "Provider did not complete")
        return self.result(context, {"provider_frame_id": receipt["frame_id"],
                           "proof_digest": digest(receipt["output"])}, receipt["evidence"])

    def check(self, context):
        observations = context["observations"]
        if any(frame["status"] != "COMPLETED" for frame in observations):
            return self.result(context, {"reason": "Prerequisite failed"},
                               ["Observed incomplete prerequisite"], verdict="HALT")
        criteria = observations[1]["output"]["criteria"]
        maker = observations[2]["output"]
        stored = self.trail.read(f"{maker['provider_frame_id']}.jsonl")
        # Independent read of the source objects, not merely the Maker claim.
        actual = validate(ROOT, self.providers, self.canonical)
        checks = {key: actual.get(key) == value for key, value in criteria.items()}
        checks["persisted_proof"] = (stored["status"] == "PASS" and stored["route"]["address"] == PROVIDER_ROUTE
            and stored["parent_id"] == self.role_frames["make"] and stored["evidence"] == actual
            and digest(actual) == maker["proof_digest"])
        return self.result(context, {"criteria": checks, "proof_digest": digest(actual)},
                           [digest(checks)], verdict="PASS" if all(checks.values()) else "LOOP")

    def reflect(self, context):
        verdict = context["check_verdict"]
        return self.result(context, {"verdict": verdict, "approval": "NOT_ISSUED",
            "lesson": "Immutable membership and persisted evidence verified" if verdict == "PASS"
            else "Do not continue until the failed or unavailable prerequisite is resolved"},
            [f"Observed Checker verdict: {verdict}"],
            next_intent="Connect a separately authorized native role host." if verdict == "PASS"
            else "Diagnose the blocked proof cycle.")

    def wrapped(self, phase, parent):
        def invoke(context):
            role = ROLES[phase]
            route = {"agent": role + "-agent", "plugin": role, "skill": phase,
                     "address": f"/{role}:{phase}:{phase}", "implementation": "local-proof-adapter"}
            span = self.trail.begin(phase, route, INTENT,
                                    {"cycle_id": context["request"]["cycle_id"]}, parent)
            self.role_frames[phase] = span["frame_id"]
            if phase == "make":
                self.maker_parent = span["frame_id"]
            print(route["address"], file=sys.stderr, flush=True)
            try:
                result = getattr(self, phase)(context)
            except Exception:
                self.trail.end(span, "FAIL", {"invocation": "INVOKED"}, {})
                raise
            self.trail.end(span, "PASS", {"invocation": "INVOKED"}, result)
            return result
        return invoke


def run(providers, project_id, grants=GRANTS):
    with tempfile.TemporaryDirectory(prefix="pmcro-cycle-provider-") as temporary:
        canonical, trails = load_reviewed(providers / "marketplace-agent", Path(temporary))
        execute = coordinator()
        trail = trails.Trail(project_id)
        cycle_id = str(uuid4())
        root = trail.begin("cycle", {"address": "/pmcro:cycle", "implementation": "reviewed-coordinator"},
                           INTENT, {"cycle_id": cycle_id, "mode": "local-federation-proof"})
        request = {"actor": "pmcro:orchestrator", "high_level_goal": "Validate the federated PMCR-O marketplace.",
            "current_intent": INTENT, "raw_input": INTENT, "workspace_id": project_id, "trail_id": trail.id,
            "cycle_id": cycle_id, "chain": CHAIN}
        host = FederationHost(providers, canonical, trail, grants)
        report = execute(request, {phase: host.wrapped(phase, root["frame_id"]) for phase in PHASES},
                         host.authorize, capabilities={CAPABILITY: host.validate_capability})
        for frame in report["frames"]:
            if frame["phase"] not in host.role_frames:
                decision = trail.begin("decision", {"address": frame["cognitive_skill"]}, INTENT,
                                       {"phase": frame["phase"]}, root["frame_id"])
                trail.end(decision, "BLOCKED", {"invocation": "NOT_INVOKED"}, frame)
        passed = (report["check_verdict"] == "PASS" and
                  all(frame["status"] == "COMPLETED" for frame in report["frames"]))
        trail.end(root, "PASS" if passed else "FAIL", {"invocation": "INVOKED"}, report)
        trail.seal("accept" if passed else "reject")
        seal, frames = trails.Trail(project_id, trail.id).verified_files()
        canonical.require(frames[f"{root['frame_id']}.jsonl"]["evidence"] == report, "Cycle seal mismatch")
        for frame in report["frames"]:
            if frame["status"] == "COMPLETED":
                persisted = frames[trails.PHASE_FILES[frame["phase"]]]
                canonical.require(persisted["frame_id"] == host.role_frames[frame["phase"]]
                    and persisted["evidence"]["output"] == frame["output"]
                    and persisted["evidence"]["evidence"] == frame["evidence"], "Phase receipt mismatch")
        return {"status": "PASS" if passed else "FAIL", "execution_mode": "LOCAL_DETERMINISTIC_ADAPTER",
                "native_role_agents": "NOT_INVOKED", "approval": "NOT_ISSUED",
                "checker": report["check_verdict"], "phases": {f["phase"]: f["status"] for f in report["frames"]},
                "trail_id": trail.id, "cycle_id": cycle_id, "trail_verified": True,
                "disposition": seal["disposition"], "frames": sum(n.endswith(".jsonl") for n in frames),
                "next_cycle_started": report["next_cycle_started"]}


def verify(providers, project_id, trail_id):
    """Reopen a completed proof in a fresh process without re-executing roles."""
    with tempfile.TemporaryDirectory(prefix="pmcro-cycle-verify-") as temporary:
        canonical, trails = load_reviewed(providers / "marketplace-agent", Path(temporary))
        seal, frames = trails.Trail(project_id, trail_id).verified_files()
        roots = [frame for name, frame in frames.items() if name.endswith(".jsonl") and frame["phase"] == "cycle"]
        canonical.require(len(roots) == 1 and seal["disposition"] == "accept", "No accepted cycle")
        root = roots[0]
        report = root["evidence"]
        canonical.require(root["status"] == "PASS" and report["check_verdict"] == "PASS"
            and report["request"]["workspace_id"] == project_id and report["request"]["trail_id"] == trail_id
            and report["request"]["chain"] == CHAIN and report["next_cycle_started"] is False
            and [f["phase"] for f in report["frames"]] == list(PHASES), "Invalid cycle receipt")
        for frame in report["frames"]:
            saved = frames[trails.PHASE_FILES[frame["phase"]]]
            canonical.require(frame["status"] == "COMPLETED" and saved["status"] == "PASS"
                and saved["parent_id"] == root["frame_id"] and saved["evidence"]["output"] == frame["output"]
                and saved["evidence"]["evidence"] == frame["evidence"]
                and saved["evidence"]["cycle_id"] == report["request"]["cycle_id"], "Invalid phase receipt")
        maker = report["frames"][2]["output"]
        checked = report["frames"][3]["output"]
        function = frames[f"{maker['provider_frame_id']}.jsonl"]
        canonical.require(function["status"] == "PASS" and function["route"]["address"] == PROVIDER_ROUTE
            and function["parent_id"] == frames[trails.PHASE_FILES["make"]]["frame_id"]
            and digest(function["evidence"]) == maker["proof_digest"] == checked["proof_digest"]
            and checked["criteria"] and all(value is True for value in checked["criteria"].values())
            and sum(name.endswith(".jsonl") for name in frames) == 7, "Invalid provider/check proof")
        return {"status": "PASS", "trail_verified": True, "trail_id": trail_id,
                "cycle_id": report["request"]["cycle_id"], "checker": "PASS",
                "frames": 7, "invocation": "NOT_INVOKED", "approval": "NOT_ISSUED"}


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--providers-dir", type=Path, required=True)
    parser.add_argument("--project-id", required=True)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--execute-proof", action="store_true", help="Grant only the fixed federation proof")
    mode.add_argument("--verify-trail", help="Reopen a completed proof without invoking roles")
    args = parser.parse_args()
    if not args.execute_proof and not args.verify_trail:
        print(json.dumps({"status": "BLOCKED", "invocation": "NOT_INVOKED"}))
        return 2
    try:
        providers = args.providers_dir.resolve(strict=True)
        result = (verify(providers, args.project_id, args.verify_trail) if args.verify_trail
                  else run(providers, args.project_id))
        print(json.dumps(result, sort_keys=True))
        return 0 if result["status"] == "PASS" else 1
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError):
        print(json.dumps({"status": "UNVERIFIED", "reason": "Cycle or private trail could not be verified"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
