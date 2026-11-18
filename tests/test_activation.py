import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "activation"


class ActivationTests(unittest.TestCase):
    def setUp(self):
        self.example = json.loads((SKILL / "assets/request.json").read_text(encoding="utf-8"))

    def run_raw(self, raw):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "request.json"
            path.write_text(raw, encoding="utf-8")
            completed = subprocess.run([sys.executable, str(SKILL / "scripts/validate.py"), "--request", str(path)], text=True, capture_output=True)
            return completed.returncode, json.loads(completed.stdout), completed.stdout

    def run_request(self, value):
        return self.run_raw(json.dumps(value))

    def assert_blocked(self, value):
        code, result, raw = self.run_request(value)
        self.assertEqual((code, result["status"], result["activated"], result["readiness"]), (1, "BLOCKED", False, "UNVERIFIED"))
        self.assertNotIn("private-synthetic-marker", raw)

    def test_example(self):
        code, result, raw = self.run_request(self.example)
        self.assertEqual((code, result["status"], result["activated"], result["readiness"], result["capability"]), (0, "NOT_INVOKED", False, "UNVERIFIED", "/pmcro:activation"))
        for marker in ("example-request", "example-correlation", "example-agent", "example-evidence", "example-host"):
            self.assertNotIn(marker, raw)
        self.example["evidence_refs"] = []
        self.assertEqual(self.run_request(self.example)[0], 0)

    def test_invalid_top_level(self):
        for request in (None, [], {}, True, "private-synthetic-marker"):
            with self.subTest(request=request):
                self.assert_blocked(request)
        for key in self.example:
            with self.subTest(missing=key):
                request = dict(self.example)
                del request[key]
                self.assert_blocked(request)

    def test_wrong_values_and_forged_flags(self):
        for key, value in (("kind", "Other"), ("version", True), ("version", 2), ("capability", "/pmcro:input"), ("request_id", ""), ("correlation_id", []), ("host", 3), ("runtime", "private-synthetic-marker\\path"), ("authorized", True), ("activated", True), ("readiness", "VERIFIED"), ("evidence_refs", ["duplicate", "duplicate"]), ("evidence_refs", ["https://example.invalid"]), ("evidence_refs", [False]), ("evidence_refs", [f"ref-{i}" for i in range(17)])):
            with self.subTest(key=key, value=value):
                self.assert_blocked(dict(self.example, **{key: value}))
        for section, edits in (("target", {"authorized": True}), ("target", {"agent": ""}), ("target", {"function": []}), ("scope", {"activated": True}), ("scope", {"max_targets": True}), ("scope", {"max_targets": 2}), ("scope", {"purpose": "execute"})):
            with self.subTest(section=section, edits=edits):
                request = copy.deepcopy(self.example)
                request[section].update(edits)
                self.assert_blocked(request)

    def test_malformed_and_duplicate_keys_do_not_leak(self):
        for raw in ('{"private-synthetic-marker":', '{"kind":"ActivationRequest","kind":"private-synthetic-marker"}'):
            code, result, output = self.run_raw(raw)
            self.assertEqual((code, result["status"], result["activated"]), (1, "BLOCKED", False))
            self.assertNotIn("private-synthetic-marker", output)

    def test_manifest_and_structure(self):
        root = json.loads((ROOT / "plugin.json").read_text())
        overlay = json.loads((ROOT / ".codex-plugin/plugin.json").read_text())
        for key in ("name", "version", "description", "author", "keywords"):
            self.assertEqual(root[key], overlay[key])
        self.assertEqual(root["version"], "0.6.0")
        self.assertEqual(root["extensions"]["com.openai"]["interface"], overlay["interface"])
        for relative in ("SKILL.md", "references/contract.md", "scripts/validate.py", "assets/request.json"):
            self.assertTrue((SKILL / relative).stat().st_size)
        self.assertFalse((ROOT / "skills/subagent").exists())


if __name__ == "__main__":
    unittest.main()
