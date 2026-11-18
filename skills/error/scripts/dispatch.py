"""Resolve the error event using the shared PMCR-O dispatcher."""
from pathlib import Path
import runpy
import sys

shared = Path(__file__).resolve().parents[2] / "pmcro" / "scripts" / "lifecycle.py"
if __name__ == "__main__":
    sys.exit(runpy.run_path(str(shared))["main"]("error"))
