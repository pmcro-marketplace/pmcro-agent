import copy
import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("self_prove.py")
spec = importlib.util.spec_from_file_location("self_prove", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def good_report():
    return {
        "kind": "PmcroSelfProof",
        "version": 1,
        "status": "PASS",
        "subject": "pmcro-marketplace/pmcro-agent",
        "subject_commit": "a" * 40,
        "artifact_digests": {
            "marketplace.yaml": "b" * 64,
            "contracts/a2a/role-services.json": "c" * 64,
            "contracts/a2a/federation-transport.json": "d" * 64,
        },
        "self_checks": {
            "marketplace": {
                "catalog_validation": "PASS",
                "provider_resolution": "PASS",
                "memberships": 8,
                "skills": 9,
                "role_invocation": "NOT_INVOKED",
            },
            "a2a_contract": {
                "status": "PASS",
                "roles": 5,
                "transport_proofs": 5,
                "provider_execution": "NOT_INVOKED",
            },
            "a2a_transport": {
                "status": "PASS",
                "services": 5,
                "provider_execution": "NOT_INVOKED",
            },
        },
        "cycle": {
            "status": "PASS",
            "checker": "PASS",
            "trail_verified": True,
            "disposition": "accept",
            "frames": 7,
            "native_role_agents": "NOT_INVOKED",
            "approval": "NOT_ISSUED",
            "next_cycle_started": False,
            "phases": {
                "orchestrate": "COMPLETED",
                "plan": "COMPLETED",
                "make": "COMPLETED",
                "check": "COMPLETED",
                "reflect": "COMPLETED",
            },
        },
        "claims": dict(mod.EXPECTED_CLAIMS),
        "proof_scope": "github-ci-local-deterministic-adapters",
    }

class SelfProofReceiptTests(unittest.TestCase):
    def reject(self, mutate):
        report = copy.deepcopy(good_report())
        mutate(report)
        with self.assertRaises(ValueError):
            mod.validate_execution_report(report)

    def test_good_receipt_passes(self):
        self.assertTrue(mod.validate_execution_report(good_report()))

    def test_failed_checker_is_rejected(self):
        self.reject(lambda r: r["cycle"].__setitem__("checker", "LOOP"))

    def test_native_role_execution_claim_is_rejected(self):
        self.reject(lambda r: r["claims"].__setitem__("native_role_agents", "INVOKED"))

    def test_missing_phase_is_rejected(self):
        self.reject(lambda r: r["cycle"]["phases"].pop("reflect"))

    def test_failed_a2a_contract_is_rejected(self):
        self.reject(lambda r: r["self_checks"]["a2a_contract"].__setitem__("status", "FAIL"))

    def test_changed_subject_is_rejected(self):
        self.reject(lambda r: r.__setitem__("subject", "other/repository"))

    def test_approval_inflation_is_rejected(self):
        self.reject(lambda r: r["claims"].__setitem__("approval", "APPROVED"))

if __name__ == "__main__":
    unittest.main()
