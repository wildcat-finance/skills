#!/usr/bin/env python3
"""Run the study's demo path and record its three observations.

Runs study.md section 1's "Working prototype" items 1 to 4 as fixed local
commands against ``--root`` (no shell, no network): the standing `measure`
action in both forms, its `--require-margin` gate, the over-the-line
`package` refusal, and the isolated-copy verification chain (verify_runtime,
the installed Horos check, the packaged evaluation check). Every disposable
checkout and generated package this script needs is a local, no-network git
clone or copy written under the system temporary directory; the only file it
writes outside that directory is the caller-named ``--out`` record.

Exit 0 once every observation matched what the study describes; exit 1 and
write nothing if a command's outcome differs from what was expected (Elenchus:
a demo command that fails is worked to its cause before any record is
written, not papered over in the output).
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath

SCHEMA = "portable-payload-demonstration/v1"
CONTROLLER = "Fiat"
GENERATOR = "scripts/portable_promise_machine.py"
REQUIRE_MARGIN = 794493
# Added to a fresh checkout's own current margin so the filler always pushes
# it past the line by a known, small amount, however that margin has moved.
OVER_LINE_CUSHION = 4096
# The installed layout PORTABLE.md documents as the package's public contract.
INSTALLED_PROMISE_MACHINE = PurePosixPath(".agents/skills/promise-machine")
INSTALLED_RUNTIME = INSTALLED_PROMISE_MACHINE / "runtime"
INSTALLED_VERIFY_RUNTIME = INSTALLED_PROMISE_MACHINE / "scripts/verify_runtime.py"
INSTALLED_HOROS = INSTALLED_RUNTIME / "plugins/horos/skills/horos/scripts/horos.py"
INSTALLED_PROMISE_MACHINE_PY = INSTALLED_RUNTIME / "scripts/promise_machine.py"
INSTALLED_MANIFEST = INSTALLED_RUNTIME / "MANIFEST.json"
FILLER_RELATIVE = PurePosixPath("plugins/_portable_payload_demo_filler/FILLER.bin")
SCRATCH_TOKEN = "<scratch>"


class DemoError(RuntimeError):
    """An observation did not match what the study's demo path describes."""


def _redact(text: str, scratch: Path) -> str:
    return text.replace(str(scratch), SCRATCH_TOKEN)


def _display_path(path: Path, root: Path, scratch: Path) -> str:
    """A stable, portable label for an absolute path used in a recorded argv."""
    for base, prefix in ((root, ""), (scratch, SCRATCH_TOKEN + "/")):
        try:
            relative = path.resolve().relative_to(base.resolve())
        except ValueError:
            continue
        return prefix + relative.as_posix() if relative.parts else prefix.rstrip("/")
    return _redact(str(path), scratch)


def _invoke(
    real_argv: list[str], display_argv: list[str], *, cwd: Path, scratch: Path,
) -> tuple[subprocess.CompletedProcess, list[str]]:
    """Run one fixed local command (no shell) and return it with a record."""
    env = dict(os.environ)
    env["NO_COLOR"] = "1"
    result = subprocess.run(  # phylax: allow subprocess: fixed local argv list, no shell, no network
        real_argv, cwd=str(cwd), capture_output=True, text=True, env=env,
    )
    return result, display_argv


def _step(label: str, display_argv: list[str], result: subprocess.CompletedProcess,
          relied_on_output_lines: list[str], **extra) -> dict:
    entry = {
        "label": label,
        "argv": display_argv,
        "exit_code": result.returncode,
        "relied_on_output_lines": relied_on_output_lines,
    }
    entry.update(extra)
    return entry


def _text_lines(result: subprocess.CompletedProcess, scratch: Path, limit: int) -> list[str]:
    text = result.stdout if result.stdout.strip() else result.stderr
    return [_redact(line, scratch) for line in text.strip().splitlines()[:limit]]


def _json_lines(measurement: dict, *keys: str) -> list[str]:
    """A compact, faithful restatement of the named sub-objects of one parsed reply."""
    lines = []
    for key in keys:
        lines.append(json.dumps({key: measurement[key]}, sort_keys=True))
    return lines


def measure_positive(python: str, root: Path, scratch: Path) -> tuple[dict, dict, list[dict]]:
    """Items 1, 2 (positive) and 4: the delivered tree, its margin, its package."""
    steps = []
    generator = root / GENERATOR

    text_argv = [python, GENERATOR, "measure"]
    result, display = _invoke([python, str(generator), "measure"], text_argv, cwd=root, scratch=scratch)
    if result.returncode != 0:
        raise DemoError(f"measure exited {result.returncode} on the delivered tree: {result.stderr}")
    steps.append(_step("measure", display, result, _text_lines(result, scratch, 5)))

    json_argv = [python, GENERATOR, "measure", "--json"]
    result, display = _invoke(
        [python, str(generator), "measure", "--json"], json_argv, cwd=root, scratch=scratch,
    )
    if result.returncode != 0:
        raise DemoError(f"measure --json exited {result.returncode} on the delivered tree: {result.stderr}")
    measurement = json.loads(result.stdout)
    measure_json_step = _step(
        "measure --json", display, result, _json_lines(measurement, "package", "runtime"),
    )
    steps.append(measure_json_step)

    package_dir = scratch / "package"
    package_argv = [python, GENERATOR, "package", "--out", "<scratch>/package"]
    result, display = _invoke(
        [python, str(generator), "package", "--out", str(package_dir)],
        package_argv, cwd=root, scratch=scratch,
    )
    if result.returncode != 0:
        raise DemoError(f"package --out exited {result.returncode} on the delivered tree: {result.stderr}")
    steps.append(_step("package --out", display, result, _text_lines(result, scratch, 1)))

    walked_files = [p for p in package_dir.rglob("*") if p.is_file()]
    walked_bytes = sum(p.stat().st_size for p in walked_files)
    manifest = json.loads((package_dir / INSTALLED_MANIFEST).read_bytes())
    agrees = (
        measurement["package"]["bytes"] == walked_bytes
        and measurement["package"]["files"] == len(walked_files)
        and measurement["runtime"]["bytes"] == manifest["total_bytes"]
        and measurement["runtime"]["files"] == manifest["file_count"]
    )
    measure_json_step["agrees_with_package_walk"] = {
        "measured": {
            "package_bytes": measurement["package"]["bytes"],
            "package_files": measurement["package"]["files"],
            "runtime_bytes": measurement["runtime"]["bytes"],
            "runtime_files": measurement["runtime"]["files"],
        },
        "walked": {
            "package_bytes": walked_bytes,
            "package_files": len(walked_files),
            "runtime_bytes_from_manifest": manifest["total_bytes"],
            "runtime_files_from_manifest": manifest["file_count"],
        },
        "equal": agrees,
    }
    if not agrees:
        raise DemoError("measure --json figures do not agree with a walk of package --out / its MANIFEST.json")

    margin_argv = [python, GENERATOR, "measure", "--require-margin", str(REQUIRE_MARGIN)]
    result, display = _invoke(
        [python, str(generator), "measure", "--require-margin", str(REQUIRE_MARGIN)],
        margin_argv, cwd=root, scratch=scratch,
    )
    if result.returncode != 0:
        raise DemoError(
            f"measure --require-margin {REQUIRE_MARGIN} exited {result.returncode} on the delivered tree: "
            f"{result.stderr}"
        )
    steps.append(_step(f"measure --require-margin {REQUIRE_MARGIN}", display, result, _text_lines(result, scratch, 5)))

    verify_argv = [python, str(_display_path(package_dir / INSTALLED_VERIFY_RUNTIME, root, scratch))]
    result, display = _invoke(
        [python, str(package_dir / INSTALLED_VERIFY_RUNTIME)], verify_argv, cwd=package_dir, scratch=scratch,
    )
    if result.returncode != 0:
        raise DemoError(f"verify_runtime.py exited {result.returncode} on the isolated copy: {result.stderr}")
    steps.append(_step("verify_runtime.py (isolated copy)", display, result, _text_lines(result, scratch, 1)))

    horos_argv = [
        python, str(_display_path(package_dir / INSTALLED_HOROS, root, scratch)),
        "check", str(_display_path(package_dir / INSTALLED_RUNTIME, root, scratch)),
    ]
    result, display = _invoke(
        [python, str(package_dir / INSTALLED_HOROS), "check", str(package_dir / INSTALLED_RUNTIME)],
        horos_argv, cwd=package_dir, scratch=scratch,
    )
    if result.returncode != 0:
        raise DemoError(f"the installed Horos check exited {result.returncode}: {result.stderr}")
    steps.append(_step("installed Horos check (isolated copy)", display, result, _text_lines(result, scratch, 1)))

    evaluation_argv = [
        python, str(_display_path(package_dir / INSTALLED_PROMISE_MACHINE_PY, root, scratch)),
        "check", "--only", "evaluation",
    ]
    result, display = _invoke(
        [python, str(package_dir / INSTALLED_PROMISE_MACHINE_PY), "check", "--only", "evaluation"],
        evaluation_argv, cwd=(package_dir / INSTALLED_RUNTIME), scratch=scratch,
    )
    if result.returncode != 0:
        raise DemoError(f"the packaged evaluation check exited {result.returncode}: {result.stderr}")
    steps.append(_step("packaged evaluation check (isolated copy)", display, result, _text_lines(result, scratch, 1)))

    exit_codes = sorted({item["exit_code"] for item in steps})
    observation = {
        "id": "positive",
        "claim": (
            "On the delivered tree, measure exits 0 in both forms and its --json "
            "figures agree with a walk of package --out and that package's "
            "MANIFEST.json; measure --require-margin exits 0; and in an isolated "
            "copy of the generated package, verify_runtime.py, the installed "
            "Horos check and the packaged evaluation check each exit 0."
        ),
        "exit_codes": exit_codes,
        "steps": steps,
    }
    return observation, measurement, steps


def _clean_clone(python: str, root: Path, scratch: Path) -> Path:
    checkout = scratch / "checkout"
    result = subprocess.run(  # phylax: allow subprocess: fixed local argv, local clone, no network
        ["git", "clone", "--local", "--quiet", "--no-hardlinks", str(root), str(checkout)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise DemoError(f"could not build the disposable checkout: {result.stderr}")
    return checkout


def _stage_filler(python: str, generator: Path, checkout: Path) -> None:
    result = subprocess.run(  # phylax: allow subprocess: fixed local argv, no shell
        [python, str(generator), "measure", "--json"],
        cwd=str(checkout), capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise DemoError(f"could not measure the disposable checkout before staging filler: {result.stderr}")
    margin = json.loads(result.stdout)["package"]["margin"]
    filler_size = max(margin, 0) + OVER_LINE_CUSHION
    filler_path = checkout / FILLER_RELATIVE
    filler_path.parent.mkdir(parents=True, exist_ok=True)
    with filler_path.open("wb") as handle:
        handle.write(b"\0" * filler_size)
    result = subprocess.run(  # phylax: allow subprocess: fixed local argv, no shell
        ["git", "add", "--", FILLER_RELATIVE.as_posix()],
        cwd=str(checkout), capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise DemoError(f"could not stage the filler file: {result.stderr}")


def measure_negative(python: str, root: Path, scratch: Path) -> tuple[dict, dict]:
    """Items 2 (negative) and 3: a disposable checkout pushed over the line."""
    generator_relative = GENERATOR
    checkout = _clean_clone(python, root, scratch)
    generator = checkout / generator_relative
    _stage_filler(python, generator, checkout)

    margin_argv = [python, generator_relative, "measure", "--require-margin", str(REQUIRE_MARGIN)]
    result, display = _invoke(
        [python, str(generator), "measure", "--require-margin", str(REQUIRE_MARGIN)],
        margin_argv, cwd=checkout, scratch=scratch,
    )
    if result.returncode != 1:
        raise DemoError(
            f"measure --require-margin {REQUIRE_MARGIN} exited {result.returncode}, not 1, "
            f"on the over-the-line checkout: {result.stderr}"
        )
    first_negative = {
        "id": "first-negative",
        "claim": (
            "On a disposable checkout pushed over the line by one staged filler "
            "file under plugins/, measure --require-margin exits 1 and names the "
            "margin."
        ),
        "exit_codes": [result.returncode],
        "steps": [
            _step(
                f"measure --require-margin {REQUIRE_MARGIN} (over-the-line checkout)",
                display, result, _text_lines(result, scratch, 3),
            )
        ],
    }
    if str(REQUIRE_MARGIN) not in (result.stdout + result.stderr) or "margin" not in (result.stdout + result.stderr):
        raise DemoError("the require-margin refusal did not name the required margin")

    json_argv = [python, generator_relative, "measure", "--json"]
    json_result, json_display = _invoke(
        [python, str(generator), "measure", "--json"], json_argv, cwd=checkout, scratch=scratch,
    )
    if json_result.returncode != 0:
        raise DemoError(
            f"measure --json exited {json_result.returncode}, not 0, on the "
            f"over-the-line checkout: {json_result.stderr}"
        )
    over_line_measurement = json.loads(json_result.stdout)
    if over_line_measurement["package"]["margin"] >= 0:
        raise DemoError("the over-the-line checkout did not carry a negative package margin")

    package_dir = scratch / "checkout-package"
    package_argv = [python, generator_relative, "package", "--out", "<scratch>/checkout-package"]
    package_result, package_display = _invoke(
        [python, str(generator), "package", "--out", str(package_dir)],
        package_argv, cwd=checkout, scratch=scratch,
    )
    if package_result.returncode != 1:
        raise DemoError(
            f"package --out exited {package_result.returncode}, not 1, on the "
            f"over-the-line checkout: {package_result.stdout}"
        )
    refusal = _redact(package_result.stdout + package_result.stderr, scratch)
    line = over_line_measurement["line"]
    for required in (str(line), "margin", "measure"):
        if required not in refusal:
            raise DemoError(f"the package refusal did not name {required!r}: {refusal!r}")

    second_negative = {
        "id": "second-negative",
        "claim": (
            "On the same over-the-line checkout, measure still exits 0 with a "
            "negative margin while package --out exits 1, refusing and naming "
            "bytes, the line, the margin and the measure action."
        ),
        "exit_codes": sorted({json_result.returncode, package_result.returncode}),
        "steps": [
            _step(
                "measure --json (over-the-line checkout)", json_display, json_result,
                _json_lines(over_line_measurement, "package"),
            ),
            _step(
                "package --out (over-the-line checkout)", package_display, package_result,
                [line.strip() for line in refusal.strip().splitlines()],
            ),
        ],
    }
    return first_negative, second_negative


def run_demo(root: Path) -> dict:
    python = "python3"
    with tempfile.TemporaryDirectory(prefix="portable-payload-demo.") as raw_scratch:
        scratch = Path(raw_scratch).resolve()
        positive, _measurement, _steps = measure_positive(python, root, scratch)
        first_negative, second_negative = measure_negative(python, root, scratch)
    return {
        "schema": SCHEMA,
        "controller": CONTROLLER,
        "source_command": GENERATOR,
        "observations": [positive, first_negative, second_negative],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, help="repository root to demonstrate")
    parser.add_argument("--out", required=True, help="path to write the demonstration record to")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    out = Path(args.out)
    try:
        record = run_demo(root)
    except DemoError as error:
        print(f"portable payload demonstration failed: {error}", file=sys.stderr)
        return 1
    out.write_text(json.dumps(record, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    print(f"wrote {len(record['observations'])} observations to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
