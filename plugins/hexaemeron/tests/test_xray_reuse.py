"""The X-Ray reuse adapter never turns old preparation into current authority.

The fixture is small enough to make every invalidation edge visible: Router
depends on Vault, which depends on Base. Tests mutate that declared graph and
the exact source bytes, then require the planner and assembler to account for
the whole current scope before promotion may touch the previous cache.
"""

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from lib import xray_reuse as reuse  # noqa: E402


FIXTURES = Path(__file__).resolve().parent / "fixtures" / "xray-reuse"
SCRIPT = Path(reuse.__file__).resolve()
DEMO = FIXTURES / "run_demo.py"
PROOF = PLUGIN_ROOT / "docs" / "xray-source-reuse" / "proof.md"
PROMISES = PLUGIN_ROOT / "PROMISES.md"
AUDIT_LOOP = PLUGIN_ROOT / "skills" / "fiat" / "references" / "audit-loop.md"
XRAY_REUSE_REFERENCE = (
    PLUGIN_ROOT / "skills" / "fiat" / "references" / "xray-reuse.md"
)
WARDEN = PLUGIN_ROOT / "agents" / "warden.md"
XRAY_SKILL = PLUGIN_ROOT / "skills" / "x-ray" / "SKILL.md"
EXPECTED_XRAY_DIGEST = (
    "b23bb94517805c1b8ce717d0e1e0282b0b5c14c7b16f4c32e73940292d3d4a41"
)


def load_demo_module():
    spec = importlib.util.spec_from_file_location("xray_reuse_demo", DEMO)
    if spec is None or spec.loader is None:
        raise AssertionError("fixture demonstration module cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
SOURCE_BOUND_FACT_KEYS = frozenset(
    {
        "access",
        "calls",
        "declarations",
        "entry_points",
        "fund_flows",
        "guards",
        "imports",
        "inheritance",
        "invariant_inputs",
        "key_logic",
        "roles",
        "state_facts",
        "transitions",
        "types",
        "value_facts",
        "writes",
    }
)


class ReuseFixture(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.project = self.root / "project"
        shutil.copytree(FIXTURES / "project", self.project)
        self.scope = json.loads((FIXTURES / "scope.json").read_text(encoding="utf-8"))
        self.scope_path = self.root / "scope.json"
        self.cache = self.root / "cache.json"
        self.candidate = self.root / "candidate.json"
        self.outputs = self.root / "outputs"
        self.outputs.mkdir()
        self.write_scope()

    def write_scope(self):
        self.scope_path.write_text(
            json.dumps(self.scope, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    def source(self, plan, path):
        return next(source for source in plan["sources"] if source["path"] == path)

    def facts(self, path, *, writes=None):
        stem = Path(path).stem
        default_writes = {
            "Base": [self.write_fact("total", "Base.sol:8", "=next")],
            "Vault": [self.write_fact("total", "Vault.sol:8", "+amount")],
            "Router": [self.write_fact("vault", "Router.sol:constructor", "=target")],
        }
        catalog = {
            "access": [f"{stem}.access"],
            "calls": [] if stem == "Base" else [f"{stem}.declared-call"],
            "declarations": [f"{stem}.declaration"],
            "entry_points": [f"{stem}.entry"],
            "fund_flows": [f"{stem}.fund-flow"],
            "guards": [f"{stem}.guard"],
            "imports": [f"{stem}.import"],
            "inheritance": [f"{stem}.inheritance"],
            "invariant_inputs": [f"{stem}.invariant-input"],
            "key_logic": [f"{stem}.key-logic"],
            "roles": [f"{stem}.role"],
            "state_facts": [f"{stem}.state"],
            "transitions": [f"{stem}.transition"],
            "types": [f"{stem}.type"],
            "value_facts": [f"{stem}.value"],
            "writes": default_writes[stem] if writes is None else writes,
        }
        return {key: catalog[key] for key in reuse.FACT_KEYS}

    def write_fact(self, variable, site, delta):
        fact = {"variable": variable, "site": site}
        if set(reuse.FACT_KEYS) == SOURCE_BOUND_FACT_KEYS:
            fact["delta"] = delta
        return fact

    def entry(self, plan, path, *, writes=None):
        source = self.source(plan, path)
        return {
            "schema": reuse.ENTRY_SCHEMA,
            "path": path,
            "source_sha256": source["source_sha256"],
            **plan["identity"],
            "dependencies": source["dependencies"],
            "dependency_digests": reuse.dependency_digests_for(
                path, plan["sources"]
            ),
            "facts": self.facts(path, writes=writes),
        }

    def fresh(self, plan, *, writes_by_path=None):
        writes_by_path = writes_by_path or {}
        return [
            self.entry(plan, path, writes=writes_by_path.get(path))
            for path in plan["dirty"]
        ]

    def write_outputs(self, *, omit=None, suffix=""):
        documents = {
            "architecture.json": json.dumps({"fixture": "xray-reuse", "suffix": suffix}),
            "entry-points.md": f"# entry points{suffix}\n",
            "invariants.md": f"# invariants{suffix}\n",
            "x-ray.md": f"# x-ray{suffix}\n",
        }
        for name, body in documents.items():
            if name != omit:
                (self.outputs / name).write_text(body, encoding="utf-8")

    def write_fixture_outputs_from_synthesis(self, candidate, directory):
        """Render deterministic fixture views without claiming model determinism."""
        directory.mkdir()
        synthesis = candidate["synthesis"]
        compact = json.dumps(synthesis, sort_keys=True, separators=(",", ":"))
        documents = {
            "architecture.json": json.dumps(
                synthesis,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            "entry-points.md": f"# fixture entry points\n\n```json\n{compact}\n```\n",
            "invariants.md": f"# fixture invariants\n\n```json\n{compact}\n```\n",
            "x-ray.md": f"# fixture x-ray\n\n```json\n{compact}\n```\n",
        }
        for name, body in documents.items():
            (directory / name).write_text(body, encoding="utf-8")

    def establish_cache(self):
        plan = reuse.plan(self.project, self.scope)
        self.assertEqual(plan["mode"], "full")
        candidate = reuse.assemble(
            self.project,
            self.scope,
            plan,
            self.fresh(plan),
            candidate_path=self.candidate,
        )
        self.write_outputs()
        reuse.bind_outputs(self.candidate, self.outputs)
        cache = reuse.promote(self.candidate, self.outputs, self.cache)
        return plan, candidate, cache


class ScopeAndEntryTests(ReuseFixture):
    def test_committed_fixture_is_a_complete_bounded_scope(self):
        material = reuse.materialize_scope(self.project, self.scope)
        self.assertEqual(
            [source["path"] for source in material["sources"]],
            ["src/Base.sol", "src/Router.sol", "src/Vault.sol"],
        )
        self.assertTrue(all(len(source["source_sha256"]) == 64 for source in material["sources"]))

    def test_traversal_absolute_backslash_and_unknown_dependencies_refuse(self):
        bad_paths = ("../Outside.sol", "/tmp/Outside.sol", "src\\Outside.sol")
        for path in bad_paths:
            with self.subTest(path=path):
                scope = copy.deepcopy(self.scope)
                scope["sources"][0]["path"] = path
                with self.assertRaises(reuse.ReuseError) as caught:
                    reuse.plan(self.project, scope)
                self.assertEqual(caught.exception.code, "unsafe-path")

        scope = copy.deepcopy(self.scope)
        scope["sources"][0]["dependencies"] = ["src/Absent.sol"]
        with self.assertRaises(reuse.ReuseError) as caught:
            reuse.plan(self.project, scope)
        self.assertEqual(caught.exception.code, "unknown-dependency")

    def test_source_symlinks_refuse_even_when_the_target_stays_inside_root(self):
        base = self.project / "src" / "Base.sol"
        target = self.project / "src" / "RealBase.sol"
        base.rename(target)
        base.symlink_to(target.name)
        with self.assertRaises(reuse.ReuseError) as caught:
            reuse.plan(self.project, self.scope)
        self.assertEqual(caught.exception.code, "unsafe-path")

    def test_model_entries_have_a_closed_source_bound_schema(self):
        plan = reuse.plan(self.project, self.scope)
        entry = self.entry(plan, plan["dirty"][0])
        entry["confidence"] = 0.99
        with self.assertRaises(reuse.ReuseError) as caught:
            reuse.validate_entry(entry)
        self.assertEqual(caught.exception.code, "invalid-schema")

        entry.pop("confidence")
        entry["source_sha256"] = "0" * 64
        with self.assertRaises(reuse.ReuseError) as caught:
            reuse.validate_entry(
                entry,
                plan["identity"],
                self.source(plan, entry["path"]),
            )
        self.assertEqual(caught.exception.code, "entry-source-mismatch")

    def test_duplicate_json_keys_and_non_standard_constants_refuse(self):
        duplicate = self.root / "duplicate.json"
        duplicate.write_text('{"schema":"one","schema":"two"}\n', encoding="utf-8")
        with self.assertRaises(reuse.ReuseError) as caught:
            reuse.load_json(duplicate)
        self.assertEqual(caught.exception.code, "duplicate-json-key")

        constant = self.root / "constant.json"
        constant.write_text('{"value":NaN}\n', encoding="utf-8")
        with self.assertRaises(reuse.ReuseError) as caught:
            reuse.load_json(constant)
        self.assertEqual(caught.exception.code, "invalid-json")

    def test_json_decoder_value_error_is_a_bounded_refusal(self):
        with mock.patch.object(
            reuse.json,
            "loads",
            side_effect=ValueError("integer conversion limit"),
        ):
            with self.assertRaises(reuse.ReuseError) as caught:
                reuse._decode_json(b"0", "hostile JSON")
        self.assertEqual(caught.exception.code, "invalid-json")

    def test_descriptor_read_error_is_a_bounded_refusal(self):
        with mock.patch.object(reuse.os, "read", side_effect=OSError("read failed")):
            with self.assertRaises(reuse.ReuseError) as caught:
                reuse.load_json(self.scope_path, "scope manifest")
        self.assertEqual(caught.exception.code, "unreadable-file")

    def test_lone_surrogate_text_is_a_bounded_refusal(self):
        scope = copy.deepcopy(self.scope)
        scope["analyzer"] = "\ud800"
        with self.assertRaises(reuse.ReuseError) as caught:
            reuse.plan(self.project, scope)
        self.assertEqual(caught.exception.code, "invalid-unicode")

    def test_non_string_object_keys_are_bounded_schema_refusals(self):
        plan, candidate, cache = self.establish_cache()
        manifest = json.loads(
            (self.outputs / reuse.OUTPUT_MANIFEST_NAME).read_text(encoding="utf-8")
        )
        cases = (
            ("scope", self.scope, reuse.validate_scope),
            ("plan", plan, reuse.validate_plan),
            ("facts", candidate["entries"][0]["facts"], reuse.validate_facts),
            ("entry", candidate["entries"][0], reuse.validate_entry),
            ("candidate", candidate, reuse.validate_candidate),
            ("cache", cache, reuse.validate_cache),
            (
                "output manifest",
                manifest,
                lambda value: reuse.validate_output_manifest(
                    value,
                    candidate,
                    manifest["outputs"],
                ),
            ),
        )
        for label, document, validator in cases:
            with self.subTest(label=label):
                hostile = copy.deepcopy(document)
                hostile[1] = True
                with self.assertRaises(reuse.ReuseError) as caught:
                    validator(hostile)
                self.assertEqual(caught.exception.code, "invalid-schema")

    def test_invalid_paths_are_bounded_at_public_filesystem_boundaries(self):
        plan = reuse.plan(self.project, self.scope)
        reuse.assemble(
            self.project,
            self.scope,
            plan,
            self.fresh(plan),
            candidate_path=self.candidate,
        )
        for hostile in ("\0", "\ud800"):
            cases = (
                ("JSON input", lambda: reuse.load_json(hostile), "unsafe-path"),
                (
                    "project root",
                    lambda: reuse.plan(hostile, self.scope),
                    "unsafe-project-root",
                ),
                (
                    "cache input",
                    lambda: reuse.plan(self.project, self.scope, hostile),
                    "unsafe-path",
                ),
                (
                    "candidate output",
                    lambda: reuse.assemble(
                        self.project,
                        self.scope,
                        plan,
                        self.fresh(plan),
                        candidate_path=hostile,
                    ),
                    "unsafe-path",
                ),
                (
                    "candidate input",
                    lambda: reuse.bind_outputs(hostile, self.outputs),
                    "unsafe-path",
                ),
                (
                    "output directory",
                    lambda: reuse.bind_outputs(self.candidate, hostile),
                    "unsafe-path",
                ),
            )
            for label, operation, code in cases:
                with self.subTest(value=ascii(hostile), label=label):
                    with self.assertRaises(reuse.ReuseError) as caught:
                        operation()
                    self.assertEqual(caught.exception.code, code)


class PlanningTests(ReuseFixture):
    def test_missing_cache_requests_full_recomputation(self):
        plan = reuse.plan(self.project, self.scope, self.cache)
        self.assertEqual(plan["mode"], "full")
        self.assertEqual(plan["reason"], "cache-missing")
        self.assertEqual(plan["dirty"], [source["path"] for source in plan["sources"]])
        self.assertEqual(plan["reusable"], [])

    def test_full_recompute_reasons_require_the_exact_full_shape(self):
        plan = reuse.plan(self.project, self.scope)
        paths = [source["path"] for source in plan["sources"]]
        for reason in (
            "cache-invalid",
            "cache-missing",
            "dependency-cycle",
            "identity-drift",
            "scope-mismatch",
        ):
            with self.subTest(reason=reason):
                spliced = copy.deepcopy(plan)
                spliced.update(
                    {
                        "mode": "incremental",
                        "reason": reason,
                        "changed": [],
                        "dirty": [],
                        "reusable": paths,
                    }
                )
                with self.assertRaises(reuse.ReuseError) as caught:
                    reuse.validate_plan(spliced)
                self.assertEqual(caught.exception.code, "incomplete-plan")

    def test_assembly_refuses_reuse_when_plan_declares_cache_missing(self):
        self.establish_cache()
        plan = reuse.plan(self.project, self.scope)
        self.assertEqual((plan["mode"], plan["reason"]), ("full", "cache-missing"))

        spliced = copy.deepcopy(plan)
        spliced.update(
            {
                "mode": "incremental",
                "changed": [],
                "dirty": [],
                "reusable": [source["path"] for source in plan["sources"]],
            }
        )
        with self.assertRaises(reuse.ReuseError) as caught:
            reuse.assemble(
                self.project,
                self.scope,
                spliced,
                [],
                cache_path=self.cache,
            )
        self.assertEqual(caught.exception.code, "incomplete-plan")

    def test_unchanged_scope_reuses_every_entry(self):
        _old_plan, _candidate, cache = self.establish_cache()
        plan = reuse.plan(self.project, self.scope, self.cache)
        self.assertEqual(plan["mode"], "incremental")
        self.assertEqual(plan["reason"], "scope-unchanged")
        self.assertEqual(plan["dirty"], [])
        self.assertEqual(plan["reusable"], cache["synthesis"]["source_inventory"])

    def test_unchanged_planning_reads_and_digests_every_current_source(self):
        self.establish_cache()
        with mock.patch.object(
            reuse,
            "_read_source",
            wraps=reuse._read_source,
        ) as reader:
            plan = reuse.plan(self.project, self.scope, self.cache)

        self.assertEqual((plan["mode"], plan["reason"]), ("incremental", "scope-unchanged"))
        self.assertEqual(
            [call.args[1] for call in reader.call_args_list],
            [source["path"] for source in plan["sources"]],
        )

    def test_scope_unchanged_requires_the_exact_incremental_shape(self):
        self.establish_cache()
        correct = reuse.plan(self.project, self.scope, self.cache)
        paths = [source["path"] for source in correct["sources"]]
        variants = (
            {
                "mode": "full",
                "changed": paths,
                "dirty": paths,
                "reusable": [],
            },
            {
                "changed": ["src/Base.sol"],
                "dirty": ["src/Base.sol"],
                "reusable": ["src/Router.sol", "src/Vault.sol"],
            },
            {"removed": ["src/Old.sol"]},
        )
        for changes in variants:
            with self.subTest(changes=changes):
                spliced = copy.deepcopy(correct)
                spliced.update(changes)
                with self.assertRaises(reuse.ReuseError) as caught:
                    reuse.validate_plan(spliced)
                self.assertEqual(caught.exception.code, "incomplete-plan")

    def test_source_drift_requires_the_exact_reverse_closure_shape(self):
        self.establish_cache()
        base = self.project / "src" / "Base.sol"
        base.write_text(
            base.read_text(encoding="utf-8") + "\n// dependency drift\n",
            encoding="utf-8",
        )
        correct = reuse.plan(self.project, self.scope, self.cache)
        paths = [source["path"] for source in correct["sources"]]
        variants = (
            {
                "changed": [],
                "dirty": [],
                "reusable": paths,
                "reverse_invalidated": [],
            },
            {
                "dirty": ["src/Base.sol"],
                "reusable": ["src/Router.sol", "src/Vault.sol"],
                "reverse_invalidated": [],
            },
            {"reverse_invalidated": []},
            {
                "mode": "full",
                "changed": paths,
                "dirty": paths,
                "reusable": [],
                "reverse_invalidated": [],
            },
            {"removed": ["src/Old.sol"]},
        )
        for changes in variants:
            with self.subTest(changes=changes):
                spliced = copy.deepcopy(correct)
                spliced.update(changes)
                with self.assertRaises(reuse.ReuseError) as caught:
                    reuse.validate_plan(spliced)
                self.assertEqual(caught.exception.code, "incomplete-plan")

    def test_body_only_drift_dirties_that_source(self):
        self.establish_cache()
        router = self.project / "src" / "Router.sol"
        router.write_text(router.read_text(encoding="utf-8") + "\n// body drift\n", encoding="utf-8")
        plan = reuse.plan(self.project, self.scope, self.cache)
        self.assertEqual(plan["changed"], ["src/Router.sol"])
        self.assertEqual(plan["dirty"], ["src/Router.sol"])
        self.assertEqual(plan["reverse_invalidated"], [])

    def test_dependency_byte_drift_invalidates_transitive_dependants(self):
        self.establish_cache()
        base = self.project / "src" / "Base.sol"
        base.write_text(base.read_text(encoding="utf-8") + "\n// dependency drift\n", encoding="utf-8")
        plan = reuse.plan(self.project, self.scope, self.cache)
        self.assertEqual(plan["changed"], ["src/Base.sol"])
        self.assertEqual(
            plan["dirty"],
            ["src/Base.sol", "src/Router.sol", "src/Vault.sol"],
        )
        self.assertEqual(
            plan["reverse_invalidated"],
            ["src/Router.sol", "src/Vault.sol"],
        )

    def test_declared_dependency_drift_dirties_the_source_and_its_dependants(self):
        self.establish_cache()
        vault = next(source for source in self.scope["sources"] if source["path"] == "src/Vault.sol")
        vault["dependencies"] = []
        plan = reuse.plan(self.project, self.scope, self.cache)
        self.assertEqual(plan["changed"], ["src/Vault.sol"])
        self.assertEqual(plan["dirty"], ["src/Router.sol", "src/Vault.sol"])
        self.assertEqual(plan["reverse_invalidated"], ["src/Router.sol"])

    def test_added_or_removed_source_forces_named_full_recomputation(self):
        self.establish_cache()
        self.scope["sources"] = [
            source for source in self.scope["sources"] if source["path"] != "src/Router.sol"
        ]
        plan = reuse.plan(self.project, self.scope, self.cache)
        self.assertEqual((plan["mode"], plan["reason"]), ("full", "scope-mismatch"))
        self.assertEqual(plan["removed"], ["src/Router.sol"])
        self.assertEqual(plan["reusable"], [])
        candidate = reuse.assemble(
            self.project,
            self.scope,
            plan,
            self.fresh(plan),
            cache_path=self.cache,
        )
        self.assertEqual(candidate["synthesis"]["source_inventory"], ["src/Base.sol", "src/Vault.sol"])
        self.assertNotIn("src/Router.sol", json.dumps(candidate))

        self.establish_cache()
        added = self.project / "src" / "Added.sol"
        added.write_text(
            "// SPDX-License-Identifier: MIT\npragma solidity ^0.8.20;\ncontract Added {}\n",
            encoding="utf-8",
        )
        self.scope["sources"].append({"path": "src/Added.sol", "dependencies": []})
        plan = reuse.plan(self.project, self.scope, self.cache)
        self.assertEqual((plan["mode"], plan["reason"]), ("full", "scope-mismatch"))
        self.assertEqual(plan["reusable"], [])

    def test_assembly_refuses_reuse_after_a_source_is_removed(self):
        self.establish_cache()
        self.scope["sources"] = [
            source
            for source in self.scope["sources"]
            if source["path"] != "src/Router.sol"
        ]
        plan = reuse.plan(self.project, self.scope, self.cache)
        self.assertEqual((plan["mode"], plan["reason"]), ("full", "scope-mismatch"))

        spliced = copy.deepcopy(plan)
        spliced.update(
            {
                "mode": "incremental",
                "changed": [],
                "dirty": [],
                "reusable": [source["path"] for source in plan["sources"]],
            }
        )
        with self.assertRaises(reuse.ReuseError) as caught:
            reuse.assemble(
                self.project,
                self.scope,
                spliced,
                [],
                cache_path=self.cache,
            )
        self.assertEqual(caught.exception.code, "incomplete-plan")

    def test_assembly_refuses_reuse_after_a_source_is_added(self):
        self.establish_cache()
        added = self.project / "src" / "Added.sol"
        added.write_text(
            "// SPDX-License-Identifier: MIT\npragma solidity ^0.8.20;\ncontract Added {}\n",
            encoding="utf-8",
        )
        self.scope["sources"].append(
            {"path": "src/Added.sol", "dependencies": []}
        )
        plan = reuse.plan(self.project, self.scope, self.cache)
        self.assertEqual((plan["mode"], plan["reason"]), ("full", "scope-mismatch"))

        spliced = copy.deepcopy(plan)
        spliced.update(
            {
                "mode": "incremental",
                "changed": ["src/Added.sol"],
                "dirty": ["src/Added.sol"],
                "reusable": [
                    source["path"]
                    for source in plan["sources"]
                    if source["path"] != "src/Added.sol"
                ],
            }
        )
        with self.assertRaises(reuse.ReuseError) as caught:
            reuse.assemble(
                self.project,
                self.scope,
                spliced,
                [self.entry(plan, "src/Added.sol", writes=[])],
                cache_path=self.cache,
            )
        self.assertEqual(caught.exception.code, "incomplete-plan")

    def test_corrupt_or_mismatched_cache_falls_back_to_full(self):
        self.establish_cache()
        self.cache.write_text("{not-json", encoding="utf-8")
        plan = reuse.plan(self.project, self.scope, self.cache)
        self.assertEqual((plan["mode"], plan["reason"]), ("full", "cache-invalid"))

        self.establish_cache()
        cache = json.loads(self.cache.read_text(encoding="utf-8"))
        cache["identity"]["config_sha256"] = "d" * 64
        for entry in cache["entries"]:
            entry["config_sha256"] = "d" * 64
        self.cache.write_text(json.dumps(cache), encoding="utf-8")
        plan = reuse.plan(self.project, self.scope, self.cache)
        self.assertEqual((plan["mode"], plan["reason"]), ("full", "identity-drift"))

    def test_a_dependency_cycle_has_a_named_full_plan(self):
        self.scope["sources"][0]["dependencies"] = ["src/Router.sol"]
        plan = reuse.plan(self.project, self.scope, self.cache)
        self.assertEqual((plan["mode"], plan["reason"]), ("full", "dependency-cycle"))

    def test_assembly_refuses_incremental_reuse_for_dependency_cycle(self):
        self.scope["sources"][0]["dependencies"] = ["src/Router.sol"]
        self.establish_cache()
        plan = reuse.plan(self.project, self.scope, self.cache)
        self.assertEqual((plan["mode"], plan["reason"]), ("full", "dependency-cycle"))

        spliced = copy.deepcopy(plan)
        paths = [source["path"] for source in plan["sources"]]
        spliced.update(
            {
                "mode": "incremental",
                "changed": [],
                "dirty": [],
                "reusable": paths,
            }
        )
        with self.assertRaises(reuse.ReuseError) as caught:
            reuse.assemble(
                self.project,
                self.scope,
                spliced,
                [],
                cache_path=self.cache,
            )
        self.assertEqual(caught.exception.code, "incomplete-plan")


class AssemblyAndPromotionTests(ReuseFixture):
    def test_candidate_target_cannot_alias_the_live_cache(self):
        self.establish_cache()
        before = self.cache.read_bytes()
        plan = reuse.plan(self.project, self.scope, self.cache)
        with self.assertRaises(reuse.ReuseError) as caught:
            reuse.assemble(
                self.project,
                self.scope,
                plan,
                [],
                cache_path=self.cache,
                candidate_path=self.cache,
            )
        self.assertEqual(caught.exception.code, "path-alias")
        self.assertEqual(self.cache.read_bytes(), before)

    def test_candidate_target_cannot_alias_an_in_scope_source(self):
        plan = reuse.plan(self.project, self.scope)
        source = self.project / "src" / "Base.sol"
        before = source.read_bytes()
        try:
            with self.assertRaises(reuse.ReuseError) as caught:
                reuse.assemble(
                    self.project,
                    self.scope,
                    plan,
                    self.fresh(plan),
                    candidate_path=source,
                )
        finally:
            source.write_bytes(before)
        self.assertEqual(caught.exception.code, "path-alias")

    def test_assembly_refuses_partial_or_extra_fresh_entries(self):
        plan = reuse.plan(self.project, self.scope)
        fresh = self.fresh(plan)
        with self.assertRaises(reuse.ReuseError) as caught:
            reuse.assemble(self.project, self.scope, plan, fresh[:-1])
        self.assertEqual(caught.exception.code, "missing-fresh-entry")

        duplicate = fresh + [fresh[0]]
        with self.assertRaises(reuse.ReuseError) as caught:
            reuse.assemble(self.project, self.scope, plan, duplicate)
        self.assertEqual(caught.exception.code, "duplicate-source")

    def test_assembly_caps_programmatic_fresh_entries_aggregate(self):
        plan = reuse.plan(self.project, self.scope)
        with mock.patch.object(reuse, "MAX_TOTAL_FRESH_JSON_BYTES", 1):
            with self.assertRaises(reuse.ReuseError) as caught:
                reuse.assemble(self.project, self.scope, plan, self.fresh(plan))
        self.assertEqual(caught.exception.code, "size-limit")

    def test_incomplete_source_bound_facts_refuse_assembly(self):
        plan = reuse.plan(self.project, self.scope)
        fresh = self.fresh(plan)
        self.assertIn("fund_flows", fresh[0]["facts"])
        del fresh[0]["facts"]["fund_flows"]
        with self.assertRaises(reuse.ReuseError) as caught:
            reuse.assemble(self.project, self.scope, plan, fresh)
        self.assertEqual(caught.exception.code, "invalid-schema")

    def test_fresh_synthesis_consumes_the_exact_current_fact_union(self):
        plan = reuse.plan(self.project, self.scope)
        candidate = reuse.assemble(
            self.project,
            self.scope,
            plan,
            self.fresh(plan),
        )
        self.assertIn("source_inputs", candidate["synthesis"])
        self.assertEqual(
            candidate["synthesis"]["source_inputs"],
            [
                {"path": entry["path"], "facts": entry["facts"]}
                for entry in candidate["entries"]
            ],
        )
        self.assertTrue(
            all(
                set(source_input["facts"]) == set(reuse.FACT_KEYS)
                for source_input in candidate["synthesis"]["source_inputs"]
            )
        )

    def test_full_and_unchanged_reuse_have_equivalent_fixture_output_bytes(self):
        full_plan = reuse.plan(self.project, self.scope)
        full_candidate = reuse.assemble(
            self.project,
            self.scope,
            full_plan,
            self.fresh(full_plan),
            candidate_path=self.candidate,
        )
        full_outputs = self.root / "full-outputs"
        self.write_fixture_outputs_from_synthesis(full_candidate, full_outputs)
        reuse.bind_outputs(self.candidate, full_outputs)
        reuse.promote(self.candidate, full_outputs, self.cache)

        unchanged_plan = reuse.plan(self.project, self.scope, self.cache)
        self.assertEqual(
            (unchanged_plan["mode"], unchanged_plan["reason"]),
            ("incremental", "scope-unchanged"),
        )
        reused_candidate_path = self.root / "reused-candidate.json"
        reused_candidate = reuse.assemble(
            self.project,
            self.scope,
            unchanged_plan,
            [],
            cache_path=self.cache,
            candidate_path=reused_candidate_path,
        )
        reuse_outputs = self.root / "reuse-outputs"
        self.write_fixture_outputs_from_synthesis(reused_candidate, reuse_outputs)

        self.assertEqual(reused_candidate, full_candidate)
        for name in reuse.FINAL_OUTPUTS:
            with self.subTest(output=name):
                self.assertEqual(
                    (reuse_outputs / name).read_bytes(),
                    (full_outputs / name).read_bytes(),
                )

    def test_assembly_refuses_source_drift_after_the_plan(self):
        plan = reuse.plan(self.project, self.scope)
        base = self.project / "src" / "Base.sol"
        base.write_text(base.read_text(encoding="utf-8") + "\n// late drift\n", encoding="utf-8")
        with self.assertRaises(reuse.ReuseError) as caught:
            reuse.assemble(self.project, self.scope, plan, self.fresh(plan))
        self.assertEqual(caught.exception.code, "scope-drift")

    def test_plan_splicing_cannot_omit_reverse_dependants(self):
        self.establish_cache()
        base = self.project / "src" / "Base.sol"
        base.write_text(base.read_text(encoding="utf-8") + "\n// changed dependency\n", encoding="utf-8")
        correct = reuse.plan(self.project, self.scope, self.cache)
        self.assertEqual(
            correct["reverse_invalidated"],
            ["src/Router.sol", "src/Vault.sol"],
        )
        spliced = copy.deepcopy(correct)
        spliced["dirty"] = ["src/Base.sol"]
        spliced["reusable"] = ["src/Router.sol", "src/Vault.sol"]
        spliced["reverse_invalidated"] = []
        with self.assertRaises(reuse.ReuseError) as caught:
            reuse.assemble(
                self.project,
                self.scope,
                spliced,
                [self.entry(correct, "src/Base.sol")],
                cache_path=self.cache,
            )
        self.assertEqual(caught.exception.code, "incomplete-plan")

    def test_substituted_cache_cannot_change_transitive_dependency_binding(self):
        self.establish_cache()
        plan = reuse.plan(self.project, self.scope, self.cache)
        cache = json.loads(self.cache.read_text(encoding="utf-8"))
        vault = next(
            entry for entry in cache["entries"] if entry["path"] == "src/Vault.sol"
        )
        vault["dependency_digests"][0]["source_sha256"] = "0" * 64
        self.cache.write_text(json.dumps(cache), encoding="utf-8")

        with self.assertRaises(reuse.ReuseError) as caught:
            reuse.assemble(
                self.project,
                self.scope,
                plan,
                [],
                cache_path=self.cache,
            )
        self.assertEqual(caught.exception.code, "entry-dependency-mismatch")

    def test_write_site_inputs_are_rebuilt_from_the_exact_current_union(self):
        self.establish_cache()
        vault = self.project / "src" / "Vault.sol"
        vault.write_text(vault.read_text(encoding="utf-8") + "\n// write-site drift\n", encoding="utf-8")
        plan = reuse.plan(self.project, self.scope, self.cache)
        candidate = reuse.assemble(
            self.project,
            self.scope,
            plan,
            self.fresh(
                plan,
                writes_by_path={
                    "src/Vault.sol": [
                        self.write_fact("shares", "Vault.sol:12", "+amount")
                    ]
                },
            ),
            cache_path=self.cache,
        )
        write_sites = {item["variable"]: item["sites"] for item in candidate["synthesis"]["write_sites"]}
        expected_share = {"path": "src/Vault.sol", "site": "Vault.sol:12"}
        replaced_total = {"path": "src/Vault.sol", "site": "Vault.sol:8"}
        if set(reuse.FACT_KEYS) == SOURCE_BOUND_FACT_KEYS:
            expected_share["delta"] = "+amount"
            replaced_total["delta"] = "+amount"
        self.assertEqual(write_sites["shares"], [expected_share])
        self.assertNotIn(
            replaced_total,
            write_sites["total"],
        )

    def test_promotion_requires_all_four_nonempty_outputs(self):
        plan = reuse.plan(self.project, self.scope)
        reuse.assemble(
            self.project,
            self.scope,
            plan,
            self.fresh(plan),
            candidate_path=self.candidate,
        )
        self.write_outputs(omit="invariants.md")
        with self.assertRaises(reuse.ReuseError) as caught:
            reuse.promote(self.candidate, self.outputs, self.cache)
        self.assertEqual(caught.exception.code, "missing-file")
        self.assertFalse(self.cache.exists())

    def test_architecture_decoder_value_error_is_a_bounded_refusal(self):
        self.write_outputs()
        with mock.patch.object(
            reuse.json,
            "loads",
            side_effect=ValueError("integer conversion limit"),
        ):
            with self.assertRaises(reuse.ReuseError) as caught:
                reuse._output_digests(self.outputs)
        self.assertEqual(caught.exception.code, "invalid-output")

    def test_promotion_binds_each_output_digest(self):
        _plan, candidate, cache = self.establish_cache()
        self.assertEqual(cache["synthesis"], candidate["synthesis"])
        for name in reuse.FINAL_OUTPUTS:
            expected = hashlib.sha256((self.outputs / name).read_bytes()).hexdigest()
            self.assertEqual(cache["outputs"][name], expected)

    def test_cache_target_cannot_alias_a_required_output(self):
        plan = reuse.plan(self.project, self.scope)
        reuse.assemble(
            self.project,
            self.scope,
            plan,
            self.fresh(plan),
            candidate_path=self.candidate,
        )
        self.write_outputs()
        reuse.bind_outputs(self.candidate, self.outputs)
        xray_output = self.outputs / "x-ray.md"
        before = xray_output.read_bytes()
        with self.assertRaises(reuse.ReuseError) as caught:
            reuse.promote(
                self.candidate,
                self.outputs,
                xray_output,
            )
        self.assertEqual(caught.exception.code, "path-alias")
        self.assertEqual(xray_output.read_bytes(), before)

    def test_promotion_accepts_the_explicit_manifest_path_that_binding_exposes(self):
        plan = reuse.plan(self.project, self.scope)
        reuse.assemble(
            self.project,
            self.scope,
            plan,
            self.fresh(plan),
            candidate_path=self.candidate,
        )
        self.write_outputs()
        manifest = self.root / "bound-outputs.json"
        reuse.bind_outputs(self.candidate, self.outputs, manifest)
        cache = reuse.promote(
            self.candidate,
            self.outputs,
            self.cache,
            manifest,
        )
        self.assertEqual(
            cache["synthesis"]["source_inventory"],
            ["src/Base.sol", "src/Router.sol", "src/Vault.sol"],
        )

    def test_promotion_refuses_wrong_scope_or_stale_output_evidence(self):
        plan = reuse.plan(self.project, self.scope)
        reuse.assemble(
            self.project,
            self.scope,
            plan,
            self.fresh(plan),
            candidate_path=self.candidate,
        )
        self.write_outputs()
        manifest = reuse.bind_outputs(self.candidate, self.outputs)
        manifest["source_inventory"] = manifest["source_inventory"][:-1]
        manifest_path = self.outputs / reuse.OUTPUT_MANIFEST_NAME
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaises(reuse.ReuseError) as caught:
            reuse.promote(self.candidate, self.outputs, self.cache)
        self.assertEqual(caught.exception.code, "output-scope-mismatch")
        self.assertFalse(self.cache.exists())

        reuse.bind_outputs(self.candidate, self.outputs)
        (self.outputs / "x-ray.md").write_text("# changed after binding\n", encoding="utf-8")
        with self.assertRaises(reuse.ReuseError) as caught:
            reuse.promote(self.candidate, self.outputs, self.cache)
        self.assertEqual(caught.exception.code, "output-digest-mismatch")
        self.assertFalse(self.cache.exists())

        self.write_outputs()
        reuse.bind_outputs(self.candidate, self.outputs)
        altered = json.loads(self.candidate.read_text(encoding="utf-8"))
        altered["entries"][0]["facts"]["guards"].append("fresh-candidate-guard")
        altered["synthesis"] = reuse.rebuild_synthesis(altered["entries"])
        self.candidate.write_text(json.dumps(altered), encoding="utf-8")
        with self.assertRaises(reuse.ReuseError) as caught:
            reuse.promote(self.candidate, self.outputs, self.cache)
        self.assertEqual(caught.exception.code, "candidate-digest-mismatch")
        self.assertFalse(self.cache.exists())

    def test_interrupted_promotion_leaves_the_previous_cache_untouched(self):
        self.establish_cache()
        before = self.cache.read_bytes()
        router = self.project / "src" / "Router.sol"
        router.write_text(router.read_text(encoding="utf-8") + "\n// next run\n", encoding="utf-8")
        plan = reuse.plan(self.project, self.scope, self.cache)
        reuse.assemble(
            self.project,
            self.scope,
            plan,
            self.fresh(plan),
            cache_path=self.cache,
            candidate_path=self.candidate,
        )
        self.write_outputs(suffix=" next")
        reuse.bind_outputs(self.candidate, self.outputs)
        with mock.patch.object(reuse.os, "replace", side_effect=OSError("interrupted")):
            with self.assertRaises(reuse.ReuseError) as caught:
                reuse.promote(self.candidate, self.outputs, self.cache)
        self.assertEqual(caught.exception.code, "atomic-write-failed")
        self.assertEqual(self.cache.read_bytes(), before)
        self.assertEqual(list(self.root.glob(".cache.json.*.tmp")), [])

    def test_atomic_staging_cleanup_preserves_the_structured_refusal(self):
        target = self.root / "target.json"
        close = reuse.os.close

        def close_then_fail(descriptor):
            close(descriptor)
            raise OSError("close failed")

        with mock.patch.object(
            reuse.os,
            "fchmod",
            side_effect=OSError("fchmod failed"),
        ), mock.patch.object(reuse.os, "close", side_effect=close_then_fail):
            with self.assertRaises(reuse.ReuseError) as caught:
                reuse._atomic_write_json(target, {"status": "candidate"})
        self.assertEqual(caught.exception.code, "atomic-write-failed")
        self.assertFalse(target.exists())

    def test_candidate_and_cache_targets_must_not_be_symlinks(self):
        target = self.root / "target.json"
        target.write_text("{}", encoding="utf-8")
        self.candidate.symlink_to(target.name)
        plan = reuse.plan(self.project, self.scope)
        with self.assertRaises(reuse.ReuseError) as caught:
            reuse.assemble(
                self.project,
                self.scope,
                plan,
                self.fresh(plan),
                candidate_path=self.candidate,
            )
        self.assertEqual(caught.exception.code, "unsafe-path")


class CompositionContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.promises = PROMISES.read_text(encoding="utf-8")
        cls.reference = XRAY_REUSE_REFERENCE.read_text(encoding="utf-8")
        cls.audit_loop = AUDIT_LOOP.read_text(encoding="utf-8")
        cls.warden = WARDEN.read_text(encoding="utf-8")

    @classmethod
    def overlay(cls):
        marker = "### hexaemeron-x-ray-preaudit\n"
        start = cls.promises.index(marker)
        following = cls.promises.find("\n### ", start + len(marker))
        return cls.promises[start : following if following >= 0 else None]

    def test_overlay_binds_the_exact_xray_and_adapter_digests(self):
        overlay = self.overlay()
        xray_digest = hashlib.sha256(XRAY_SKILL.read_bytes()).hexdigest()
        adapter_digest = hashlib.sha256(SCRIPT.read_bytes()).hexdigest()
        self.assertEqual(xray_digest, EXPECTED_XRAY_DIGEST)
        self.assertIn(
            "- Path: `plugins/hexaemeron/skills/x-ray/SKILL.md`", overlay
        )
        self.assertIn(f"- SHA-256: `{xray_digest}`", overlay)
        self.assertIn("`plugins/hexaemeron/lib/xray_reuse.py`", overlay)
        self.assertIn(f"SHA-256 `{adapter_digest}`", overlay)

    def test_overlay_keeps_reuse_inside_the_xray_preparation_boundary(self):
        overlay = " ".join(self.overlay().split())
        for clause in (
            "preparation layer only",
            "complete current logical scope",
            "every current source was read and digested",
            "exact current fact union",
            "exact current union",
            "fresh global synthesis",
            "named full recomputation",
        ):
            self.assertIn(clause, overlay)
        for output in reuse.FINAL_OUTPUTS:
            self.assertIn(f"`{output}`", overlay)
        self.assertIn(
            "no global synthesis, final output, finding, or security conclusion is reusable",
            overlay,
        )

    def test_audit_operation_requires_full_scope_fresh_synthesis_and_outputs(self):
        surfaces = {
            "reference": " ".join(self.reference.split()),
            "audit-loop": " ".join(self.audit_loop.split()),
            "warden": " ".join(self.warden.split()),
        }
        self.assertIn(
            "[X-Ray source-reuse protocol](xray-reuse.md)", self.audit_loop
        )
        self.assertIn(
            "`<plugin-root>/skills/fiat/references/xray-reuse.md`", self.warden
        )
        for name, text in surfaces.items():
            with self.subTest(surface=name):
                self.assertIn("preparation layer only", text)
                self.assertIn("full logical scope", text)
                self.assertIn("fresh global synthesis", text)
                self.assertIn("all four final outputs", text)
                self.assertIn("Any cache uncertainty", text)
                self.assertIn("full recomputation", text)
        for output in reuse.FINAL_OUTPUTS:
            self.assertIn(f"`{output}`", self.reference)

    def test_reuse_never_skips_the_pinned_full_scope_source_reads(self):
        xray = XRAY_SKILL.read_text(encoding="utf-8")
        self.assertIn("One Read call per file", xray)
        self.assertIn("Read each file listed below", xray)
        for text in (self.reference, self.audit_loop, self.warden):
            normal = " ".join(text.split()).lower()
            self.assertIn("read and digest every current source", normal)
            self.assertIn(
                "reuse replaces only preparation-fact regeneration", normal
            )

    def test_preparation_schema_covers_pinned_source_bound_inputs(self):
        self.assertEqual(
            set(reuse.FACT_KEYS),
            SOURCE_BOUND_FACT_KEYS,
        )
        facts = {key: [] for key in reuse.FACT_KEYS}
        facts["writes"] = [
            {"delta": "+amount", "site": "Vault.sol:12", "variable": "shares"}
        ]
        facts = reuse.validate_facts(facts)
        self.assertEqual(set(facts["writes"][0]), {"delta", "site", "variable"})

    def test_digest_preconditions_run_before_the_vendored_xray_instruction(self):
        reference_link = "[X-Ray source-reuse protocol](xray-reuse.md)"
        warden_reference = (
            "`<plugin-root>/skills/fiat/references/xray-reuse.md`"
        )
        warden_xray = "`<plugin-root>/skills/x-ray/SKILL.md`"
        self.assertLess(
            self.audit_loop.index(reference_link),
            self.audit_loop.index("`x-ray` pass first"),
        )
        self.assertLess(
            self.warden.index(warden_reference),
            self.warden.index(warden_xray),
        )
        for text in (self.audit_loop, self.warden):
            self.assertIn(
                "complete its digest preconditions", " ".join(text.split())
            )

    def test_reference_keeps_cache_material_out_of_every_fiat_surface(self):
        text = " ".join(self.reference.split())
        for material in (
            "cache paths",
            "cache keys",
            "cache payloads",
            "cache verdicts",
        ):
            self.assertIn(material, text)
        for surface in (
            "`hexctl` state",
            "its ledger",
            "a Warden brief or audit directive",
            "an audit-round receipt",
            "any other Fiat receipt",
        ):
            self.assertIn(surface, text)

    def test_fiat_boundary_does_not_suppress_audit_finding_evidence(self):
        warden = " ".join(self.warden.split())
        self.assertNotIn("audit directive and record", warden)
        self.assertIn(
            "The audit record may name this working material when a finding needs it",
            warden,
        )
        self.assertIn("without giving it controller authority", warden)
        for text in (warden, " ".join(self.audit_loop.split())):
            self.assertIn("cache verdicts", text)
            self.assertNotIn("manifests, and verdicts", text)


class FixtureDemonstrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.demo = load_demo_module()
        process = subprocess.run(
            [sys.executable, str(DEMO), "--samples", "3"],
            text=True,
            capture_output=True,
            check=False,
            timeout=30,
        )
        if process.returncode:
            raise AssertionError(process.stderr)
        cls.proof = json.loads(process.stdout)

    def test_reported_source_reads_are_observed_adapter_reads(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project, scope, cache = self.demo.workspace(root)
            observed = []
            read_source = self.demo.reuse._read_source

            def counted(project_root, relative):
                observed.append(relative)
                return read_source(project_root, relative)

            self.demo.reuse._read_source = counted
            try:
                evidence, _duration = self.demo.execute(
                    project, scope, cache, root, "read-count"
                )
            finally:
                self.demo.reuse._read_source = read_source

        self.assertEqual(evidence["source_reads"], len(observed))
        self.assertEqual(
            evidence["source_read_paths"],
            [
                "src/Base.sol",
                "src/Router.sol",
                "src/Vault.sol",
                "src/Base.sol",
                "src/Router.sol",
                "src/Vault.sol",
            ],
        )

    def test_every_scenario_matches_an_independent_full_recompute(self):
        for name, scenario in self.proof["scenarios"].items():
            with self.subTest(scenario=name):
                self.assertIn("full_recompute", scenario)
                self.assertIn("matches_full_recompute", scenario)
                reference = scenario["full_recompute"]
                matches = scenario["matches_full_recompute"]
                self.assertEqual(
                    (reference["plan"]["mode"], reference["plan"]["reason"]),
                    ("full", "cache-missing"),
                )
                self.assertEqual(reference["fresh_extractions"], len(scenario["source_inventory"]))
                self.assertEqual(reference["reused_entries"], 0)
                self.assertEqual(
                    matches,
                    {"candidate": True, "fact_union": True, "outputs": True},
                )
                self.assertEqual(scenario["outputs"], reference["outputs"])
                self.assertEqual(
                    scenario["fact_union_sha256"], reference["fact_union_sha256"]
                )
                self.assertEqual(
                    scenario["candidate_sha256"], reference["candidate_sha256"]
                )

    def test_body_only_case_changes_executable_body_without_interface_drift(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project, scope, cache = self.demo.workspace(root)
            router = project / "src" / "Router.sol"
            before = router.read_text(encoding="utf-8")
            variants = self.demo.body_only(project, scope, cache)
            after = router.read_text(encoding="utf-8")

        def executable_lines(source):
            return [
                line.strip()
                for line in source.splitlines()
                if line.strip() and not line.strip().startswith("//")
            ]

        self.assertEqual(variants, {"src/Router.sol": "body-v2"})
        self.assertNotEqual(executable_lines(before), executable_lines(after))
        self.assertIn("Vault public immutable vault;", before)
        self.assertIn("Vault public immutable vault;", after)
        self.assertIn("function route(uint256 amount) external", before)
        self.assertIn("function route(uint256 amount) external", after)

    def test_exactly_three_paired_samples_preserve_all_four_outputs(self):
        timing = self.proof["timing"]
        self.assertEqual(len(timing["samples"]), 3)
        for sample in timing["samples"]:
            self.assertGreater(sample["full_wall_time_ns"], 0)
            self.assertGreater(sample["unchanged_wall_time_ns"], 0)
            self.assertTrue(sample["outputs_equal"])
            self.assertEqual(sample["full_outputs"], sample["unchanged_outputs"])
            self.assertEqual(set(sample["full_outputs"]), set(reuse.FINAL_OUTPUTS))
        for mode in ("full", "unchanged"):
            values = [
                sample[f"{mode}_wall_time_ns"] for sample in timing["samples"]
            ]
            self.assertEqual(timing[f"{mode}_spread_ns"], max(values) - min(values))

    def test_full_and_unchanged_have_exact_extraction_and_reuse_counts(self):
        full = self.proof["scenarios"]["full"]
        unchanged = self.proof["scenarios"]["unchanged"]
        self.assertEqual(
            (full["plan"]["mode"], full["plan"]["reason"]),
            ("full", "cache-missing"),
        )
        self.assertEqual(
            (full["source_reads"], full["fresh_extractions"], full["reused_entries"]),
            (6, 3, 0),
        )
        self.assertEqual(
            (unchanged["plan"]["mode"], unchanged["plan"]["reason"]),
            ("incremental", "scope-unchanged"),
        )
        self.assertEqual(
            (
                unchanged["source_reads"],
                unchanged["fresh_extractions"],
                unchanged["reused_entries"],
            ),
            (6, 0, 3),
        )
        self.assertEqual(full["outputs"], unchanged["outputs"])
        self.assertEqual(full["fact_union_sha256"], unchanged["fact_union_sha256"])

    def test_drift_removal_and_corrupt_cache_have_exact_safe_plans(self):
        scenarios = self.proof["scenarios"]
        expected = {
            "body-only": {
                "mode": "incremental",
                "reason": "source-drift",
                "dirty": ["src/Router.sol"],
                "reusable": ["src/Base.sol", "src/Vault.sol"],
                "removed": [],
                "reverse_invalidated": [],
            },
            "dependency-drift": {
                "mode": "incremental",
                "reason": "source-drift",
                "dirty": ["src/Base.sol", "src/Router.sol", "src/Vault.sol"],
                "reusable": [],
                "removed": [],
                "reverse_invalidated": ["src/Router.sol", "src/Vault.sol"],
            },
            "write-site-drift": {
                "mode": "incremental",
                "reason": "source-drift",
                "dirty": ["src/Router.sol", "src/Vault.sol"],
                "reusable": ["src/Base.sol"],
                "removed": [],
                "reverse_invalidated": ["src/Router.sol"],
            },
            "source-removal": {
                "mode": "full",
                "reason": "scope-mismatch",
                "dirty": ["src/Base.sol", "src/Vault.sol"],
                "reusable": [],
                "removed": ["src/Router.sol"],
                "reverse_invalidated": [],
            },
            "corrupt-cache": {
                "mode": "full",
                "reason": "cache-invalid",
                "dirty": ["src/Base.sol", "src/Router.sol", "src/Vault.sol"],
                "reusable": [],
                "removed": [],
                "reverse_invalidated": [],
            },
        }
        for name, plan in expected.items():
            with self.subTest(scenario=name):
                actual = scenarios[name]["plan"]
                for key, value in plan.items():
                    self.assertEqual(actual[key], value)
                self.assertEqual(
                    scenarios[name]["fresh_extractions"], len(plan["dirty"])
                )
                self.assertEqual(
                    scenarios[name]["reused_entries"], len(plan["reusable"])
                )
                self.assertEqual(scenarios[name]["stale_removed_rows"], [])
                self.assertEqual(
                    set(scenarios[name]["outputs"]), set(reuse.FINAL_OUTPUTS)
                )
        removal = scenarios["source-removal"]
        self.assertEqual(
            removal["source_inventory"], ["src/Base.sol", "src/Vault.sol"]
        )
        self.assertNotIn("src/Router.sol", removal["source_digests"])
        self.assertNotIn(
            "src/Router.sol", json.dumps(removal["write_sites"], sort_keys=True)
        )

    def test_write_site_drift_rebuilds_the_complete_current_write_map(self):
        writes = self.proof["scenarios"]["write-site-drift"]["write_sites"]
        total = next(item for item in writes if item["variable"] == "total")
        self.assertEqual(
            total["sites"],
            [
                {"path": "src/Base.sol", "site": "Base.sol:8", "delta": "=next"},
                {
                    "path": "src/Vault.sol",
                    "site": "Vault.sol:8",
                    "delta": "+amount+1",
                },
            ],
        )

    def test_environment_and_limits_keep_the_claim_bounded(self):
        self.assertEqual(
            self.proof["schema"], "hexaemeron.xray.reuse-fixture-proof.v1"
        )
        self.assertFalse(self.proof["environment"]["network"])
        self.assertEqual(self.proof["limits"]["samples_per_mode"], 3)
        self.assertEqual(self.proof["limits"]["warmups_discarded"], 0)
        self.assertNotIn("speedup", self.proof)
        self.assertEqual(
            self.proof["environment"]["xray_skill_sha256"], EXPECTED_XRAY_DIGEST
        )
        self.assertEqual(
            self.proof["environment"]["adapter_sha256"],
            hashlib.sha256(SCRIPT.read_bytes()).hexdigest(),
        )

    def test_durable_proof_embeds_parseable_recorded_evidence(self):
        document = PROOF.read_text(encoding="utf-8")
        raw_section = document.split("## raw stdout\n", 1)[1]
        raw = raw_section.split("```json\n", 1)[1].split("\n```", 1)[0]
        recorded = json.loads(raw)
        self.assertEqual(
            recorded["schema"], "hexaemeron.xray.reuse-fixture-proof.v1"
        )
        self.assertEqual(set(recorded["scenarios"]), set(self.proof["scenarios"]))
        self.assertEqual(recorded["scenarios"], self.proof["scenarios"])
        self.assertEqual(recorded["limits"], self.proof["limits"])
        self.assertEqual(len(recorded["timing"]["samples"]), 3)
        self.assertEqual(
            recorded["scenarios"]["full"]["outputs"],
            recorded["scenarios"]["unchanged"]["outputs"],
        )
        self.assertEqual(
            recorded["environment"]["adapter_sha256"],
            hashlib.sha256(SCRIPT.read_bytes()).hexdigest(),
        )
        self.assertEqual(
            recorded["environment"]["xray_skill_sha256"], EXPECTED_XRAY_DIGEST
        )
        for sample in recorded["timing"]["samples"]:
            row = (
                f'| {sample["sample"]} | {sample["full_wall_time_ns"]} | '
                f'{sample["unchanged_wall_time_ns"]} | yes |'
            )
            self.assertIn(row, document)
        self.assertIn(
            f'Full spread: {recorded["timing"]["full_spread_ns"]} ns.',
            document,
        )
        self.assertIn(
            f'Unchanged spread: {recorded["timing"]["unchanged_spread_ns"]} ns.',
            document,
        )


class CommandTests(ReuseFixture):
    def test_assemble_cli_refuses_candidate_aliases_consumed_inputs(self):
        plan = reuse.plan(self.project, self.scope)
        plan_path = self.root / "plan.json"
        plan_path.write_text(
            json.dumps(plan, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        fresh_paths = []
        for index, entry in enumerate(self.fresh(plan)):
            path = self.root / f"fresh-{index}.json"
            path.write_text(
                json.dumps(entry, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            fresh_paths.append(path)
        command = [
            sys.executable,
            str(SCRIPT),
            "assemble",
            "--project-root",
            str(self.project),
            "--scope",
            str(self.scope_path),
            "--plan",
            str(plan_path),
        ]
        for path in fresh_paths:
            command.extend(("--fresh-entry", str(path)))

        aliases = (
            ("scope", self.scope_path),
            ("plan", plan_path),
            ("fresh entry", fresh_paths[0]),
            ("source", self.project / "src" / "Base.sol"),
        )
        for label, target in aliases:
            with self.subTest(label=label):
                before = target.read_bytes()
                process = subprocess.run(
                    [*command, "--candidate", str(target)],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                if target.read_bytes() != before:
                    target.write_bytes(before)
                self.assertEqual(process.returncode, 2, process.stderr)
                refusal = json.loads(process.stderr)
                self.assertEqual(refusal["code"], "path-alias")

    def test_plan_cli_refuses_output_aliases_consumed_inputs(self):
        self.establish_cache()
        aliases = (
            ("scope", self.scope_path),
            ("cache", self.cache),
            ("source", self.project / "src" / "Base.sol"),
        )
        for label, target in aliases:
            with self.subTest(label=label):
                before = target.read_bytes()
                process = subprocess.run(
                    [
                        sys.executable,
                        str(SCRIPT),
                        "plan",
                        "--project-root",
                        str(self.project),
                        "--scope",
                        str(self.scope_path),
                        "--cache",
                        str(self.cache),
                        "--write-plan",
                        str(target),
                    ],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                if target.read_bytes() != before:
                    target.write_bytes(before)
                self.assertEqual(process.returncode, 2, process.stderr)
                refusal = json.loads(process.stderr)
                self.assertEqual(refusal["code"], "path-alias")

    def test_fresh_entry_loader_caps_aggregate_json_bytes(self):
        first = self.root / "first-entry.json"
        second = self.root / "second-entry.json"
        first.write_text("{}\n", encoding="utf-8")
        second.write_text("{}\n", encoding="utf-8")
        with mock.patch.object(
            reuse,
            "MAX_TOTAL_FRESH_JSON_BYTES",
            5,
            create=True,
        ):
            with self.assertRaises(reuse.ReuseError) as caught:
                reuse._load_fresh([str(first), str(second)])
        self.assertEqual(caught.exception.code, "size-limit")

    def test_plan_cli_emits_stable_json_and_writes_the_full_plan(self):
        plan_path = self.root / "plan.json"
        process = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "plan",
                "--project-root",
                str(self.project),
                "--scope",
                str(self.scope_path),
                "--cache",
                str(self.cache),
                "--write-plan",
                str(plan_path),
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(process.returncode, 0, process.stderr)
        result = json.loads(process.stdout)
        self.assertEqual(result["schema"], reuse.RESULT_SCHEMA)
        self.assertEqual((result["operation"], result["mode"]), ("plan", "full"))
        self.assertEqual(json.loads(plan_path.read_text(encoding="utf-8"))["schema"], reuse.PLAN_SCHEMA)

    def test_cli_refusal_is_json_and_does_not_traceback(self):
        self.scope["sources"][0]["path"] = "../Outside.sol"
        self.write_scope()
        process = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "plan",
                "--project-root",
                str(self.project),
                "--scope",
                str(self.scope_path),
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(process.returncode, 2)
        refusal = json.loads(process.stderr)
        self.assertEqual((refusal["status"], refusal["code"]), ("refused", "unsafe-path"))
        self.assertNotIn("Traceback", process.stderr)


if __name__ == "__main__":
    unittest.main()
