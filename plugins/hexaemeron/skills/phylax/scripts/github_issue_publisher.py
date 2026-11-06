#!/usr/bin/env python3
"""Closed offline conformance and read-only deployment predicate commands."""
import sys
from github_issue_publisher_lib.canonical import canonical_json
from github_issue_publisher_lib.errors import PublisherError


def main(argv=None):
    arguments = sys.argv[1:] if argv is None else argv
    try:
        if arguments and arguments[0] == "conformance":
            from github_issue_publisher_lib.conformance import run_command
            return run_command(arguments)
        if len(arguments) == 5 and arguments[0:2] == ["check-deployment", "--caller"] and arguments[3] == "--release-sha256":
            from github_issue_publisher_lib.deployment import check_deployment
            result = check_deployment(caller=arguments[2], release_sha256=arguments[4])
            sys.stdout.buffer.write(canonical_json(result) + b"\n")
            return 0 if result["outcome"] == "passed" else 1
        raise PublisherError("GIP199", "cli.arguments")
    except Exception:
        sys.stderr.buffer.write(canonical_json(PublisherError("GIP199", "cli.arguments").diagnostic()) + b"\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
