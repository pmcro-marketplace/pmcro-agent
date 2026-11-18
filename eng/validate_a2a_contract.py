#!/usr/bin/env python3
"""Validate the PMCR-O A2A federation contract against the authored marketplace."""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts" / "a2a" / "role-services.json"
MARKETPLACE = ROOT / "marketplace.yaml"
ROLES = ("orchestrator", "planner", "maker", "checker", "reflector")
EXPECTED_SKILLS = {
    "orchestrator": "orchestrate",
    "planner": "plan",
    "maker": "make",
    "checker": "check",
    "reflector": "reflect",
}

def require(condition, message):
    if not condition:
        raise ValueError(message)

def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def validate(contract=None, marketplace=None):
    contract = load(CONTRACT) if contract is None else contract
    marketplace = load(MARKETPLACE) if marketplace is None else marketplace

    require(contract.get("kind") == "PmcroA2AFederation" and contract.get("version") == 1,
            "invalid A2A federation kind/version")

    protocol = contract.get("protocol", {})
    require(protocol.get("name") == "A2A" and protocol.get("version") == "1.0",
            "A2A protocol must be version 1.0")
    require(set(protocol.get("bindings", [])) == {"http-json", "json-rpc"},
            "both HTTP+JSON and JSON-RPC bindings are required")

    af = protocol.get("agent_framework", {})
    require(af.get("server_registration") == "AddA2AServer", "stale A2A server registration API")
    require(af.get("http_json_mapping") == "MapA2AHttpJson", "stale HTTP+JSON mapping API")
    require(af.get("json_rpc_mapping") == "MapA2AJsonRpc", "stale JSON-RPC mapping API")
    require(af.get("agent_card_mapping") == "MapWellKnownAgentCard", "stale agent-card mapping API")
    require(af.get("background_responses") is False,
            "background A2A responses are not authorized by this contract")
    require(af.get("durable_session_store_required") is True
            and af.get("durable_task_store_required") is True,
            "production A2A requires durable session/task storage")

    gov = contract.get("governance", {})
    require(gov.get("global_lifecycle_owner") == "orchestrator-agent",
            "global lifecycle owner must be Orchestrator Agent")
    require(gov.get("next_cycle_dispatch_owner") == "orchestrator-agent",
            "next-cycle dispatch owner must be Orchestrator Agent")
    require(gov.get("tool_boundary") == "mcp", "MCP must remain the tool/resource boundary")
    require(gov.get("trail_boundary") == "pmcro-trail", "Trail boundary changed")
    required_corr = {"workspace_id", "trail_id", "cycle_id", "a2a_context_id", "a2a_task_id"}
    require(set(gov.get("correlation_fields", [])) == required_corr,
            "A2A/Trail correlation fields are incomplete")

    roles = contract.get("roles", {})
    require(tuple(roles.keys()) == ROLES, "role order or membership changed")
    entries = {p["name"]: p for p in marketplace.get("plugins", []) if p.get("enabled") is True}

    endpoints, servers, agents = set(), set(), set()
    for role in ROLES:
        item = roles[role]
        agent = f"{role}-agent"
        plugin = role
        skill = EXPECTED_SKILLS[role]
        require(item.get("agent") == agent, f"{role}: wrong agent")
        require(item.get("plugin") == plugin, f"{role}: wrong plugin")
        require(item.get("skill") == skill, f"{role}: wrong skill")
        require(item.get("repository") == f"pmcro-marketplace/{agent}", f"{role}: wrong repository")

        service = item.get("service", {})
        require(service.get("mode") == "independent-host", f"{role}: not an independent service")
        require(service.get("server_name") == agent, f"{role}: server name mismatch")
        require(service.get("endpoint") == f"/a2a/{role}", f"{role}: endpoint mismatch")
        require(service.get("well_known_agent_card") is True, f"{role}: agent card required")

        require(agent not in agents, "duplicate agent")
        require(service["server_name"] not in servers, "duplicate A2A server name")
        require(service["endpoint"] not in endpoints, "duplicate A2A endpoint")
        agents.add(agent); servers.add(service["server_name"]); endpoints.add(service["endpoint"])

        mp = entries.get(plugin)
        require(mp is not None, f"{role}: missing marketplace membership")
        require(mp.get("agent") == agent, f"{role}: marketplace agent mismatch")
        require(skill in mp.get("skills", []), f"{role}: marketplace skill mismatch")
        require(mp.get("source", {}).get("repository") == item["repository"],
                f"{role}: marketplace repository mismatch")

        if role == "orchestrator":
            require(item.get("may_advance_global_lifecycle") is True
                    and item.get("may_dispatch_next_cycle") is True,
                    "Orchestrator must own lifecycle advancement and dispatch")
        else:
            require(item.get("may_advance_global_lifecycle") is False,
                    f"{role}: cannot advance global lifecycle")
            require(item.get("may_dispatch_next_cycle") is False,
                    f"{role}: cannot dispatch next cycle")

    require(roles["maker"].get("mcp_access") == "authorized-actuators",
            "Maker must own authorized actuator access")
    require(roles["checker"].get("mcp_access") == "read-only-verification",
            "Checker must remain independent/read-only")
    require(roles["reflector"].get("next_intent_target") == "orchestrator-agent",
            "Reflector may only propose next intent back to Orchestrator")

    return {
        "status": "PASS",
        "roles": len(ROLES),
        "bindings": sorted(protocol["bindings"]),
        "global_lifecycle_owner": gov["global_lifecycle_owner"],
        "tool_boundary": gov["tool_boundary"],
        "background_responses": af["background_responses"],
        "durable_state_required": True
    }

def main():
    try:
        print(json.dumps(validate(), sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(json.dumps({"status":"FAIL","error":str(exc)}, sort_keys=True))
        return 1

if __name__ == "__main__":
    sys.exit(main())
