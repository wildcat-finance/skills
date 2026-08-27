#!/usr/bin/env python3
"""Explicit network and offline command boundary for Compound III Phase 0."""

import argparse
import os
from pathlib import Path
import sys
import tempfile

from alexandria_lib.canonical import canonical_bytes
from alexandria_lib.compound_phase0 import build, capture, check_phase0
from alexandria_lib.compound_registry import registry_bytes
from alexandria_lib.errors import AlexandriaError


def parser():
    value = argparse.ArgumentParser(description="Capture and verify the bounded Compound III Phase 0 corpus.")
    commands = value.add_subparsers(dest="command", metavar="{registry,capture,build,check}")
    registry = commands.add_parser("registry", help="generate the pinned 28-market Comet registry")
    registry.add_argument("--comet-repository", required=True, type=Path)
    registry.add_argument("--output", required=True, type=Path)
    capture_parser = commands.add_parser("capture", help="capture the fixed corpus from the explicit RPC endpoint")
    capture_parser.add_argument("--registry", required=True, type=Path)
    capture_parser.add_argument("--corpus", required=True, type=Path)
    capture_parser.add_argument("--comet-repository", required=True, type=Path)
    capture_parser.add_argument("--output", required=True, type=Path)
    build_parser = commands.add_parser("build", help="ingest and verify a captured source directory offline")
    build_parser.add_argument("--input", required=True, type=Path)
    build_parser.add_argument("--output", required=True, type=Path)
    check = commands.add_parser("check", help="verify the Compound method release offline")
    check.add_argument("release", type=Path)
    return value


def main(argv=None):
    value = parser()
    args = value.parse_args(argv)
    if args.command is None:
        value.print_help(sys.stderr)
        return 2
    try:
        if args.command == "registry":
            data = registry_bytes(args.comet_repository)
            output = args.output.absolute()
            output.parent.mkdir(parents=True, exist_ok=True)
            if output.exists() or output.is_symlink():
                raise AlexandriaError("registry output already exists")
            descriptor, temporary_name = tempfile.mkstemp(
                dir=output.parent, prefix=f".{output.name}.", suffix=".tmp"
            )
            try:
                with os.fdopen(descriptor, "wb") as handle:
                    descriptor = None
                    handle.write(data)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temporary_name, output)
                temporary_name = None
            finally:
                if descriptor is not None:
                    os.close(descriptor)
                if temporary_name is not None:
                    Path(temporary_name).unlink(missing_ok=True)
            print(args.output)
        elif args.command == "capture":
            capture(args.registry, args.corpus, args.comet_repository, args.output)
            print(args.output)
        elif args.command == "build":
            print(build(args.input, args.output))
        elif args.command == "check":
            sys.stdout.buffer.write(canonical_bytes(check_phase0(args.release)))
        return 0
    except (AlexandriaError, OSError) as error:
        print(f"compound-v3-phase0: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
