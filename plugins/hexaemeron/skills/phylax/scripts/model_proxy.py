#!/usr/bin/env python3
"""Compile a digest-bound accepted job into a credential-free proxy policy."""

from __future__ import annotations

import argparse
import sys

from model_proxy_lib import (
    DIAGNOSTIC_SCHEMA,
    POLICY_SCHEMA,
    PolicyError,
    canonical_json,
    compile_policy_file,
    verify_golden,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    compile_command = commands.add_parser(
        "compile-policy", help="compile one accepted-job evidence file"
    )
    compile_command.add_argument("--accepted-job", required=True, metavar="PATH")
    compile_command.add_argument("--expect", metavar="PATH")
    return parser


def _write_diagnostic(value: dict[str, str]) -> None:
    sys.stderr.buffer.write(canonical_json(value) + b"\n")


def _compile(arguments: argparse.Namespace) -> int:
    result = compile_policy_file(arguments.accepted_job)
    if arguments.expect is not None:
        verify_golden(result, arguments.expect)
    sys.stdout.buffer.write(result.policy_bytes + b"\n")
    _write_diagnostic(
        {
            "schema": DIAGNOSTIC_SCHEMA,
            "outcome": "compiled",
            "policy_schema": POLICY_SCHEMA,
            "profile": result.profile,
            "jobspec_sha256": result.jobspec_sha256,
            "policy_sha256": result.policy_sha256,
        }
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    try:
        if arguments.command == "compile-policy":
            return _compile(arguments)
    except PolicyError as error:
        _write_diagnostic(error.diagnostic())
        return 2
    except (OSError, RuntimeError, TypeError, ValueError):
        _write_diagnostic(
            {
                "schema": DIAGNOSTIC_SCHEMA,
                "outcome": "refused",
                "code": "MP199",
                "field": "compiler.internal",
            }
        )
        return 3
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
