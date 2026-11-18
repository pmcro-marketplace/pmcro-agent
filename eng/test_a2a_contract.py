import copy
import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("validate_a2a_contract.py")
spec = importlib.util.spec_from_file_location("validate_a2a_contract", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class A2AContractTests(unittest.TestCase):
    def setUp(self):
        self.contract = mod.load(mod.CONTRACT)
        self.marketplace = mod.load(mod.MARKETPLACE)

    def validate_bad(self, mutate):
        bad = copy.deepcopy(self.contract)
        mutate(bad)
        with self.assertRaises(ValueError):
            mod.validate(bad, copy.deepcopy(self.marketplace))

    def test_canonical_contract_passes_with_five_transport_proofs(self):
        result = mod.validate(copy.deepcopy(self.contract), copy.deepcopy(self.marketplace))
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["transport_proofs"], 5)
        self.assertEqual(result["provider_execution"], "NOT_INVOKED")

    def test_checker_cannot_advance_global_lifecycle(self):
        self.validate_bad(lambda x: x["roles"]["checker"].__setitem__("may_advance_global_lifecycle", True))

    def test_duplicate_a2a_endpoint_is_rejected(self):
        self.validate_bad(lambda x: x["roles"]["planner"]["service"].__setitem__(
            "endpoint", x["roles"]["maker"]["service"]["endpoint"]))

    def test_mcp_tool_boundary_cannot_be_replaced_by_a2a(self):
        self.validate_bad(lambda x: x["governance"].__setitem__("tool_boundary", "a2a"))

    def test_built_in_host_cannot_claim_task_lifecycle(self):
        self.validate_bad(lambda x: x["protocol"]["agent_framework"].__setitem__(
            "built_in_task_resumption", True))

    def test_missing_or_failed_transport_proof_is_rejected(self):
        self.validate_bad(lambda x: x["roles"]["planner"]["proof"].__setitem__("status", "FAIL"))

    def test_transport_proof_cannot_claim_role_execution(self):
        self.validate_bad(lambda x: x["roles"]["orchestrator"]["proof"].__setitem__(
            "provider_execution", "PASS"))

    def test_maker_transport_proof_cannot_connect_actuators(self):
        self.validate_bad(lambda x: x["roles"]["maker"]["proof"].__setitem__(
            "actuator_mcp", "CONNECTED"))

    def test_checker_transport_proof_cannot_allow_mutation(self):
        self.validate_bad(lambda x: x["roles"]["checker"]["proof"].__setitem__(
            "mutation", "ALLOWED"))

    def test_reflector_transport_proof_cannot_dispatch_next_cycle(self):
        self.validate_bad(lambda x: x["roles"]["reflector"]["proof"].__setitem__(
            "next_cycle_dispatch", True))

    def test_role_must_match_marketplace_membership(self):
        bad_marketplace = copy.deepcopy(self.marketplace)
        next(p for p in bad_marketplace["plugins"] if p["name"] == "planner")["skills"] = ["other"]
        with self.assertRaises(ValueError):
            mod.validate(copy.deepcopy(self.contract), bad_marketplace)

if __name__ == "__main__":
    unittest.main()
