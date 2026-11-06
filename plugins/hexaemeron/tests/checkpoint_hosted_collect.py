#!/usr/bin/env python3
"""Collect real checkpoint conformance streams on one declared Actions runner."""
import argparse
import json
from pathlib import Path
import checkpoint_hosted_evidence as hosted


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--profile", choices=tuple(hosted.PROFILES), required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    try:
        result = hosted.collect(hosted.ROOT, args.profile, Path(args.out))
        print(json.dumps({"event": "checkpoint_hosted_collected", "profile": args.profile,
                          "checkout_sha": result["checkout_sha"], "run_id": result["run_id"],
                          "run_attempt": result["run_attempt"], "complete": True}, sort_keys=True))
        return 0
    except (hosted.owner.Refusal, hosted.NativeRefusal, OSError, ValueError, KeyError, TypeError) as error:
        code = str(error) if isinstance(error, hosted.owner.Refusal) else (
            error.code if isinstance(error, hosted.NativeRefusal) else "collection-unavailable")
        print(json.dumps({"event": "checkpoint_hosted_refused", "profile": args.profile,
                          "complete": False, "code": code}, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
