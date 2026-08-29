"""Repo-wide plugin-contract assertions, defined once.

Several invariants hold for every plugin: its manifests and marketplace entry
state one agreed version, its human-facing description is identical across
hosts, the Promise Machine router reaches its runtime contract, and the
marketplace points at its local source path. The root suite (``tests/``) checks
these across all plugins from the outside; individual plugin suites used to
re-implement the same checks for themselves, so a single invariant lived in a
dozen copies that could drift apart.

This module is that invariant, stated once. The root suite loops it over every
plugin; a plugin suite that wants the check to fail in its own run (before the
root suite has to say so) calls it for itself.

Import contract
---------------
Each plugin suite runs under its own top-level import root
(``discover -t plugins/<name>``), so the package name ``tests`` binds to that
plugin's ``tests/`` package, not the repository one. This module therefore
lives at the repository root under a unique name, and callers reach it by
putting the repository root on ``sys.path`` first::

    import sys
    sys.path.insert(0, str(REPO_ROOT))   # the repo root Path the suite computed
    from repo_contract import assert_version_agreement

The functions take the calling ``TestCase`` so a failure is reported through
the caller's own suite, and the plugin name. They locate every file from this
module's own position, so callers pass nothing else.
"""

from pathlib import Path
import json
import re


ROOT = Path(__file__).resolve().parent
PLUGINS = ROOT / "plugins"
CLAUDE_MARKETPLACE = ROOT / ".claude-plugin" / "marketplace.json"
CODEX_MARKETPLACE = ROOT / ".agents" / "plugins" / "marketplace.json"
ROUTER = ROOT / ".agents" / "skills" / "promise-machine" / "SKILL.md"


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _claude_entry(name):
    for entry in _load(CLAUDE_MARKETPLACE)["plugins"]:
        if entry["name"] == name:
            return entry
    raise AssertionError(f"{name} has no Claude marketplace entry")


def assert_version_agreement(test, name, expected=None):
    """Both host manifests and the marketplace entry state one version.

    Pass ``expected`` to pin the exact value as well. Subsumes the per-plugin
    copies and mirrors ``tests/test_version_propagation.py``.
    """
    plugin = PLUGINS / name
    claude = _load(plugin / ".claude-plugin" / "plugin.json")["version"]
    codex = _load(plugin / ".codex-plugin" / "plugin.json")["version"]
    listed = _claude_entry(name)["version"]
    test.assertEqual(codex, claude, f"{name}: Codex version {codex} != Claude {claude}")
    test.assertEqual(listed, claude, f"{name}: marketplace {listed} != Claude {claude}")
    if expected is not None:
        test.assertEqual(claude, expected, f"{name}: version {claude} != expected {expected}")


def assert_host_descriptions_agree(test, name):
    """The human-facing description is identical across every host surface.

    Claude manifest, Codex manifest, the Codex interface shortDescription, the
    marketplace entry, and the OpenAI agent file where one ships. Mirrors
    ``tests/test_marketplace_prose.py``'s cross-host check.
    """
    expected = _claude_entry(name)["description"]
    plugin = PLUGINS / name
    for host in (".claude-plugin", ".codex-plugin"):
        manifest = _load(plugin / host / "plugin.json")
        test.assertEqual(
            manifest["description"], expected,
            f"{name}/{host} description drifts from the marketplace entry",
        )
    codex = _load(plugin / ".codex-plugin" / "plugin.json")
    test.assertEqual(
        codex["interface"]["shortDescription"], expected,
        f"{name}: Codex interface shortDescription drifts",
    )
    agent = plugin / "skills" / name / "agents" / "openai.yaml"
    if agent.is_file():
        match = re.search(
            r'(?m)^  short_description: ["\']?([^"\'\n]+)',
            agent.read_text(encoding="utf-8"),
        )
        test.assertIsNotNone(match, str(agent))
        test.assertEqual(match.group(1), expected, f"{name}: OpenAI short_description drifts")


def assert_router_reaches(test, name, skill=None):
    """The Promise Machine router links the plugin's runtime contract, and that
    contract references its canonical skill.

    ``skill`` defaults to the plugin name; pass it when the canonical skill
    directory differs (e.g. lemma's ``chunk``). The root suite owns the stronger
    set-equality check that the router reaches *exactly* every plugin; this is
    the per-plugin membership a plugin suite asserts for itself.
    """
    skill = skill or name
    links = re.findall(r"\[[^]]+\]\(([^)]+)\)", ROUTER.read_text(encoding="utf-8"))
    test.assertIn(
        f"../../../plugins/{name}/AGENTS.md", links,
        f"promise-machine router does not link plugins/{name}/AGENTS.md",
    )
    contract = (PLUGINS / name / "AGENTS.md").read_text(encoding="utf-8")
    test.assertIn(
        f"`skills/{skill}/SKILL.md`", contract,
        f"{name} AGENTS.md does not reference skills/{skill}/SKILL.md",
    )


def assert_marketplace_source_path(test, name):
    """Both marketplaces point the entry at the local ./plugins/<name> path."""
    claude_entry = _claude_entry(name)
    codex_entry = next(
        entry for entry in _load(CODEX_MARKETPLACE)["plugins"] if entry["name"] == name
    )
    test.assertEqual(claude_entry["source"], f"./plugins/{name}")
    test.assertEqual(codex_entry["source"]["path"], f"./plugins/{name}")
