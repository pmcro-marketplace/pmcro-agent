import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
EVENTS = ["agent-startup","input","pre-model-call","post-model-call","pre-tool-call","post-tool-call","handoff","output","error","agent-shutdown"]

class LifecycleTests(unittest.TestCase):
    def run_event(self, event, context):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "context.json"
            path.write_text(json.dumps(context), encoding="utf-8")
            result = subprocess.run([sys.executable, str(ROOT / "skills" / event / "scripts" / "dispatch.py"), "--context", str(path)], text=True, capture_output=True)
            return result.returncode, json.loads(result.stdout)

    def test_all_boundaries(self):
        for event in EVENTS:
            with self.subTest(event=event):
                skill = ROOT / "skills" / event
                example = json.loads((skill / "assets" / "request.json").read_text())
                for relative in ("SKILL.md", "references/contract.md", "scripts/dispatch.py", "assets/request.json"):
                    self.assertTrue((skill / relative).stat().st_size)
                code, result = self.run_event(event, example)
                self.assertEqual((code, result["status"], result["invoked"], result["capability"]), (0, "NOT_INVOKED", False, f"/pmcro:{event}"))
                example["event"]["name"] = "wrong"
                code, result = self.run_event(event, example)
                self.assertEqual((code, result["status"], result["invoked"]), (1, "BLOCKED", False))

    def test_manifest_parity(self):
        root = json.loads((ROOT / "plugin.json").read_text())
        overlay = json.loads((ROOT / ".codex-plugin/plugin.json").read_text())
        for field in ("name", "version", "description"):
            self.assertEqual(root[field], overlay[field])
        self.assertEqual(root["extensions"]["com.openai"]["interface"], overlay["interface"])

    def test_malformed_input(self):
        for value in (None, [], {}, {"kind": "LifecycleContext", "version": True}):
            code, result = self.run_event("input", value)
            self.assertEqual((code, result["status"], result["invoked"]), (1, "BLOCKED", False))

if __name__ == "__main__":
    unittest.main()
