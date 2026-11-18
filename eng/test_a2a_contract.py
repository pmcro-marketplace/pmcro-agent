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

    def test_canonical_contract_passes(self):
        result = mod.validate(copy.deepcopy(self.contract), copy.deepcopy(self.marketplace))
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["roles"], 5)
        self.assertEqual(result["built_in_response_mode"], "message-only")

    def test_checker_cannot_advance_global_lifecycle(self):
        bad = copy.deepcopy(self.contract)
        bad["roles"]["checker"]["may_advance_global_lifecycle"] = True
        with self.assertRaises(ValueError):
            mod.validate(bad, copy.deepcopy(self.marketplace))

    def test_duplicate_a2a_endpoint_is_rejected(self):
        bad = copy.deepcopy(self.contract)
        bad["roles"]["planner"]["service"]["endpoint"] = bad["roles"]["maker"]["service"]["endpoint"]
        with self.assertRaises(ValueError):
            mod.validate(bad, copy.deepcopy(self.marketplace))

    def test_mcp_tool_boundary_cannot_be_replaced_by_a2a(self):
        bad = copy.deepcopy(self.contract)
        bad["governance"]["tool_boundary"] = "a2a"
        with self.assertRaises(ValueError):
            mod.validate(bad, copy.deepcopy(self.marketplace))

    def test_built_in_host_cannot_claim_task_lifecycle(self):
        bad = copy.deepcopy(self.contract)
        bad["protocol"]["agent_framework"]["built_in_task_resumption"] = True
        with self.assertRaises(ValueError):
            mod.validate(bad, copy.deepcopy(self.marketplace))

    def test_task_id_is_optional_for_message_only_host(self):
        bad = copy.deepcopy(self.contract)
        bad["governance"]["required_correlation_fields"].append("a2a_task_id")
        bad["governance"]["optional_correlation_fields"] = []
        with self.assertRaises(ValueError):
            mod.validate(bad, copy.deepcopy(self.marketplace))

    def test_role_must_match_marketplace_membership(self):
        bad_marketplace = copy.deepcopy(self.marketplace)
        next(p for p in bad_marketplace["plugins"] if p["name"] == "planner")["skills"] = ["other"]
        with self.assertRaises(ValueError):
            mod.validate(copy.deepcopy(self.contract), bad_marketplace)

if __name__ == "__main__":
    unittest.main()
