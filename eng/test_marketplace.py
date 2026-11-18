"""Regression checks for the PMCR-O catalog's fail-closed source admission."""
import copy
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from validate_marketplace import ROOT, load_reviewed, validate


class MarketplaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.providers = Path(os.environ["PMCRO_PROVIDERS_DIR"]).resolve()
        cls.temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        cls.canonical, _ = load_reviewed(cls.providers / "marketplace-agent", Path(cls.temp.name))
        cls.data = json.loads((ROOT / "marketplace.yaml").read_text())

    def test_real_catalog(self):
        result = validate(ROOT, self.providers, self.canonical)
        self.assertEqual(result["memberships"], 8)
        self.assertEqual(result["skills"], 9)
        self.assertEqual(result["role_invocation"], "NOT_INVOKED")

    def rejected(self, mutate):
        candidate = copy.deepcopy(self.data)
        mutate(candidate)
        with patch.object(self.canonical, "parse", return_value=candidate):
            # Isolate shape assertions; actual package identities are tested above.
            with patch.object(self.canonical, "verify_git_member"):
                with self.assertRaises(ValueError):
                    validate(ROOT, self.providers, self.canonical)

    def test_duplicate(self):
        self.rejected(lambda data: data["plugins"].append(data["plugins"][0]))

    def test_missing_role(self):
        self.rejected(lambda data: data["plugins"].pop(1))

    def test_unpinned_role(self):
        self.rejected(lambda data: data["plugins"][1]["source"].update(ref="main"))

    def test_fake_skill(self):
        self.rejected(lambda data: data["plugins"][2]["skills"].append("create-task"))

    def test_unreviewed_trail_provider(self):
        self.rejected(lambda data: data["plugins"][-1]["source"].update(ref="0" * 40))


if __name__ == "__main__":
    unittest.main()
