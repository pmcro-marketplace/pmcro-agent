"""Actual provider-backed tests of the local role adapter and trail boundaries."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from run_cycle import GRANTS, CAPABILITY, run, verify


class HostTests(unittest.TestCase):
    def setUp(self):
        self.providers = Path(os.environ["PMCRO_PROVIDERS_DIR"]).resolve()
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        for path in (self.home / ".pmcro", self.home / ".pmcro/projects", self.home / ".pmcro/projects/proof"):
            path.mkdir(mode=0o700)
        self.env = patch.dict(os.environ, {"HOME": str(self.home)})
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_complete_live_cycle(self):
        result = run(self.providers, "proof")
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(set(result["phases"].values()), {"COMPLETED"})
        self.assertEqual(result["native_role_agents"], "NOT_INVOKED")
        self.assertEqual(result["frames"], 7)
        self.assertEqual(verify(self.providers, "proof", result["trail_id"])["status"], "PASS")

    def test_dual_grant_denied(self):
        result = run(self.providers, "proof", GRANTS - {"/pmcro:planner"})
        self.assertEqual(result["phases"]["plan"], "DENIED")
        self.assertEqual(result["phases"]["make"], "BLOCKED")
        self.assertEqual(result["checker"], "HALT")
        self.assertEqual(result["disposition"], "reject")
        self.assertTrue(result["trail_verified"])

    def test_provider_denied(self):
        result = run(self.providers, "proof", GRANTS - {CAPABILITY})
        self.assertEqual(result["phases"]["make"], "FAILED")
        self.assertEqual(result["checker"], "HALT")

    def test_tamper_fails_reopen(self):
        result = run(self.providers, "proof")
        path = self.home / ".pmcro/projects/proof/trails" / result["trail_id"] / "01-check.jsonl"
        path.write_bytes(path.read_bytes() + b" ")
        with self.assertRaises(ValueError):
            verify(self.providers, "proof", result["trail_id"])


if __name__ == "__main__":
    unittest.main()
