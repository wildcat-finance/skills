#!/usr/bin/env python3
"""Run the #2014 conformance specimens due after each implementation step."""

import argparse
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[3]
TEST_MODULE = "plugins.hexaemeron.tests.test_fiat_commit_supersession"


def live_platform_readback(controller, root: Path) -> list[str]:
    """Recheck the exact published final Step range before integration."""
    controller.verify_run(str(root))
    state = controller.load_state(str(root))
    if state.get("phase") != "integrate" or not state.get("steps"):
        raise ValueError("platform readback requires the pushed final Step at integration")
    receipt = state["steps"][-1].get("receipts", {}).get("push")
    if not isinstance(receipt, dict):
        raise ValueError("final Step has no push receipt")
    commits = receipt.get("verified_commits")
    if not isinstance(commits, list) or not commits or commits != receipt.get("github_verified"):
        raise ValueError("final Step has no exact GitHub-verified range")
    if controller.verify_github_commits(str(root), commits) != commits:
        raise ValueError("host readback differs from the exact final Step range")
    return commits


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--criterion", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    if args.candidate != "append-only-map" or args.criterion not in (
        "uid-admission", "effective-ancestry", "platform-readback"
    ):
        parser.error("this source implements only the three append-only-map conformance criteria")
    command = (
        "python3 plugins/hexaemeron/tests/fiat_commit_supersession_proof.py "
        f"--candidate {args.candidate} --criterion {args.criterion} "
        f"--report {args.report}"
    )
    tests = subprocess.run(
        [sys.executable, "-m", "unittest", TEST_MODULE, "-v"],
        cwd=ROOT, capture_output=True, timeout=60,
    )
    if tests.returncode != 0:
        print(f"{args.criterion} specimens failed; report was not written", file=sys.stderr)
        return 1
    if args.criterion == "platform-readback":
        sys.path.insert(0, str(ROOT / "plugins" / "hexaemeron" / "skills" / "fiat" / "scripts"))
        import hexctl
        try:
            commits = live_platform_readback(hexctl, ROOT)
        except (SystemExit, ValueError) as error:
            print(f"platform readback refused: {error}", file=sys.stderr)
            return 1
        print(f"platform readback verified {len(commits)} exact published SHA(s)")
    report = {
        "schema": "protasis-design-report/v1",
        "candidate": args.candidate,
        "criterion": args.criterion,
        "value": True,
        "unit": "boolean",
        "command": command,
        "exit": 0,
    }
    destination = Path(args.report)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(report, sort_keys=True, separators=(",", ":")), encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
