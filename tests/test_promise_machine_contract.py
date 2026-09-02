import copy
import importlib
import json
import hashlib
import io
import os
import re
from contextlib import ExitStack, redirect_stdout
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from scripts import promise_machine as promise_machine_module


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "promise_machine.py"
LAW = ROOT / "PROMISE_MACHINE.md"
LICENSE = ROOT / "LICENSE"
FIXTURE = ROOT / "tests" / "fixtures" / "promise-machine" / "divergent-copy"
FIXTURES = ROOT / "tests" / "fixtures" / "promise-machine"
PROMISE_FIELDS = (
    "Promise",
    "Evidence",
    "Evidence classes",
    "Boundary",
    "Authorises",
    "Consequence",
    "Refuses",
    "Recovery",
    "Exceptions",
)
OBLIGATION_REGISTRY = ROOT / "tests" / "promise_machine_obligations.json"
OBLIGATION_FIXTURES = FIXTURES / "obligations"
CONSEQUENCE_FIXTURES = FIXTURES / "consequences"
EXCEPTION_FIXTURES = FIXTURES / "exceptions"
RUNTIME_FIXTURES = FIXTURES / "runtime"
COMPOSITION_FIXTURES = FIXTURES / "composition"
COMPOSITION_CASES = COMPOSITION_FIXTURES / "cases.json"
PROMISE_ID_HISTORY = ROOT / "tests" / "promise_machine_id_history.json"
FIAT_ENTRY_REF = "7e97b5195d5b0e43146b4200f26cd41b89003413"
PYTHON_RUNTIME_BINDINGS = {
    "promise_id": "adapter_output.binding.promise_id",
    "subject": "adapter_output.binding.subject",
    "scope": "adapter_output.binding.scope",
    "evidence_references": "adapter_output.references",
    "evidence_classes": "adapter_output.classes",
    "unknowns": "adapter_output.unresolved",
    "transition": "adapter_output.transition",
    "exception": "adapter_output.exception",
    "source_digest": "adapter_output.source_digest",
}
DURABLE_OBLIGATION_STUDY = (
    ROOT / "docs" / "promise-machine" / "obligation-gates" / "study.md"
)
DURABLE_OBLIGATION_RUNBOOK = (
    ROOT / "docs" / "promise-machine" / "obligation-gates" / "runbook.md"
)
RECEIPTED_OBLIGATION_STUDY_SHA256 = (
    "cd39131e527cfd0a670757610e1e42016c7a7eede27b403d563c10b22b40ae1c"
)
RECEIPTED_OBLIGATION_RUNBOOK_SHA256 = (
    "c4daddbe2a12f3c8c9360d25d635755a77ca17e72d9291cfa0ead1525f654e42"
)


def discovered_plugins():
    """Count what ships rather than what a literal here remembers.

    Every count below used to be written in by hand, so a new plugin landed
    with these cases passing while none of them had looked at it. Deriving the
    expectations from disk and from the coverage ledger turns that omission
    back into a failure.
    """
    return sorted(
        path.parent.parent.name
        for path in (ROOT / "plugins").glob("*/.claude-plugin/plugin.json")
    )


def discovered_canonical_skills():
    """Every SKILL.md under a plugin's skills tree, nested ones included.

    Fizz carries two sub-skills, so a shallow glob undercounts. The checker
    walks the tree; this walks the same tree rather than restating its total.
    """
    return sorted((ROOT / "plugins").glob("*/skills/**/SKILL.md"))


# The vendored Pashov set is upstream-owned and fixed at five skills. That one
# stays a written expectation: the suite should refuse a silent addition to
# somebody else's licensed tree, not absorb it.
VENDORED_SKILLS = 5


def coverage_rows():
    payload = json.loads(
        (ROOT / "tests" / "promise_machine_coverage.json").read_text(encoding="utf-8")
    )
    return payload["rows"]


def rows_in(*groups):
    return [row for row in coverage_rows() if row["group"] in groups]


def write_obligation_fixture(root):
    shutil.copy2(LAW, root / LAW.name)
    registry = root / "tests" / "promise_machine_obligations.json"
    registry.parent.mkdir(parents=True)
    shutil.copy2(OBLIGATION_REGISTRY, registry)
    shutil.copytree(FIXTURES, root / "tests" / "fixtures" / "promise-machine")
    composition = json.loads(COMPOSITION_CASES.read_text(encoding="utf-8"))
    sources = {
        reference["path"]
        for relation in composition["relations"]
        for role in ("producer", "consumer")
        for reference in relation["positive"][role]["bindings"][
            "evidence-references"
        ]
    }
    for source in sources:
        destination = root / source
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / source, destination)
    return registry


def rewrite_registry(path, mutate):
    document = json.loads(path.read_text(encoding="utf-8"))
    mutate(document)
    path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")


def load_fixture(relative_path):
    return json.loads((FIXTURES / relative_path).read_text(encoding="utf-8"))


def copy_semantic_fixtures(root):
    destination = root / "tests" / "fixtures" / "promise-machine"
    destination.parent.mkdir(parents=True)
    shutil.copytree(FIXTURES, destination)
    return destination


def semantic_codes(findings):
    return [finding.code for finding in findings]


def declared_runtime_records():
    """Discover level-two and level-three rows from authored promise blocks."""
    coverage = json.loads(
        (ROOT / "tests" / "promise_machine_coverage.json").read_text(
            encoding="utf-8"
        )
    )
    records = {}
    for row in coverage["rows"]:
        declaration_path = (
            ROOT / "plugins" / "hexaemeron" / "PROMISES.md"
            if row["group"] == "vendored"
            else ROOT / row["skill_path"]
        )
        source = declaration_path.read_text(encoding="utf-8")
        marker = f"### {row['promise_id']}"
        start = source.find(marker)
        if start < 0:
            continue
        following = source.find("\n### ", start + len(marker))
        section = source[start : following if following >= 0 else None]
        consequence_match = re.search(r"^- Consequence:\s*([0-3])\s*$", section, re.M)
        classes_match = re.search(r"^- Evidence classes:\s*(.+?)\s*$", section, re.M)
        if consequence_match is None or classes_match is None:
            continue
        consequence = int(consequence_match.group(1))
        if consequence < 2:
            continue
        classes = frozenset(
            item.strip().strip("`").split(":", 1)[0]
            for item in re.split(r"[,;]", classes_match.group(1))
            if item.strip()
        )
        records[row["promise_id"]] = promise_machine_module.PromiseRecord(
            row["promise_id"],
            row["skill_path"],
            row["group"],
            classes,
            consequence,
        )
    return records


def load_runtime_selector(descriptor):
    path = ROOT / descriptor["path"]
    document = json.loads(path.read_text(encoding="utf-8"))
    return copy.deepcopy(document["specimens"][descriptor["selector"]])


def set_dotted(document, dotted, value):
    target = document
    parts = dotted.split(".")
    for part in parts[:-1]:
        target = target[part]
    target[parts[-1]] = value


def mutate_runtime_field(result, binding, field, value):
    mutated = copy.deepcopy(result)
    set_dotted(mutated, binding["bindings"][field], value)
    mutated["promise_machine"][field] = copy.deepcopy(value)
    return mutated


def fixture_runtime_binding(source, digest):
    specimen = {
        "path": "tests/runtime-specimen.json",
        "selector": "positive",
        "sha256": "0" * 64,
    }
    negative = dict(specimen)
    negative["selector"] = "negative"
    negative["finding"] = "PM095"
    negative["field"] = "source_digest"
    return {
        "source": source,
        "selector": "test_positive",
        "sha256": digest,
        "reader": "python-result-adapter-v1",
        "bindings": dict(PYTHON_RUNTIME_BINDINGS),
        "positive": specimen,
        "negative": negative,
    }



def run_cli(*arguments):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *map(str, arguments)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def fixture_promise_fields():
    return {
        "Promise": "The named check accepted the subject.",
        "Evidence": "example check record",
        "Evidence classes": "checked",
        "Boundary": "No claim beyond the named rule.",
        "Authorises": "Use of the checked result.",
        "Consequence": "1",
        "Refuses": "Use of a missing or failed result.",
        "Recovery": "Repair the input and rerun the check.",
        "Exceptions": "none",
    }


def promise_semantic_sha256(fields):
    encoded = json.dumps(
        {field: fields[field] for field in PROMISE_FIELDS},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def history_snapshot(skill_path, fields):
    return {
        "skill_path": skill_path,
        "semantic_sha256": promise_semantic_sha256(fields),
    }


def history_row(
    promise_id,
    *,
    entry=None,
    current=None,
    action="unchanged",
    predecessors=(),
    successors=(),
):
    return {
        "promise_id": promise_id,
        "entry": copy.deepcopy(entry),
        "current": copy.deepcopy(current),
        "continuity": {
            "action": action,
            "predecessors": list(predecessors),
            "successors": list(successors),
        },
    }


def write_history(root, entries, *, entry_ref=FIAT_ENTRY_REF):
    entry_inventory = sorted(
        (
            {
                "promise_id": row["promise_id"],
                **copy.deepcopy(row["entry"]),
            }
            for row in entries
            if row["entry"] is not None
        ),
        key=lambda row: row["promise_id"],
    )
    encoded = json.dumps(
        entry_inventory, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    document = {
        "contract": "promise-machine/v1",
        "schema": "promise-machine-id-history/v1",
        "entry_ref": entry_ref,
        "entry_count": len(entry_inventory),
        "entry_inventory_sha256": hashlib.sha256(encoded).hexdigest(),
        "entries": copy.deepcopy(entries),
    }
    history = root / "tests" / "promise_machine_id_history.json"
    history.parent.mkdir(parents=True, exist_ok=True)
    history.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    return history, document


def make_plugin(root, name="example"):
    plugin = root / "plugins" / name
    for host in (".claude-plugin", ".codex-plugin"):
        manifest = plugin / host / "plugin.json"
        manifest.parent.mkdir(parents=True)
        manifest.write_text(
            json.dumps({"name": name, "version": "0.0.0"}) + "\n",
            encoding="utf-8",
        )
    return plugin


def make_licensed_plugin(root, name="example"):
    plugin = make_plugin(root, name)
    licence = LICENSE.read_bytes()
    (root / "LICENSE").write_bytes(licence)
    (plugin / "LICENSE").write_bytes(licence)
    for host in (".claude-plugin", ".codex-plugin"):
        manifest = plugin / host / "plugin.json"
        document = json.loads(manifest.read_text(encoding="utf-8"))
        document["license"] = "Apache-2.0"
        document["author"] = {"name": "Wildcat Labs"}
        manifest.write_text(json.dumps(document) + "\n", encoding="utf-8")
    write_skill(plugin)
    return plugin


def write_skill(plugin, name="example", *, promise_id="example-check", fields=None):
    directory = plugin / "skills" / name
    directory.mkdir(parents=True)
    values = fixture_promise_fields()
    if fields is not None:
        values = fields
    rows = "\n".join(f"- {field}: {value}" for field, value in values.items())
    (directory / "SKILL.md").write_text(
        "---\n"
        f"name: {name}\n"
        "description: A fixture skill.\n"
        "---\n\n"
        f"# {name}\n\n"
        "## Promise Machine contract\n\n"
        f"### {promise_id}\n\n"
        f"{rows}\n",
        encoding="utf-8",
    )
    (directory / "EVOLUTION.md").write_text("# Evolution\n", encoding="utf-8")
    return directory


def write_vendored_skill(plugin, name="upstream"):
    directory = plugin / "skills" / name
    directory.mkdir(parents=True)
    skill = directory / "SKILL.md"
    skill.write_text(
        "---\n"
        f"name: {name}\n"
        "description: A vendored fixture skill.\n"
        "---\n\n"
        f"# {name}\n",
        encoding="utf-8",
    )
    (directory / "NOTICE.md").write_text(
        "# Notice\n\n"
        "This directory is vendored verbatim.\n\n"
        "- Upstream: https://example.invalid/upstream\n"
        "- Release tag: v0.0.0\n"
        "- Vendored: 2026-08-20\n",
        encoding="utf-8",
    )
    (directory / "LICENSE").write_text("Fixture licence.\n", encoding="utf-8")
    return skill


def write_overlay(root, skill, *, promise_id="hexaemeron-upstream-run", digest=None):
    digest = digest or hashlib.sha256(skill.read_bytes()).hexdigest()
    path = skill.relative_to(root).as_posix()
    overlay = root / "plugins" / "hexaemeron" / "PROMISES.md"
    overlay.write_text(
        "# Hexaemeron Promise Machine overlays\n\n"
        f"### {promise_id}\n\n"
        f"- Path: `{path}`\n"
        "- Repository: `https://github.com/example/upstream.git`\n"
        "- Commit: `0123456789abcdef0123456789abcdef01234567`\n"
        "- Upstream path: `upstream/SKILL.md`\n"
        f"- Upstream SHA-256: `{digest}`\n"
        f"- Local SHA-256: `{digest}`\n"
        "- Verification status: upstream-bytes-verified, "
        "local-bytes-identical, publisher-authentication-unknown\n"
        "- Promise: The named vendored operation completed.\n"
        "- Evidence: The digest-matched instruction and operation record.\n"
        "- Evidence classes: checked, recorded\n"
        "- Boundary: The result covers only the named operation.\n"
        "- Authorises: Use of the recorded result inside its boundary.\n"
        "- Consequence: 1\n"
        "- Refuses: A stale digest or failed operation.\n"
        "- Recovery: Reconcile the instruction and rerun the operation.\n"
        "- Exceptions: none\n",
        encoding="utf-8",
    )
    return overlay


def write_coverage_fixture(root):
    plugin = make_plugin(root, "hexaemeron")
    write_skill(plugin, "elenchus")
    vendored = write_vendored_skill(plugin)
    write_overlay(root, vendored)
    evidence_path = root / "tests" / "evidence.py"
    evidence_path.parent.mkdir(parents=True)
    selectors = {
        "p": "test_positive",
        "m": "test_missing",
        "s": "test_subject_mismatch",
        "o": "test_overclaim",
        "r": "test_recovery",
    }
    evidence_path.write_text(
        "\n".join(f"def {selector}():\n    pass\n" for selector in selectors.values()),
        encoding="utf-8",
    )
    evidence = {
        key: {
            "path": "tests/evidence.py",
            "selector": selector,
            "claim": f"Fixture {key} evidence.",
        }
        for key, selector in selectors.items()
    }
    document = {
        "contract": "promise-machine/v1",
        "schema": "promise-machine-coverage/v1",
        "handoffs": [],
        "evidence": evidence,
        "rows": [
            {
                "promise_id": "example-check",
                "skill_path": "plugins/hexaemeron/skills/elenchus/SKILL.md",
                "group": "executable",
                "cases": {
                    "P": "p",
                    "M": "m",
                    "S": "s",
                    "O": "o",
                    "R": "r",
                    "X": {
                        "not_applicable": True,
                        "reason": "The fixture supports no exceptions.",
                    },
                },
            },
            {
                "promise_id": "hexaemeron-upstream-run",
                "skill_path": "plugins/hexaemeron/skills/upstream/SKILL.md",
                "group": "vendored",
                "cases": None,
                "pending": "Runbook Step 8 classifies vendored evidence.",
            },
        ],
    }
    coverage = root / "tests" / "promise_machine_coverage.json"
    coverage.write_text(json.dumps(document), encoding="utf-8")
    return coverage, document


class PromiseLawTests(unittest.TestCase):
    def test_repository_law_and_copies_are_clean(self):
        completed = run_cli("check", "--only", "law,copies")
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn(
            "clean: %d plugin(s), %d copy/copies"
            % (len(discovered_plugins()), len(discovered_plugins())),
            completed.stdout,
        )

    def test_sync_check_is_read_only_and_clean(self):
        before = {path: path.read_bytes() for path in ROOT.glob("plugins/*/PROMISE_MACHINE.md")}
        completed = run_cli("sync", "--check")
        after = {path: path.read_bytes() for path in ROOT.glob("plugins/*/PROMISE_MACHINE.md")}
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(before, after)

    def test_all_plugin_copies_are_exact_and_marked(self):
        law = LAW.read_bytes()
        copies = sorted(ROOT.glob("plugins/*/PROMISE_MACHINE.md"))
        self.assertEqual(len(copies), len(discovered_plugins()))
        for copy in copies:
            with self.subTest(copy=copy):
                self.assertEqual(copy.read_bytes(), law)
                self.assertTrue(
                    any(
                        b"copies=generated" in line
                        for line in copy.read_bytes().splitlines()[:5]
                    )
                )


class PromiseObligationTests(unittest.TestCase):
    def test_durable_specification_copies_are_the_fresh_receipted_sources(self):
        expected = {
            DURABLE_OBLIGATION_STUDY: RECEIPTED_OBLIGATION_STUDY_SHA256,
            DURABLE_OBLIGATION_RUNBOOK: RECEIPTED_OBLIGATION_RUNBOOK_SHA256,
        }
        for path, digest in expected.items():
            with self.subTest(path=path.name):
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), digest)

    def test_repository_obligation_registry_and_specimens_are_clean(self):
        completed = run_cli("check", "--only", "obligations", "--json")
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(report["counts"]["obligations"], 18)
        self.assertEqual(report["findings"], [])

    def test_marked_structural_claims_match_their_production_gates(self):
        text = LAW.read_text(encoding="utf-8")
        expected = {
            "law-contract-identity": (
                "> Obligation: This authored law names only `promise-machine/v1` as its\n"
                "> contract identity."
            ),
            "law-generated-copy-identity": (
                "> Obligation: This authored law header carries the fixed\n"
                "> `promise-machine/v1` canonical and generated-copy identity marker."
            ),
            "law-governing-principle": (
                "> Obligation: This authored law carries the settled governing-principle\n"
                "> sentence exactly."
            ),
            "law-declaration-fields": (
                "> Obligation: This authored law contains each of the nine required promise\n"
                "> declaration-field tokens."
            ),
            "law-required-sections": (
                "> Obligation: Every required normative section of this authored law appears\n"
                "> exactly once."
            ),
            "law-unknowns-non-authorising": (
                "> Obligation: `unknown`, `not-run`, missing, stale or unresolved evidence never\n"
                "> authorises a positive transition."
            ),
            "law-consequence-separation": (
                "> Obligation: Consequence levels zero through three take distinct enforcement\n"
                "> paths, and level three never accepts level-two-only evidence."
            ),
            "law-runtime-result-binding": (
                "> Obligation: Every level-two or level-three runtime promise resolves its\n"
                "> native binding fields through a bounded source-bound reader; level three\n"
                "> also resolves authority and independently inspectable evidence."
            ),
            "law-composition-lemma-boundary": (
                "> Obligation: Relation `lemma-retrieval-to-berean-corpus` preserves its subject,\n"
                "> scope, source links, chunk locations, evidence references and classes, time\n"
                "> domain, unknowns, conflicts, refusals and recovery, and refuses answer truth."
            ),
            "law-composition-lazarus-boundary": (
                "> Obligation: Relation `lazarus-rpc-to-berean-answer` preserves its subject,\n"
                "> scope, block, RPC methods, proof relation, evidence references and classes,\n"
                "> time domain, unknowns, conflicts, refusals and recovery, and refuses proof or\n"
                "> answer truth that its recorded evidence did not establish."
            ),
            "law-composition-berean-boundary": (
                "> Obligation: Relation `berean-promotion-to-ariadne-capture` preserves its\n"
                "> subject, scope, release digests, evidence references and classes, time domain,\n"
                "> unknowns, conflicts, refusals and recovery, and refuses answer truth and model\n"
                "> quality."
            ),
            "law-composition-janus-boundary": (
                "> Obligation: Relation `janus-bounded-to-ariadne-capture` preserves its subject,\n"
                "> scope, adapter, manifest, recorder, bounded search, evidence references and\n"
                "> classes, time domain, unknowns, conflicts, refusals and recovery, and refuses\n"
                "> hook safety, complete liveness and cross-host conformance."
            ),
            "law-composition-ariadne-boundary": (
                "> Obligation: Relation `ariadne-verification-to-fiat-delivery` preserves its\n"
                "> subject, scope, artefact digest, predicate type, signature-verifier state,\n"
                "> evidence references and classes, time domain, unknowns, conflicts, refusals\n"
                "> and recovery, and refuses author identity without an external verifier."
            ),
            "law-composition-fiat-observation-boundary": (
                "> Obligation: Relation `fiat-observation-to-synkrisis-cohort` preserves its\n"
                "> subject, scope, validator, capture boundary, receipt, evidence references and\n"
                "> classes, time domain, unknowns, conflicts, refusals and recovery, and refuses\n"
                "> event truth and delivery evidence."
            ),
            "law-composition-synkrisis-boundary": (
                "> Obligation: Relation `synkrisis-verification-to-fiat-integration` preserves\n"
                "> its subject, scope, cohort, findings and report digests, counterevidence,\n"
                "> unknown runs, evidence references and classes, time domain, unknowns,\n"
                "> conflicts, refusals and recovery, and refuses cause, model quality and\n"
                "> authority to act."
            ),
            "law-refusal-shape": (
                "> Obligation: Every refusal report names the promise id, failed field or\n"
                "> evidence, consequence level, blocked transition and recovery action."
            ),
            "law-exception-resolution": (
                "> Obligation: Every exception resolves its authority, promise and gate,\n"
                "> subject, scope, durable record, expiry, revocation state and recovery path."
            ),
            "law-core-checker-side-effects": (
                "> Obligation: The core checker reaches no network, reads no credential and\n"
                "> executes no shell, subprocess, dynamic code or evidence command."
            ),
        }
        for obligation_id, clause in expected.items():
            with self.subTest(obligation_id=obligation_id):
                marker = (
                    f"<!-- promise-machine-obligation: id={obligation_id} -->"
                )
                self.assertIn(f"{marker}\n{clause}", text)

    def test_contract_identity_gate_rejects_an_unrecognised_declaration(self):
        declaration = "The shared contract identity is `promise-machine/v1`."
        text = LAW.read_text(encoding="utf-8").replace(
            declaration,
            "The shared contract identity is `different-contract/v1`."
            f"\n\n    {declaration}",
            1,
        )
        findings = promise_machine_module.validate_law_document(
            text.encode("utf-8"), text, "contract-identity-decoy.md"
        )
        self.assertIn("PM007", [finding.code for finding in findings])

    def test_required_section_gate_ignores_a_fenced_heading_decoy(self):
        text = LAW.read_text(encoding="utf-8").replace(
            "## Scope", "## Scope changed", 1
        )
        text += "\n```markdown\n## Scope\n```\n"
        findings = promise_machine_module.validate_law_document(
            text.encode("utf-8"), text, "required-section-decoy.md"
        )
        self.assertIn("PM006", [finding.code for finding in findings])

    def test_declaration_field_gate_ignores_an_indented_code_decoy(self):
        field = "- `Recovery`"
        text = LAW.read_text(encoding="utf-8").replace(field, "- Recovery", 1)
        text += f"\n    {field}\n"
        findings = promise_machine_module.validate_law_document(
            text.encode("utf-8"), text, "declaration-field-decoy.md"
        )
        self.assertIn("PM008", [finding.code for finding in findings])

    def test_governing_principle_gate_ignores_a_fenced_quote_decoy(self):
        principle = (
            "> No skill may claim more than its evidence establishes, or authorise a more\n"
            "> consequential transition than that evidence warrants."
        )
        text = LAW.read_text(encoding="utf-8").replace(
            principle,
            "> No skill may claim more than its evidence records, or authorise a more\n"
            "> consequential transition than that evidence warrants.",
            1,
        )
        text += f"\n```markdown\n{principle}\n```\n"
        findings = promise_machine_module.validate_law_document(
            text.encode("utf-8"), text, "governing-principle-decoy.md"
        )
        self.assertIn("PM009", [finding.code for finding in findings])

    def test_law_gates_ignore_commonmark_raw_html_block_content(self):
        cases = {
            "raw-text": "<script>\n## Scope\n</script>",
            "comment": "<!--\n## Scope\n-->",
            "processing": "<?\n## Scope\n?>",
            "declaration": "<!DOCTYPE\n## Scope\n>",
            "cdata": "<![CDATA[\n## Scope\n]]>",
            "block-tag": "<div>\n## Scope\n</div>\n",
            "generic-tag": "<x-decoy>\n## Scope\n</x-decoy>\n",
            "raw-text-marker": (
                "<script><!-- promise-machine-obligation: malformed\n"
                "## Scope\n</script>"
            ),
            "block-tag-marker": (
                "<div><!-- promise-machine-obligation: malformed\n"
                "## Scope\n</div>\n"
            ),
            "generic-tag-marker": (
                '<x-decoy data="<!-- promise-machine-obligation: malformed">\n'
                "## Scope\n</x-decoy>\n"
            ),
        }
        for name, block in cases.items():
            with self.subTest(name=name):
                lines = promise_machine_module.markdown_unfenced_lines(block)
                self.assertNotIn("## Scope", lines)
        paragraph_lines = promise_machine_module.markdown_unfenced_lines(
            "paragraph\n<x-decoy>\n## Scope"
        )
        self.assertIn("## Scope", paragraph_lines)

    def test_law_gates_ignore_type_seven_closing_tag_blocks(self):
        law = LAW.read_text(encoding="utf-8")
        for tag in ("script", "pre", "style", "textarea"):
            with self.subTest(tag=tag):
                text = law.replace(
                    "## Scope", f"</{tag}>\n## Scope\n\n", 1
                )
                findings = promise_machine_module.validate_law_document(
                    text.encode("utf-8"), text, f"{tag}-closing-tag-decoy.md"
                )
                self.assertIn("PM006", [finding.code for finding in findings])

    def test_compact_self_closing_raw_text_tags_do_not_hide_law_headings(self):
        law = LAW.read_text(encoding="utf-8")
        for tag in ("script", "pre", "style", "textarea"):
            with self.subTest(tag=tag):
                text = f"{law}\n<{tag}/>\n## Scope\n\n"
                findings = promise_machine_module.validate_law_document(
                    text.encode("utf-8"), text, f"{tag}-self-closing-decoy.md"
                )
                self.assertIn("PM006", [finding.code for finding in findings])

    def test_malformed_type_six_slash_tags_do_not_hide_law_headings(self):
        law = LAW.read_text(encoding="utf-8")
        for opener in ("<div/not-a-tag>", "</div/not-a-tag>", "<div/", "</div/"):
            with self.subTest(opener=opener):
                text = f"{law}\n{opener}\n## Scope\n\n"
                findings = promise_machine_module.validate_law_document(
                    text.encode("utf-8"), text, "type-six-slash-decoy.md"
                )
                self.assertIn("PM006", [finding.code for finding in findings])

    def test_law_gates_track_blocks_before_a_generic_html_block(self):
        cases = {
            "setext-heading": "lead\n---",
            "thematic-break": "* * *",
            "indented-code": "    code",
            "link-reference": "[label]: /target",
            "blockquote": ">quoted",
            "non-one-ordered-list": "2. item",
        }
        for name, prefix in cases.items():
            with self.subTest(name=name):
                lines = promise_machine_module.markdown_unfenced_lines(
                    f"{prefix}\n<x-decoy>\n## Scope\n</x-decoy>\n"
                )
                self.assertNotIn("## Scope", lines)

    def test_contract_identity_gate_ignores_an_html_comment_decoy(self):
        declaration = "The shared contract identity is `promise-machine/v1`."
        text = LAW.read_text(encoding="utf-8").replace(
            declaration, f"<!--\n{declaration}\n-->", 1
        )
        findings = promise_machine_module.validate_law_document(
            text.encode("utf-8"), text, "contract-identity-html-decoy.md"
        )
        self.assertIn("PM007", [finding.code for finding in findings])

    def test_law_gates_reject_non_commonmark_line_separator_decoys(self):
        separators = (
            "\v",
            "\f",
            "\x1c",
            "\x1d",
            "\x1e",
            "\x85",
            "\u2028",
            "\u2029",
        )
        for separator in separators:
            with self.subTest(separator=ascii(separator)):
                text = LAW.read_text(encoding="utf-8").replace(
                    "## Scope", f"not-a-heading{separator}## Scope", 1
                )
                findings = promise_machine_module.validate_law_document(
                    text.encode("utf-8"), text, "line-separator-decoy.md"
                )
                self.assertIn("PM006", [finding.code for finding in findings])

    def test_required_section_gate_ignores_yaml_frontmatter_decoy(self):
        text = LAW.read_text(encoding="utf-8").replace(
            "## Scope", "## Scope changed", 1
        )
        text = f"---\n## Scope\n---\n{text}"
        findings = promise_machine_module.validate_law_document(
            text.encode("utf-8"), text, "frontmatter-decoy.md"
        )
        self.assertIn("PM006", [finding.code for finding in findings])

    def test_required_section_gate_counts_commonmark_heading_forms(self):
        law = LAW.read_text(encoding="utf-8")
        cases = {
            "indented-atx": "   ## Scope",
            "closing-hashes": "## Scope ##",
            "setext": "Scope\n-----",
        }
        for name, duplicate in cases.items():
            with self.subTest(name=name):
                text = f"{law}\n{duplicate}\n"
                findings = promise_machine_module.validate_law_document(
                    text.encode("utf-8"), text, f"{name}-section-decoy.md"
                )
                self.assertIn("PM006", [finding.code for finding in findings])

    def test_required_section_gate_rejects_container_nested_heading_decoys(self):
        law = LAW.read_text(encoding="utf-8")
        hidden = {
            "blockquote": "> ## Scope",
            "continued-blockquote": "> paragraph\n> ## Scope",
            "blockquote-list": "> - item\n>   ## Scope",
            "unordered-dash": "- item\n  ## Scope",
            "unordered-plus": "+ item\n  ## Scope",
            "unordered-star": "* item\n  ## Scope",
            "empty-unordered": "-\n  ## Scope",
            "unordered-leading-indent": " - item\n   ## Scope",
            "unordered-two-space-padding": "-  item\n   ## Scope",
            "unordered-five-space-padding": "-     item\n  ## Scope",
            "ordered-dot": "1. item\n   ## Scope",
            "ordered-parenthesis": "9) item\n   ## Scope",
            "empty-ordered": "1.\n   ## Scope",
            "mixed-unordered-ordered": "- outer\n  1. inner\n   ## Scope",
            "mixed-ordered-unordered": "1. outer\n   - inner\n   ## Scope",
            "lazy-continuation": "- item\nlazy continuation\n  ## Scope",
            "blank-continuation": "- item\n\n  ## Scope",
            "nested-setext": "- item\n\n  Scope\n  -----",
            "nested-blockquote": "- item\n  > quote\n  ## Scope",
            "nested-fence": "- item\n  ```\n  body\n  ```\n  ## Scope",
            "nested-html": "- item\n  <div>\n  body\n\n  ## Scope",
            "nested-indented-code": "- item\n      code\n  ## Scope",
            "nested-link-reference": "- item\n  [label]: /target\n  ## Scope",
            "nested-thematic-break": "- item\n  ***\n  ## Scope",
            "tab-padded-inline-heading": "-\t## Scope",
            "tab-indented-heading": "- item\n\t## Scope",
            "space-tab-indented-heading": "- item\n  \t## Scope",
        }
        for digits in range(1, 10):
            number = "1" * digits
            hidden[f"ordered-{digits}-digit-dot"] = f"{number}. ## Scope"
            hidden[f"ordered-{digits}-digit-parenthesis"] = f"{number}) ## Scope"
        for name, replacement in hidden.items():
            with self.subTest(name=name):
                text = law.replace("## Scope", replacement, 1)
                findings = promise_machine_module.validate_law_document(
                    text.encode("utf-8"), text, f"{name}-container-decoy.md"
                )
                self.assertIn("PM006", [finding.code for finding in findings])

        visible = {
            "after-bullet-indent-one": "- item\n ## Scope",
            "after-ordered-indent-two": "1. item\n  ## Scope",
            "after-two-digit-ordered": "10. item\n   ## Scope",
            "after-nine-digit-ordered": "123456789) item\n   ## Scope",
            "after-tab-padded-marker": "-\titem\n   ## Scope",
            "after-top-level-fence": "- item\n```\nbody\n```\n  ## Scope",
            "after-top-level-html": "- item\n<div>\nbody\n\n  ## Scope",
            "after-ended-list-paragraph": "- item\n\noutside\n  ## Scope",
            "after-blockquote": "> quote\n  ## Scope",
            "non-one-ordered-paragraph-continuation": (
                "paragraph\n2. continuation\n   ## Scope"
            ),
        }
        for name, replacement in visible.items():
            with self.subTest(name=name):
                text = law.replace("## Scope", replacement, 1)
                findings = promise_machine_module.validate_law_document(
                    text.encode("utf-8"), text, f"{name}-root-heading.md"
                )
                self.assertNotIn("PM006", [finding.code for finding in findings])

    def test_section_gates_stop_at_commonmark_h1_and_h2_boundaries(self):
        law = LAW.read_text(encoding="utf-8")
        declaration = "The shared contract identity is `promise-machine/v1`."
        cases = {
            "indented-atx": f"   # Moved identity\n{declaration}",
            "setext": f"Moved identity\n==============\n{declaration}",
            "setext-after-non-one-list-marker": (
                f"Moved identity\n2. continuation\n---\n{declaration}"
            ),
        }
        for name, replacement in cases.items():
            with self.subTest(name=name):
                text = law.replace(declaration, replacement, 1)
                findings = promise_machine_module.validate_law_document(
                    text.encode("utf-8"), text, f"{name}-section-boundary.md"
                )
                self.assertIn("PM007", [finding.code for finding in findings])

    def test_law_gates_honour_remaining_html_block_boundaries(self):
        law = LAW.read_text(encoding="utf-8")
        cases = {
            "lowercase-declaration-is-visible": (
                f"{law}\n<!doctype\n## Scope\n>\n",
                "PM006",
            ),
            "hgroup-type-six-is-hidden": (
                law.replace("## Scope", "## Scope changed", 1)
                + "\n<hgroup\n## Scope\n\n",
                "PM006",
            ),
        }
        for name, (text, expected) in cases.items():
            with self.subTest(name=name):
                findings = promise_machine_module.validate_law_document(
                    text.encode("utf-8"), text, f"{name}.md"
                )
                self.assertIn(expected, [finding.code for finding in findings])

    def test_fenced_obligation_marker_cannot_replace_an_authored_clause(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            write_obligation_fixture(target)
            law = target / LAW.name
            marker = (
                "<!-- promise-machine-obligation: id=law-contract-identity -->"
            )
            clause = (
                "> Obligation: This authored law names only `promise-machine/v1` as its\n"
                "> contract identity."
            )
            text = law.read_text(encoding="utf-8").replace(
                f"{marker}\n{clause}", f"```markdown\n{marker}\n{clause}\n```", 1
            )
            law.write_text(text, encoding="utf-8")
            completed = run_cli(
                "check", "--root", target, "--only", "obligations", "--json"
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM085", [item["code"] for item in report["findings"]])

    def test_raw_html_obligation_marker_cannot_replace_an_authored_clause(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            write_obligation_fixture(target)
            law = target / LAW.name
            marker = (
                "<!-- promise-machine-obligation: id=law-contract-identity -->"
            )
            clause = (
                "> Obligation: This authored law names only `promise-machine/v1` as its\n"
                "> contract identity."
            )
            text = law.read_text(encoding="utf-8").replace(
                f"{marker}\n{clause}",
                f"<div>\n{marker}\n{clause}\n</div>\n",
                1,
            )
            law.write_text(text, encoding="utf-8")
            completed = run_cli(
                "check", "--root", target, "--only", "obligations", "--json"
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM085", [item["code"] for item in report["findings"]])

    def test_unclosed_obligation_comment_cannot_expose_hidden_law_content(self):
        text = LAW.read_text(encoding="utf-8").replace(
            "## Scope",
            "<!-- promise-machine-obligation: malformed\n## Scope\n-->",
            1,
        )
        findings = promise_machine_module.validate_law_document(
            text.encode("utf-8"), text, "unclosed-obligation-comment.md"
        )
        self.assertIn("PM006", [finding.code for finding in findings])

    def test_each_normative_root_promise_section_is_required(self):
        headings = (
            "## First-party licence promise",
            "## Run observation promise",
            "## Contributor ranking promise",
            "## Router selection promise",
        )
        for heading in headings:
            with self.subTest(heading=heading), tempfile.TemporaryDirectory() as directory:
                target = Path(directory)
                shutil.copy2(LAW, target / LAW.name)
                law = target / LAW.name
                law.write_text(
                    law.read_text(encoding="utf-8").replace(
                        heading, f"{heading} changed", 1
                    ),
                    encoding="utf-8",
                )
                completed = run_cli(
                    "check", "--root", target, "--only", "law", "--json"
                )
            report = json.loads(completed.stdout)
            self.assertEqual(completed.returncode, 1)
            self.assertIn("PM006", [item["code"] for item in report["findings"]])

    def test_law_and_registry_reads_are_capped_before_loading_payload(self):
        real_read = os.read
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            cases = (
                (
                    target / "law.md",
                    b"# law\n",
                    promise_machine_module.MAX_MARKDOWN_BYTES,
                    lambda path: promise_machine_module.read_markdown(
                        path,
                        target,
                        missing_code="PM001",
                        unsafe_code="PM002",
                    ),
                ),
                (
                    target / "registry.json",
                    b"{}\n",
                    promise_machine_module.MAX_JSON_BYTES,
                    lambda path: promise_machine_module.read_json(path, target),
                ),
            )
            for path, payload, limit, load in cases:
                with self.subTest(path=path.name):
                    path.write_bytes(payload)
                    calls = []

                    def guarded_read(descriptor, size):
                        calls.append(size)
                        if size < 0 or size > min(64 * 1024, limit + 1):
                            raise AssertionError("input reader requested unbounded bytes")
                        return real_read(descriptor, size)

                    with mock.patch.object(os, "read", guarded_read):
                        loaded, findings = load(path)
                    self.assertIsNotNone(loaded)
                    self.assertEqual(findings, [])
                    self.assertTrue(calls)

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unavailable")
    def test_open_time_symlink_swap_is_refused_without_reading_outside(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            target_root = base / "repo"
            target_root.mkdir()
            target = target_root / "registry.json"
            outside = base / "outside.json"
            target.write_text('{"inside": true}\n', encoding="utf-8")
            outside.write_text('{"outside": true}\n', encoding="utf-8")

            real_path_open = Path.open
            real_os_open = os.open
            swapped = False

            def swap_target():
                nonlocal swapped
                if swapped:
                    return
                swapped = True
                target.unlink()
                target.symlink_to(outside)

            def swap_before_path_open(candidate, *args, **kwargs):
                if candidate == target:
                    swap_target()
                return real_path_open(candidate, *args, **kwargs)

            def swap_before_os_open(candidate, flags, mode=0o777, *, dir_fd=None):
                if candidate == target.name and dir_fd is not None:
                    swap_target()
                return real_os_open(candidate, flags, mode, dir_fd=dir_fd)

            with (
                mock.patch.object(Path, "open", swap_before_path_open),
                mock.patch.object(os, "open", swap_before_os_open),
            ):
                document, findings = promise_machine_module.read_json(
                    target, target_root, noun="race specimen"
                )

        self.assertTrue(swapped)
        self.assertIsNone(document)
        self.assertEqual([finding.code for finding in findings], ["PM021"])

    def test_sync_comparison_does_not_load_an_unbounded_copy(self):
        with tempfile.TemporaryDirectory() as directory:
            target_root = Path(directory)
            plugin = target_root / "plugins" / "example"
            plugin.mkdir(parents=True)
            destination = plugin / LAW.name
            destination.write_bytes(
                b"x" * (promise_machine_module.MAX_MARKDOWN_BYTES + 1)
            )
            law = LAW.read_bytes()
            real_read_bytes = Path.read_bytes
            unbounded_reads = []

            def record_unbounded_copy_read(candidate):
                if candidate == destination:
                    unbounded_reads.append(candidate)
                return real_read_bytes(candidate)

            with mock.patch.object(Path, "read_bytes", record_unbounded_copy_read):
                written, findings = promise_machine_module.sync_copies(
                    target_root, law, [plugin]
                )

            self.assertEqual(unbounded_reads, [])
            self.assertEqual(written, 1)
            self.assertEqual(findings, [])
            self.assertEqual(destination.read_bytes(), law)

    def test_unmarked_explicit_obligation_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            write_obligation_fixture(target)
            law = target / LAW.name
            law.write_text(
                law.read_text(encoding="utf-8")
                + "\n> Obligation: This explicit clause has no stable marker.\n",
                encoding="utf-8",
            )
            completed = run_cli(
                "check", "--root", target, "--only", "obligations", "--json"
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM080", [item["code"] for item in report["findings"]])

    def test_malformed_obligation_marker_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            write_obligation_fixture(target)
            law = target / LAW.name
            text = law.read_text(encoding="utf-8").replace(
                "<!-- promise-machine-obligation: id=law-contract-identity -->",
                "<!-- promise-machine-obligation: id=LAW-CONTRACT-IDENTITY -->",
                1,
            )
            law.write_text(text, encoding="utf-8")
            completed = run_cli(
                "check", "--root", target, "--only", "obligations", "--json"
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM080", [item["code"] for item in report["findings"]])

    def test_duplicate_obligation_marker_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            write_obligation_fixture(target)
            law = target / LAW.name
            law.write_text(
                law.read_text(encoding="utf-8")
                + "\n<!-- promise-machine-obligation: id=law-contract-identity -->\n"
                "> Obligation: This duplicate must not define a second clause.\n",
                encoding="utf-8",
            )
            completed = run_cli(
                "check", "--root", target, "--only", "obligations", "--json"
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM081", [item["code"] for item in report["findings"]])

    def test_obligation_markers_cannot_swap_their_owned_clauses(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            write_obligation_fixture(target)
            law = target / LAW.name
            contract_marker = (
                "<!-- promise-machine-obligation: id=law-contract-identity -->"
            )
            principle_marker = (
                "<!-- promise-machine-obligation: id=law-governing-principle -->"
            )
            text = law.read_text(encoding="utf-8")
            text = text.replace(contract_marker, "<!-- marker-swap -->", 1)
            text = text.replace(principle_marker, contract_marker, 1)
            text = text.replace("<!-- marker-swap -->", principle_marker, 1)
            law.write_text(text, encoding="utf-8")
            completed = run_cli(
                "check", "--root", target, "--only", "obligations", "--json"
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        mismatches = [
            item
            for item in report["findings"]
            if item["code"] == "PM086"
            and item["obligation_id"]
            in {"law-contract-identity", "law-governing-principle"}
        ]
        self.assertEqual(len(mismatches), 2)

    def test_marker_and_registry_clause_digests_cannot_move_as_a_pair(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            registry = write_obligation_fixture(target)
            law = target / LAW.name
            contract_marker = (
                "<!-- promise-machine-obligation: id=law-contract-identity -->"
            )
            principle_marker = (
                "<!-- promise-machine-obligation: id=law-governing-principle -->"
            )
            text = law.read_text(encoding="utf-8")
            text = text.replace(contract_marker, "<!-- marker-swap -->", 1)
            text = text.replace(principle_marker, contract_marker, 1)
            text = text.replace("<!-- marker-swap -->", principle_marker, 1)
            law.write_text(text, encoding="utf-8")

            def swap_clause_digests(document):
                rows = {row["id"]: row for row in document["obligations"]}
                contract_digest = rows["law-contract-identity"].get(
                    "clause_sha256", ""
                )
                principle_digest = rows["law-governing-principle"].get(
                    "clause_sha256", ""
                )
                rows["law-contract-identity"]["clause_sha256"] = principle_digest
                rows["law-governing-principle"]["clause_sha256"] = contract_digest

            rewrite_registry(registry, swap_clause_digests)
            completed = run_cli(
                "check", "--root", target, "--only", "obligations", "--json"
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        mismatches = [
            item
            for item in report["findings"]
            if item["code"] == "PM086"
            and item["obligation_id"]
            in {"law-contract-identity", "law-governing-principle"}
        ]
        self.assertEqual(len(mismatches), 2)

    def test_orphan_obligation_marker_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            write_obligation_fixture(target)
            law = target / LAW.name
            law.write_text(
                law.read_text(encoding="utf-8")
                + "\n<!-- promise-machine-obligation: id=law-orphan -->\n",
                encoding="utf-8",
            )
            completed = run_cli(
                "check", "--root", target, "--only", "obligations", "--json"
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM080", [item["code"] for item in report["findings"]])

    def test_missing_marker_leaves_the_clause_unmarked_and_row_extra(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            write_obligation_fixture(target)
            law = target / LAW.name
            law.write_text(
                law.read_text(encoding="utf-8").replace(
                    "<!-- promise-machine-obligation: id=law-required-sections -->\n",
                    "",
                    1,
                ),
                encoding="utf-8",
            )
            completed = run_cli(
                "check", "--root", target, "--only", "obligations", "--json"
            )
        report = json.loads(completed.stdout)
        codes = [item["code"] for item in report["findings"]]
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM080", codes)
        self.assertIn("PM085", codes)

    def test_masked_lines_adjacent_to_an_obligation_clause_do_not_crash(self):
        marker = "<!-- promise-machine-obligation: id=law-contract-identity -->"
        clause_end = "> contract identity."
        cases = {
            "masked-before": (
                marker,
                "<!-- ordinary authored comment -->",
                1,
                {"PM080", "PM085", "PM086"},
            ),
            "masked-after": (
                clause_end,
                clause_end + "\n<!-- ordinary authored comment -->",
                0,
                set(),
            ),
        }
        for name, (old, new, returncode, expected_codes) in cases.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                target = Path(directory)
                write_obligation_fixture(target)
                law = target / LAW.name
                law.write_text(
                    law.read_text(encoding="utf-8").replace(old, new, 1),
                    encoding="utf-8",
                )
                completed = run_cli(
                    "check", "--root", target, "--only", "obligations", "--json"
                )
            self.assertEqual(completed.returncode, returncode, completed.stderr)
            self.assertNotIn("Traceback", completed.stderr)
            report = json.loads(completed.stdout)
            self.assertEqual(
                expected_codes,
                {item["code"] for item in report["findings"]},
            )

    def test_missing_registry_row_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            registry = write_obligation_fixture(target)
            rewrite_registry(registry, lambda doc: doc["obligations"].pop())
            completed = run_cli(
                "check", "--root", target, "--only", "obligations", "--json"
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM085", [item["code"] for item in report["findings"]])

    def test_duplicate_registry_row_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            registry = write_obligation_fixture(target)
            rewrite_registry(
                registry,
                lambda doc: doc["obligations"].append(dict(doc["obligations"][0])),
            )
            completed = run_cli(
                "check", "--root", target, "--only", "obligations", "--json"
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM085", [item["code"] for item in report["findings"]])

    def test_unknown_gate_selector_is_refused_with_actionable_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            registry = write_obligation_fixture(target)
            rewrite_registry(
                registry,
                lambda doc: doc["obligations"][0].update(gate="law.not-a-gate"),
            )
            completed = run_cli(
                "check", "--root", target, "--only", "obligations", "--json"
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        matches = [item for item in report["findings"] if item["code"] == "PM086"]
        self.assertEqual(len(matches), 1)
        finding = matches[0]
        self.assertEqual(finding["obligation_id"], "law-contract-identity")
        self.assertEqual(finding["consequence"], 3)
        self.assertTrue(finding["blocked_transition"])
        self.assertTrue(finding["recovery"])

    def test_obligation_refusal_text_preserves_the_structured_action_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            registry = write_obligation_fixture(target)
            rewrite_registry(
                registry,
                lambda doc: doc["obligations"][0].update(gate="law.not-a-gate"),
            )
            structured = run_cli(
                "check", "--root", target, "--only", "obligations", "--json"
            )
            rendered = run_cli(
                "check", "--root", target, "--only", "obligations"
            )
        matches = [
            item for item in json.loads(structured.stdout)["findings"]
            if item["code"] == "PM086"
        ]
        self.assertEqual(structured.returncode, 1)
        self.assertEqual(rendered.returncode, 1)
        self.assertEqual(len(matches), 1)
        finding = matches[0]
        self.assertIn(f"obligation={finding['obligation_id']}", rendered.stdout)
        self.assertIn(f"consequence={finding['consequence']}", rendered.stdout)
        self.assertIn(
            f"blocked={finding['blocked_transition']!r}", rendered.stdout
        )
        self.assertIn(f"recovery={finding['recovery']!r}", rendered.stdout)

    def test_obligation_id_cannot_be_rebound_to_another_production_gate(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            registry = write_obligation_fixture(target)
            rewrite_registry(
                registry,
                lambda doc: doc["obligations"][0].update(
                    gate="law.governing-principle", finding="PM009"
                ),
            )
            specimen = (
                target
                / "tests"
                / "fixtures"
                / "promise-machine"
                / "obligations"
                / "law-contract-identity.json"
            )
            document = json.loads(specimen.read_text(encoding="utf-8"))
            document["mutation"]["old"] = (
                "No skill may claim more than its evidence establishes"
            )
            document["mutation"]["new"] = (
                "No skill may claim more than its evidence records"
            )
            specimen.write_text(json.dumps(document) + "\n", encoding="utf-8")
            completed = run_cli(
                "check", "--root", target, "--only", "obligations", "--json"
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        rebound = [
            item
            for item in report["findings"]
            if item["code"] == "PM086"
            and item["obligation_id"] == "law-contract-identity"
        ]
        self.assertEqual(len(rebound), 1)

    def test_missing_specimen_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            registry = write_obligation_fixture(target)
            rewrite_registry(
                registry,
                lambda doc: doc["obligations"][0].update(
                    specimen="tests/fixtures/promise-machine/obligations/missing.json"
                ),
            )
            completed = run_cli(
                "check", "--root", target, "--only", "obligations", "--json"
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM087", [item["code"] for item in report["findings"]])

    def test_escaping_specimen_path_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            registry = write_obligation_fixture(target)
            rewrite_registry(
                registry,
                lambda doc: doc["obligations"][0].update(specimen="../outside.json"),
            )
            completed = run_cli(
                "check", "--root", target, "--only", "obligations", "--json"
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM087", [item["code"] for item in report["findings"]])

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unavailable")
    def test_symlinked_specimen_is_refused_without_following_it(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "repo"
            target.mkdir()
            registry = write_obligation_fixture(target)
            outside = Path(directory) / "outside.json"
            outside.write_text("{}\n", encoding="utf-8")
            linked = (
                target
                / "tests"
                / "fixtures"
                / "promise-machine"
                / "obligations"
                / "linked.json"
            )
            linked.symlink_to(outside)
            rewrite_registry(
                registry,
                lambda doc: doc["obligations"][0].update(
                    specimen="tests/fixtures/promise-machine/obligations/linked.json"
                ),
            )
            completed = run_cli(
                "check", "--root", target, "--only", "obligations", "--json"
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM087", [item["code"] for item in report["findings"]])

    def test_unexpected_specimen_finding_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            write_obligation_fixture(target)
            specimen = (
                target
                / "tests"
                / "fixtures"
                / "promise-machine"
                / "obligations"
                / "law-contract-identity.json"
            )
            document = json.loads(specimen.read_text(encoding="utf-8"))
            document["mutation"]["old"] = "## Contract identity"
            document["mutation"]["new"] = "## Contract identity changed"
            specimen.write_text(json.dumps(document) + "\n", encoding="utf-8")
            completed = run_cli(
                "check", "--root", target, "--only", "obligations", "--json"
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM089", [item["code"] for item in report["findings"]])

    def test_duplicate_registry_json_key_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            registry = write_obligation_fixture(target)
            text = registry.read_text(encoding="utf-8").replace(
                '  "schema": "promise-machine-obligations/v1",',
                '  "schema": "promise-machine-obligations/v1",\n'
                '  "schema": "promise-machine-obligations/v1",',
                1,
            )
            registry.write_text(text, encoding="utf-8")
            completed = run_cli(
                "check", "--root", target, "--only", "obligations", "--json"
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM082", [item["code"] for item in report["findings"]])

    def test_non_unicode_scalar_json_strings_are_refused_before_use(self):
        cases = {
            "registry-path": ("registry", "PM082"),
            "specimen-mutation": ("specimen", "PM088"),
        }
        for name, (subject, code) in cases.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                target = Path(directory)
                registry = write_obligation_fixture(target)
                if subject == "registry":
                    rewrite_registry(
                        registry,
                        lambda doc: doc["obligations"][0].update(
                            specimen=(
                                "tests/fixtures/promise-machine/obligations/"
                                "\ud800.json"
                            )
                        ),
                    )
                else:
                    specimen = (
                        target
                        / "tests"
                        / "fixtures"
                        / "promise-machine"
                        / "obligations"
                        / "law-contract-identity.json"
                    )
                    document = json.loads(specimen.read_text(encoding="utf-8"))
                    document["mutation"]["new"] = "\ud800"
                    specimen.write_text(json.dumps(document) + "\n", encoding="utf-8")
                completed = run_cli(
                    "check", "--root", target, "--only", "obligations"
                )
            self.assertEqual(completed.returncode, 1)
            self.assertIn(code, completed.stdout)
            self.assertNotIn("Traceback", completed.stderr)

    def test_registry_only_obligation_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            registry = write_obligation_fixture(target)
            rewrite_registry(
                registry,
                lambda doc: doc["obligations"][0].update(id="law-registry-only"),
            )
            completed = run_cli(
                "check", "--root", target, "--only", "obligations", "--json"
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM085", [item["code"] for item in report["findings"]])

    def test_specimen_id_must_match_its_registry_row(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            write_obligation_fixture(target)
            specimen = (
                target
                / "tests"
                / "fixtures"
                / "promise-machine"
                / "obligations"
                / "law-contract-identity.json"
            )
            document = json.loads(specimen.read_text(encoding="utf-8"))
            document["obligation_id"] = "law-required-sections"
            specimen.write_text(json.dumps(document) + "\n", encoding="utf-8")
            completed = run_cli(
                "check", "--root", target, "--only", "obligations", "--json"
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM088", [item["code"] for item in report["findings"]])

    def test_invalid_consequence_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            registry = write_obligation_fixture(target)
            rewrite_registry(
                registry,
                lambda doc: doc["obligations"][0].update(consequence=4),
            )
            completed = run_cli(
                "check", "--root", target, "--only", "obligations", "--json"
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM084", [item["code"] for item in report["findings"]])

    def test_a_retained_row_detects_removal_of_its_production_gate(self):
        real_validator = promise_machine_module.validate_law_document

        def without_governing_principle_gate(payload, text, shown):
            return [
                finding
                for finding in real_validator(payload, text, shown)
                if finding.code != "PM009"
            ]

        with mock.patch.object(
            promise_machine_module,
            "validate_law_document",
            without_governing_principle_gate,
        ):
            law, law_findings = promise_machine_module.check_law(ROOT)
            _, findings = promise_machine_module.check_obligations(ROOT, law)
        self.assertEqual(law_findings, [])
        failed = [
            finding
            for finding in findings
            if finding.code == "PM089"
            and finding.obligation_id == "law-governing-principle"
        ]
        self.assertEqual(len(failed), 1)


class PromiseCompositionGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = json.loads(COMPOSITION_CASES.read_text(encoding="utf-8"))
        cls.coverage = json.loads(
            (ROOT / "tests" / "promise_machine_coverage.json").read_text(
                encoding="utf-8"
            )
        )

    def relation(self, relation_id):
        return next(
            item for item in self.cases["relations"]
            if item["relation_id"] == relation_id
        )

    def assert_positive(self, relation_id):
        relation = self.relation(relation_id)
        spec = promise_machine_module.COMPOSITION_RELATIONS[relation_id]
        findings = promise_machine_module.validate_composition_record(
            ROOT,
            spec,
            copy.deepcopy(relation["positive"]),
            f"{COMPOSITION_CASES.relative_to(ROOT).as_posix()}#{relation_id}.positive",
        )
        self.assertEqual(findings, [])

    def assert_negative(self, relation_id, index):
        relation = self.relation(relation_id)
        spec = promise_machine_module.COMPOSITION_RELATIONS[relation_id]
        negative = relation["negative"][index]
        mutated, error = promise_machine_module.apply_composition_mutations(
            relation["positive"], negative["mutations"]
        )
        self.assertIsNone(error)
        path = (
            f"{COMPOSITION_CASES.relative_to(ROOT).as_posix()}#"
            f"{relation_id}.negative[{index}]"
        )
        findings = promise_machine_module.validate_composition_record(
            ROOT, spec, mutated, path
        )
        self.assertEqual(semantic_codes(findings), ["PM097"])
        finding = findings[0]
        producer = relation["positive"]["producer"]["promise_id"]
        consumer = relation["positive"]["consumer"]["promise_id"]
        self.assertEqual(finding.promise_id, producer)
        self.assertEqual(finding.obligation_id, relation["obligation_id"])
        self.assertEqual(
            finding.blocked_transition,
            relation["positive"]["consumer"]["transition"],
        )
        for value in (relation_id, producer, consumer, negative["field"]):
            self.assertIn(value, finding.message)
        self.assertTrue(finding.recovery)

    def test_lemma_relation_accepts_its_bounded_positive_case(self):
        self.assert_positive("lemma-retrieval-to-berean-corpus")

    def test_lazarus_relation_accepts_its_bounded_positive_case(self):
        self.assert_positive("lazarus-rpc-to-berean-answer")

    def test_berean_relation_accepts_its_bounded_positive_case(self):
        self.assert_positive("berean-promotion-to-ariadne-capture")

    def test_janus_relation_accepts_its_bounded_positive_case(self):
        self.assert_positive("janus-bounded-to-ariadne-capture")

    def test_ariadne_relation_accepts_its_bounded_positive_case(self):
        self.assert_positive("ariadne-verification-to-fiat-delivery")

    def test_fiat_observation_relation_accepts_its_bounded_positive_case(self):
        self.assert_positive("fiat-observation-to-synkrisis-cohort")

    def test_synkrisis_relation_accepts_its_bounded_positive_case(self):
        self.assert_positive("synkrisis-verification-to-fiat-integration")

    def test_lemma_relation_refuses_a_changed_producer_identity(self):
        self.assert_negative("lemma-retrieval-to-berean-corpus", 0)

    def test_lemma_relation_refuses_a_strengthened_consumer_transition(self):
        self.assert_negative("lemma-retrieval-to-berean-corpus", 1)

    def test_lazarus_relation_refuses_lost_evidence_references(self):
        self.assert_negative("lazarus-rpc-to-berean-answer", 0)

    def test_lazarus_relation_refuses_an_unproved_proof_claim(self):
        self.assert_negative("lazarus-rpc-to-berean-answer", 1)

    def test_berean_relation_refuses_dropped_unknowns(self):
        self.assert_negative("berean-promotion-to-ariadne-capture", 0)

    def test_berean_relation_refuses_answer_truth_overclaim(self):
        self.assert_negative("berean-promotion-to-ariadne-capture", 1)

    def test_janus_relation_refuses_dropped_conflicts(self):
        self.assert_negative("janus-bounded-to-ariadne-capture", 0)

    def test_janus_relation_refuses_broadened_scope(self):
        self.assert_negative("janus-bounded-to-ariadne-capture", 1)

    def test_ariadne_relation_refuses_a_changed_subject(self):
        self.assert_negative("ariadne-verification-to-fiat-delivery", 0)

    def test_ariadne_relation_refuses_a_weakened_consequence(self):
        self.assert_negative("ariadne-verification-to-fiat-delivery", 1)

    def test_fiat_observation_relation_refuses_delivery_evidence_overclaim(self):
        self.assert_negative("fiat-observation-to-synkrisis-cohort", 0)

    def test_fiat_observation_relation_refuses_lost_recovery(self):
        self.assert_negative("fiat-observation-to-synkrisis-cohort", 1)

    def test_synkrisis_relation_refuses_lost_counterevidence(self):
        self.assert_negative("synkrisis-verification-to-fiat-integration", 0)

    def test_synkrisis_relation_refuses_model_graded_domain_overclaim(self):
        self.assert_negative("synkrisis-verification-to-fiat-integration", 1)

    def test_repository_declares_exactly_the_seven_root_law_relations(self):
        expected = {
            "lemma-retrieval-to-berean-corpus",
            "lazarus-rpc-to-berean-answer",
            "berean-promotion-to-ariadne-capture",
            "janus-bounded-to-ariadne-capture",
            "ariadne-verification-to-fiat-delivery",
            "fiat-observation-to-synkrisis-cohort",
            "synkrisis-verification-to-fiat-integration",
        }
        self.assertEqual(set(promise_machine_module.COMPOSITION_RELATIONS), expected)
        self.assertEqual(
            {item["relation_id"] for item in self.cases["relations"]}, expected
        )

    def test_registered_composition_classes_are_owned_by_native_promises(self):
        inventory, findings = promise_machine_module.discover_inventory(ROOT)
        self.assertEqual(findings, [])
        findings = promise_machine_module.validate_composition_registrations(
            ROOT, inventory
        )
        self.assertEqual(findings, [])

    def test_composition_refuses_an_undeclared_producer_class(self):
        relation_id = "lemma-retrieval-to-berean-corpus"
        spec = copy.deepcopy(
            promise_machine_module.COMPOSITION_RELATIONS[relation_id]
        )
        spec["producer_classes"] = ("recorded", "attested")
        spec["consumer_classes"] = ("recorded", "attested", "checked")
        inventory, inventory_findings = promise_machine_module.discover_inventory(
            ROOT
        )
        self.assertEqual(inventory_findings, [])
        with mock.patch.dict(
            promise_machine_module.COMPOSITION_RELATIONS,
            {relation_id: spec},
        ):
            findings = promise_machine_module.validate_composition_registrations(
                ROOT, inventory
            )
        self.assertEqual(semantic_codes(findings), ["PM097"])
        self.assertIn("not declared by promise lemma-corpus-provenance", findings[0].message)

    def test_composition_refuses_an_undeclared_consumer_addition(self):
        relation_id = "berean-promotion-to-ariadne-capture"
        spec = copy.deepcopy(
            promise_machine_module.COMPOSITION_RELATIONS[relation_id]
        )
        spec["consumer_classes"] = (*spec["consumer_classes"], "attested")
        inventory, inventory_findings = promise_machine_module.discover_inventory(
            ROOT
        )
        self.assertEqual(inventory_findings, [])
        with mock.patch.dict(
            promise_machine_module.COMPOSITION_RELATIONS,
            {relation_id: spec},
        ):
            findings = promise_machine_module.validate_composition_registrations(
                ROOT, inventory
            )
        self.assertEqual(semantic_codes(findings), ["PM097"])
        self.assertIn("not declared by promise ariadne-capture-statement", findings[0].message)

    def test_composition_refuses_a_dropped_inherited_class(self):
        relation_id = "synkrisis-verification-to-fiat-integration"
        spec = copy.deepcopy(
            promise_machine_module.COMPOSITION_RELATIONS[relation_id]
        )
        spec["consumer_classes"] = ("recorded",)
        inventory, inventory_findings = promise_machine_module.discover_inventory(
            ROOT
        )
        self.assertEqual(inventory_findings, [])
        with mock.patch.dict(
            promise_machine_module.COMPOSITION_RELATIONS,
            {relation_id: spec},
        ):
            findings = promise_machine_module.validate_composition_registrations(
                ROOT, inventory
            )
        self.assertEqual(semantic_codes(findings), ["PM097"])
        self.assertIn("dropped producer classes ['recomputed']", findings[0].message)

    def test_composition_refuses_an_unknown_native_promise_identity(self):
        relation_id = "ariadne-verification-to-fiat-delivery"
        spec = copy.deepcopy(
            promise_machine_module.COMPOSITION_RELATIONS[relation_id]
        )
        spec["producer"] = "missing-native-promise"
        inventory, inventory_findings = promise_machine_module.discover_inventory(
            ROOT
        )
        self.assertEqual(inventory_findings, [])
        with mock.patch.dict(
            promise_machine_module.COMPOSITION_RELATIONS,
            {relation_id: spec},
        ):
            findings = promise_machine_module.validate_composition_registrations(
                ROOT, inventory
            )
        self.assertEqual(semantic_codes(findings), ["PM097"])
        self.assertIn("resolves 0 times", findings[0].message)

    def test_composition_obligation_evaluator_checks_native_promise_classes(self):
        relation_id = "berean-promotion-to-ariadne-capture"
        spec = copy.deepcopy(
            promise_machine_module.COMPOSITION_RELATIONS[relation_id]
        )
        spec["consumer_classes"] = (*spec["consumer_classes"], "attested")
        registry = json.loads(OBLIGATION_REGISTRY.read_text(encoding="utf-8"))
        row = next(
            item
            for item in registry["obligations"]
            if item["id"] == spec["obligation_id"]
        )
        inventory, inventory_findings = promise_machine_module.discover_inventory(
            ROOT
        )
        self.assertEqual(inventory_findings, [])
        with mock.patch.dict(
            promise_machine_module.COMPOSITION_RELATIONS,
            {relation_id: spec},
        ):
            findings = (
                promise_machine_module.validate_composition_obligation_specimen(
                    ROOT,
                    COMPOSITION_CASES.relative_to(ROOT),
                    copy.deepcopy(self.cases),
                    row,
                    inventory=inventory,
                )
            )
        self.assertEqual(semantic_codes(findings), ["PM089"])
        self.assertIn("did not resolve its native promise boundary", findings[0].message)

    def test_repository_composition_fixture_digest_is_coverage_bound(self):
        count, findings = promise_machine_module.check_composition(
            ROOT, self.coverage
        )
        self.assertEqual(count, 7)
        self.assertEqual(findings, [])

    def test_composition_cli_executes_all_seven_relations(self):
        completed = run_cli("check", "--only", "composition", "--json")
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(report["counts"]["composition_relations"], 7)
        self.assertEqual(report["findings"], [])

    def test_each_relation_has_one_positive_and_two_negative_cases(self):
        self.assertEqual(len(self.cases["relations"]), 7)
        for relation in self.cases["relations"]:
            with self.subTest(relation=relation["relation_id"]):
                self.assertEqual(set(relation), {
                    "obligation_id", "relation_id", "positive", "negative"
                })
                self.assertEqual(len(relation["negative"]), 2)

    def test_removing_each_relation_is_refused_by_stable_identity(self):
        for removed in self.cases["relations"]:
            with self.subTest(relation=removed["relation_id"]):
                document = copy.deepcopy(self.cases)
                document["relations"] = [
                    item for item in document["relations"]
                    if item["relation_id"] != removed["relation_id"]
                ]
                count, findings = promise_machine_module.validate_composition_cases(
                    ROOT, document, COMPOSITION_CASES.relative_to(ROOT).as_posix()
                )
                self.assertEqual(count, 6)
                self.assertEqual(semantic_codes(findings), ["PM097"])
                self.assertEqual(findings[0].obligation_id, removed["obligation_id"])

    def test_duplicate_relation_identity_is_refused(self):
        document = copy.deepcopy(self.cases)
        document["relations"].append(copy.deepcopy(document["relations"][0]))
        _, findings = promise_machine_module.validate_composition_cases(
            ROOT, document, COMPOSITION_CASES.relative_to(ROOT).as_posix()
        )
        self.assertEqual(semantic_codes(findings), ["PM097"])
        self.assertIn("repeated", findings[0].message)

    def test_unknown_relation_identity_is_refused(self):
        document = copy.deepcopy(self.cases)
        document["relations"][0]["relation_id"] = "unknown-relation"
        _, findings = promise_machine_module.validate_composition_cases(
            ROOT, document, COMPOSITION_CASES.relative_to(ROOT).as_posix()
        )
        self.assertIn("PM097", semantic_codes(findings))
        self.assertTrue(any("unknown-relation" in item.message for item in findings))

    def test_recorded_evidence_cannot_be_promoted_to_proved_by_composition(self):
        relation = self.relation("lazarus-rpc-to-berean-answer")
        record = copy.deepcopy(relation["positive"])
        record["consumer"]["bindings"]["evidence-classes"] = [
            "recorded", "checked", "proved"
        ]
        findings = promise_machine_module.validate_composition_record(
            ROOT,
            promise_machine_module.COMPOSITION_RELATIONS[relation["relation_id"]],
            record,
            "recorded-strengthening.json",
        )
        self.assertEqual(semantic_codes(findings), ["PM097"])
        self.assertIn("evidence-classes", findings[0].message)


class PromiseSemanticGateTests(unittest.TestCase):
    def transition(self, level):
        return load_fixture(f"consequences/level-{level}.json")

    def evaluate(self, document, *, root=ROOT, expected=None):
        return promise_machine_module.evaluate_transition_record(
            root,
            document,
            "semantic-test.json",
            expected_obligation=expected or document.get("obligation_id"),
        )

    def valid_exception(self):
        return load_fixture("exceptions/valid.json")

    def exception_expected(self):
        return {
            "promise_id": "fixture-promise",
            "gate": "fixture.gate",
            "subject": "fixture-subject",
            "scope": "fixture-scope",
            "consequence": 3,
            "transition": "publish the fixture result",
        }

    def check_exception(self, document, *, evaluated_at="2026-08-30T00:00:00Z"):
        return promise_machine_module.validate_exception_record(
            ROOT,
            document,
            "exception-test.json",
            expected=self.exception_expected(),
            evaluated_at=evaluated_at,
        )

    def test_level_zero_uses_its_content_only_path(self):
        self.assertEqual(self.evaluate(self.transition(0)), [])

    def test_level_one_uses_structure_and_provenance(self):
        self.assertEqual(self.evaluate(self.transition(1)), [])

    def test_level_two_uses_tests_negative_and_recovery_evidence(self):
        self.assertEqual(self.evaluate(self.transition(2)), [])

    def test_level_three_adds_authority_and_independent_evidence(self):
        self.assertEqual(self.evaluate(self.transition(3)), [])

        for source in ("content", "authority"):
            with self.subTest(source=source):
                replayed = self.transition(3)
                independent = next(
                    item for item in replayed["evidence"] if item["role"] == "independent"
                )
                if source == "content":
                    reused = next(
                        item for item in replayed["evidence"] if item["role"] == "content"
                    )["reference"]
                else:
                    reused = replayed["authority"]
                independent["reference"] = dict(reused)
                self.assertEqual(semantic_codes(self.evaluate(replayed)), ["PM090"])

    def test_level_three_refuses_a_level_two_only_replay(self):
        document = load_fixture("consequences/level-3-level-2-only.json")
        self.assertEqual(semantic_codes(self.evaluate(document)), ["PM090"])

    def test_visible_unknowns_cannot_authorise_a_positive_transition(self):
        document = load_fixture("consequences/unknown.json")
        self.assertEqual(semantic_codes(self.evaluate(document)), ["PM091"])
        document["unknowns"] = ["unresolved"] * 65
        self.assertEqual(semantic_codes(self.evaluate(document)), ["PM090"])

    def test_unknown_or_malformed_evidence_cannot_authorise(self):
        document = self.transition(0)
        document["obligation_id"] = "law-unknowns-non-authorising"
        document["evidence"][0]["status"] = "unknown"
        self.assertEqual(semantic_codes(self.evaluate(document)), ["PM091"])

        for field, value in (("class", []), ("status", {})):
            with self.subTest(field=field):
                malformed = self.transition(0)
                malformed["evidence"][0][field] = value
                self.assertEqual(semantic_codes(self.evaluate(malformed)), ["PM090"])

    def test_not_run_evidence_status_cannot_authorise(self):
        document = self.transition(0)
        document["obligation_id"] = "law-unknowns-non-authorising"
        document["evidence"][0]["status"] = "not-run"
        self.assertEqual(semantic_codes(self.evaluate(document)), ["PM091"])

    def test_missing_evidence_cannot_authorise(self):
        document = self.transition(0)
        document["obligation_id"] = "law-unknowns-non-authorising"
        document["evidence"] = []
        self.assertEqual(semantic_codes(self.evaluate(document)), ["PM091"])

    def test_stale_evidence_status_cannot_authorise(self):
        document = self.transition(0)
        document["obligation_id"] = "law-unknowns-non-authorising"
        document["evidence"][0]["status"] = "stale"
        self.assertEqual(semantic_codes(self.evaluate(document)), ["PM091"])

    def test_missing_transition_declaration_is_refused(self):
        paths = (
            "tests/fixtures/promise-machine/consequences/declarations/missing.json",
            "tests/fixtures/promise-machine/consequences/declarations/invalid\u0000.json",
        )
        for path in paths:
            with self.subTest(path=path):
                document = self.transition(0)
                document["declaration"] = {"path": path, "sha256": "0" * 64}
                self.assertEqual(semantic_codes(self.evaluate(document)), ["PM090"])

    def test_stale_transition_declaration_digest_is_refused(self):
        document = self.transition(0)
        document["declaration"]["sha256"] = "0" * 64
        self.assertEqual(semantic_codes(self.evaluate(document)), ["PM090"])

    def test_mismatched_transition_declaration_is_refused(self):
        mutations = (
            ("level-0.json", "promise_id", "different-promise", False),
            ("level-0.json", "consequence", False, False),
            ("level-1.json", "consequence", True, False),
        ) + tuple(
            ("level-0.json", "transition", f"publish{separator}second", True)
            for separator in ("\n", "\r", "\u2028", "\u2029")
        )
        for fixture, field, value, mirror in mutations:
            with self.subTest(fixture=fixture, field=field, value=value):
                with tempfile.TemporaryDirectory() as directory:
                    target = Path(directory)
                    copy_semantic_fixtures(target)
                    transition_path = (
                        target
                        / "tests/fixtures/promise-machine/consequences"
                        / fixture
                    )
                    document = json.loads(
                        transition_path.read_text(encoding="utf-8")
                    )
                    declaration_path = target / document["declaration"]["path"]
                    declaration = json.loads(
                        declaration_path.read_text(encoding="utf-8")
                    )
                    declaration[field] = value
                    if mirror:
                        document[field] = value
                    declaration_path.write_text(
                        json.dumps(declaration, indent=2) + "\n", encoding="utf-8"
                    )
                    document["declaration"]["sha256"] = hashlib.sha256(
                        declaration_path.read_bytes()
                    ).hexdigest()
                    findings = self.evaluate(document, root=target)
                self.assertEqual(semantic_codes(findings), ["PM090"])

    def test_evidence_subject_must_match_the_transition(self):
        document = self.transition(1)
        document["evidence"][0]["subject"] = "different-subject"
        self.assertEqual(semantic_codes(self.evaluate(document)), ["PM090"])

    def test_evidence_scope_must_match_the_transition(self):
        document = self.transition(1)
        document["evidence"][0]["scope"] = "different-scope"
        self.assertEqual(semantic_codes(self.evaluate(document)), ["PM090"])

    def test_complete_exception_is_accepted_inside_its_recorded_time(self):
        self.assertEqual(self.check_exception(self.valid_exception()), [])

    def test_absent_exception_reference_is_refused(self):
        document = self.transition(3)
        document["exception"] = {
            "path": "tests/fixtures/promise-machine/exceptions/missing.json",
            "sha256": "0" * 64,
        }
        self.assertEqual(semantic_codes(self.evaluate(document)), ["PM093"])

    def test_exception_without_a_durable_reason_record_is_refused(self):
        document = self.valid_exception()
        document["record"] = {
            "path": "tests/fixtures/promise-machine/exceptions/missing.md",
            "sha256": "0" * 64,
        }
        self.assertEqual(semantic_codes(self.check_exception(document)), ["PM093"])
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            copy_semantic_fixtures(target)
            blank = (
                target
                / "tests/fixtures/promise-machine/exceptions/blank.md"
            )
            blank.write_bytes(b"")
            blank_document = self.valid_exception()
            blank_document["record"] = {
                "path": blank.relative_to(target).as_posix(),
                "sha256": hashlib.sha256(b"").hexdigest(),
            }
            findings = promise_machine_module.validate_exception_record(
                target,
                blank_document,
                "blank-reason.json",
                expected=self.exception_expected(),
                evaluated_at="2026-08-30T00:00:00Z",
            )
        self.assertEqual(semantic_codes(findings), ["PM093"])

    def test_expired_exception_is_refused(self):
        document = self.valid_exception()
        document["expiry"] = {"at": "2026-08-29T23:59:59Z"}
        self.assertEqual(semantic_codes(self.check_exception(document)), ["PM093"])

    def test_revoked_exception_is_refused(self):
        document = self.valid_exception()
        document["revoked"] = True
        self.assertEqual(semantic_codes(self.check_exception(document)), ["PM093"])

    def test_unresolvable_exception_authority_is_refused(self):
        document = self.valid_exception()
        document["authority"]["reference"] = {
            "path": "tests/fixtures/promise-machine/consequences/missing-authority.json",
            "sha256": "0" * 64,
        }
        self.assertEqual(semantic_codes(self.check_exception(document)), ["PM093"])
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            copy_semantic_fixtures(target)
            padded = self.valid_exception()
            authority_path = target / padded["authority"]["reference"]["path"]
            authority = json.loads(authority_path.read_text(encoding="utf-8"))
            authority["id"] = " fixture-authority "
            authority_path.write_text(
                json.dumps(authority, indent=2) + "\n", encoding="utf-8"
            )
            padded["authority"]["id"] = " fixture-authority "
            padded["authority"]["reference"]["sha256"] = hashlib.sha256(
                authority_path.read_bytes()
            ).hexdigest()
            findings = promise_machine_module.validate_exception_record(
                target,
                padded,
                "padded-authority.json",
                expected=self.exception_expected(),
                evaluated_at="2026-08-30T00:00:00Z",
            )
        self.assertEqual(semantic_codes(findings), ["PM093"])

    def test_exception_promise_must_match_the_transition(self):
        document = self.valid_exception()
        document["promise_id"] = "different-promise"
        self.assertEqual(semantic_codes(self.check_exception(document)), ["PM093"])

    def test_exception_gate_must_match_the_transition(self):
        document = self.valid_exception()
        document["gate"] = "different.gate"
        self.assertEqual(semantic_codes(self.check_exception(document)), ["PM093"])

    def test_exception_subject_must_match_the_transition(self):
        document = self.valid_exception()
        document["subject"] = "different-subject"
        self.assertEqual(semantic_codes(self.check_exception(document)), ["PM093"])

    def test_exception_scope_must_match_the_transition(self):
        document = self.valid_exception()
        document["scope"] = "different-scope"
        self.assertEqual(semantic_codes(self.check_exception(document)), ["PM093"])

    def test_calendar_invalid_exception_expiry_is_refused(self):
        document = self.valid_exception()
        document["expiry"] = {"at": "2026-02-30T00:00:00Z"}
        self.assertEqual(semantic_codes(self.check_exception(document)), ["PM093"])

    def test_calendar_invalid_exception_evaluation_time_is_refused(self):
        findings = self.check_exception(
            self.valid_exception(), evaluated_at="2026-02-30T00:00:00Z"
        )
        self.assertEqual(semantic_codes(findings), ["PM093"])

    def test_non_expiring_exception_requires_a_reason(self):
        reasons = ("", " padded reason ") + tuple(
            f"reason{separator}second" for separator in ("\n", "\r", "\u2028", "\u2029")
        )
        for reason in reasons:
            with self.subTest(reason=reason):
                document = self.valid_exception()
                document["expiry"] = {"not_applicable": reason}
                self.assertEqual(
                    semantic_codes(self.check_exception(document)), ["PM093"]
                )

    def test_repository_core_checker_source_is_static_guard_clean(self):
        count, findings = promise_machine_module.check_core_imports(ROOT)
        self.assertEqual(count, 1)
        self.assertEqual(findings, [])

    def test_forbidden_network_credential_and_process_imports_are_refused(self):
        sources = (
            "import socket\n",
            "from urllib import request\n",
            "import httpx\nhttpx.get('https://example.invalid')\n",
            "import aiohttp\naiohttp.ClientSession()\n",
            "import urllib3\nurllib3.PoolManager()\n",
            "import websockets\nwebsockets.connect('wss://example.invalid')\n",
            "import getpass\n",
            "import subprocess\n",
            "import asyncio\n",
            "import ctypes\nctypes.CDLL(None).system(b'fixture')\n",
            "import pty\npty.spawn(['/bin/sh'])\n",
            "import concurrent.futures\nconcurrent.futures.ProcessPoolExecutor()\n",
            "from os import *\nsystem('fixture')\n",
        )
        for source in sources:
            with self.subTest(source=source.strip()):
                findings = promise_machine_module.check_core_source_text(
                    source, "forbidden-import.py"
                )
                self.assertEqual(semantic_codes(findings), ["PM094"])

    def test_forbidden_shell_dynamic_and_environment_calls_are_refused(self):
        sources = (
            "import os\nos.system('fixture')\n",
            "import os\nos.getenv('TOKEN')\n",
            "eval('1 + 1')\n",
            "compile('1', '<fixture>', 'eval')\n",
            "import os\nos.environ['TOKEN']\n",
            "import builtins\nbuiltins.eval('1 + 1')\n",
            "__builtins__.eval('1 + 1')\n",
            "__builtins__['exec']('fixture = 1')\n",
            "open('fixture', 'w').write('x')\n",
            "from pathlib import Path\nPath('fixture').write_text('x')\n",
            "from pathlib import Path\nPath('fixture').write_bytes(b'x')\n",
            "from pathlib import Path\nPath('fixture').open('w').write('x')\n",
            "from pathlib import Path\nPath('fixture').replace('target')\n",
            "from pathlib import Path\npath = Path('fixture')\npath.replace('target')\n",
            "import tempfile\ntempfile.NamedTemporaryFile()\n",
            "import tempfile\ntempfile.TemporaryFile()\n",
            "import os\nos.rename('fixture', 'target')\n",
            "import os\nos.write(1, b'x')\n",
            "import os\nos.putenv('FIAT884', 'x')\n",
            "import os\nos.unsetenv('FIAT884')\n",
            "import os\nos.chdir('/tmp')\n",
            "import os\nos.umask(0)\n",
            "import os\nos.kill(1, 0)\n",
            "from pathlib import Path\nPath('/etc/passwd').read_text()\n",
            "from pathlib import Path\n(Path.home() / '.config').read_text()\n",
            "import os\nos.open('/etc/passwd', os.O_RDONLY)\n",
        )
        for source in sources:
            with self.subTest(source=source.splitlines()[-1]):
                findings = promise_machine_module.check_core_source_text(
                    source, "forbidden-call.py"
                )
                self.assertEqual(semantic_codes(findings), ["PM094"])

    def test_aliases_and_dynamic_lookups_cannot_hide_forbidden_calls(self):
        sources = (
            "import os as operating\noperating.system('fixture')\n",
            "from os import system as launch\nlaunch('fixture')\n",
            "import os\ngetattr(os, 'system')('fixture')\n",
            "import builtins\ngetattr(builtins, 'eval')('1 + 1')\n",
            "import builtins\nbuiltins.__dict__['eval']('1 + 1')\n",
            "import os\nos.__dict__['system']('fixture')\n",
            "import os\nos.getenvb(b'SECRET')\n",
            "import os\nos.environb[b'SECRET']\n",
            "getattr(__builtins__, 'open')('/etc/passwd')\n",
            "__builtins__.open('/etc/passwd')\n",
            "__builtins__['open']('/etc/passwd')\n",
            "import os\ngetattr(os, 'open')('/etc/passwd', os.O_RDONLY)\n",
            "from pathlib import Path\ngetattr(Path, 'home')().joinpath('.config').read_text()\n",
            "import os\ngetattr(os, 'rename')('fixture', 'target')\n",
            "from pathlib import Path\ngetattr(Path, 'write_text')(Path('fixture'), 'x')\n",
            "import tempfile\ngetattr(tempfile, 'mkstemp')()\n",
            "__builtins__.get('open')('/etc/passwd')\n",
            "import os\nvars(os)['open']('/etc/passwd', os.O_RDONLY)\n",
            "from pathlib import Path\nvars(Path)['home']().joinpath('.config').read_text()\n",
            "import tempfile\ntempfile.__dict__['mkstemp']()\n",
        )
        for source in sources:
            with self.subTest(source=source.splitlines()[-1]):
                findings = promise_machine_module.check_core_source_text(
                    source, "forbidden-alias.py"
                )
                self.assertEqual(semantic_codes(findings), ["PM094"])

    def test_core_check_remains_clean_when_network_and_children_are_denied(self):
        confined_root = ROOT.resolve()
        real_os_fdopen = os.fdopen
        real_os_open = os.open
        real_path_open = Path.open

        def inside_root(path):
            try:
                candidate = Path(path)
            except TypeError:
                return False
            if not candidate.is_absolute():
                candidate = confined_root / candidate
            try:
                candidate.resolve(strict=False).relative_to(confined_root)
            except (OSError, RuntimeError, ValueError):
                return False
            return True

        def guarded_os_fdopen(descriptor, mode="r", *args, **kwargs):
            if any(marker in mode for marker in "wax+"):
                raise AssertionError("write-capable os.fdopen used")
            return real_os_fdopen(descriptor, mode, *args, **kwargs)

        def guarded_os_open(path, flags, *args, **kwargs):
            write_flags = (
                os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND
            )
            if flags & write_flags:
                raise AssertionError("write-capable os.open used")
            if kwargs.get("dir_fd") is None and not inside_root(path):
                raise AssertionError("out-of-root os.open used")
            return real_os_open(path, flags, *args, **kwargs)

        def guarded_path_open(path, mode="r", *args, **kwargs):
            if any(marker in mode for marker in "wax+"):
                raise AssertionError("write-capable Path.open used")
            if not inside_root(path):
                raise AssertionError("out-of-root Path.open used")
            return real_path_open(path, mode, *args, **kwargs)

        denied = mock.Mock(side_effect=AssertionError("side effect used"))
        patches = (
            mock.patch("socket.socket", side_effect=AssertionError("network used")),
            mock.patch.object(
                subprocess, "Popen", side_effect=AssertionError("child used")
            ),
            mock.patch("builtins.open", denied),
            mock.patch.object(promise_machine_module, "atomic_write", denied),
            mock.patch.object(os, "fdopen", side_effect=guarded_os_fdopen),
            mock.patch.object(os, "open", side_effect=guarded_os_open),
            mock.patch.object(Path, "open", new=guarded_path_open),
        )
        patches += tuple(
            mock.patch.object(os, name, denied)
            for name in ("getenv", "getenvb")
            if hasattr(os, name)
        )
        denied_attributes = (
            (
                os,
                (
                    "chmod",
                    "chown",
                    "chdir",
                    "chroot",
                    "fchdir",
                    "fchmod",
                    "fchown",
                    "ftruncate",
                    "lchmod",
                    "lchown",
                    "link",
                    "kill",
                    "killpg",
                    "makedirs",
                    "mkdir",
                    "mkfifo",
                    "mknod",
                    "pwrite",
                    "pwritev",
                    "putenv",
                    "remove",
                    "removedirs",
                    "rename",
                    "renames",
                    "replace",
                    "rmdir",
                    "symlink",
                    "truncate",
                    "umask",
                    "unlink",
                    "unsetenv",
                    "utime",
                    "write",
                    "writev",
                ),
            ),
            (
                Path,
                (
                    "chmod",
                    "hardlink_to",
                    "lchmod",
                    "link_to",
                    "mkdir",
                    "rename",
                    "replace",
                    "rmdir",
                    "symlink_to",
                    "touch",
                    "unlink",
                    "write_bytes",
                    "write_text",
                ),
            ),
            (
                tempfile,
                (
                    "NamedTemporaryFile",
                    "SpooledTemporaryFile",
                    "TemporaryDirectory",
                    "TemporaryFile",
                    "mkdtemp",
                    "mkstemp",
                ),
            ),
        )
        for owner, names in denied_attributes:
            patches += tuple(
                mock.patch.object(owner, name, denied)
                for name in names
                if hasattr(owner, name)
            )
        output = io.StringIO()
        with ExitStack() as stack:
            for patch in patches:
                stack.enter_context(patch)
            with redirect_stdout(output):
                status = promise_machine_module.main(
                    [
                        "check",
                        "--only",
                        "obligations,contracts,exceptions,imports",
                        "--json",
                    ]
                )
        report = json.loads(output.getvalue())
        self.assertEqual(status, 0)
        self.assertEqual(report["findings"], [])

    def test_refusal_payload_requires_every_actionable_field(self):
        valid = {
            "code": "PM092",
            "fault": "obligation",
            "path": "fixture.json",
            "message": "fixture refusal",
            "remedy": "repair the fixture",
            "promise_id": "fixture-promise",
            "obligation_id": "law-refusal-shape",
            "consequence": 2,
            "blocked_transition": "publish the fixture",
            "recovery": "repair and rerun the fixture",
        }
        self.assertEqual(
            promise_machine_module.validate_refusal_payload(valid, "fixture.json"),
            [],
        )
        for field in valid:
            with self.subTest(field=field):
                incomplete = dict(valid)
                incomplete.pop(field)
                findings = promise_machine_module.validate_refusal_payload(
                    incomplete, "fixture.json"
                )
                self.assertEqual(semantic_codes(findings), ["PM092"])

        for field in (
            "fault",
            "path",
            "message",
            "remedy",
            "blocked_transition",
            "recovery",
        ):
            with self.subTest(padded=field):
                padded = dict(valid)
                padded[field] = f" {padded[field]} "
                findings = promise_machine_module.validate_refusal_payload(
                    padded, "fixture.json"
                )
                self.assertEqual(semantic_codes(findings), ["PM092"])

        terminated = (
            ("fault", "\n"),
            ("path", "\r"),
            ("message", "\u2028"),
            ("remedy", "\u2029"),
            ("blocked_transition", "\n"),
            ("recovery", "\n"),
        )
        for field, separator in terminated:
            with self.subTest(terminated=field, separator=repr(separator)):
                multiline = dict(valid)
                multiline[field] = f"{multiline[field]}{separator}continued"
                findings = promise_machine_module.validate_refusal_payload(
                    multiline, "fixture.json"
                )
                self.assertEqual(semantic_codes(findings), ["PM092"])

    def test_text_and_json_reports_share_one_actionable_finding(self):
        finding = promise_machine_module.Finding(
            "PM099",
            "structural",
            "fixture.json",
            "fixture failure",
            "repair the fixture",
            promise_id="INVALID PROMISE",
            obligation_id="INVALID OBLIGATION",
        )
        json_output = io.StringIO()
        with redirect_stdout(json_output):
            json_status = promise_machine_module.report(
                "check", ROOT, [], [finding], as_json=True
            )
        text_output = io.StringIO()
        with redirect_stdout(text_output):
            text_status = promise_machine_module.report(
                "check", ROOT, [], [finding], as_json=False
            )
        payload = json.loads(json_output.getvalue())["findings"][0]
        rendered = text_output.getvalue()
        self.assertEqual((json_status, text_status), (1, 1))
        self.assertEqual(payload["promise_id"], "promise-machine-contract")
        self.assertIsNone(payload["obligation_id"])
        self.assertIn(f"promise={payload['promise_id']}", rendered)
        self.assertIn(f"consequence={payload['consequence']}", rendered)
        self.assertIn(f"blocked={payload['blocked_transition']!r}", rendered)
        self.assertIn(f"recovery={payload['recovery']!r}", rendered)

    def test_declared_exceptions_require_structured_canonical_records(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            plugin = make_plugin(target)
            fields = {
                "Promise": "The named check accepted the subject.",
                "Evidence": "example record",
                "Evidence classes": "checked",
                "Boundary": "No claim beyond the named rule.",
                "Authorises": "Use of the checked result.",
                "Consequence": "1",
                "Refuses": "Use of a failed result.",
                "Recovery": "Repair and rerun.",
                "Exceptions": (
                    "authority: fixture; scope: fixture; record: fixture; expiry: never"
                ),
            }
            write_skill(plugin, fields=fields)
            completed = run_cli(
                "check", "--root", target, "--only", "inventory,structure", "--json"
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM038", [item["code"] for item in report["findings"]])

        for field in ("id", "gate", "subject", "scope", "recovery"):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as directory:
                target = Path(directory)
                copy_semantic_fixtures(target)
                exception = self.valid_exception()
                exception[field] = f" {exception[field]} "
                if field in {"gate", "subject", "scope"}:
                    authority_path = target / exception["authority"]["reference"]["path"]
                    authority = json.loads(authority_path.read_text(encoding="utf-8"))
                    authority[field] = exception[field]
                    authority_path.write_text(
                        json.dumps(authority, indent=2) + "\n", encoding="utf-8"
                    )
                    exception["authority"]["reference"]["sha256"] = hashlib.sha256(
                        authority_path.read_bytes()
                    ).hexdigest()
                exception_path = (
                    target
                    / "tests/fixtures/promise-machine/exceptions/declared-padded.json"
                )
                exception_path.write_text(
                    json.dumps(exception, indent=2) + "\n", encoding="utf-8"
                )
                reference = json.dumps(
                    {
                        "path": exception_path.relative_to(target).as_posix(),
                        "sha256": hashlib.sha256(exception_path.read_bytes()).hexdigest(),
                    },
                    separators=(",", ":"),
                )
                error = promise_machine_module.declared_exception_error(
                    target, reference, "fixture-promise"
                )
                self.assertEqual(
                    error,
                    "exception record has an unsupported shape or promise identity",
                )


class PromiseLicenceTests(unittest.TestCase):
    def test_repository_first_party_licences_are_clean(self):
        completed = run_cli("check", "--only", "licences", "--json")
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertTrue(report["ok"])
        self.assertEqual(
            report["counts"]["licensed_plugins"], len(discovered_plugins())
        )

    def test_missing_root_licence_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            plugin = make_licensed_plugin(target)
            (target / "LICENSE").unlink()
            completed = run_cli(
                "check", "--root", target, "--only", "licences", "--json"
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM072", [item["code"] for item in report["findings"]])

    def test_drifting_plugin_licence_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            plugin = make_licensed_plugin(target)
            (plugin / "LICENSE").write_text("different\n", encoding="utf-8")
            completed = run_cli(
                "check", "--root", target, "--only", "licences", "--json"
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM074", [item["code"] for item in report["findings"]])

    def test_inconsistent_host_manifest_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            plugin = make_licensed_plugin(target)
            manifest = plugin / ".codex-plugin" / "plugin.json"
            document = json.loads(manifest.read_text(encoding="utf-8"))
            document["license"] = "MIT"
            manifest.write_text(json.dumps(document) + "\n", encoding="utf-8")
            completed = run_cli(
                "check", "--root", target, "--only", "licences", "--json"
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM075", [item["code"] for item in report["findings"]])

    def test_vendored_skill_licence_is_outside_first_party_check(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            plugin = make_licensed_plugin(target)
            vendored = write_vendored_skill(plugin)
            self.assertNotEqual((vendored.parent / "LICENSE").read_bytes(), LICENSE.read_bytes())
            completed = run_cli(
                "check", "--root", target, "--only", "licences", "--json"
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertTrue(report["ok"])

    def test_json_report_matches_the_text_result(self):
        completed = run_cli("check", "--only", "law,copies", "--json")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        report = json.loads(completed.stdout)
        self.assertEqual(report["contract"], "promise-machine/v1")
        self.assertTrue(report["ok"])
        self.assertEqual(report["counts"]["plugins"], len(discovered_plugins()))
        self.assertEqual(report["findings"], [])

    def test_divergent_copy_fixture_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            shutil.copy2(LAW, target / LAW.name)
            shutil.copytree(FIXTURE / "plugins", target / "plugins")
            completed = run_cli("check", "--root", target, "--only", "law,copies", "--json")
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertEqual([item["code"] for item in report["findings"]], ["PM014"])

    def test_empty_plugin_set_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            shutil.copy2(LAW, target / LAW.name)
            (target / "plugins").mkdir()
            completed = run_cli("check", "--root", target, "--only", "law,copies", "--json")
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM010", [item["code"] for item in report["findings"]])

    def test_copy_only_refuses_an_absent_root_law(self):
        completed = run_cli(
            "check", "--root", FIXTURE, "--only", "copies", "--json"
        )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertFalse(report["ok"])
        self.assertIn("PM001", [item["code"] for item in report["findings"]])

    def test_law_only_does_not_require_a_plugin_tree(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            shutil.copy2(LAW, target / LAW.name)
            completed = run_cli(
                "check", "--root", target, "--only", "law", "--json"
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertTrue(report["ok"])
        self.assertEqual(report["counts"]["plugins"], 0)

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unavailable")
    def test_symlinked_copy_is_refused_without_following_it(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "repo"
            target.mkdir()
            shutil.copy2(LAW, target / LAW.name)
            plugin = make_plugin(target)
            outside = Path(directory) / "outside.md"
            outside.write_bytes(LAW.read_bytes())
            (plugin / LAW.name).symlink_to(outside)
            completed = run_cli("sync", "--root", target, "--json")
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM013", [item["code"] for item in report["findings"]])

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unavailable")
    def test_symlinked_plugin_directory_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "repo"
            target.mkdir()
            shutil.copy2(LAW, target / LAW.name)
            (target / "plugins").mkdir()
            outside = Path(directory) / "outside"
            make_plugin(outside)
            (target / "plugins" / "escape").symlink_to(outside / "plugins" / "example")
            completed = run_cli("sync", "--root", target, "--json")
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM011", [item["code"] for item in report["findings"]])

    def test_sync_repairs_a_divergent_fixed_destination(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            shutil.copy2(LAW, target / LAW.name)
            plugin = make_plugin(target)
            destination = plugin / LAW.name
            destination.write_text("drift\n", encoding="utf-8")
            completed = run_cli("sync", "--root", target, "--json")
            leftovers = list(plugin.glob(f".{LAW.name}.*"))
            repaired = destination.read_bytes()
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(report["counts"]["written"], 1)
        self.assertEqual(repaired, LAW.read_bytes())
        self.assertEqual(leftovers, [])


class PromiseInventoryTests(unittest.TestCase):
    def test_repository_inventory_is_derived_from_disk(self):
        completed = run_cli("inventory", "--json")
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(report["counts"]["plugins"], len(discovered_plugins()))
        discovered = len(discovered_canonical_skills())
        self.assertEqual(report["counts"]["canonical_skills"], discovered)
        self.assertEqual(
            report["counts"]["governed_skills"], discovered - VENDORED_SKILLS
        )
        self.assertEqual(report["counts"]["vendored_skills"], VENDORED_SKILLS)
        self.assertEqual(report["counts"]["routers"], 1)

    def test_nested_fizz_subsidiaries_are_discovered(self):
        completed = run_cli("inventory", "--json")
        report = json.loads(completed.stdout)
        paths = {item["path"] for item in report["inventory"]["skills"]}
        self.assertIn(
            "plugins/hexaemeron/skills/fizz/skills/fizz-convert/SKILL.md", paths
        )
        self.assertIn(
            "plugins/hexaemeron/skills/fizz/skills/fizz-sync/SKILL.md", paths
        )

    def test_inventory_text_and_json_results_agree(self):
        json_run = run_cli("inventory", "--json")
        text_run = run_cli("inventory")
        report = json.loads(json_run.stdout)
        self.assertEqual(json_run.returncode, text_run.returncode)
        for key in ("plugins", "canonical_skills", "governed_skills", "vendored_skills"):
            self.assertIn(f"{key}={report['counts'][key]}", text_run.stdout)

    def test_empty_canonical_skill_set_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            make_plugin(target)
            completed = run_cli("inventory", "--root", target, "--json")
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM020", [item["code"] for item in report["findings"]])

    def test_unclassified_skill_fixture_is_refused(self):
        completed = run_cli(
            "inventory", "--root", FIXTURES / "unclassified-skill", "--json"
        )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM024", [item["code"] for item in report["findings"]])

    def test_vendored_skill_without_complete_ownership_binding_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            plugin = make_plugin(target)
            skill = plugin / "skills" / "upstream"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                "---\nname: upstream\ndescription: fixture\n---\n", encoding="utf-8"
            )
            (skill / "NOTICE.md").write_text(
                "This skill is vendored verbatim.\n\n- Upstream: https://example.invalid\n"
                "- Release tag: v1\n- Vendored: today\n",
                encoding="utf-8",
            )
            completed = run_cli("inventory", "--root", target, "--json")
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM026", [item["code"] for item in report["findings"]])

    def test_inventory_does_not_claim_copy_checks_it_did_not_run(self):
        completed = run_cli("inventory", "--json")
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(report["counts"]["copies"], 0)
        checked = run_cli("check", "--only", "inventory,structure")
        self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)
        self.assertIn("0 copy/copies", checked.stdout)

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unavailable")
    def test_symlinked_router_directory_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "repo"
            target.mkdir()
            plugin = make_plugin(target)
            write_skill(plugin)
            router_root = target / ".agents" / "skills"
            router_root.mkdir(parents=True)
            outside = Path(directory) / "outside" / "router"
            outside.mkdir(parents=True)
            (outside / "SKILL.md").write_text(
                "---\nname: router\ndescription: fixture\n---\n", encoding="utf-8"
            )
            (router_root / "router").symlink_to(outside, target_is_directory=True)
            completed = run_cli("inventory", "--root", target, "--json")
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM025", [item["code"] for item in report["findings"]])

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unavailable")
    def test_symlinked_overlay_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "repo"
            target.mkdir()
            plugin = make_plugin(target)
            write_skill(plugin)
            outside = Path(directory) / "outside.md"
            outside.write_text("# Outside\n", encoding="utf-8")
            (plugin / "PROMISES.md").symlink_to(outside)
            completed = run_cli("inventory", "--root", target, "--json")
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM025", [item["code"] for item in report["findings"]])


class PromiseStructureTests(unittest.TestCase):
    def test_standalone_contract_population_is_complete(self):
        expected = {
            "plugins/alexandria/skills/alexandria/SKILL.md": {
                "alexandria-raw-release",
                "alexandria-derived-view",
                "alexandria-release-statement",
                "alexandria-address-query",
                "alexandria-compound-method-proof",
            },
            "plugins/ariadne/skills/ariadne/SKILL.md": {
                "ariadne-capture-statement",
                "ariadne-inspect-statement",
                "ariadne-verify-statement",
                "ariadne-replay-command",
            },
            "plugins/berean/skills/berean/SKILL.md": {
                "berean-corpus-binding",
                "berean-answer-evidence",
                "berean-evaluation-report",
                "berean-release-promotion",
            },
            "plugins/brevitas/skills/brevitas/SKILL.md": {
                "brevitas-structure-check",
                "brevitas-evidence-preservation",
            },
            "plugins/hermes/skills/hermes/SKILL.md": {
                "hermes-corpus-selection",
                "hermes-sealed-baseline",
                "hermes-candidate-acceptance",
                "hermes-baseline-promotion",
            },
            "plugins/horos/skills/horos/SKILL.md": {
                "horos-boundary-scan",
                "horos-boundary-check",
                "horos-census",
                "horos-skeleton-map",
            },
            "plugins/janus/skills/janus/SKILL.md": {
                "janus-manifest-validation",
                "janus-bounded-conformance",
                "janus-report-rendering",
            },
            "plugins/lazarus/skills/lazarus/SKILL.md": {
                "lazarus-fixture-capture",
                "lazarus-fixture-verification",
                "lazarus-exact-replay",
                "lazarus-preservation-release",
            },
            "plugins/lemma/skills/lemma/SKILL.md": {
                "lemma-solidity-chunks",
                "lemma-markdown-chunks",
                "lemma-chunk-validation",
                "lemma-corpus-provenance",
            },
            "plugins/pandects/skills/pandects/SKILL.md": {
                "pandects-law-contract",
                "pandects-catalogue-render",
                "pandects-broken-specimen",
                "pandects-search-record",
            },
            "plugins/probitas/skills/probitas/SKILL.md": {
                "probitas-evidence-collection",
                "probitas-dossier-rendering",
                "probitas-dossier-verification",
                "probitas-statement-emission",
            },
            "plugins/sapheneia/skills/sapheneia/SKILL.md": {
                "sapheneia-session-shape",
                "sapheneia-deactivation",
                "sapheneia-durable-record-shape",
            },
            "plugins/synkrisis/skills/synkrisis/SKILL.md": {
                "synkrisis-cohort-construction",
                "synkrisis-bounded-diagnosis",
                "synkrisis-report-verification",
            },
            "plugins/tabularium/skills/tabularium/SKILL.md": {
                "tabularium-release-build",
                "tabularium-release-verification",
                "tabularium-compound-witness",
            },
        }
        for path, promise_ids in expected.items():
            with self.subTest(path=path):
                text = (ROOT / path).read_text(encoding="utf-8")
                self.assertEqual(text.splitlines().count("## Promise Machine contract"), 1)
                contract = text.split("## Promise Machine contract", 1)[1]
                contract = contract.split("\n## ", 1)[0]
                self.assertEqual(
                    {
                        line.removeprefix("### ")
                        for line in contract.splitlines()
                        if line.startswith("### ")
                    },
                    promise_ids,
                )

        completed = run_cli("check", "--only", "structure,contracts", "--json")
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertTrue(report["ok"])
        self.assertEqual(
            report["counts"]["promises"], len(rows_in("executable", "prompt"))
        )

    def test_hexaemeron_contract_population_is_complete(self):
        expected = {
            "elenchus": {"elenchus-fixed-and-guarded"},
            "ephoros": {"ephoros-mechanical-gate", "ephoros-observability-review"},
            "fiat": {
                "fiat-controller-checkpoint",
                "fiat-design-evidence",
                "fiat-study-amendment",
                "fiat-runbook-amendment",
                "fiat-run-observation-binding",
                "fiat-receipted-delivery",
                "fiat-local-retirement",
                "fiat-version-resolution",
                "fiat-final-integration",
            },
            "hypomnema": {"hypomnema-pointer-gate", "hypomnema-record-placement"},
            "imprimatur": {"imprimatur-prose-gate"},
            "kronos": {
                "kronos-frontier-ranking",
                "kronos-fiat-dispatch",
                "kronos-parked-lane",
            },
            "metron": {"metron-budget-verdict", "metron-change-decision"},
            "phylax": {"phylax-mechanical-gate", "phylax-boundary-review"},
            "protasis": {"protasis-study-readiness", "protasis-runbook-readiness"},
            "vulgate": {"vulgate-register-rewrite"},
        }
        for skill, promise_ids in expected.items():
            path = ROOT / "plugins" / "hexaemeron" / "skills" / skill / "SKILL.md"
            with self.subTest(skill=skill):
                text = path.read_text(encoding="utf-8")
                self.assertEqual(text.splitlines().count("## Promise Machine contract"), 1)
                contract = text.split("## Promise Machine contract", 1)[1]
                contract = contract.split("\n## ", 1)[0]
                self.assertEqual(
                    {
                        line.removeprefix("### ")
                        for line in contract.splitlines()
                        if line.startswith("### ")
                    },
                    promise_ids,
                )


class PromiseOverlayTests(unittest.TestCase):
    def test_repository_overlay_population_is_complete_and_digest_bound(self):
        expected = {
            "plugins/hexaemeron/skills/fizz/SKILL.md": (
                "fizz/SKILL.md",
                "fa706e94e9ec3456528985548f46461d44442d9223e26b2a0dbbb8b5f522172a",
                "62a60df4cec160511b8ef36433eef7c8805d0b4a398491293eb4542ab73539bd",
                "local-bytes-modified",
            ),
            "plugins/hexaemeron/skills/fizz/skills/fizz-convert/SKILL.md": (
                "fizz/skills/fizz-convert/SKILL.md",
                "59cd4b4ef5dc56315782a7d25222afb286a24e63e438530cbd0044293ea54af7",
                "59cd4b4ef5dc56315782a7d25222afb286a24e63e438530cbd0044293ea54af7",
                "local-bytes-identical",
            ),
            "plugins/hexaemeron/skills/fizz/skills/fizz-sync/SKILL.md": (
                "fizz/skills/fizz-sync/SKILL.md",
                "e969cd8a447941989715840e24aa6a915c0fd795effabd912b3c627598a95e16",
                "e969cd8a447941989715840e24aa6a915c0fd795effabd912b3c627598a95e16",
                "local-bytes-identical",
            ),
            "plugins/hexaemeron/skills/x-ray/SKILL.md": (
                "x-ray/SKILL.md",
                "b23bb94517805c1b8ce717d0e1e0282b0b5c14c7b16f4c32e73940292d3d4a41",
                "b23bb94517805c1b8ce717d0e1e0282b0b5c14c7b16f4c32e73940292d3d4a41",
                "local-bytes-identical",
            ),
            "plugins/hexaemeron/skills/solidity-auditor/SKILL.md": (
                "solidity-auditor/SKILL.md",
                "1c1cf4e99d042e7aadc56b622d97a07d3286f4786838a05510697c814d1e983f",
                "1c1cf4e99d042e7aadc56b622d97a07d3286f4786838a05510697c814d1e983f",
                "local-bytes-identical",
            ),
        }
        text = (ROOT / "plugins" / "hexaemeron" / "PROMISES.md").read_text(
            encoding="utf-8"
        )
        for path, (upstream_path, upstream_digest, local_digest, relation) in expected.items():
            with self.subTest(path=path):
                self.assertIn(f"- Path: `{path}`", text)
                self.assertIn(
                    "- Repository: `https://github.com/pashov/skills.git`", text
                )
                self.assertIn(
                    "- Commit: `aadee2ca49cae20246af378ef791d2d4f941e237`", text
                )
                self.assertIn(f"- Upstream path: `{upstream_path}`", text)
                self.assertIn(f"- Upstream SHA-256: `{upstream_digest}`", text)
                self.assertIn(f"- Local SHA-256: `{local_digest}`", text)
                self.assertIn(
                    "- Verification status: upstream-bytes-verified, "
                    f"{relation}, publisher-authentication-unknown",
                    text,
                )

        completed = run_cli("check", "--only", "contracts,overlays", "--json")
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertTrue(report["ok"])
        self.assertEqual(report["counts"]["promises"], len(coverage_rows()))
        self.assertEqual(report["counts"]["overlays"], 1)

    def test_one_byte_vendored_mutation_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            plugin = make_plugin(target, "hexaemeron")
            skill = write_vendored_skill(plugin)
            write_overlay(target, skill)
            clean = run_cli("check", "--root", target, "--only", "overlays", "--json")
            skill.write_bytes(skill.read_bytes() + b"x")
            drifted = run_cli(
                "check", "--root", target, "--only", "overlays", "--json"
            )
        self.assertEqual(clean.returncode, 0, clean.stdout + clean.stderr)
        report = json.loads(drifted.stdout)
        self.assertEqual(drifted.returncode, 1)
        self.assertIn("PM057", [item["code"] for item in report["findings"]])

    def test_missing_overlay_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            plugin = make_plugin(target, "hexaemeron")
            write_vendored_skill(plugin)
            completed = run_cli(
                "check", "--root", target, "--only", "overlays", "--json"
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM050", [item["code"] for item in report["findings"]])

    def test_overlay_cannot_bind_a_first_party_skill(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            plugin = make_plugin(target, "hexaemeron")
            skill = write_skill(plugin) / "SKILL.md"
            write_overlay(target, skill)
            completed = run_cli(
                "check", "--root", target, "--only", "overlays", "--json"
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM055", [item["code"] for item in report["findings"]])

    def test_missing_or_duplicate_provenance_field_is_refused(self):
        mutations = {
            "missing": lambda text: text.replace(
                "- Repository: `https://github.com/example/upstream.git`\n", ""
            ),
            "duplicate": lambda text: text.replace(
                "- Repository: `https://github.com/example/upstream.git`\n",
                "- Repository: `https://github.com/example/upstream.git`\n" * 2,
            ),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                target = Path(directory)
                plugin = make_plugin(target, "hexaemeron")
                skill = write_vendored_skill(plugin)
                overlay = write_overlay(target, skill)
                overlay.write_text(
                    mutate(overlay.read_text(encoding="utf-8")), encoding="utf-8"
                )
                completed = run_cli(
                    "check", "--root", target, "--only", "overlays", "--json"
                )
            report = json.loads(completed.stdout)
            self.assertEqual(completed.returncode, 1)
            self.assertIn("PM054", [item["code"] for item in report["findings"]])

    def test_overlay_fields_cannot_be_borrowed_from_a_later_section(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            plugin = make_plugin(target, "hexaemeron")
            skill = write_vendored_skill(plugin)
            overlay = write_overlay(target, skill)
            text = overlay.read_text(encoding="utf-8").replace(
                "- Repository: `https://github.com/example/upstream.git`\n", ""
            )
            overlay.write_text(
                text
                + "\n## Unrelated example\n\n"
                + "- Repository: `https://github.com/example/upstream.git`\n",
                encoding="utf-8",
            )
            completed = run_cli(
                "check", "--root", target, "--only", "overlays", "--json"
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM054", [item["code"] for item in report["findings"]])

    def test_container_hidden_overlay_declaration_is_refused(self):
        wrappers = {
            "fenced": ("```text\n", "```\n"),
            "raw-html": ("<div>\n", "</div>\n"),
        }
        for name, (opening, closing) in wrappers.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                target = Path(directory)
                plugin = make_plugin(target, "hexaemeron")
                skill = write_vendored_skill(plugin)
                overlay = write_overlay(target, skill)
                text = overlay.read_text(encoding="utf-8")
                heading, declaration = text.split("\n\n", 1)
                overlay.write_text(
                    f"{heading}\n\n{opening}{declaration}{closing}",
                    encoding="utf-8",
                )
                completed = run_cli(
                    "check", "--root", target, "--only", "overlays", "--json"
                )
            report = json.loads(completed.stdout)
            self.assertEqual(completed.returncode, 1)
            self.assertIn("PM052", [item["code"] for item in report["findings"]])

    def test_unsafe_overlay_path_is_refused_before_filesystem_observation(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            plugin = make_plugin(target, "hexaemeron")
            skill = write_vendored_skill(plugin)
            overlay = write_overlay(target, skill)
            declared = skill.relative_to(target).as_posix()
            overlay.write_text(
                overlay.read_text(encoding="utf-8").replace(
                    f"- Path: `{declared}`", "- Path: `plugins/\x00/SKILL.md`"
                ),
                encoding="utf-8",
            )
            completed = run_cli(
                "check", "--root", target, "--only", "overlays", "--json"
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1, completed.stderr)
        self.assertIn("PM055", [item["code"] for item in report["findings"]])

    def test_mutable_commit_and_switched_repository_host_are_refused(self):
        mutations = {
            "mutable-commit": (
                "`0123456789abcdef0123456789abcdef01234567`",
                "`v0.0.0`",
                "PM061",
            ),
            "switched-host": (
                "https://github.com/example/upstream.git",
                "https://gitlab.example/example/upstream.git",
                "PM060",
            ),
            "unsafe-upstream-path": (
                "`upstream/SKILL.md`",
                "`../outside/SKILL.md`",
                "PM062",
            ),
            "malformed-digests": (
                "`" + hashlib.sha256(
                    (
                        "---\nname: upstream\ndescription: A vendored fixture skill.\n"
                        "---\n\n# upstream\n"
                    ).encode("utf-8")
                ).hexdigest() + "`",
                "`not-a-digest`",
                "PM056",
            ),
        }
        for name, (old, new, code) in mutations.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                target = Path(directory)
                plugin = make_plugin(target, "hexaemeron")
                skill = write_vendored_skill(plugin)
                overlay = write_overlay(target, skill)
                overlay.write_text(
                    overlay.read_text(encoding="utf-8").replace(old, new),
                    encoding="utf-8",
                )
                completed = run_cli(
                    "check", "--root", target, "--only", "overlays", "--json"
                )
            report = json.loads(completed.stdout)
            self.assertEqual(completed.returncode, 1)
            self.assertIn(code, [item["code"] for item in report["findings"]])

    def test_verification_status_preserves_unknown_and_matches_digests(self):
        mutations = {
            "strengthened-publisher": (
                "publisher-authentication-unknown",
                "publisher-authentication-verified",
            ),
            "false-modified-relation": (
                "local-bytes-identical",
                "local-bytes-modified",
            ),
        }
        for name, (old, new) in mutations.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                target = Path(directory)
                plugin = make_plugin(target, "hexaemeron")
                skill = write_vendored_skill(plugin)
                overlay = write_overlay(target, skill)
                overlay.write_text(
                    overlay.read_text(encoding="utf-8").replace(old, new),
                    encoding="utf-8",
                )
                completed = run_cli(
                    "check", "--root", target, "--only", "overlays", "--json"
                )
            report = json.loads(completed.stdout)
            self.assertEqual(completed.returncode, 1)
            self.assertIn("PM063", [item["code"] for item in report["findings"]])


class VendoredUpstreamVerifierTests(unittest.TestCase):
    class Response:
        def __init__(self, payload=b"", *, status=200, headers=None):
            self.status = status
            self._stream = io.BytesIO(payload)
            self._headers = headers or {}

        def getheader(self, name):
            return self._headers.get(name)

        def read(self, size=-1):
            return self._stream.read(size)

    class Connection:
        def __init__(self, response):
            self.response = response
            self.requested = []
            self.closed = False

        def request(self, method, target, *, headers):
            self.requested.append((method, target, headers))

        def getresponse(self):
            return self.response

        def close(self):
            self.closed = True

    def make_fixture(self, root):
        plugin = make_plugin(root, "hexaemeron")
        skill = write_vendored_skill(plugin)
        write_overlay(root, skill)
        return skill, skill.relative_to(root).as_posix()

    def verifier(self):
        return importlib.import_module("scripts.verify_vendored_provenance")

    def test_exact_immutable_upstream_bytes_are_verified(self):
        verifier = self.verifier()
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            skill, selected = self.make_fixture(target)
            connection = self.Connection(self.Response(skill.read_bytes()))
            calls = []

            def factory(host, *, timeout, context):
                calls.append((host, timeout, context))
                return connection

            verified, findings = verifier.verify_selected(
                target, [selected], connection_factory=factory
            )
        self.assertEqual(findings, [])
        self.assertEqual(len(verified), 1)
        self.assertEqual(verified[0]["local_path"], selected)
        self.assertEqual(verified[0]["publisher_authentication"], "unknown")
        self.assertEqual(calls[0][0], "raw.githubusercontent.com")
        self.assertEqual(
            connection.requested[0][1],
            "/example/upstream/0123456789abcdef0123456789abcdef01234567/"
            "upstream/SKILL.md",
        )
        self.assertTrue(connection.closed)

    def test_redirect_is_refused_without_following_it(self):
        verifier = self.verifier()
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            _, selected = self.make_fixture(target)
            connections = []

            def factory(host, *, timeout, context):
                connection = self.Connection(
                    self.Response(
                        status=302,
                        headers={"Location": "https://evil.example/payload"},
                    )
                )
                connections.append((host, connection))
                return connection

            verified, findings = verifier.verify_selected(
                target, [selected], connection_factory=factory
            )
        self.assertEqual(verified, [])
        self.assertEqual([item.code for item in findings], ["PV003"])
        self.assertEqual([host for host, _ in connections], ["raw.githubusercontent.com"])
        self.assertEqual(len(connections[0][1].requested), 1)

    def test_oversized_or_digest_mismatched_upstream_bytes_are_refused(self):
        verifier = self.verifier()
        cases = {
            "oversized": self.Response(
                b"",
                headers={"Content-Length": str(verifier.MAX_UPSTREAM_BYTES + 1)},
            ),
            "digest-mismatch": self.Response(b"wrong bytes"),
        }
        for name, response in cases.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                target = Path(directory)
                _, selected = self.make_fixture(target)

                def factory(host, *, timeout, context):
                    return self.Connection(response)

                verified, findings = verifier.verify_selected(
                    target, [selected], connection_factory=factory
                )
            self.assertEqual(verified, [])
            self.assertEqual(
                [item.code for item in findings],
                ["PV003" if name == "oversized" else "PV004"],
            )

    def test_selection_is_explicit_unique_and_declared(self):
        verifier = self.verifier()
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            _, selected = self.make_fixture(target)
            for selection in (
                [],
                [selected, selected],
                ["plugins/hexaemeron/skills/other/SKILL.md"],
            ):
                with self.subTest(selection=selection):
                    verified, findings = verifier.verify_selected(
                        target,
                        selection,
                        connection_factory=mock.Mock(
                            side_effect=AssertionError("network must not run")
                        ),
                    )
                    self.assertEqual(verified, [])
                    self.assertEqual([item.code for item in findings], ["PV001"])

    def test_slow_final_read_cannot_cross_the_total_deadline(self):
        verifier = self.verifier()

        class Clock:
            def __init__(self):
                self.value = 0.0

            def __call__(self):
                return self.value

        clock = Clock()

        class SlowEOFResponse(self.Response):
            def read(self, size=-1):
                clock.value += verifier.TOTAL_TIMEOUT_SECONDS + 1.0
                return b""

        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            skill, selected = self.make_fixture(target)
            overlay = target / "plugins" / "hexaemeron" / "PROMISES.md"
            local_digest = hashlib.sha256(skill.read_bytes()).hexdigest()
            empty_digest = hashlib.sha256(b"").hexdigest()
            overlay.write_text(
                overlay.read_text(encoding="utf-8")
                .replace(
                    f"- Upstream SHA-256: `{local_digest}`",
                    f"- Upstream SHA-256: `{empty_digest}`",
                )
                .replace("local-bytes-identical", "local-bytes-modified"),
                encoding="utf-8",
            )
            connection = self.Connection(SlowEOFResponse())

            def factory(host, *, timeout, context):
                return connection

            verified, findings = verifier.verify_selected(
                target,
                [selected],
                connection_factory=factory,
                clock=clock,
            )
        self.assertEqual(verified, [])
        self.assertEqual([item.code for item in findings], ["PV003"])


class PromiseHistoryTests(unittest.TestCase):
    def make_single_history(self, root):
        plugin = make_plugin(root)
        skill = write_skill(plugin)
        snapshot = history_snapshot(
            (skill / "SKILL.md").relative_to(root).as_posix(),
            fixture_promise_fields(),
        )
        entries = [
            history_row(
                "example-check", entry=snapshot, current=snapshot, action="unchanged"
            )
        ]
        history, document = write_history(root, entries)
        return skill / "SKILL.md", history, document

    def test_repository_history_is_seeded_and_complete(self):
        document = json.loads(PROMISE_ID_HISTORY.read_text(encoding="utf-8"))
        self.assertEqual(document["entry_ref"], FIAT_ENTRY_REF)
        self.assertEqual(document["entry_count"], 80)
        self.assertEqual(len(document["entries"]), 80)
        self.assertEqual(
            len({row["promise_id"] for row in document["entries"]}), 80
        )
        completed = run_cli("check", "--only", "history", "--json")
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(report["counts"]["history_entries"], 80)
        self.assertEqual(report["counts"]["active_history_ids"], 80)

    def test_deleted_or_duplicated_history_id_is_refused(self):
        for name in ("deleted", "duplicated"):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                target = Path(directory)
                _, history, document = self.make_single_history(target)
                if name == "deleted":
                    document["entries"].clear()
                    expected = "PM100"
                else:
                    document["entries"].append(copy.deepcopy(document["entries"][0]))
                    expected = "PM102"
                history.write_text(
                    json.dumps(document, indent=2) + "\n", encoding="utf-8"
                )
                completed = run_cli(
                    "check", "--root", target, "--only", "history", "--json"
                )
            report = json.loads(completed.stdout)
            self.assertEqual(completed.returncode, 1)
            self.assertIn(expected, [item["code"] for item in report["findings"]])

    def test_malformed_entry_ref_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            _, history, document = self.make_single_history(target)
            document["entry_ref"] = "v1"
            history.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
            completed = run_cli(
                "check", "--root", target, "--only", "history", "--json"
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM101", [item["code"] for item in report["findings"]])

    def test_non_object_history_returns_a_stable_finding(self):
        for document in ([], None, "history"):
            with self.subTest(document=document), tempfile.TemporaryDirectory() as directory:
                target = Path(directory)
                _, history, _ = self.make_single_history(target)
                history.write_text(
                    json.dumps(document, indent=2) + "\n", encoding="utf-8"
                )
                completed = run_cli(
                    "check", "--root", target, "--only", "history", "--json"
                )
            report = json.loads(completed.stdout)
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertIn("PM100", [item["code"] for item in report["findings"]])

    def test_unhashable_continuity_action_returns_a_stable_finding(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            _, history, document = self.make_single_history(target)
            document["entries"][0]["continuity"]["action"] = []
            history.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
            completed = run_cli(
                "check", "--root", target, "--only", "history", "--json"
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1, completed.stderr)
        self.assertIn("PM105", [item["code"] for item in report["findings"]])

    def test_invalid_rename_shape_returns_a_stable_finding(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            plugin = make_plugin(target)
            skill = write_skill(plugin, promise_id="replacement-check") / "SKILL.md"
            snapshot = history_snapshot(
                skill.relative_to(target).as_posix(), fixture_promise_fields()
            )
            entries = [
                history_row(
                    "example-check",
                    entry=None,
                    current=None,
                    action="renamed",
                    successors=("replacement-check",),
                ),
                history_row(
                    "replacement-check",
                    entry=None,
                    current=snapshot,
                    action="introduced",
                    predecessors=("example-check",),
                ),
            ]
            write_history(target, entries)
            completed = run_cli(
                "check", "--root", target, "--only", "history", "--json"
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1, completed.stderr)
        self.assertIn("PM105", [item["code"] for item in report["findings"]])

    def test_missing_declaration_and_undeclared_active_id_are_refused(self):
        mutations = ("missing-declaration", "undeclared-active")
        for name in mutations:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                target = Path(directory)
                skill, history, document = self.make_single_history(target)
                if name == "missing-declaration":
                    skill.write_text(
                        skill.read_text(encoding="utf-8").replace(
                            "### example-check", "### replacement-check"
                        ),
                        encoding="utf-8",
                    )
                else:
                    ghost = history_snapshot(
                        "plugins/example/skills/ghost/SKILL.md",
                        fixture_promise_fields(),
                    )
                    document["entries"].append(
                        history_row(
                            "ghost-check",
                            entry=None,
                            current=ghost,
                            action="introduced",
                        )
                    )
                    history.write_text(
                        json.dumps(document, indent=2) + "\n", encoding="utf-8"
                    )
                completed = run_cli(
                    "check", "--root", target, "--only", "history", "--json"
                )
            report = json.loads(completed.stdout)
            self.assertEqual(completed.returncode, 1)
            self.assertIn("PM103", [item["code"] for item in report["findings"]])

    def test_unrecorded_retirement_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            _, history, document = self.make_single_history(target)
            document["entries"][0]["current"] = None
            history.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
            completed = run_cli(
                "check", "--root", target, "--only", "history", "--json"
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM105", [item["code"] for item in report["findings"]])

    def test_explicit_rename_is_accepted(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            plugin = make_plugin(target)
            skill = write_skill(plugin, promise_id="replacement-check") / "SKILL.md"
            snapshot = history_snapshot(
                skill.relative_to(target).as_posix(), fixture_promise_fields()
            )
            entries = [
                history_row(
                    "example-check",
                    entry=snapshot,
                    current=None,
                    action="renamed",
                    successors=("replacement-check",),
                ),
                history_row(
                    "replacement-check",
                    entry=None,
                    current=snapshot,
                    action="introduced",
                    predecessors=("example-check",),
                ),
            ]
            write_history(target, entries)
            completed = run_cli(
                "check", "--root", target, "--only", "history", "--json"
            )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_explicit_split_is_accepted(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            plugin = make_plugin(target)
            left = write_skill(plugin, "left", promise_id="left-check") / "SKILL.md"
            right = write_skill(plugin, "right", promise_id="right-check") / "SKILL.md"
            entry = history_snapshot(
                "plugins/example/skills/original/SKILL.md", fixture_promise_fields()
            )
            left_snapshot = history_snapshot(
                left.relative_to(target).as_posix(), fixture_promise_fields()
            )
            right_snapshot = history_snapshot(
                right.relative_to(target).as_posix(), fixture_promise_fields()
            )
            entries = [
                history_row(
                    "example-check",
                    entry=entry,
                    current=None,
                    action="split",
                    successors=("left-check", "right-check"),
                ),
                history_row(
                    "left-check",
                    entry=None,
                    current=left_snapshot,
                    action="introduced",
                    predecessors=("example-check",),
                ),
                history_row(
                    "right-check",
                    entry=None,
                    current=right_snapshot,
                    action="introduced",
                    predecessors=("example-check",),
                ),
            ]
            write_history(target, entries)
            completed = run_cli(
                "check", "--root", target, "--only", "history", "--json"
            )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_broken_rename_edge_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            plugin = make_plugin(target)
            skill = write_skill(plugin, promise_id="replacement-check") / "SKILL.md"
            snapshot = history_snapshot(
                skill.relative_to(target).as_posix(), fixture_promise_fields()
            )
            entries = [
                history_row(
                    "example-check",
                    entry=snapshot,
                    current=None,
                    action="renamed",
                    successors=("replacement-check",),
                ),
                history_row(
                    "replacement-check",
                    entry=None,
                    current=snapshot,
                    action="introduced",
                ),
            ]
            write_history(target, entries)
            completed = run_cli(
                "check", "--root", target, "--only", "history", "--json"
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM106", [item["code"] for item in report["findings"]])

    def test_semantic_split_cannot_reuse_one_id(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            skill, history, document = self.make_single_history(target)
            changed_fields = fixture_promise_fields()
            changed_fields["Promise"] = "Two unrelated outcomes are now accepted."
            skill.write_text(
                skill.read_text(encoding="utf-8").replace(
                    fixture_promise_fields()["Promise"], changed_fields["Promise"]
                ),
                encoding="utf-8",
            )
            document["entries"][0]["current"] = history_snapshot(
                skill.relative_to(target).as_posix(), changed_fields
            )
            history.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
            completed = run_cli(
                "check", "--root", target, "--only", "history", "--json"
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM104", [item["code"] for item in report["findings"]])


class PromiseStructureValidationTests(unittest.TestCase):
    def test_contract_component_refuses_an_absent_section(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            plugin = make_plugin(target)
            skill = write_skill(plugin)
            (skill / "SKILL.md").write_text(
                "---\nname: example\ndescription: A fixture skill.\n---\n\n# Example\n",
                encoding="utf-8",
            )
            completed = run_cli(
                "check", "--root", target, "--only", "contracts", "--json"
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM031", [item["code"] for item in report["findings"]])

    def test_missing_contract_fixture_is_refused(self):
        completed = run_cli(
            "check",
            "--root",
            FIXTURES / "missing-contract",
            "--only",
            "inventory,structure",
            "--json",
        )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM031", [item["code"] for item in report["findings"]])

    def test_each_missing_promise_field_is_refused(self):
        for missing in PROMISE_FIELDS:
            with self.subTest(field=missing), tempfile.TemporaryDirectory() as directory:
                target = Path(directory)
                plugin = make_plugin(target)
                values = {
                    field: "none" if field == "Exceptions" else "fixture value"
                    for field in PROMISE_FIELDS
                    if field != missing
                }
                if "Evidence classes" in values:
                    values["Evidence classes"] = "checked"
                if "Consequence" in values:
                    values["Consequence"] = "1"
                write_skill(plugin, fields=values)
                completed = run_cli(
                    "check", "--root", target, "--only", "inventory,structure", "--json"
                )
            report = json.loads(completed.stdout)
            self.assertEqual(completed.returncode, 1)
            self.assertIn("PM034", [item["code"] for item in report["findings"]])

    def test_unsupported_evidence_class_fixture_is_refused(self):
        completed = run_cli(
            "check",
            "--root",
            FIXTURES / "unsupported-evidence-class",
            "--only",
            "inventory,structure",
            "--json",
        )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM036", [item["code"] for item in report["findings"]])

    def test_no_recovery_fixture_is_refused(self):
        completed = run_cli(
            "check",
            "--root",
            FIXTURES / "no-recovery",
            "--only",
            "inventory,structure",
            "--json",
        )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM034", [item["code"] for item in report["findings"]])

    def test_duplicate_promise_ids_are_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            plugin = make_plugin(target)
            write_skill(plugin, "one", promise_id="same-promise")
            write_skill(plugin, "two", promise_id="same-promise")
            completed = run_cli(
                "check", "--root", target, "--only", "inventory,structure", "--json"
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM035", [item["code"] for item in report["findings"]])

    def test_unattributed_exception_fixture_is_refused(self):
        completed = run_cli(
            "check",
            "--root",
            FIXTURES / "unattributed-exception",
            "--only",
            "inventory,structure",
            "--json",
        )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM038", [item["code"] for item in report["findings"]])

    def test_exception_keywords_without_structured_attribution_are_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            plugin = make_plugin(target)
            fields = {
                "Promise": "The named check accepted the subject.",
                "Evidence": "example record",
                "Evidence classes": "checked",
                "Boundary": "No claim beyond the named rule.",
                "Authorises": "Use of the checked result.",
                "Consequence": "1",
                "Refuses": "Use of a failed result.",
                "Recovery": "Repair and rerun.",
                "Exceptions": (
                    "Authority is absent, scope is unknown, no record exists and expiry never applies."
                ),
            }
            write_skill(plugin, fields=fields)
            completed = run_cli(
                "check", "--root", target, "--only", "inventory,structure", "--json"
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM038", [item["code"] for item in report["findings"]])

    def test_vendored_instruction_cannot_author_its_own_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            plugin = make_plugin(target)
            skill = write_skill(plugin, "upstream")
            (skill / "EVOLUTION.md").unlink()
            (skill / "LICENSE").write_text("fixture licence\n", encoding="utf-8")
            (skill / "NOTICE.md").write_text(
                "This skill is vendored verbatim.\n\n- Upstream: https://example.invalid\n"
                "- Release tag: v1\n- Vendored: today\n",
                encoding="utf-8",
            )
            completed = run_cli(
                "check", "--root", target, "--only", "inventory,structure", "--json"
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM029", [item["code"] for item in report["findings"]])


class PromiseIdentityTests(unittest.TestCase):
    def test_repository_identity_router_versions_and_hosts_are_clean(self):
        completed = run_cli(
            "check", "--only", "identity,routers,versions,hosts", "--json"
        )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertTrue(report["ok"])
        self.assertEqual(
            report["counts"]["canonical_skills"], len(discovered_canonical_skills())
        )
        self.assertEqual(report["counts"]["routers"], 1)
        shipped = len(discovered_plugins())
        self.assertEqual(report["counts"]["claude_plugins"], shipped)
        self.assertEqual(report["counts"]["codex_plugins"], shipped)
        self.assertEqual(report["counts"]["package_versions"], len(discovered_plugins()))
        self.assertEqual(
            report["counts"]["skill_versions"],
            len(discovered_canonical_skills()) - VENDORED_SKILLS,
        )

    def test_unresolved_router_fixture_is_refused(self):
        completed = run_cli(
            "check",
            "--root",
            FIXTURES / "unresolved-router",
            "--only",
            "routers",
            "--json",
        )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM041", [item["code"] for item in report["findings"]])

    def test_duplicate_canonical_fixture_is_refused(self):
        completed = run_cli(
            "check",
            "--root",
            FIXTURES / "duplicate-canonical",
            "--only",
            "identity",
            "--json",
        )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM044", [item["code"] for item in report["findings"]])

    def test_package_as_skill_version_fixture_is_refused(self):
        completed = run_cli(
            "check",
            "--root",
            FIXTURES / "package-as-skill-version",
            "--only",
            "versions",
            "--json",
        )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM046", [item["code"] for item in report["findings"]])

    def test_router_with_a_behavioural_version_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            plugin = make_plugin(target)
            write_skill(plugin)
            router = target / ".agents" / "skills" / "promise-machine" / "SKILL.md"
            router.parent.mkdir(parents=True)
            router.write_text(
                "---\nname: promise-machine\ndescription: fixture\n"
                "metadata:\n  version: \"1.0.0\"\n---\n\n"
                "# Promise Machine\n\n[Root](../../../AGENTS.md)\n",
                encoding="utf-8",
            )
            (target / "AGENTS.md").write_text("# Runtime\n", encoding="utf-8")
            completed = run_cli(
                "check", "--root", target, "--only", "routers", "--json"
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM043", [item["code"] for item in report["findings"]])

    def test_body_text_cannot_supply_frontmatter_identity_or_version(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            plugin = make_plugin(target)
            skill = plugin / "skills" / "example"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                "---\ndescription: fixture\n---\n\n# Example\n\n"
                "name: example\n\n  version: \"0.0.0\"\n",
                encoding="utf-8",
            )
            (skill / "EVOLUTION.md").write_text(
                "# Evolution\n\n- Current version: `example-v0.0.0`\n",
                encoding="utf-8",
            )
            completed = run_cli(
                "check", "--root", target, "--only", "identity,versions", "--json"
            )
        report = json.loads(completed.stdout)
        codes = [item["code"] for item in report["findings"]]
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM023", codes)
        self.assertIn("PM046", codes)

    def test_duplicate_skill_metadata_versions_are_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            plugin = make_plugin(target)
            skill = plugin / "skills" / "example"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                "---\nname: example\ndescription: fixture\nmetadata:\n"
                "  version: \"0.0.0\"\n  version: \"0.0.0\"\n---\n",
                encoding="utf-8",
            )
            (skill / "EVOLUTION.md").write_text(
                "# Evolution\n\n- Current version: `example-v0.0.0`\n",
                encoding="utf-8",
            )
            completed = run_cli(
                "check", "--root", target, "--only", "versions", "--json"
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM046", [item["code"] for item in report["findings"]])

    def test_package_marketplace_version_mismatch_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            plugin = make_plugin(target)
            write_skill(plugin)
            marketplace = target / ".claude-plugin" / "marketplace.json"
            marketplace.parent.mkdir()
            marketplace.write_text(
                json.dumps(
                    {
                        "name": "fixture",
                        "plugins": [
                            {
                                "name": "example",
                                "source": "./plugins/example",
                                "version": "9.9.9",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            completed = run_cli(
                "check", "--root", target, "--only", "versions", "--json"
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM045", [item["code"] for item in report["findings"]])

    def test_body_version_example_does_not_version_the_router(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            plugin = make_plugin(target)
            write_skill(plugin)
            (target / "AGENTS.md").write_text("# Root runtime\n", encoding="utf-8")
            (plugin / "AGENTS.md").write_text(
                "# Plugin runtime\n\n`skills/example/SKILL.md`\n", encoding="utf-8"
            )
            router = target / ".agents" / "skills" / "promise-machine" / "SKILL.md"
            router.parent.mkdir(parents=True)
            router.write_text(
                "---\nname: promise-machine\ndescription: fixture\n---\n\n"
                "# Promise Machine\n\n[Root](../../../AGENTS.md)\n"
                "[Example](../../../plugins/example/AGENTS.md)\n\n"
                "An unrelated example may contain:\n\n  version: \"1.0.0\"\n",
                encoding="utf-8",
            )
            completed = run_cli(
                "check", "--root", target, "--only", "routers", "--json"
            )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)


class PromiseCoverageTests(unittest.TestCase):
    def test_repository_executable_coverage_is_complete(self):
        completed = run_cli(
            "coverage", "--check", "--group", "executable", "--json"
        )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertTrue(report["ok"])
        self.assertEqual(report["counts"]["coverage_rows"], len(coverage_rows()))
        self.assertEqual(
            report["counts"]["coverage_selected"], len(rows_in("executable"))
        )

    def test_berean_and_janus_boundaries_are_explicit(self):
        coverage = json.loads(
            (ROOT / "tests" / "promise_machine_coverage.json").read_text(
                encoding="utf-8"
            )
        )
        rows = {row["promise_id"]: row for row in coverage["rows"]}
        self.assertEqual(
            set(rows["berean-answer-evidence"]["preserves"]),
            {
                "answer-truth-refused",
                "read-class",
                "source-class",
                "subject",
                "time-domain",
            },
        )
        self.assertEqual(
            set(rows["janus-bounded-conformance"]["preserves"]),
            {
                "adapter",
                "bounded-search",
                "cross-host-refused",
                "manifest",
                "recorder",
                "safety-refused",
                "unknown-effect-refused",
            },
        )
        self.assertEqual(
            {
                (handoff["producer"], handoff["consumer"])
                for handoff in coverage["handoffs"]
            },
            {
                ("lazarus-fixture-verification", "berean-answer-evidence"),
                ("berean-release-promotion", "ariadne-capture-statement"),
            },
        )

    def test_run_observation_coverage_binds_the_exact_release_surface(self):
        coverage = json.loads(
            (ROOT / "tests" / "promise_machine_coverage.json").read_text(
                encoding="utf-8"
            )
        )["run_observation"]
        self.assertEqual(coverage["contract"], "promise-machine-run-observation/v1")
        self.assertEqual(
            coverage["promise_id"],
            "promise-machine-run-observation-structural-validation",
        )
        self.assertIn(
            "### promise-machine-run-observation-structural-validation",
            (ROOT / "PROMISE_MACHINE.md").read_text(encoding="utf-8"),
        )
        bound = [coverage["runtime"], coverage["schema_source"], coverage["documentation"]]
        bound.extend(coverage["fixtures"])
        bound.append({key: coverage["tests"][key] for key in ("path", "sha256")})
        for item in bound:
            with self.subTest(path=item["path"]):
                path = ROOT / item["path"]
                self.assertTrue(path.is_file())
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), item["sha256"])
        tests = (ROOT / coverage["tests"]["path"]).read_text(encoding="utf-8")
        for selector in coverage["tests"]["selectors"]:
            with self.subTest(selector=selector):
                self.assertIn(f"def {selector}(", tests)
        self.assertIn("structurally conforming", coverage["transition"])

    def test_run_observation_binding_coverage_binds_the_exact_release_surface(self):
        coverage = json.loads(
            (ROOT / "tests" / "promise_machine_coverage.json").read_text(
                encoding="utf-8"
            )
        )["run_observation_binding"]
        self.assertEqual(coverage["contract"], "fiat-run-observation-binding/v1")
        self.assertIn(
            "fiat-run-observation-binding",
            {row["promise_id"] for row in json.loads(
                (ROOT / "tests" / "promise_machine_coverage.json").read_text(
                    encoding="utf-8"
                )
            )["rows"]},
        )
        self.assertIn(
            "### fiat-run-observation-binding",
            (ROOT / "plugins/hexaemeron/skills/fiat/SKILL.md").read_text(
                encoding="utf-8"
            ),
        )
        bound = [
            coverage["controller"],
            coverage["validator"],
            coverage["documentation"],
            coverage["decision"],
            coverage["fixture_manifest"],
            coverage["reporter"],
        ]
        bound.extend(
            {key: item[key] for key in ("path", "sha256")}
            for item in coverage["tests"]
        )
        for item in bound:
            with self.subTest(path=item["path"]):
                path = ROOT / item["path"]
                self.assertTrue(path.is_file())
                self.assertEqual(
                    hashlib.sha256(path.read_bytes()).hexdigest(), item["sha256"]
                )
        for item in coverage["tests"]:
            source = (ROOT / item["path"]).read_text(encoding="utf-8")
            for selector in item["selectors"]:
                with self.subTest(path=item["path"], selector=selector):
                    self.assertIn(f"def {selector}(", source)
        self.assertIn("without advancing Fiat", coverage["transition"])

    def test_runtime_positive_selectors_reject_declaration_text_decoys(self):
        cases = {
            "python-string": (
                Path("decoy.py"),
                '\"\"\"\ndef test_positive():\n    pass\n\"\"\"\n',
            ),
            "solidity-comment": (
                Path("decoy.sol"),
                "/*\nfunction test_positive() external {}\n*/\n",
            ),
        }
        for label, (path, source) in cases.items():
            with self.subTest(label=label):
                self.assertFalse(
                    promise_machine_module.selector_resolves(
                        path, source, "test_positive"
                    )
                )

        self.assertTrue(
            promise_machine_module.selector_resolves(
                Path("live.py"),
                "class Tests:\n    async def test_positive(self):\n        pass\n",
                "test_positive",
            )
        )
        self.assertTrue(
            promise_machine_module.selector_resolves(
                Path("live.sol"),
                "contract Tests {\nfunction test_positive() external {}\n}\n",
                "test_positive",
            )
        )

    def test_repository_high_consequence_runtime_bindings_are_complete(self):
        coverage = json.loads(
            (ROOT / "tests" / "promise_machine_coverage.json").read_text(
                encoding="utf-8"
            )
        )
        records = declared_runtime_records()
        common_fields = {
            "promise_id",
            "subject",
            "scope",
            "evidence_references",
            "evidence_classes",
            "unknowns",
            "transition",
            "exception",
            "source_digest",
        }
        level_three_fields = {"authority", "inspectable_evidence"}
        self.assertEqual(len(records), 45)
        self.assertEqual(set(coverage["runtime"]), set(records))
        native_maps = set()
        for promise_id, binding in coverage["runtime"].items():
            with self.subTest(promise_id=promise_id):
                record = records[promise_id]
                expected_fields = common_fields | (
                    level_three_fields if record.consequence == 3 else set()
                )
                self.assertEqual(
                    set(binding),
                    {
                        "source",
                        "selector",
                        "sha256",
                        "reader",
                        "bindings",
                        "positive",
                        "negative",
                    },
                )
                self.assertIn(
                    binding["reader"],
                    {
                        "native-json-v1",
                        "python-result-adapter-v1",
                        "markdown-result-adapter-v1",
                    },
                )
                self.assertEqual(set(binding["bindings"]), expected_fields)
                self.assertTrue(all(binding["bindings"].values()))
                native_map = tuple(sorted(binding["bindings"].items()))
                self.assertNotIn(native_map, native_maps)
                native_maps.add(native_map)
                source = ROOT / binding["source"]
                row = next(
                    item for item in coverage["rows"] if item["promise_id"] == promise_id
                )
                positive_evidence = coverage["evidence"][row["cases"]["P"]]
                self.assertEqual(binding["source"], positive_evidence["path"])
                self.assertEqual(binding["selector"], positive_evidence["selector"])
                self.assertTrue(source.is_file())
                self.assertEqual(
                    hashlib.sha256(source.read_bytes()).hexdigest(), binding["sha256"]
                )
                self.assertEqual(
                    set(binding["positive"]), {"path", "selector", "sha256"}
                )
                self.assertEqual(
                    set(binding["negative"]),
                    {"path", "selector", "sha256", "finding", "field"},
                )
                self.assertEqual(binding["negative"]["finding"], "PM095")
                self.assertIn(binding["negative"]["field"], binding["bindings"])
                self.assertNotEqual(
                    binding["positive"]["selector"], binding["negative"]["selector"]
                )
                for specimen in (binding["positive"], binding["negative"]):
                    path = ROOT / specimen["path"]
                    self.assertTrue(path.is_file())
                    self.assertEqual(
                        hashlib.sha256(path.read_bytes()).hexdigest(),
                        specimen["sha256"],
                    )
                    path.relative_to(RUNTIME_FIXTURES)

    def test_runtime_cli_executes_every_bound_specimen(self):
        commands = (
            ("coverage", "--check", "--json"),
            ("check", "--only", "runtime", "--json"),
            (
                "check",
                "--only",
                "obligations,contracts,coverage,runtime",
                "--json",
            ),
        )
        for command in commands:
            with self.subTest(command=command):
                completed = run_cli(*command)
                report = json.loads(completed.stdout)
                self.assertEqual(
                    completed.returncode, 0, completed.stdout + completed.stderr
                )
                self.assertEqual(report["findings"], [])
                self.assertEqual(report["counts"]["runtime_bindings"], 35)

    def test_repository_runtime_specimens_use_the_production_reader(self):
        coverage = json.loads(
            (ROOT / "tests" / "promise_machine_coverage.json").read_text(
                encoding="utf-8"
            )
        )
        records = declared_runtime_records()
        for promise_id, binding in coverage["runtime"].items():
            record = records[promise_id]
            positive = load_runtime_selector(binding["positive"])
            negative = load_runtime_selector(binding["negative"])
            with self.subTest(promise_id=promise_id, specimen="positive"):
                findings = promise_machine_module.validate_runtime_result(
                    ROOT,
                    record,
                    binding,
                    positive,
                    binding["positive"]["path"],
                )
                self.assertEqual(findings, [])
                self.assertFalse(positive["promise_machine"]["transition"]["operation_ran"])
                self.assertTrue(positive["promise_machine"]["unknowns"])
            with self.subTest(promise_id=promise_id, specimen="negative"):
                findings = promise_machine_module.validate_runtime_result(
                    ROOT,
                    record,
                    binding,
                    negative,
                    binding["negative"]["path"],
                )
                self.assertEqual(semantic_codes(findings), ["PM095"])
                self.assertEqual(findings[0].promise_id, promise_id)
                self.assertEqual(findings[0].consequence, record.consequence)
                self.assertTrue(findings[0].blocked_transition)
                self.assertTrue(findings[0].recovery)

    def test_every_runtime_binding_field_has_a_red_mutation(self):
        coverage = json.loads(
            (ROOT / "tests" / "promise_machine_coverage.json").read_text(
                encoding="utf-8"
            )
        )
        records = declared_runtime_records()
        mutations = {
            "promise_id": "wrong-promise",
            "subject": "",
            "scope": "",
            "evidence_references": [],
            "evidence_classes": ["unknown"],
            "unknowns": [],
            "transition": {
                "status": "authorised",
                "action": "claim that the domain operation ran",
                "operation_ran": True,
            },
            "exception": {"status": "missing"},
            "source_digest": "0" * 64,
            "authority": None,
            "inspectable_evidence": None,
        }
        for promise_id, binding in coverage["runtime"].items():
            record = records[promise_id]
            positive = load_runtime_selector(binding["positive"])
            for field in binding["bindings"]:
                with self.subTest(promise_id=promise_id, field=field):
                    mutated = mutate_runtime_field(
                        positive, binding, field, mutations[field]
                    )
                    findings = promise_machine_module.validate_runtime_result(
                        ROOT,
                        record,
                        binding,
                        mutated,
                        binding["positive"]["path"],
                    )
                    self.assertEqual(semantic_codes(findings), ["PM095"])
                    self.assertIn(field, findings[0].message)

    def test_level_two_result_cannot_replay_at_level_three(self):
        coverage = json.loads(
            (ROOT / "tests" / "promise_machine_coverage.json").read_text(
                encoding="utf-8"
            )
        )
        records = declared_runtime_records()
        promise_id = next(
            item for item, record in records.items() if record.consequence == 2
        )
        record = records[promise_id]
        level_three = promise_machine_module.PromiseRecord(
            record.promise_id,
            record.skill_path,
            record.group,
            record.evidence_classes,
            3,
        )
        binding = coverage["runtime"][promise_id]
        result = load_runtime_selector(binding["positive"])
        findings = promise_machine_module.validate_runtime_result(
            ROOT, level_three, binding, result, binding["positive"]["path"]
        )
        self.assertEqual(semantic_codes(findings), ["PM095"])
        self.assertIn("authority", findings[0].message)

    def test_level_three_authority_and_evidence_require_distinct_bytes(self):
        coverage = json.loads(
            (ROOT / "tests" / "promise_machine_coverage.json").read_text(
                encoding="utf-8"
            )
        )
        records = declared_runtime_records()
        promise_id = "ariadne-verify-statement"
        record = records[promise_id]
        binding = copy.deepcopy(coverage["runtime"][promise_id])
        positive = load_runtime_selector(binding["positive"])
        source_path = Path(binding["source"])
        authority_path = Path(
            promise_machine_module.runtime_authority_path(ROOT, record)
        )
        payload = (ROOT / source_path).read_bytes()
        digest = hashlib.sha256(payload).hexdigest()

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for relative in (source_path, authority_path):
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(payload)
            binding["sha256"] = digest
            result = mutate_runtime_field(
                positive, binding, "source_digest", digest
            )
            references = copy.deepcopy(
                result["promise_machine"]["evidence_references"]
            )
            for reference in references:
                reference["sha256"] = digest
            result = mutate_runtime_field(
                result, binding, "evidence_references", references
            )
            inspectable = copy.deepcopy(
                result["promise_machine"]["inspectable_evidence"]
            )
            inspectable["sha256"] = digest
            result = mutate_runtime_field(
                result, binding, "inspectable_evidence", inspectable
            )
            authority = copy.deepcopy(result["promise_machine"]["authority"])
            authority["reference"]["sha256"] = digest
            result = mutate_runtime_field(result, binding, "authority", authority)
            findings = promise_machine_module.validate_runtime_result(
                root,
                record,
                binding,
                result,
                "same-bytes-different-paths",
            )

        self.assertEqual(semantic_codes(findings), ["PM095"])
        self.assertIn("inspectable_evidence", findings[0].message)

    def test_runtime_binding_refuses_missing_evidence_reference_and_header_mismatch(self):
        coverage = json.loads(
            (ROOT / "tests" / "promise_machine_coverage.json").read_text(
                encoding="utf-8"
            )
        )
        records = declared_runtime_records()
        promise_id = next(iter(sorted(records)))
        record = records[promise_id]
        binding = coverage["runtime"][promise_id]
        positive = load_runtime_selector(binding["positive"])

        absent = mutate_runtime_field(
            positive,
            binding,
            "evidence_references",
            [
                {
                    "path": "tests/fixtures/promise-machine/runtime/absent.json",
                    "sha256": "0" * 64,
                    "evidence_class": "checked",
                }
            ],
        )
        findings = promise_machine_module.validate_runtime_result(
            ROOT, record, binding, absent, binding["positive"]["path"]
        )
        self.assertEqual(semantic_codes(findings), ["PM095"])
        self.assertIn("evidence_references", findings[0].message)

        mismatched = copy.deepcopy(positive)
        mismatched["promise_machine"]["subject"] = "a different subject"
        findings = promise_machine_module.validate_runtime_result(
            ROOT, record, binding, mismatched, binding["positive"]["path"]
        )
        self.assertEqual(semantic_codes(findings), ["PM095"])
        self.assertIn("subject", findings[0].message)

    def test_runtime_satisfying_classes_require_corresponding_references(self):
        coverage = json.loads(
            (ROOT / "tests" / "promise_machine_coverage.json").read_text(
                encoding="utf-8"
            )
        )
        records = declared_runtime_records()
        promise_id = "alexandria-derived-view"
        record = records[promise_id]
        binding = coverage["runtime"][promise_id]
        positive = load_runtime_selector(binding["positive"])
        unreferenced_class = mutate_runtime_field(
            positive,
            binding,
            "evidence_classes",
            ["checked", "recorded"],
        )
        findings = promise_machine_module.validate_runtime_result(
            ROOT,
            record,
            binding,
            unreferenced_class,
            binding["positive"]["path"],
        )
        self.assertEqual(semantic_codes(findings), ["PM095"])
        self.assertIn("evidence_references", findings[0].message)
        self.assertIn("recorded", findings[0].message)

    def test_runtime_unknown_codes_are_unique(self):
        coverage = json.loads(
            (ROOT / "tests" / "promise_machine_coverage.json").read_text(
                encoding="utf-8"
            )
        )
        records = declared_runtime_records()
        promise_id = "alexandria-derived-view"
        record = records[promise_id]
        binding = coverage["runtime"][promise_id]
        positive = load_runtime_selector(binding["positive"])
        unknowns = copy.deepcopy(positive["promise_machine"]["unknowns"])
        repeated = mutate_runtime_field(
            positive,
            binding,
            "unknowns",
            unknowns + [copy.deepcopy(unknowns[0])],
        )
        findings = promise_machine_module.validate_runtime_result(
            ROOT,
            record,
            binding,
            repeated,
            binding["positive"]["path"],
        )
        self.assertEqual(semantic_codes(findings), ["PM095"])
        self.assertIn("unknowns", findings[0].message)

    def test_runtime_evidence_references_are_unique(self):
        coverage = json.loads(
            (ROOT / "tests" / "promise_machine_coverage.json").read_text(
                encoding="utf-8"
            )
        )
        records = declared_runtime_records()
        promise_id = "alexandria-derived-view"
        record = records[promise_id]
        binding = coverage["runtime"][promise_id]
        positive = load_runtime_selector(binding["positive"])
        references = copy.deepcopy(
            positive["promise_machine"]["evidence_references"]
        )
        repeated = mutate_runtime_field(
            positive,
            binding,
            "evidence_references",
            references + [copy.deepcopy(references[0])],
        )
        findings = promise_machine_module.validate_runtime_result(
            ROOT,
            record,
            binding,
            repeated,
            binding["positive"]["path"],
        )
        self.assertEqual(semantic_codes(findings), ["PM095"])
        self.assertIn("evidence_references", findings[0].message)

    def test_runtime_negative_specimens_name_and_isolate_their_field(self):
        coverage = json.loads(
            (ROOT / "tests" / "promise_machine_coverage.json").read_text(
                encoding="utf-8"
            )
        )
        declared_fields = {
            binding["negative"].get("field")
            for binding in coverage["runtime"].values()
        }
        self.assertNotIn(None, declared_fields)
        for promise_id, binding in coverage["runtime"].items():
            with self.subTest(promise_id=promise_id):
                field = binding["negative"].get("field")
                self.assertIn(field, binding["bindings"])
                positive = load_runtime_selector(binding["positive"])
                negative = load_runtime_selector(binding["negative"])
                self.assertIsNone(
                    promise_machine_module.runtime_negative_mutation_error(
                        binding, positive, negative
                    )
                )

        binding = coverage["runtime"]["alexandria-derived-view"]
        positive = load_runtime_selector(binding["positive"])
        wrong_field = mutate_runtime_field(
            positive, binding, "promise_id", "wrong-promise"
        )
        error = promise_machine_module.runtime_negative_mutation_error(
            binding, positive, wrong_field
        )
        self.assertIn("does not mutate declared field", error)
        negative = load_runtime_selector(binding["negative"])
        extra_field = mutate_runtime_field(
            negative, binding, "promise_id", "wrong-promise"
        )
        error = promise_machine_module.runtime_negative_mutation_error(
            binding, positive, extra_field
        )
        self.assertIn("outside declared field", error)
        wrong_kind = copy.deepcopy(binding)
        wrong_kind["negative"]["field"] = []
        error = promise_machine_module.runtime_negative_mutation_error(
            wrong_kind, positive, negative
        )
        self.assertIn("does not name one declared runtime field", error)

    def test_runtime_specimen_reads_refuse_hostile_paths_and_bytes(self):
        record = promise_machine_module.PromiseRecord(
            "fixture-promise",
            "plugins/fixture/skills/fixture/SKILL.md",
            "executable",
            frozenset({"checked"}),
            2,
        )

        def descriptor(path, payload=None):
            digest = hashlib.sha256(payload).hexdigest() if payload is not None else "0" * 64
            return {"path": path, "selector": "positive", "sha256": digest}

        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory).resolve()
            runtime = target / "tests" / "fixtures" / "promise-machine" / "runtime"
            runtime.mkdir(parents=True)
            outside = target.parent / f"{target.name}-outside.json"
            outside.write_text('{}\n', encoding="utf-8")
            self.addCleanup(lambda: outside.unlink(missing_ok=True))

            cases = []
            cases.append(("escape", descriptor("../outside.json")))

            linked = runtime / "linked.json"
            linked.symlink_to(outside)
            cases.append(("symlink", descriptor(linked.relative_to(target).as_posix())))

            nonfile = runtime / "directory.json"
            nonfile.mkdir()
            cases.append(("non-file", descriptor(nonfile.relative_to(target).as_posix())))

            oversized = b"{" + b" " * (promise_machine_module.MAX_JSON_BYTES + 1)
            oversized_path = runtime / "oversized.json"
            oversized_path.write_bytes(oversized)
            cases.append(
                (
                    "oversize",
                    descriptor(oversized_path.relative_to(target).as_posix(), oversized),
                )
            )

            invalid = b"{\"schema\":\"x\",\"specimens\":{\"positive\":\xff}}"
            invalid_path = runtime / "invalid.json"
            invalid_path.write_bytes(invalid)
            cases.append(
                (
                    "invalid-utf8",
                    descriptor(invalid_path.relative_to(target).as_posix(), invalid),
                )
            )

            duplicate = b'{"schema":"x","schema":"x","specimens":{"positive":{}}}'
            duplicate_path = runtime / "duplicate.json"
            duplicate_path.write_bytes(duplicate)
            cases.append(
                (
                    "duplicate-key",
                    descriptor(duplicate_path.relative_to(target).as_posix(), duplicate),
                )
            )

            for label, item in cases:
                with self.subTest(label=label):
                    loaded, findings = promise_machine_module.read_runtime_specimen(
                        target, item, record, "positive"
                    )
                    self.assertIsNone(loaded)
                    self.assertEqual(semantic_codes(findings), ["PM095"])

    def test_high_consequence_promise_without_runtime_binding_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            coverage_path, document = write_coverage_fixture(target)
            skill = target / "plugins/hexaemeron/skills/elenchus/SKILL.md"
            skill.write_text(
                skill.read_text(encoding="utf-8").replace(
                    "- Consequence: 1", "- Consequence: 2"
                ),
                encoding="utf-8",
            )
            coverage_path.write_text(json.dumps(document), encoding="utf-8")
            completed = run_cli(
                "coverage", "--check", "--root", target, "--group", "executable", "--json"
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM070", [item["code"] for item in report["findings"]])

    def test_runtime_binding_source_must_be_confined(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            coverage_path, document = write_coverage_fixture(target)
            skill = target / "plugins/hexaemeron/skills/elenchus/SKILL.md"
            skill.write_text(
                skill.read_text(encoding="utf-8").replace(
                    "- Consequence: 1", "- Consequence: 2"
                ),
                encoding="utf-8",
            )
            document["runtime"] = {
                "example-check": fixture_runtime_binding(
                    "../outside.json", "0" * 64
                )
            }
            coverage_path.write_text(json.dumps(document), encoding="utf-8")
            completed = run_cli(
                "coverage", "--check", "--root", target, "--group", "executable", "--json"
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM070", [item["code"] for item in report["findings"]])

    def test_runtime_binding_source_must_be_the_covered_positive_surface(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            coverage_path, document = write_coverage_fixture(target)
            skill = target / "plugins/hexaemeron/skills/elenchus/SKILL.md"
            skill.write_text(
                skill.read_text(encoding="utf-8").replace(
                    "- Consequence: 1", "- Consequence: 2"
                ),
                encoding="utf-8",
            )
            unrelated = target / "tests" / "unrelated.py"
            unrelated.write_text("def unrelated():\n    pass\n", encoding="utf-8")
            source = unrelated.relative_to(target).as_posix()
            source_digest = hashlib.sha256(unrelated.read_bytes()).hexdigest()
            values = {
                "promise_id": "example-check",
                "subject": f"runtime source {source}",
                "scope": "structural binding for example-check",
                "evidence_references": [
                    {
                        "path": source,
                        "sha256": source_digest,
                        "evidence_class": "checked",
                    }
                ],
                "evidence_classes": ["checked"],
                "unknowns": [
                    {
                        "code": "domain-operation-not-run",
                        "detail": "The structural reader did not run the domain operation.",
                    }
                ],
                "transition": {
                    "status": "structurally-bound",
                    "action": "structurally bind example-check without running its domain operation",
                    "operation_ran": False,
                },
                "exception": {"status": "none"},
                "source_digest": source_digest,
            }
            positive = {
                "schema": "promise-machine-python-result-adapter/v1",
                "adapter_output": {},
                "promise_machine": copy.deepcopy(values),
            }
            for field, dotted in PYTHON_RUNTIME_BINDINGS.items():
                cursor = positive
                parts = dotted.split(".")
                for part in parts[:-1]:
                    cursor = cursor.setdefault(part, {})
                cursor[parts[-1]] = copy.deepcopy(values[field])
            negative = mutate_runtime_field(
                positive,
                {"bindings": PYTHON_RUNTIME_BINDINGS},
                "source_digest",
                "0" * 64,
            )
            specimen_path = (
                target
                / "tests"
                / "fixtures"
                / "promise-machine"
                / "runtime"
                / "example-check.json"
            )
            specimen_path.parent.mkdir(parents=True)
            specimen_path.write_text(
                json.dumps(
                    {
                        "schema": "promise-machine-runtime-specimens/v1",
                        "specimens": {"positive": positive, "negative": negative},
                    }
                ),
                encoding="utf-8",
            )
            specimen_digest = hashlib.sha256(specimen_path.read_bytes()).hexdigest()
            binding = fixture_runtime_binding(source, source_digest)
            for kind in ("positive", "negative"):
                binding[kind]["path"] = specimen_path.relative_to(target).as_posix()
                binding[kind]["sha256"] = specimen_digest
            document["runtime"] = {"example-check": binding}
            coverage_path.write_text(json.dumps(document), encoding="utf-8")
            completed = run_cli(
                "coverage",
                "--check",
                "--root",
                target,
                "--group",
                "executable",
                "--json",
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM095", [item["code"] for item in report["findings"]])
        self.assertTrue(
            any("positive evidence" in item["message"] for item in report["findings"])
        )

    def test_runtime_binding_source_digest_must_be_current(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            coverage_path, document = write_coverage_fixture(target)
            skill = target / "plugins/hexaemeron/skills/elenchus/SKILL.md"
            skill.write_text(
                skill.read_text(encoding="utf-8").replace(
                    "- Consequence: 1", "- Consequence: 2"
                ),
                encoding="utf-8",
            )
            document["runtime"] = {
                "example-check": fixture_runtime_binding(
                    "tests/evidence.py", "0" * 64
                )
            }
            coverage_path.write_text(json.dumps(document), encoding="utf-8")
            completed = run_cli(
                "coverage", "--check", "--root", target, "--group", "executable", "--json"
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM071", [item["code"] for item in report["findings"]])

    def test_runtime_catalogue_reports_every_independent_row_fault(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            coverage_path, document = write_coverage_fixture(target)
            skill = target / "plugins/hexaemeron/skills/elenchus/SKILL.md"
            skill.write_text(
                skill.read_text(encoding="utf-8").replace(
                    "- Consequence: 1", "- Consequence: 2"
                ),
                encoding="utf-8",
            )
            source = target / "tests/evidence.py"
            specimen = (
                target
                / "tests"
                / "fixtures"
                / "promise-machine"
                / "runtime"
                / "example-check.json"
            )
            specimen.parent.mkdir(parents=True)
            specimen.write_text("{}\n", encoding="utf-8")
            binding = fixture_runtime_binding(
                "tests/evidence.py", hashlib.sha256(source.read_bytes()).hexdigest()
            )
            for kind in ("positive", "negative"):
                binding[kind]["path"] = specimen.relative_to(target).as_posix()
                binding[kind]["sha256"] = f"malformed-{kind}-digest"
            document["runtime"] = {"example-check": binding}
            coverage_path.write_text(json.dumps(document), encoding="utf-8")
            completed = run_cli(
                "check", "--only", "runtime", "--root", target, "--json"
            )
        report = json.loads(completed.stdout)
        messages = [item["message"] for item in report["findings"]]
        self.assertEqual(completed.returncode, 1)
        self.assertEqual([item["code"] for item in report["findings"]], ["PM095"] * 2)
        self.assertTrue(
            any("runtime positive specimen digest is malformed" in item for item in messages)
        )
        self.assertTrue(
            any("runtime negative specimen digest is malformed" in item for item in messages)
        )

    def test_runtime_binding_source_read_is_bounded(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            coverage_path, document = write_coverage_fixture(target)
            skill = target / "plugins/hexaemeron/skills/elenchus/SKILL.md"
            skill.write_text(
                skill.read_text(encoding="utf-8").replace(
                    "- Consequence: 1", "- Consequence: 2"
                ),
                encoding="utf-8",
            )
            oversized = target / "tests/oversized.bin"
            oversized.write_bytes(b"x" * (1024 * 1024 + 1))
            document["runtime"] = {
                "example-check": fixture_runtime_binding(
                    "tests/oversized.bin",
                    hashlib.sha256(oversized.read_bytes()).hexdigest(),
                )
            }
            coverage_path.write_text(json.dumps(document), encoding="utf-8")
            completed = run_cli(
                "coverage", "--check", "--root", target, "--group", "executable", "--json"
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM070", [item["code"] for item in report["findings"]])

    def test_repository_prompt_and_vendored_coverage_is_complete(self):
        completed = run_cli(
            "coverage", "--check", "--group", "prompt,vendored", "--json"
        )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertTrue(report["ok"])
        self.assertEqual(report["counts"]["coverage_rows"], len(coverage_rows()))
        self.assertEqual(report["counts"]["coverage_selected"], 17)

    def test_prompt_and_vendored_evaluations_never_claim_proof(self):
        coverage = json.loads(
            (ROOT / "tests" / "promise_machine_coverage.json").read_text(
                encoding="utf-8"
            )
        )
        selected = [
            row for row in coverage["rows"] if row["group"] in {"prompt", "vendored"}
        ]
        self.assertEqual(len(selected), 17)
        self.assertTrue(all("pending" not in row for row in selected))
        self.assertTrue(
            all(row["evaluation"]["status"] in {"recorded", "unknown"} for row in selected)
        )

    def run_mutation(self, mutate):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            coverage_path, document = write_coverage_fixture(target)
            mutate(document)
            coverage_path.write_text(json.dumps(document), encoding="utf-8")
            completed = run_cli(
                "coverage",
                "--check",
                "--root",
                target,
                "--group",
                "executable",
                "--json",
            )
        return completed, json.loads(completed.stdout)

    def run_vendored_mutation(self, mutate):
        def complete(document):
            row = document["rows"][1]
            row["cases"] = dict(document["rows"][0]["cases"])
            row.pop("pending")
            for evidence in document["evidence"].values():
                evidence["evidence_class"] = "checked"
            row["evaluation"] = {
                "status": "recorded",
                "model": "not-run",
                "prompt": "Fixture prompt.",
                "corpus": "tests/evidence.py",
                "disposition": "Fixture classifications recorded.",
            }
            mutate(document)

        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            coverage_path, document = write_coverage_fixture(target)
            complete(document)
            coverage_path.write_text(json.dumps(document), encoding="utf-8")
            completed = run_cli(
                "coverage",
                "--check",
                "--root",
                target,
                "--group",
                "vendored",
                "--json",
            )
        return completed, json.loads(completed.stdout)

    def test_missing_coverage_row_is_refused(self):
        completed, report = self.run_mutation(
            lambda document: document["rows"].pop(0)
        )
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM062", [item["code"] for item in report["findings"]])

    def test_unresolved_test_selector_is_refused(self):
        def mutate(document):
            document["evidence"]["p"]["selector"] = "test_absent"

        completed, report = self.run_mutation(mutate)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM065", [item["code"] for item in report["findings"]])

    def test_one_selector_cannot_satisfy_incompatible_cases(self):
        def mutate(document):
            document["rows"][0]["cases"]["M"] = "p"

        completed, report = self.run_mutation(mutate)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM067", [item["code"] for item in report["findings"]])

    def test_material_missing_case_cannot_be_inapplicable(self):
        def mutate(document):
            document["rows"][0]["cases"]["M"] = {
                "not_applicable": True,
                "reason": "Fixture claim.",
            }

        completed, report = self.run_mutation(mutate)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM066", [item["code"] for item in report["findings"]])

    def test_inapplicability_requires_a_reason(self):
        def mutate(document):
            document["rows"][0]["cases"]["X"] = {"not_applicable": True}

        completed, report = self.run_mutation(mutate)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM064", [item["code"] for item in report["findings"]])

    def test_unsupported_evidence_class_is_refused(self):
        def mutate(document):
            document["evidence"]["p"]["evidence_class"] = "anecdotal"

        completed, report = self.run_mutation(mutate)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM064", [item["code"] for item in report["findings"]])

    def test_evidence_class_must_be_accepted_by_the_promise(self):
        def mutate(document):
            document["evidence"]["p"]["evidence_class"] = "recorded"

        completed, report = self.run_mutation(mutate)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM064", [item["code"] for item in report["findings"]])

    def test_duplicate_json_key_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            coverage_path, _ = write_coverage_fixture(target)
            coverage_path.write_text(
                '{"contract":"promise-machine/v1",'
                '"contract":"promise-machine/v1"}',
                encoding="utf-8",
            )
            completed = run_cli(
                "coverage",
                "--check",
                "--root",
                target,
                "--group",
                "executable",
                "--json",
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM061", [item["code"] for item in report["findings"]])

    def test_selected_pending_row_is_refused(self):
        def mutate(document):
            document["rows"][0]["cases"] = None
            document["rows"][0]["pending"] = "Later."

        completed, report = self.run_mutation(mutate)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM066", [item["code"] for item in report["findings"]])

    def test_prompt_or_vendored_evaluation_provenance_is_required(self):
        completed, report = self.run_vendored_mutation(
            lambda document: document["rows"][1].pop("evaluation")
        )
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM069", [item["code"] for item in report["findings"]])

    def test_prompt_or_vendored_evaluation_may_not_claim_proof(self):
        def mutate(document):
            document["rows"][1]["evaluation"]["status"] = "proved"

        completed, report = self.run_vendored_mutation(mutate)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM069", [item["code"] for item in report["findings"]])

    def test_prompt_or_vendored_evaluation_corpus_must_resolve(self):
        def mutate(document):
            document["rows"][1]["evaluation"]["corpus"] = "tests/missing.json"

        completed, report = self.run_vendored_mutation(mutate)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM069", [item["code"] for item in report["findings"]])

    def test_prompt_or_vendored_evaluation_corpus_must_be_repository_relative(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            coverage_path, document = write_coverage_fixture(target)
            row = document["rows"][1]
            row["cases"] = dict(document["rows"][0]["cases"])
            row.pop("pending")
            for evidence in document["evidence"].values():
                evidence["evidence_class"] = "checked"
            row["evaluation"] = {
                "status": "recorded",
                "model": "not-run",
                "prompt": "Fixture prompt.",
                "corpus": str((target / "tests" / "evidence.py").resolve()),
                "disposition": "Fixture classifications recorded.",
            }
            coverage_path.write_text(json.dumps(document), encoding="utf-8")
            completed = run_cli(
                "coverage",
                "--check",
                "--root",
                target,
                "--group",
                "vendored",
                "--json",
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM069", [item["code"] for item in report["findings"]])


class PromiseEvaluationGateTests(unittest.TestCase):
    def copy_evaluation_fixture(self, target):
        coverage = json.loads(
            (ROOT / promise_machine_module.COVERAGE_PATH).read_text(encoding="utf-8")
        )
        selected = [
            row
            for row in coverage["rows"]
            if row.get("evaluation", {}).get("gate")
            == promise_machine_module.EVALUATION_GATE
        ]
        paths = {
            promise_machine_module.COVERAGE_PATH,
            promise_machine_module.EVALUATION_TEMPLATE_PATH,
            promise_machine_module.EVALUATION_ANSWERS_PATH,
            promise_machine_module.OVERLAY_PATH,
        }
        for row in selected:
            paths.add(Path(row["skill_path"]))
            paths.add(Path(row["evaluation"]["corpus"]))
            paths.add(Path(row["evaluation"]["run"]))
        for relative_path in paths:
            destination = target / relative_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / relative_path, destination)
        return selected

    def run_fixture(self, mutate=None):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        target = Path(directory.name)
        self.copy_evaluation_fixture(target)
        if mutate is not None:
            mutate(target)
        completed = run_cli(
            "check", "--root", target, "--only", "evaluation", "--json"
        )
        return completed, json.loads(completed.stdout)

    def rewrite_json(self, path, mutate):
        document = json.loads(path.read_text(encoding="utf-8"))
        mutate(document)
        path.write_text(
            json.dumps(document, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    def rebind_evaluation_tree(self, target):
        coverage = json.loads(
            (target / promise_machine_module.COVERAGE_PATH).read_text(
                encoding="utf-8"
            )
        )
        selected = [
            row
            for row in coverage["rows"]
            if row.get("evaluation", {}).get("gate")
            == promise_machine_module.EVALUATION_GATE
        ]
        paths = {
            promise_machine_module.COVERAGE_PATH.as_posix(),
            promise_machine_module.EVALUATION_TEMPLATE_PATH.as_posix(),
        }
        for row in selected:
            paths.add(row["skill_path"])
            paths.add(row["evaluation"]["corpus"])
            if row["group"] == "vendored":
                paths.add(promise_machine_module.OVERLAY_PATH.as_posix())
        inventory = [
            {
                "path": path,
                "sha256": hashlib.sha256((target / path).read_bytes()).hexdigest(),
            }
            for path in sorted(paths)
        ]
        run_path = target / selected[0]["evaluation"]["run"]

        def change(document):
            document["prompt_template_sha256"] = hashlib.sha256(
                (target / promise_machine_module.EVALUATION_TEMPLATE_PATH).read_bytes()
            ).hexdigest()
            document["tree_sha256"] = promise_machine_module.evaluation_digest(
                inventory
            )

        self.rewrite_json(run_path, change)

    def test_evaluation_is_a_selectable_repository_check(self):
        self.assertEqual(
            promise_machine_module.parse_only("evaluation"),
            {"evaluation"},
        )

    def test_repository_evaluation_record_is_complete(self):
        completed = run_cli("check", "--only", "evaluation", "--json")
        self.assertEqual(
            completed.returncode,
            0,
            completed.stdout + completed.stderr,
        )
        report = json.loads(completed.stdout)
        self.assertTrue(report["ok"])
        self.assertEqual(report["counts"]["evaluation_cases"], 11)
        self.assertEqual(report["counts"]["evaluation_outcomes"], 55)

    def test_copied_evaluation_record_is_self_contained(self):
        completed, report = self.run_fixture()
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertTrue(report["ok"])

    def test_missing_gate_row_and_not_run_model_refuse(self):
        def mutate(target):
            coverage = target / promise_machine_module.COVERAGE_PATH

            def change(document):
                selected = [
                    row
                    for row in document["rows"]
                    if row.get("evaluation", {}).get("gate")
                    == promise_machine_module.EVALUATION_GATE
                ]
                selected[0]["evaluation"].pop("gate")
                selected[1]["evaluation"]["model"] = "not-run"

            self.rewrite_json(coverage, change)

        completed, report = self.run_fixture(mutate)
        self.assertEqual(completed.returncode, 1)
        codes = [item["code"] for item in report["findings"]]
        self.assertIn("PM107", codes)
        self.assertIn("PM108", codes)

    def test_missing_extra_partial_and_not_run_answers_refuse(self):
        mutations = (
            lambda answers: answers.pop(sorted(answers)[0]),
            lambda answers: answers.__setitem__("extra-promise", "{}"),
            lambda answers: answers.__setitem__(sorted(answers)[0], '{"E01":"refuse"}'),
            lambda answers: answers.__setitem__(sorted(answers)[0], "not-run"),
            lambda answers: answers.__setitem__(
                sorted(answers)[0], "[" * 5_000 + "0" + "]" * 5_000
            ),
        )
        for index, mutation in enumerate(mutations):
            with self.subTest(index=index):
                def mutate(target, mutation=mutation):
                    path = target / promise_machine_module.EVALUATION_ANSWERS_PATH
                    self.rewrite_json(path, lambda document: mutation(document["answers"]))

                completed, report = self.run_fixture(mutate)
                self.assertEqual(completed.returncode, 1)
                self.assertIn("PM109", [item["code"] for item in report["findings"]])

    def test_open_evaluation_corpus_refuses(self):
        def mutate(target):
            coverage = json.loads(
                (target / promise_machine_module.COVERAGE_PATH).read_text(
                    encoding="utf-8"
                )
            )
            selected = next(
                row
                for row in coverage["rows"]
                if row.get("evaluation", {}).get("gate")
                == promise_machine_module.EVALUATION_GATE
            )
            path = target / selected["evaluation"]["corpus"]
            self.rewrite_json(
                path,
                lambda document: document.__setitem__(
                    "model_answers", {"leaked": True}
                ),
            )

        completed, report = self.run_fixture(mutate)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM107", [item["code"] for item in report["findings"]])

    def test_invalid_prompt_template_refuses_even_when_hashes_are_rebound(self):
        def mutate(target):
            path = target / promise_machine_module.EVALUATION_TEMPLATE_PATH
            path.write_text(
                path.read_text(encoding="utf-8").replace("{request}", "request"),
                encoding="utf-8",
            )
            self.rebind_evaluation_tree(target)

        completed, report = self.run_fixture(mutate)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM107", [item["code"] for item in report["findings"]])

    def test_non_scalar_evaluation_dispositions_refuse(self):
        def corpus_mutation(target):
            coverage = json.loads(
                (target / promise_machine_module.COVERAGE_PATH).read_text(
                    encoding="utf-8"
                )
            )
            selected = next(
                row
                for row in coverage["rows"]
                if row.get("evaluation", {}).get("gate")
                == promise_machine_module.EVALUATION_GATE
            )
            path = target / selected["evaluation"]["corpus"]
            self.rewrite_json(
                path,
                lambda document: document["cases"][selected["promise_id"]]["P"].__setitem__(
                    "disposition", []
                ),
            )

        def answer_mutation(target):
            path = target / promise_machine_module.EVALUATION_ANSWERS_PATH

            def change(document):
                first = sorted(document["answers"])[0]
                answer = json.loads(document["answers"][first])
                answer["E01"] = []
                document["answers"][first] = json.dumps(answer)

            self.rewrite_json(path, change)

        def skill_path_mutation(target):
            path = target / promise_machine_module.COVERAGE_PATH

            def change(document):
                selected = next(
                    row
                    for row in document["rows"]
                    if row.get("evaluation", {}).get("gate")
                    == promise_machine_module.EVALUATION_GATE
                )
                selected["skill_path"] = []

            self.rewrite_json(path, change)

        for mutate, code in (
            (corpus_mutation, "PM107"),
            (answer_mutation, "PM109"),
            (skill_path_mutation, "PM107"),
        ):
            with self.subTest(mutate=mutate.__name__):
                completed, report = self.run_fixture(mutate)
                self.assertEqual(completed.returncode, 1)
                self.assertIn(code, [item["code"] for item in report["findings"]])

    def test_edited_answer_or_run_record_refuses(self):
        mutations = (
            lambda target: self.rewrite_json(
                target / promise_machine_module.EVALUATION_ANSWERS_PATH,
                lambda document: document["answers"].__setitem__(
                    sorted(document["answers"])[0],
                    document["answers"][sorted(document["answers"])[0]].replace(
                        '"accept"', '"refuse"', 1
                    ),
                ),
            ),
            lambda target: self.rewrite_json(
                target
                / "docs/promise-machine/obligation-gates/evaluation-run.json",
                lambda document: document["counts"].__setitem__("passed", 54),
            ),
        )
        for index, mutate in enumerate(mutations):
            with self.subTest(index=index):
                completed, report = self.run_fixture(mutate)
                self.assertEqual(completed.returncode, 1)
                self.assertIn("PM109", [item["code"] for item in report["findings"]])

    def test_model_and_date_must_be_complete_and_real(self):
        mutations = (
            lambda document: document.__setitem__("model", "qwen"),
            lambda document: document.__setitem__("model", 7),
            lambda document: document.__setitem__("date", "2026-02-30"),
        )
        for index, mutation in enumerate(mutations):
            with self.subTest(index=index):
                def mutate(target, mutation=mutation):
                    self.rewrite_json(
                        target
                        / "docs/promise-machine/obligation-gates/evaluation-run.json",
                        mutation,
                    )

                completed, report = self.run_fixture(mutate)
                self.assertEqual(completed.returncode, 1)
                self.assertIn("PM108", [item["code"] for item in report["findings"]])

    def test_grade_cannot_claim_or_replace_domain_evidence(self):
        def coverage_claim(target):
            path = target / promise_machine_module.COVERAGE_PATH

            def change(document):
                selected = next(
                    row
                    for row in document["rows"]
                    if row.get("evaluation", {}).get("gate")
                    == promise_machine_module.EVALUATION_GATE
                )
                selected["evaluation"]["domain_evidence"] = "supplied-by-grade"

            self.rewrite_json(path, change)

        def run_claim(target):
            self.rewrite_json(
                target
                / "docs/promise-machine/obligation-gates/evaluation-run.json",
                lambda document: document.__setitem__(
                    "domain_evidence", "claimed-by-grade"
                ),
            )

        for mutate in (coverage_claim, run_claim):
            with self.subTest(mutate=mutate.__name__):
                completed, report = self.run_fixture(mutate)
                self.assertEqual(completed.returncode, 1)
                self.assertIn("PM110", [item["code"] for item in report["findings"]])

    def test_missing_or_symlinked_record_refuses(self):
        def missing(target):
            (target / promise_machine_module.EVALUATION_ANSWERS_PATH).unlink()

        def linked(target):
            path = target / promise_machine_module.EVALUATION_ANSWERS_PATH
            outside = target.parent / f"{target.name}-outside.json"
            outside.write_bytes(path.read_bytes())
            self.addCleanup(outside.unlink, missing_ok=True)
            path.unlink()
            path.symlink_to(outside)

        for mutate in (missing, linked):
            with self.subTest(mutate=mutate.__name__):
                completed, report = self.run_fixture(mutate)
                self.assertEqual(completed.returncode, 1)
                self.assertIn("PM109", [item["code"] for item in report["findings"]])


if __name__ == "__main__":
    unittest.main()
