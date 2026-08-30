"""The suite has one Python contract and one exact execution image.

The repository runs every Python workflow on the exact patch in
``.python-version`` and keeps the durable minor contract in ``pyproject.toml``.
Current runtime prose points to those files instead of carrying another
interpreter claim. Historical evidence keeps the versions it actually
observed.

The dependency half of this gate is deliberately narrower than a package
audit. It proves that every declared Lazarus dependency is an exact pin, that
the lock contains the same direct pin, and that CI installs the lock rather
than resolving the direct requirements again. It does not claim that the
packages are trustworthy or free of advisories.
"""

from pathlib import Path
import json
import re
import sys
import tomllib
import unittest


ROOT = Path(__file__).resolve().parents[1]
PYTHON_VERSION = ROOT / ".python-version"
PYPROJECT = ROOT / "pyproject.toml"
WORKFLOWS = ROOT / ".github" / "workflows"
README = ROOT / "README.md"
LAZARUS = ROOT / "plugins" / "lazarus"

REQUIRED_MINOR = "==3.14.*"
EXACT_VERSION = "3.14.6"
PYTHON_WORKFLOWS = {
    "contributors.yml",
    "dead-code.yml",
    "janus.yml",
    "lazarus.yml",
    "pandects.yml",
    "plugins.yml",
    "repo.yml",
    "synkrisis.yml",
}
PULL_REQUEST_WORKFLOWS = PYTHON_WORKFLOWS - {"contributors.yml"}
# Required gates carry no path filter, so they have no filter to inspect.
UNFILTERED_GATES = {"plugins.yml", "repo.yml"}
PATH_FILTERED_PULL_REQUEST_WORKFLOWS = PULL_REQUEST_WORKFLOWS - UNFILTERED_GATES
BRANCH_CI_WORKFLOWS = PULL_REQUEST_WORKFLOWS | {
    "janus-forge.yml",
    "pandects-forge.yml",
}
PLUGIN_WORKFLOW_PATHS = {
    "janus.yml": {
        "plugins/janus/**",
        ".python-version",
        "pyproject.toml",
        ".github/workflows/janus.yml",
    },
    "lazarus.yml": {
        "plugins/lazarus/**",
        "docs/lazarus-multi-provider-chain-anchor/**",
        "docs/lazarus-receipt-inclusion-proofs/**",
        "docs/decisions/ADR-037-prove-receipts-with-a-full-ordered-witness.md",
        ".python-version",
        "pyproject.toml",
        ".github/workflows/lazarus.yml",
    },
    "pandects.yml": {
        "plugins/pandects/**",
        ".python-version",
        "pyproject.toml",
        ".github/workflows/pandects.yml",
    },
    "synkrisis.yml": {
        "plugins/synkrisis/**",
        "docs/synkrisis/**",
        "scripts/run_observation.py",
        ".python-version",
        "pyproject.toml",
        ".github/workflows/synkrisis.yml",
    },
}
DEPENDENCY_FILES = {
    "plugins/lazarus/requirements.lock",
    "plugins/lazarus/requirements.txt",
}
PIN_REFERENCING_PROSE = {
    "AGENTS.md",
    "README.md",
    "docs/decisions/ADR-038-pin-the-python-suite-to-one-interpreter.md",
    "docs/decisions/ADR-042-advance-the-python-suite-to-3-14.md",
    "plugins/ariadne/docs/design.md",
    "plugins/berean/README.md",
    "plugins/berean/skills/berean/SKILL.md",
    "plugins/brevitas/AGENTS.md",
    "plugins/hermes/AGENTS.md",
    "plugins/hexaemeron/skills/elenchus/SKILL.md",
    "plugins/hexaemeron/skills/protasis/SKILL.md",
    "plugins/janus/README.md",
    "plugins/lazarus/README.md",
    "plugins/lemma/AGENTS.md",
    "plugins/lemma/README.md",
    "plugins/pandects/docs/design.md",
    "plugins/probitas/README.md",
    "plugins/probitas/docs/adding-a-venue.md",
    "plugins/tabularium/README.md",
}
EXACT_PIN = re.compile(
    r"(?P<name>[a-z0-9]+(?:[-_.][a-z0-9]+)*)"
    r"(?P<extras>\[[a-z0-9,-]+\])?=="
    r"(?P<version>\d+\.\d+\.\d+)"
)
RUNTIME_VERSION_CLAIM = re.compile(
    r"(?i)(?:\b(?:cpython|python)\s+(?:version(?:s)?\b|3(?:\.\d+){0,2}\b)"
    r"|\bsupported\s+python\s+versions\b"
    r"|\buv\s+run\s+--python\s+3(?:\.\d+){1,2}\b)"
)


def exact_pins(text, source):
    """Return normalised package names and refuse every non-exact line."""
    pins = {}
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        match = EXACT_PIN.fullmatch(line)
        if match is None:
            raise ValueError(f"{source}:{number}: not an exact package pin: {line}")
        name = re.sub(r"[-_.]+", "-", match.group("name")).lower()
        if name in pins:
            raise ValueError(f"{source}:{number}: duplicate package pin: {name}")
        pins[name] = line
    if not pins:
        raise ValueError(f"{source}: no package pins")
    return pins


def dependency_drift(direct_text, lock_text):
    """Name direct pins absent from, or different in, the resolved lock."""
    direct = exact_pins(direct_text, "requirements.txt")
    locked = exact_pins(lock_text, "requirements.lock")
    return {
        name: {"direct": pin, "locked": locked.get(name)}
        for name, pin in direct.items()
        if locked.get(name) != pin
    }


def workflow_event_body(source, event):
    """Return one event mapping without parsing GitHub's YAML extensions."""
    match = re.search(
        rf"(?ms)^  {re.escape(event)}:\n(?P<body>.*?)(?=^  [a-z_]+:|\Z)",
        source,
    )
    if match is None:
        raise ValueError(f"workflow has no {event} event")
    return match["body"]


def workflow_event_paths(source, event):
    """Return the quoted path filters from one workflow event."""
    body = workflow_event_body(source, event)
    match = re.search(
        r"(?m)^    paths:\n(?P<paths>(?:      - .+\n)+)",
        body,
    )
    if match is None:
        raise ValueError(f"workflow {event} event has no paths")
    return set(re.findall(r'^      - "([^"]+)"$', match["paths"], re.M))


def workflow_event_branches(source, event):
    """Return the quoted or plain branch filters from one workflow event."""
    body = workflow_event_body(source, event)
    match = re.search(
        r"(?m)^    branches:\n(?P<branches>(?:      - .+\n)+)",
        body,
    )
    if match is None:
        return set()
    return set(
        value.strip('"')
        for value in re.findall(r"^      - (.+)$", match["branches"], re.M)
    )


def is_current_runtime_prose(path):
    """Exclude immutable evidence, receipted records, fixtures, and vendored skills."""
    relative = path.relative_to(ROOT)
    parts = relative.parts
    name = relative.name.lower()
    if parts[:4] == (".agents", "skills", "promise-machine", "runtime"):
        return False
    if "audit" in parts or "baseline" in parts:
        return False
    if "tests" in parts and "fixtures" in parts:
        return False
    if name in {"evolution.md", "promise_machine.md"}:
        return False
    if name in {"study.md", "runbook.md", "proof.md", "benchmark.md"}:
        return False
    if name.endswith(("-study.md", "-runbook.md", "-proof.md", "-benchmark.md")):
        return False
    if parts[:3] == ("docs", "promise-machine", "evidence"):
        return False
    vendored = (
        ("plugins", "hexaemeron", "skills", "fizz"),
        ("plugins", "hexaemeron", "skills", "solidity-auditor"),
        ("plugins", "hexaemeron", "skills", "x-ray"),
    )
    return not any(parts[: len(prefix)] == prefix for prefix in vendored)


class PythonRuntimeContractTests(unittest.TestCase):
    def test_durable_minor_contract_is_exact(self):
        document = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
        self.assertEqual(
            document,
            {
                "project": {
                    "name": "wildcat-skills",
                    "version": "0",
                    "requires-python": REQUIRED_MINOR,
                }
            },
        )

    def test_exact_execution_pin_is_exact_and_matches_the_minor(self):
        raw = PYTHON_VERSION.read_bytes()
        self.assertEqual(raw, (EXACT_VERSION + "\n").encode("ascii"))
        major, minor, patch = (int(part) for part in EXACT_VERSION.split("."))
        self.assertEqual(REQUIRED_MINOR, f"=={major}.{minor}.*")
        self.assertGreaterEqual(patch, 0)

    def test_the_suite_is_running_on_the_exact_cpython_image(self):
        expected = tuple(int(part) for part in EXACT_VERSION.split("."))
        self.assertEqual(sys.implementation.name, "cpython")
        self.assertEqual(
            sys.version_info[:3],
            expected,
            f"run the suite with the CPython pin in {PYTHON_VERSION}",
        )

    def test_every_python_workflow_reads_the_exact_pin(self):
        found = set()
        invokes_python = set()
        for path in sorted(WORKFLOWS.glob("*.yml")):
            text = path.read_text(encoding="utf-8")
            command_lines = [
                line
                for line in text.splitlines()
                if not line.lstrip().startswith("#")
                and "actions/setup-python@" not in line
                and "python-version" not in line
            ]
            if any(
                re.search(r"\bpython(?:3(?:\.\d+)*)?\b", line)
                for line in command_lines
            ):
                invokes_python.add(path.name)
            setup_count = text.count("uses: actions/setup-python@")
            if not setup_count:
                continue
            found.add(path.name)
            with self.subTest(workflow=path.name):
                self.assertEqual(
                    text.count('python-version-file: ".python-version"'),
                    setup_count,
                )
                self.assertNotRegex(text, r"(?m)^\s+python-version:")
                self.assertNotIn("matrix.python-version", text)
        self.assertEqual(found, PYTHON_WORKFLOWS)
        self.assertEqual(invokes_python, found)

    def test_pull_request_workflows_run_when_either_contract_file_changes(self):
        for name in sorted(PATH_FILTERED_PULL_REQUEST_WORKFLOWS):
            text = (WORKFLOWS / name).read_text(encoding="utf-8")
            with self.subTest(workflow=name):
                self.assertEqual(text.count('- ".python-version"'), 2)
                self.assertEqual(text.count('- "pyproject.toml"'), 2)

    def test_feature_pushes_do_not_duplicate_pull_request_runs(self):
        for name in sorted(BRANCH_CI_WORKFLOWS):
            text = (WORKFLOWS / name).read_text(encoding="utf-8")
            with self.subTest(workflow=name):
                self.assertEqual(workflow_event_branches(text, "push"), {"main"})
                self.assertNotIn(
                    "    branches:", workflow_event_body(text, "pull_request")
                )
                self.assertIn("  workflow_dispatch:\n", text)

    def test_plugin_workflows_follow_only_their_owned_inputs(self):
        for name, expected in sorted(PLUGIN_WORKFLOW_PATHS.items()):
            text = (WORKFLOWS / name).read_text(encoding="utf-8")
            for event in ("push", "pull_request"):
                with self.subTest(workflow=name, event=event):
                    self.assertEqual(workflow_event_paths(text, event), expected)

    def test_required_gates_carry_no_path_filter(self):
        """Every gate main requires must run on every pull request.

        A required status check that a pull request never produces blocks that
        pull request with no way to clear it, and the suite already asserts
        over paths no filter listed: .horos/boundary.json, audit/,
        CONTRIBUTORS.md, LICENSE and .gitignore. Both reasons say the root
        gate is unfiltered, so no filter may reappear on either event.
        """
        for name in sorted(UNFILTERED_GATES):
            text = (WORKFLOWS / name).read_text(encoding="utf-8")
            for event in ("push", "pull_request"):
                with self.subTest(workflow=name, event=event):
                    with self.assertRaises(ValueError):
                        workflow_event_paths(text, event)

    def test_complete_plugin_gate_runs_the_one_full_graph(self):
        workflow = WORKFLOWS / "plugins.yml"
        self.assertTrue(workflow.is_file(), "the complete plugin workflow is missing")
        text = workflow.read_text(encoding="utf-8")
        self.assertEqual(text.count("  plugins:\n"), 1)
        self.assertIn("permissions:\n  contents: read\n", text)
        self.assertEqual(text.count("fetch-depth: 0"), 1)
        self.assertIn("uses: actions/setup-node@v7", text)
        self.assertIn('node-version: "26.6.0"', text)
        self.assertIn("uses: foundry-rs/foundry-toolchain@v1", text)
        self.assertIn("version: v1.7.1", text)
        self.assertIn(
            "run: python3 -m pip install --requirement "
            "plugins/lazarus/requirements.lock",
            text,
        )
        historical_key = (
            ROOT
            / "plugins"
            / "hexaemeron"
            / "tests"
            / "fixtures"
            / "signing-keys"
            / "shoggoth-636ec19d.asc"
        )
        self.assertTrue(historical_key.is_file())
        self.assertIn(
            "EXPECTED_GPG_FINGERPRINT: "
            "636EC19DE45DF10F3CE6206F57742DA1ABED6F46",
            text,
        )
        self.assertIn(
            "gpg --batch --import \"$key_path\"",
            text,
        )
        self.assertEqual(
            text.count(
                "run: python3 scripts/run_checks.py --full "
                "--report tmp/checks/plugins.json"
            ),
            1,
        )
        self.assertIn("if: always()", text)
        self.assertIn("uses: actions/upload-artifact@v4", text)
        self.assertIn("path: tmp/checks/plugins.json", text)
        self.assertNotIn("continue-on-error", text)
        self.assertNotIn("github.event.pull_request", text)

    def test_complete_graph_has_one_owned_suite_scope_for_every_plugin(self):
        graph = json.loads((ROOT / "tests" / "check-map-v1.json").read_text())
        plugins = {
            path.name for path in (ROOT / "plugins").iterdir() if path.is_dir()
        }
        owners = {
            item["path"].removeprefix("plugins/"): item["scope"]
            for item in graph["owners"]
            if item["path"].startswith("plugins/")
            and "/" not in item["path"][8:]
        }
        self.assertEqual(set(owners), plugins)
        for plugin in sorted(plugins):
            with self.subTest(plugin=plugin):
                self.assertEqual(owners[plugin], plugin)
                self.assertIn(plugin, graph["scopes"])
                self.assertIn(plugin, graph["dependencies"])
                checks = [
                    graph["checks"][check_id]
                    for check_id in graph["scopes"][plugin]["checks"]
                ]
                self.assertTrue(any(check["kind"] == "suite" for check in checks))

    def test_readme_points_to_both_contract_layers_and_the_decision(self):
        text = README.read_text(encoding="utf-8")
        self.assertIn("[`pyproject.toml`](./pyproject.toml)", text)
        self.assertIn("[`.python-version`](./.python-version)", text)
        self.assertIn("[ADR-038]", text)
        self.assertIn("[ADR-042]", text)

    def test_current_runtime_prose_points_to_the_pin(self):
        for relative in sorted(PIN_REFERENCING_PROSE):
            path = ROOT / relative
            with self.subTest(path=relative):
                self.assertTrue(path.is_file())
                self.assertIn(".python-version", path.read_text(encoding="utf-8"))

        stale = {}
        for path in ROOT.rglob("*.md"):
            if not is_current_runtime_prose(path):
                continue
            match = RUNTIME_VERSION_CLAIM.search(path.read_text(encoding="utf-8"))
            if match is not None:
                stale[path.relative_to(ROOT).as_posix()] = match.group(0)
        self.assertEqual(stale, {})


class PythonDependencyContractTests(unittest.TestCase):
    def test_the_dependency_manifest_inventory_is_closed(self):
        found = {
            path.relative_to(ROOT).as_posix()
            for path in ROOT.glob("plugins/*/requirements*")
            if path.is_file()
        }
        self.assertEqual(found, DEPENDENCY_FILES)

    def test_every_lazarus_direct_pin_matches_the_lock(self):
        direct = (LAZARUS / "requirements.txt").read_text(encoding="utf-8")
        locked = (LAZARUS / "requirements.lock").read_text(encoding="utf-8")
        self.assertEqual(dependency_drift(direct, locked), {})

    def test_dependency_manifests_point_to_the_interpreter_pin(self):
        for name in ("requirements.txt", "requirements.lock"):
            text = (LAZARUS / name).read_text(encoding="utf-8")
            with self.subTest(name=name):
                self.assertIn("../../.python-version", text.splitlines()[0])

    def test_a_changed_direct_version_is_reported_as_drift(self):
        drift = dependency_drift(
            "jsonschema==4.25.2\n",
            "attrs==26.1.0\njsonschema==4.25.1\n",
        )
        self.assertEqual(
            drift,
            {
                "jsonschema": {
                    "direct": "jsonschema==4.25.2",
                    "locked": "jsonschema==4.25.1",
                }
            },
        )

    def test_an_unpinned_requirement_is_refused(self):
        with self.assertRaisesRegex(ValueError, "not an exact package pin"):
            exact_pins("jsonschema>=4.25.1\n", "requirements.txt")

    def test_lazarus_ci_installs_only_the_resolved_lock(self):
        text = (WORKFLOWS / "lazarus.yml").read_text(encoding="utf-8")
        self.assertIn(
            "python3 -m pip install --requirement plugins/lazarus/requirements.lock",
            text,
        )
        self.assertNotIn(
            "python3 -m pip install --requirement plugins/lazarus/requirements.txt",
            text,
        )
        self.assertIn("plugins/lazarus/requirements.txt", text)
        self.assertIn("plugins/lazarus/requirements.lock", text)


if __name__ == "__main__":
    unittest.main()
