#!/usr/bin/env python3
"""Run one Janus invariant fuzz campaign, under Echidna or under Medusa.

The single positional argument names the engine. The launcher runs that
engine with a pinned argv and no shell, from the harness directory resolved
relative to this file, so a campaign does not depend on the caller's cwd.

Medusa's compilation target must be an absolute path: crytic-compile's
Foundry platform compares it against the resolved project root and a relative
target raises FileNotFoundError. An absolute path is machine-specific and so
is not committed. `adapters/medusa/medusa.json` therefore carries an empty
target, and this launcher renders a complete config into a temporary file at
run time, leaving the committed config untouched.

Rendering into a temporary file moves the config away from the harness, and
Medusa resolves `corpusDirectory` relative to the config rather than to the
working directory -- so the corpus is absolutised here too. Without that the
campaign still runs and still reports the configured relative path, but the
corpus is written beside the temporary config and lost with it.

Echidna needs no such treatment: it accepts the suite path as its argument.

Both engines are pointed at the suite file rather than at the project,
because the harness keeps its fuzz adapter outside `src` and `test` and
crytic-compile skips `./test/**` on the Foundry platform.

Neither engine is run concurrently with the other; each invocation runs one.
The launcher's exit code is the engine's exit code.

A non-zero exit is expected here, and it is not a regression. Neither Echidna
2.3.3 nor Medusa 1.5.1 implements the `keyExistsJson`, `parseJsonUint` and
`parseJsonString` cheatcodes `ManifestReader` is built on: the cheatcode
address carries code under both, but a call to `keyExistsJson(string,string)`
fails, so every manifest the suite generates reverts with empty return data
before the reader resolves anything. Property `GL00` in the suite says exactly
that and fails, which is the point -- `GL01` to `GL08` are negated ghost flags
set only after a successful resolve, so without GL00 a campaign that resolves
nothing reports eight green ticks and no evidence. The properties are asserted
where they can actually fail by `ManifestFuzzInvariantTest` in
`harness/test/ManifestReader.t.sol`, under Foundry's invariant engine, which
does carry the cheatcodes. Run these campaigns to see whether either engine
has gained JSON cheatcode support; read `forge test` for the invariant result.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HARNESS_DIR = Path(__file__).resolve().parent.parent / "harness"

SUITE = Path("adapters") / "ManifestFuzz.sol"
CONTRACT = "ManifestFuzz"
ECHIDNA_CONFIG = Path("adapters") / "echidna" / "echidna.yaml"
MEDUSA_CONFIG = Path("adapters") / "medusa" / "medusa.json"

ENGINES = ("echidna", "medusa")


def _run(argv: list[str]) -> int:
    completed = subprocess.run(argv, cwd=HARNESS_DIR, check=False)
    return completed.returncode


def _run_echidna() -> int:
    return _run(
        [
            "echidna",
            str(SUITE),
            "--contract",
            CONTRACT,
            "--config",
            str(ECHIDNA_CONFIG),
            "--format",
            "text",
        ]
    )


def _run_medusa() -> int:
    committed = HARNESS_DIR / MEDUSA_CONFIG
    try:
        config = json.loads(committed.read_text())
    except (OSError, ValueError) as error:
        print(f"cannot read {MEDUSA_CONFIG}: {error}", file=sys.stderr)
        return 1

    platform = config.get("compilation", {}).get("platformConfig")
    if not isinstance(platform, dict):
        print(f"{MEDUSA_CONFIG} has no compilation.platformConfig", file=sys.stderr)
        return 1

    suite = HARNESS_DIR / SUITE
    if not suite.is_file():
        print(f"suite not found: {suite}", file=sys.stderr)
        return 1
    platform["target"] = str(suite)

    fuzzing = config.get("fuzzing")
    if not isinstance(fuzzing, dict):
        print(f"{MEDUSA_CONFIG} has no fuzzing section", file=sys.stderr)
        return 1
    corpus = fuzzing.get("corpusDirectory")
    if not isinstance(corpus, str) or not corpus:
        print(f"{MEDUSA_CONFIG} has no fuzzing.corpusDirectory", file=sys.stderr)
        return 1
    fuzzing["corpusDirectory"] = str(HARNESS_DIR / corpus)

    # A temporary config, so the committed one keeps its empty target and the
    # working tree stays clean across a campaign.
    with tempfile.TemporaryDirectory() as scratch:
        rendered = Path(scratch) / "medusa.json"
        rendered.write_text(json.dumps(config, indent=2) + "\n")
        return _run(["medusa", "fuzz", "--config", str(rendered)])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("engine", choices=ENGINES, help="the fuzzing engine to run")
    args = parser.parse_args(argv)

    if args.engine == "echidna":
        return _run_echidna()
    return _run_medusa()


if __name__ == "__main__":
    sys.exit(main())
