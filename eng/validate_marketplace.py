"""Validate the PMCR-O federation with the reviewed Marketplace Agent."""
import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORG = "pmcro-marketplace"
# Trust boundary for executable validation and trail code, not another catalog.
REVIEWED_PROVIDER = "5a384a33fed247fb2b85b177ccb9b6ca3901c36c"
EXPECTED = {
    "pmcro": {"interpret", "pmcro"}, "orchestrator": {"orchestrate"},
    "planner": {"plan"}, "maker": {"make"}, "checker": {"check"},
    "reflector": {"reflect"}, "hook": {"hook"}, "marketplace": {"marketplace"},
}


def git(path, *args):
    return subprocess.run(["git", "--no-replace-objects", "-C", str(path), *args],
                          check=True, capture_output=True, timeout=30).stdout


def load_reviewed(provider, directory):
    origin = git(provider, "remote", "get-url", "origin").decode().strip()
    if origin not in {f"https://github.com/{ORG}/marketplace-agent", f"https://github.com/{ORG}/marketplace-agent.git"}:
        raise ValueError("Wrong Marketplace Agent origin")
    if git(provider, "rev-parse", f"{REVIEWED_PROVIDER}^{{commit}}").decode().strip() != REVIEWED_PROVIDER:
        raise ValueError("Reviewed provider missing")
    for file in ("validate_catalogs.py", "trail.py"):
        name = f"skills/marketplace/scripts/{file}"
        entry = git(provider, "ls-tree", REVIEWED_PROVIDER, "--", name).decode().split()
        if len(entry) != 4 or entry[0] not in {"100644", "100755"} or entry[1] != "blob" or entry[3] != name:
            raise ValueError("Invalid provider object")
        (directory / file).write_bytes(git(provider, "show", f"{REVIEWED_PROVIDER}:{name}"))
    sys.path.insert(0, str(directory))
    import validate_catalogs
    import trail
    return validate_catalogs, trail


def validate(root, providers, canonical):
    data = canonical.parse((root / "marketplace.yaml").read_text(encoding="utf-8"))
    canonical.require(set(data) == {"kind", "version", "name", "source", "plugins"} and
        data["kind"] == "Marketplace" and type(data["version"]) is int and data["version"] == 1
        and data["name"] == "pmcro-agent" and data["source"] == {
            "type": "github-repository", "repository": f"{ORG}/pmcro-agent", "path": "marketplace.yaml"
        }, "Invalid catalog identity")
    canonical.require(isinstance(data["plugins"], list), "Invalid plugin list")
    seen = set()
    skills = 0
    for member in data["plugins"]:
        name = member["name"]
        canonical.require(set(member) == {"name", "agent", "enabled", "skills", "source"}
            and name in EXPECTED and name not in seen and member["agent"] == f"{name}-agent"
            and member["enabled"] is True and isinstance(member["skills"], list)
            and len(member["skills"]) == len(EXPECTED[name]) and set(member["skills"]) == EXPECTED[name],
            "Unexpected plugin membership")
        source = member["source"]
        canonical.require(set(source) == {"type", "repository", "ref", "path"}
            and source["type"] == "github-plugin" and source["repository"] == f"{ORG}/{name}-agent"
            and source["path"] == "." and isinstance(source["ref"], str)
            and re.fullmatch("[0-9a-f]{40}", source["ref"]), "Unpinned or incorrect source")
        if name == "marketplace":
            canonical.require(source["ref"] == REVIEWED_PROVIDER, "Provider requires reviewed pin")
        checkout = root if name == "pmcro" else providers / f"{name}-agent"
        canonical.verify_git_member(source, name, member["skills"], checkout)
        paths = set(git(checkout, "ls-tree", "-r", "--name-only", source["ref"]).decode().splitlines())
        for skill in member["skills"]:
            for component in ("scripts", "references", "assets"):
                canonical.require(any(p.startswith(f"skills/{skill}/{component}/") for p in paths),
                                  "Missing required skill artifact")
        seen.add(name)
        skills += len(member["skills"])
    canonical.require(seen == set(EXPECTED), "Required plugin missing")
    return {"catalog_validation": "PASS", "provider_resolution": "PASS",
            "memberships": len(seen), "skills": skills, "role_invocation": "NOT_INVOKED",
            "approval": "NOT_ISSUED"}


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--providers-dir", type=Path, required=True)
    parser.add_argument("--project-id", help="Write a private validation trail in a pre-registered scope")
    args = parser.parse_args()
    try:
        with tempfile.TemporaryDirectory(prefix="pmcro-reviewed-") as temp:
            providers = args.providers_dir.resolve(strict=True)
            canonical, trails = load_reviewed(providers / "marketplace-agent", Path(temp))
            audit = trails.Trail(args.project_id) if args.project_id else None
            span = audit.begin("function", {"agent": "marketplace-agent", "plugin": "marketplace",
                "skill": "marketplace", "address": "/marketplace:marketplace:validate"},
                "Validate pinned PMCR-O marketplace membership", {"catalog": "pmcro-agent"}) if audit else None
            try:
                result = validate(ROOT, providers, canonical)
            except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
                if audit:
                    audit.end(span, "FAIL", {"invocation": "INVOKED"}, {"catalog_validation": "FAIL"})
                    audit.seal("reject")
                raise
            if audit:
                audit.end(span, "PASS", {"invocation": "INVOKED"}, result)
                audit.seal("accept")
                reopened = trails.Trail(args.project_id, audit.id)
                seal, frames = reopened.verified_files()
                canonical.require(seal["disposition"] == "accept" and
                    frames[f"{span['frame_id']}.jsonl"]["evidence"] == result, "Trail receipt mismatch")
                result.update(trail_id=audit.id, trail_frame_id=span["frame_id"], trail_verified=True)
            print(json.dumps(result, sort_keys=True))
            return 0
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
        print(json.dumps({"catalog_validation": "FAIL", "role_invocation": "NOT_INVOKED"}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
