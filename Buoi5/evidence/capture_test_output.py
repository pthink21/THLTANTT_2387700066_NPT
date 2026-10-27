"""Run the published unittest suites and retain clean UTF-8 stdout/stderr."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).parents[1]
for suite in ("sast-tool", "dast-tool"):
    result = subprocess.run(
        [sys.executable, "-X", "utf8", "-m", "unittest", "discover", "-s", "tests", "-v"],
        cwd=ROOT / suite, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    (ROOT / "evidence" / f"{suite.split('-')[0]}-tests.txt").write_text(
        result.stdout + result.stderr, encoding="utf-8"
    )
    print(f"{suite}: exit={result.returncode}")
    if result.returncode:
        raise SystemExit(result.returncode)
