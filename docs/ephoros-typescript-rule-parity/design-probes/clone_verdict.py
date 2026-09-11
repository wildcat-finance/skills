"""E001 findings the shipped checker reports over the pinned application clone.

Resolves the conformance cell once the TypeScript recognisers land.  Exits 0
and prints the count, so the count rather than the lint's own exit status is
what the design record reads.
"""
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CLONE = ROOT / ".hexaemeron" / "validation" / "wildcat-app-v2"
SCRIPT = ROOT / "plugins" / "hexaemeron" / "skills" / "ephoros" / "scripts" / "ephoros.py"

spec = importlib.util.spec_from_file_location("ephoros_lint", SCRIPT)
ephoros = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ephoros)


def main():
    findings = []
    for path in ephoros.walk([str(CLONE)]):
        findings.extend(ephoros.check(path))
    counts = {}
    for finding in findings:
        counts[finding.code] = counts.get(finding.code, 0) + 1
    print(json.dumps({"clone": "wildcat-app-v2@564a189b", "counts": counts,
                      "e001": counts.get("E001", 0)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
