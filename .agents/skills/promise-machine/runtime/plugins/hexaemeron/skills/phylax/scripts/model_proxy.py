#!/usr/bin/env python3
"""Check the credential-free model proxy policy, framing, and provider boundaries."""

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
from model_proxy_lib.framing import check_framing_manifest
from model_proxy_lib.provider import PROVIDER_MANIFEST_SCHEMA, check_provider_manifest


class _DiagnosticArgumentParser(argparse.ArgumentParser):
    """Refuse malformed argv without retaining argparse's value-bearing text."""

    def error(self, _message: str) -> None:
        raise PolicyError("MP122", "cli.arguments")


def _parser() -> argparse.ArgumentParser:
    parser = _DiagnosticArgumentParser(description=__doc__, allow_abbrev=False)
    commands = parser.add_subparsers(dest="command", required=True)
    compile_command = commands.add_parser(
        "compile-policy",
        help="compile one accepted-job evidence file",
        allow_abbrev=False,
    )
    compile_command.add_argument("--accepted-job", required=True, metavar="PATH")
    compile_command.add_argument("--expect", metavar="PATH")
    frame_command = commands.add_parser(
        "check-frames",
        help="check bounded request and response frame vectors",
        allow_abbrev=False,
    )
    frame_command.add_argument("--manifest", required=True, metavar="PATH")
    provider_command = commands.add_parser(
        "provider-demo",
        help="check injected provider mapping and response vectors",
        allow_abbrev=False,
    )
    provider_command.add_argument("--manifest", required=True, metavar="PATH")
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


def _check_frames(arguments: argparse.Namespace) -> int:
    result = check_framing_manifest(arguments.manifest)
    sys.stdout.buffer.write(
        canonical_json(
            {
                "schema": DIAGNOSTIC_SCHEMA,
                "outcome": "frames_checked",
                "manifest_schema": "model-proxy-framing-cases/v1",
                "cases": result.cases,
                "requests": result.requests,
                "policy_sha256": result.policy_sha256,
            }
        )
        + b"\n"
    )
    return 0


def _provider_demo(arguments: argparse.Namespace) -> int:
    result = check_provider_manifest(arguments.manifest)
    sys.stdout.buffer.write(
        canonical_json(
            {
                "schema": DIAGNOSTIC_SCHEMA,
                "outcome": "provider_checked",
                "manifest_schema": PROVIDER_MANIFEST_SCHEMA,
                "cases": result.cases,
                "requests": result.requests,
                "policy_sha256": result.policy_sha256,
            }
        )
        + b"\n"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    try:
        arguments = _parser().parse_args(argv)
        if arguments.command == "compile-policy":
            return _compile(arguments)
        if arguments.command == "check-frames":
            return _check_frames(arguments)
        if arguments.command == "provider-demo":
            return _provider_demo(arguments)
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
