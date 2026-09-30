#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Wildcat Labs
"""Exercise declared preparation and hostile inputs and bounded compiler processes."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import preparation as p

FIXTURES = Path(__file__).parent / "fixtures/issue-1366-remaining"


def fixture_request(fixture, name):
    raw = p.encode(fixture["original"])
    remaps = fixture["original"].get("settings", {}).get("remappings", [])
    new_remaps = fixture["prepared_control"].get("settings", {}).get("remappings", [])
    mapped = name == "virtual-path-input.json"
    return {"schema": "lemma-preparation-request/v1",
            "input": {"path": "original.json", "sha256": p.digest(raw)},
            "compiler": {"runtime": {"path": "node", "sha256": "0" * 64},
                         "driver": {"path": "driver.cjs", "sha256": fixture["compiler"]["driver_sha256"]},
                         "artifact": {"path": "soljson.js", "sha256": fixture["compiler"]["artifact_sha256"]},
                         "version": fixture["compiler"]["version"]},
            "target": fixture["target"],
            "transforms": {"metadata_target": name == "metadata-target-input.json",
                           "target_closure": name == "target-closure-input.json",
                           "source_map": fixture["source_map"] if mapped else {},
                           "remappings": [{"original": a, "prepared": b}
                                          for a, b in zip(remaps, new_remaps)] if mapped else []},
            "selection": {"include": ["**"], "exclude": []}}


class JsonComplexityCapacityTests(unittest.TestCase):
    def test_compiler_json_can_exceed_the_ast_visit_budget(self):
        raw = b"[" + b"0," * 1_000_000 + b"0]"
        try:
            decoded = p.decode(raw, p.MAX_OUTPUT)
        except p.Refusal as exc:
            self.fail(f"healthy compiler-shaped JSON exceeded the shared AST budget: {exc}")
        self.assertEqual(len(decoded), 1_000_001)

    def test_json_value_ceiling_is_separate_and_bounded(self):
        self.assertEqual(getattr(p, "MAX_JSON_VALUES", None), 4_000_000)
        self.assertEqual(p.MAX_NODES, 1_000_000)
        with mock.patch.object(p, "MAX_JSON_VALUES", 3, create=True):
            self.assertEqual(p.decode(b"[0,0]"), [0, 0])
            with self.assertRaisesRegex(p.Refusal, "json-complexity"):
                p.decode(b"[0,0,0]")

    def test_json_object_keys_consume_the_value_budget(self):
        with mock.patch.object(p, "MAX_JSON_VALUES", 3, create=True):
            self.assertEqual(p.decode(b'{"a":0}'), {"a": 0})
            with self.assertRaisesRegex(p.Refusal, "json-complexity"):
                p.decode(b'{"a":0,"b":0}')

    def test_depth_byte_and_malformed_input_limits_remain(self):
        self.assertEqual(p.MAX_DEPTH, 128)
        with self.assertRaisesRegex(p.Refusal, "json-complexity"):
            p.decode(b"[" * 129 + b"0" + b"]" * 129)
        with self.assertRaisesRegex(p.Refusal, "json-size"):
            p.decode(b"[0]", 2)
        for raw in (b'{"a":0,"a":1}', b'[NaN]', b'\xff'):
            with self.subTest(raw=raw):
                with self.assertRaises(p.Refusal):
                    p.decode(raw)


class PreparationTests(unittest.TestCase):
    def setUp(self):
        self.name = "target-closure-input.json"
        self.fixture = json.loads((FIXTURES / self.name).read_bytes())
        self.request = fixture_request(self.fixture, self.name)
        self.raw = p.encode(self.fixture["original"])

    def replay(self, query):
        calls = [call for call in self.fixture["calls"] if call["request"] == query]
        self.assertTrue(calls, "unknown compiler transcript request")
        return copy.deepcopy(calls[0]["response"])

    def derive(self, request=None):
        return p.derive(self.raw, self.request if request is None else request, self.replay)

    def test_all_public_preparations_replay(self):
        for name in ("target-closure-input.json", "metadata-target-input.json", "virtual-path-input.json"):
            with self.subTest(name=name):
                self.fixture = json.loads((FIXTURES / name).read_bytes())
                request = fixture_request(self.fixture, name)
                raw = p.encode(self.fixture["original"])
                prepared, manifest = p.derive(raw, request, self.replay)
                self.assertEqual(p.verify_manifest(raw, prepared, manifest), manifest)
                self.assertEqual(json.loads(prepared)["sources"], self.fixture["prepared_control"]["sources"])
                self.assertEqual(raw, p.encode(self.fixture["original"]))

    def test_unknown_fields_and_transforms_refuse(self):
        for path in ((), ("compiler",), ("target",), ("transforms",), ("selection",)):
            with self.subTest(path=path):
                request = copy.deepcopy(self.request)
                target = request
                for key in path:
                    target = target[key]
                target["unknown"] = True
                with self.assertRaises(p.Refusal):
                    self.derive(request)

    def test_input_pin_refuses(self):
        self.request["input"]["sha256"] = "0" * 64
        with self.assertRaisesRegex(p.Refusal, "input-digest"):
            self.derive()

    def test_json_hostile_inputs(self):
        for raw in (b'{"a":1,"a":2}', b'{"a":NaN}', b'{"a":1e999}', b'\xff', b'{',
                    b'{"a":"\\ud800"}', b'[' * 140 + b'0' + b']' * 140):
            with self.subTest(raw=raw[:30]):
                with self.assertRaises(p.Refusal):
                    p.decode(raw)
        with self.assertRaisesRegex(p.Refusal, "json-size"):
            p.decode(b'{}', 1)
        with mock.patch.object(p, "MAX_JSON_VALUES", 2):
            with self.assertRaisesRegex(p.Refusal, "json-complexity"):
                p.decode(b'[1,2]')

    def test_json_keys_and_large_integers_refuse_without_parser_errors(self):
        for raw in (b'{"\\ud800":1}', ('[' + '1' * 5000 + ']').encode()):
            with self.subTest(raw_prefix=raw[:12]):
                try:
                    p.decode(raw)
                except p.Refusal:
                    continue
                except Exception as exc:
                    self.fail("parser escaped refusal boundary: " + type(exc).__name__)
                self.fail("invalid JSON key was admitted")

    def test_target_missing_or_ambiguous_refuses(self):
        self.request["target"] = {"source": "missing.sol", "contract": "Target"}
        with self.assertRaisesRegex(p.Refusal, "target-source-missing"):
            self.derive()
        output = self.replay(self.fixture["calls"][-1]["request"])
        nodes = output["sources"]["Target.sol"]["ast"]["nodes"]
        nodes.append(copy.deepcopy(next(n for n in nodes if n.get("name") == "Target")))
        with self.assertRaisesRegex(p.Refusal, "target-missing-or-ambiguous"):
            p.target_exists(output, "Target.sol", "Target")

    def test_metadata_requires_exact_declared_target(self):
        fixture = json.loads((FIXTURES / "metadata-target-input.json").read_bytes())
        request = fixture_request(fixture, "metadata-target-input.json")
        for value in (None, {}, [], {"Target.sol": "Other"}, {"Target.sol": "Target", "Other.sol": "Other"}):
            raw = copy.deepcopy(fixture["original"])
            raw["settings"]["compilationTarget"] = value
            data = p.encode(raw)
            request["input"]["sha256"] = p.digest(data)
            with self.subTest(value=value), self.assertRaisesRegex(p.Refusal, "metadata-target"):
                p.derive(data, request, self.replay)

    def test_missing_wrong_edges_refuse_and_legal_cycle_terminates(self):
        for mutation in ("missing", "wrong", "cycle"):
            def compiler(query):
                out = self.replay(query)
                for name, entry in out["sources"].items():
                    if "ast" not in entry:
                        continue
                    for node in entry["ast"]["nodes"]:
                        if node["nodeType"] == "ImportDirective":
                            if mutation == "missing":
                                node["absolutePath"] = "missing.sol"
                            elif mutation == "wrong":
                                node["sourceUnit"] += 10
                    if mutation == "cycle" and name == "Base.sol":
                        entry["ast"]["nodes"].append({"nodeType": "ImportDirective", "absolutePath": "Target.sol",
                                                       "sourceUnit": out["sources"]["Target.sol"]["ast"]["id"]})
                return out
            if mutation == "cycle":
                prepared, _ = p.derive(self.raw, self.request, compiler)
                self.assertEqual(set(p.decode(prepared)["sources"]), {"Base.sol", "Target.sol"})
            else:
                with self.subTest(mutation=mutation), self.assertRaises(p.Refusal):
                    p.derive(self.raw, self.request, compiler)

    def test_mapping_and_remapping_hostile_cases(self):
        fixture = json.loads((FIXTURES / "virtual-path-input.json").read_bytes())
        for mutation in ("collision", "missing", "escape", "target", "prefix", "context"):
            request = fixture_request(fixture, "virtual-path-input.json")
            transform = request["transforms"]
            keys = list(transform["source_map"])
            if mutation == "collision":
                transform["source_map"][keys[1]] = transform["source_map"][keys[0]]
            elif mutation == "missing":
                del transform["source_map"][keys[0]]
            elif mutation == "escape":
                transform["source_map"][keys[0]] = "../escape.sol"
            elif mutation == "target":
                transform["remappings"][0]["prepared"] = "@reference/=wrong/"
            elif mutation == "prefix":
                transform["remappings"][0]["prepared"] = "@other/=reference/"
            else:
                transform["remappings"][0]["prepared"] = "context/:@reference/=reference/"
            with self.subTest(mutation=mutation), self.assertRaises(p.Refusal):
                p.derive(p.encode(fixture["original"]), request, self.replay)

    def test_manifest_changes_and_extra_transcripts_refuse(self):
        prepared, manifest = self.derive()
        mutations = ("reverse", "source", "selection", "extra", "digest", "output")
        for mutation in mutations:
            changed = copy.deepcopy(manifest)
            if mutation == "reverse":
                changed["reverse_map"]["Target.sol"] = "Other.sol"
            elif mutation == "source":
                changed["sources"][0]["sha256"] = "0" * 64
            elif mutation == "selection":
                changed["selected"] = []
            elif mutation == "extra":
                changed["transcripts"].append(changed["transcripts"][-1])
            elif mutation == "digest":
                changed["transcripts"][0]["input_sha256"] = "0" * 64
            else:
                changed["transcripts"][0]["output"]["sources"] = {}
            with self.subTest(mutation=mutation), self.assertRaises(p.Refusal):
                p.verify_manifest(self.raw, prepared, changed)
        with self.assertRaises(p.Refusal):
            p.verify_manifest(self.raw, prepared + b' ', manifest)

    def test_selection_must_match_and_keep_target(self):
        for selection in ({"include": ["absent/**"], "exclude": []},
                          {"include": ["**"], "exclude": ["absent/**"]},
                          {"include": ["**"], "exclude": ["Target.sol"]}):
            self.request["selection"] = selection
            with self.subTest(selection=selection), self.assertRaises(p.Refusal):
                self.derive()

    def test_regular_reads_reject_links_directories_and_escape(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            (root / "file").write_bytes(b'abc')
            (root / "link").symlink_to(root / "file")
            (root / "dir").mkdir()
            (root / "dir-link").symlink_to(root / "dir", target_is_directory=True)
            (root / "dir/file").write_bytes(b'abc')
            for path in (root / "link", root / "dir", root / "dir-link/file", root / "../file"):
                with self.subTest(path=path), self.assertRaises(p.Refusal):
                    p.read_regular(path)
            with self.assertRaises(p.Refusal):
                p.read_pin({"path": "../file", "sha256": "0" * 64}, root)
            with self.assertRaises(p.Refusal):
                p.read_pin({"path": "file", "sha256": "0" * 64}, root)
            with self.assertRaises(p.Refusal):
                p.read_regular(root / "file", 2)

    def test_existing_output_survives_and_interruption_has_no_manifest(self):
        prepared, manifest = self.derive()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            existing = root / "existing"
            existing.mkdir()
            (existing / "keep").write_bytes(b'unchanged')
            with self.assertRaises(p.Refusal):
                p.publish(existing, prepared, manifest)
            self.assertEqual((existing / "keep").read_bytes(), b'unchanged')
            real = p.os.open
            def interrupt(path, *args, **kwargs):
                if path == "manifest.json":
                    raise OSError("interrupted")
                return real(path, *args, **kwargs)
            with mock.patch.object(p.os, "open", side_effect=interrupt), self.assertRaises(p.Refusal):
                p.publish(root / "partial", prepared, manifest)
            self.assertEqual((root / "partial/prepared.json").read_bytes(), prepared)
            self.assertFalse((root / "partial/manifest.json").exists())



class EvidenceTests(unittest.TestCase):
    def setUp(self):
        import contextlib
        import io
        import subprocess
        import corpus_evidence as ce
        self.ce = ce
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        fixture = json.loads((FIXTURES / "metadata-target-input.json").read_bytes())
        request = fixture_request(fixture, "metadata-target-input.json")
        original = p.encode(fixture["original"])
        request["input"] = self.write("original.json", original)
        for key in ("runtime", "driver", "artifact"):
            request["compiler"][key] = self.write(key, b"public fixture compiler component")
        def compile_input(query):
            return copy.deepcopy(next(c["response"] for c in fixture["calls"] if c["request"] == query))
        prepared, manifest = p.derive(original, request, compile_input)
        prepared_pin = self.write("prepared.json", prepared)
        manifest_pin = self.write("manifest.json", p.encode(manifest))
        builds = []
        sol = ce.solidity_module()
        for number in (1, 2):
            out = self.root / str(number)
            out.mkdir()
            argv = ["solidity.py", "--input", str(self.root / "prepared.json"),
                    "--solc", "fixture", "--expect-solc", request["compiler"]["version"],
                    "--include", "Target.sol", "--source-ref", "captured:" + p.digest(original),
                    "--out", str(out / "chunks.jsonl")]
            def compiler(command, **kwargs):
                if command[-1] == "--version":
                    return subprocess.CompletedProcess(command, 0, "Version: " + request["compiler"]["version"], "")
                return subprocess.CompletedProcess(command, 0, json.dumps(compile_input(json.loads(kwargs["input"]))), "")
            with (mock.patch.object(sys, "argv", argv), mock.patch.object(sol.subprocess, "run", side_effect=compiler),
                  contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO())):
                self.assertEqual(sol.main(), 0)
            builds.append({"chunks": self.local(out / "chunks.jsonl"), "provenance": self.local(out / "provenance.jsonl")})
        census = ce.event_census(p.decode(prepared), manifest["transcripts"][-1]["output"], ["Target.sol"])
        self.partition = {"id": "sample", "input_id": "family/set-001", "prepared": prepared_pin,
                          "manifest": manifest_pin, "builds": builds, "census": self.write("census.json", p.encode(census))}
        address = "0x" + "1" * 40
        source = {"source_sets": [{"id": "set-001", "compiler": request["compiler"]["version"],
                                  "build_input": {"sha256": p.digest(original), "bytes": len(original)},
                                  "reproduction": {"members": [address]}}]}
        obs = {"code": [{"address": address}]}
        records = []
        full = {}
        for kind, document in (("source_match", source), ("observations", obs)):
            raw = p.encode(document)
            local = self.write(kind + ".json", raw)
            full[kind] = {"commit": "1" * 40, "path": "family/" + kind + ".json",
                          "sha256": local["sha256"], "bytes": len(raw)}
            records.append({"commit": "1" * 40, "path": full[kind]["path"], "local": local})
        registry = {"targets": [{"id": "aave-v3", "status": "resolved", "full_records": full,
                                  "deployment": {"full_subject_set": {"count": 1,
                                     "sha256": p.digest((address + "\n").encode())}}}]}
        self.bundle = {"schema": "lemma-corpus-evidence/v1", "registry": self.write("registry.json", p.encode(registry)),
                       "records": records, "inputs": [{"id": "family/set-001", "local": request["input"]}],
                       "rows": [{"id": "aave-v3", "disposition": "complete", "partitions": ["sample"]}],
                       "partitions": [self.partition], "aggregate": {"registry_rows": 1, "required_inputs": 1,
                       "verified_inputs": 1, "partitions": 1, "events": 1,
                       "chunks": len((self.root / "1/chunks.jsonl").read_bytes().splitlines())}}

    def local(self, path):
        return {"path": str(path.relative_to(self.root)), "sha256": p.digest(path.read_bytes())}

    def write(self, name, raw):
        path = self.root / name
        path.write_bytes(raw)
        return self.local(path)

    def test_complete_join_recomputes(self):
        result = self.ce.verify_bundle(self.bundle, self.root, complete=True, full=True)
        self.assertEqual(result["aggregate"], self.bundle["aggregate"])
        self.assertEqual(result["custody"]["missing"], [])

    def test_missing_duplicate_extra_rows_and_partitions_refuse(self):
        for field in ("records", "inputs", "rows", "partitions"):
            for mutation in ("missing", "duplicate", "extra"):
                bundle = copy.deepcopy(self.bundle)
                if mutation == "missing":
                    bundle[field] = []
                elif mutation == "duplicate":
                    bundle[field].append(copy.deepcopy(bundle[field][0]))
                else:
                    row = copy.deepcopy(bundle[field][0])
                    if field == "records":
                        row["path"] = "unknown.json"
                    else:
                        row["id"] = "unknown"
                    bundle[field].append(row)
                with self.subTest(field=field, mutation=mutation), self.assertRaises(p.Refusal):
                    self.ce.verify_bundle(bundle, self.root, complete=True, full=True)

    def test_altered_artifact_bytes_and_forged_counts_refuse(self):
        for category in ("manifest", "prepared", "census", "corpus", "provenance", "compiler"):
            if category in ("manifest", "prepared", "census"):
                pin = self.partition[category]
            elif category == "compiler":
                pin = {"path": "driver"}
            else:
                pin = self.partition["builds"][0]["chunks" if category == "corpus" else "provenance"]
            path = self.root / pin["path"]
            original = path.read_bytes()
            path.write_bytes(original + b' ')
            try:
                with self.subTest(category=category), self.assertRaises(p.Refusal):
                    self.ce.verify_bundle(self.bundle, self.root, complete=True, full=True)
            finally:
                path.write_bytes(original)
        bundle = copy.deepcopy(self.bundle)
        bundle["aggregate"]["events"] += 1
        with self.assertRaisesRegex(p.Refusal, "aggregate-mismatch"):
            self.ce.verify_bundle(bundle, self.root, complete=True, full=True)

    def test_missing_custody_does_not_become_zero(self):
        expected = {"family/set-001": {"input": {"sha256": "0" * 64, "bytes": 12}}}
        state = self.ce.custody(expected, [{"id": "family/set-001", "local": None}], self.root)
        self.assertEqual(state["required"], 1)
        self.assertEqual(state["verified"], 0)
        self.assertEqual(state["missing"][0]["bytes"], 12)
        bundle = copy.deepcopy(self.bundle)
        bundle["inputs"][0]["local"] = None
        with self.assertRaisesRegex(p.Refusal, "custody-incomplete"):
            self.ce.verify_bundle(bundle, self.root, complete=True)

    def test_changed_reverse_map_with_rebound_manifest_pin_refuses(self):
        path = self.root / "manifest.json"
        manifest = p.decode(path.read_bytes(), p.MAX_ARTIFACT)
        manifest["reverse_map"]["Target.sol"] = "Forged.sol"
        self.partition["manifest"] = self.write("manifest.json", p.encode(manifest))
        with self.assertRaisesRegex(p.Refusal, "manifest-mismatch"):
            self.ce.verify_bundle(self.bundle, self.root)

    def test_rebound_event_signature_and_metadata_refuse(self):
        sol = self.ce.solidity_module()
        original = [json.loads(line) for line in (self.root / "1/chunks.jsonl").read_bytes().splitlines()]
        for field in ("signature", "line", "model_text", "embed_text", "breadcrumb", "exposed_by"):
            chunks = copy.deepcopy(original)
            event = next(chunk for chunk in chunks if chunk["kind"] == "Event")
            if field == "signature":
                event["detail"]["signature"] = "Changed(address)"
                event["id"] = event["id"].replace("Changed(uint256)", "Changed(address)")
            elif field == "line":
                event["line"] += 1
            elif field == "exposed_by":
                event["detail"][field] = ["Other"]
            else:
                event[field] = "different event metadata"
            build_id = sol.corpus_build_id(chunks)
            for chunk in chunks:
                chunk["corpus_build_id"] = build_id
            for build in self.partition["builds"]:
                path = self.root / build["chunks"]["path"]
                path.write_bytes(b"".join(p.encode(chunk) for chunk in chunks))
                build["chunks"] = self.local(path)
                path = self.root / build["provenance"]["path"]
                provenance = json.loads(path.read_bytes())
                provenance["corpus_build_id"] = build_id
                path.write_bytes(p.encode(provenance))
                build["provenance"] = self.local(path)
            with self.subTest(field=field):
                self.assertEqual(sol._schema.validate([sol._schema.Chunk(**c) for c in chunks]), [])
                with self.assertRaisesRegex(p.Refusal, "corpus-chunk-(set|mismatch)"):
                    self.ce.verify_bundle(self.bundle, self.root, complete=True, full=True)

    def test_rebound_non_event_omission_refuses(self):
        sol = self.ce.solidity_module()
        chunks = [json.loads(line) for line in (self.root / "1/chunks.jsonl").read_bytes().splitlines()]
        self.assertEqual(len(chunks), 2)
        chunks = [chunk for chunk in chunks if chunk["kind"] == "Event"]
        build_id = sol.corpus_build_id(chunks)
        for chunk in chunks:
            chunk["corpus_build_id"] = build_id
        for build in self.partition["builds"]:
            path = self.root / build["chunks"]["path"]
            path.write_bytes(b"".join(p.encode(chunk) for chunk in chunks))
            build["chunks"] = self.local(path)
            path = self.root / build["provenance"]["path"]
            provenance = json.loads(path.read_bytes())
            provenance["corpus_build_id"], provenance["chunk_count"] = build_id, len(chunks)
            path.write_bytes(p.encode(provenance))
            build["provenance"] = self.local(path)
        self.bundle["aggregate"]["chunks"] = len(chunks)
        with self.assertRaisesRegex(p.Refusal, "corpus-chunk-set"):
            self.ce.verify_bundle(self.bundle, self.root, complete=True, full=True)


class CompilerBoundaryTests(unittest.TestCase):
    def test_group_signal_precedes_reap_and_refuses_lost_child_ownership(self):
        # Intercept every group signal; these children have no descendants.
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            script = root / "child.py"
            script.write_text("print('ok')\n")
            runner = object.__new__(p.PinnedCompiler)
            runner.argv, runner.root = [sys.executable, str(script)], root
            runner.compiler = {key: {"path": key, "sha256": "0" * 64}
                               for key in ("runtime", "driver", "artifact")}
            for stolen, cleanup in ((False, False), (False, True), (True, False)):
                script.write_text("import time; time.sleep(0.15)\n" if cleanup else "print('ok')\n")
                events, children = [], []
                real_popen, real_waitid = p.subprocess.Popen, p.os.waitid
                def launch(*args, **kwargs):
                    child = real_popen(*args, **kwargs)
                    children.append(child)
                    real_wait = child.wait
                    def wait(*args, **kwargs):
                        result = real_wait(*args, **kwargs)
                        events.append("reap")
                        return result
                    child.wait = wait
                    return child
                def observe(*args):
                    if stolen:
                        children[0].wait()
                        raise ChildProcessError("child already reaped")
                    self.assertTrue(args[2] & p.os.WNOWAIT)
                    return real_waitid(*args)
                with (self.subTest(stolen=stolen, cleanup=cleanup),
                      mock.patch.object(p, "DEADLINE", 0.05 if cleanup else 5),
                      mock.patch.object(p.subprocess, "Popen", side_effect=launch),
                      mock.patch.object(p.os, "waitid", side_effect=observe),
                      mock.patch.object(p.os, "killpg", side_effect=lambda *_: events.append("signal")),
                      mock.patch.object(p, "read_pin", return_value=b"")):
                    if stolen:
                        with self.assertRaisesRegex(p.Refusal, "compiler-child-ownership"):
                            runner.run(b"", "--standard-json")
                        self.assertNotIn("signal", events)
                    elif cleanup:
                        with self.assertRaisesRegex(p.Refusal, "compiler-timeout"):
                            runner.run(b"", "--standard-json")
                        self.assertEqual(events, ["signal", "reap"])
                    else:
                        self.assertEqual(runner.run(b"", "--standard-json"), b"ok\n")
                        self.assertEqual(events, ["reap"])

    def test_each_compiler_component_pin_is_checked_before_execution(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            compiler = {"version": "0.8.25+commit.b61c2a91"}
            for field in ("runtime", "driver", "artifact"):
                (root / field).write_bytes(b"fixture")
                compiler[field] = {"path": field, "sha256": p.digest(b"fixture")}
            for field in ("runtime", "driver", "artifact"):
                changed = copy.deepcopy(compiler)
                changed[field]["sha256"] = "0" * 64
                with self.subTest(field=field), mock.patch.object(p.PinnedCompiler, "run") as run:
                    with self.assertRaisesRegex(p.Refusal, "pin-mismatch"):
                        p.PinnedCompiler(changed, root)
                    run.assert_not_called()
            with mock.patch.object(p.PinnedCompiler, "run", return_value=b"Version: 0.8.24+commit.e11b9ed9"):
                with self.assertRaisesRegex(p.Refusal, "compiler-version-mismatch"):
                    p.PinnedCompiler(compiler, root)

    def test_source_limit_and_unknown_content_refuse(self):
        document = {"language": "Solidity", "sources": {"A.sol": {"content": ""},
                    "B.sol": {"content": ""}}, "settings": {}}
        with mock.patch.object(p, "MAX_SOURCES", 1), self.assertRaisesRegex(p.Refusal, "source-count"):
            p.source_document(p.encode(document))
        document["sources"]["A.sol"] = {"urls": ["https://example.invalid/source"]}
        with self.assertRaisesRegex(p.Refusal, "source-fields"):
            p.source_document(p.encode(document))

    def test_wrong_request_types_and_compiler_shapes_refuse(self):
        fixture = json.loads((FIXTURES / "metadata-target-input.json").read_bytes())
        for field, value in (("target", None), ("compiler", []), ("transforms", "bad"),
                             ("selection", {"include": [[]], "exclude": []})):
            request = fixture_request(fixture, "metadata-target-input.json")
            request[field] = value
            with self.subTest(field=field), self.assertRaises(p.Refusal):
                p.derive(p.encode(fixture["original"]), request, lambda _: {})
        request = fixture_request(fixture, "metadata-target-input.json")
        for output in (None, [], {"sources": {"Target.sol": []}}, {"errors": [None]}):
            with self.subTest(output=output), self.assertRaises(p.Refusal):
                p.derive(p.encode(fixture["original"]), request, lambda _: output)

    def test_process_output_deadline_exit_and_environment_boundaries(self):
        # Real child processes exercise the runner's pipe and process cleanup.
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            script = root / "child.py"
            runner = object.__new__(p.PinnedCompiler)
            runner.argv = [sys.executable, str(script)]
            runner.compiler = {key: {"path": key, "sha256": "0" * 64}
                               for key in ("runtime", "driver", "artifact")}
            runner.root = root
            for program, category, limit, deadline in (
                ("import os; os.write(1, b'x' * 8192)", "compiler-output-size", 1024, 5),
                ("import os; os.write(2, b'x' * 8192)", "compiler-output-size", 1024, 5),
                ("import time; time.sleep(10)", "compiler-timeout", 8192, 0.1),
                ("raise SystemExit(7)", "compiler-process", 8192, 5),
            ):
                with self.subTest(category=category, program=program):
                    script.write_text(program)
                    children = []
                    real_popen = p.subprocess.Popen
                    def launch(*args, **kwargs):
                        child = real_popen(*args, **kwargs)
                        children.append(child)
                        return child
                    with mock.patch.object(p, "MAX_OUTPUT", limit), mock.patch.object(p, "DEADLINE", deadline), mock.patch.object(p.subprocess, "Popen", side_effect=launch):
                        with self.assertRaisesRegex(p.Refusal, category):
                            runner.run(b"", "--standard-json")
                    self.assertEqual(len(children), 1)
                    self.assertIsNotNone(children[0].poll())
            script.write_text("import os; print(os.environ.get('LEMMA_TEST_SECRET', 'absent'))")
            with mock.patch.dict(p.os.environ, {"LEMMA_TEST_SECRET": "private"}), mock.patch.object(p, "read_pin", return_value=b"") as pins:
                self.assertEqual(runner.run(b"", "--standard-json"), b"absent\n")
                self.assertEqual(pins.call_count, 3)
            with mock.patch.object(p, "read_pin", side_effect=p.Refusal("pin-mismatch")):
                with self.assertRaisesRegex(p.Refusal, "pin-mismatch"):
                    runner.run(b"", "--standard-json")

    def test_timeout_kills_descendant_after_parent_exits(self):
        # The parent has exited before timeout; its child still owns both pipes.
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            script, marker = root / "child.py", root / "survived"
            script.write_text("import os,time\nif os.fork(): os._exit(0)\n"
                              "time.sleep(0.8)\nopen(" + repr(str(marker)) +
                              ", 'w').write('survived')\nos._exit(0)\n")
            runner = object.__new__(p.PinnedCompiler)
            runner.argv = [sys.executable, str(script)]
            runner.compiler, runner.root = {}, root
            children = []
            real_popen = p.subprocess.Popen
            def launch(*args, **kwargs):
                child = real_popen(*args, **kwargs)
                children.append(child)
                return child
            with mock.patch.object(p, "DEADLINE", 0.4), mock.patch.object(p.subprocess, "Popen", side_effect=launch):
                with self.assertRaisesRegex(p.Refusal, "compiler-timeout"):
                    runner.run(b"", "--standard-json")
            self.assertEqual(children[0].returncode, 0, "parent must exit before timeout")
            p.time.sleep(1.0)
            self.assertFalse(marker.exists(), "compiler descendant survived the timeout")

    def test_aggregate_transcript_limit_refuses(self):
        fixture = json.loads((FIXTURES / "metadata-target-input.json").read_bytes())
        request = fixture_request(fixture, "metadata-target-input.json")
        output = next(c["response"] for c in fixture["calls"] if c["label"] == "prepared-ast")
        with mock.patch.object(p, "MAX_ARTIFACT", 1), self.assertRaisesRegex(p.Refusal, "transcript-total-size"):
            p.derive(p.encode(fixture["original"]), request, lambda _: output)


class CompilerCleanupTests(unittest.TestCase):
    def cleanup_case(self, terminal, probe):
        # Model the native overflow/exit race with an unreaped child identity.
        events = []
        child = mock.Mock(pid=12345, returncode=None)
        child.stdout, child.stderr = mock.Mock(), mock.Mock()
        child.stdout.fileno.return_value = 10
        child.stderr.fileno.return_value = 11
        def reap():
            events.append(("reap",))
            child.returncode = 0
            return 0
        child.wait.side_effect = reap
        def signal_group(pid, sig):
            events.append(("signal", sig, child.returncode))
            if sig:
                raise PermissionError(1, "fixture zombie-only group")
            if probe == "absent":
                raise ProcessLookupError(3, "fixture absent group")
            if probe == "unknown":
                raise PermissionError(1, "fixture unknown group")
        selector = mock.MagicMock()
        selector.__enter__.return_value = selector
        selector.get_map.return_value = {10: child.stdout}
        selector.select.return_value = [(mock.Mock(fd=10, fileobj=child.stdout), 1)]
        runner = object.__new__(p.PinnedCompiler)
        runner.argv, runner.compiler, runner.root = [], {}, Path(".")
        with mock.patch.object(p.subprocess, "Popen", return_value=child), \
             mock.patch.object(p.selectors, "DefaultSelector", return_value=selector), \
             mock.patch.object(p.os, "set_blocking"), \
             mock.patch.object(p.os, "read", return_value=b"oversized"), \
             mock.patch.object(p.os, "waitid", return_value=terminal), \
             mock.patch.object(p.os, "killpg", side_effect=signal_group), \
             mock.patch.object(p, "MAX_OUTPUT", 1):
            try:
                runner.run(b"", "--standard-json")
            except Exception as exc:
                result = exc
            else:
                result = None
        self.assertTrue(child.stdout.close.called and child.stderr.close.called)
        self.assertFalse(any(row[0] == "signal" and row[1] != 0 and row[2] is not None
                             for row in events), "delivering signal after reap")
        return result, events

    def test_zombie_only_group_restores_original_overflow_refusal(self):
        result, events = self.cleanup_case(mock.Mock(si_status=0), "absent")
        self.assertIsInstance(result, p.Refusal)
        self.assertEqual(str(result), "compiler-output-size")
        self.assertIn(("signal", 0, 0), events)

    def test_live_leader_permission_error_does_not_reap_or_probe(self):
        result, events = self.cleanup_case(None, "absent")
        self.assertIsInstance(result, PermissionError)
        self.assertEqual(events, [("signal", p.signal.SIGKILL, None)])

    def test_retained_live_group_permission_error_still_refuses(self):
        result, events = self.cleanup_case(mock.Mock(si_status=0), "live")
        self.assertIsInstance(result, PermissionError)
        self.assertIn(("signal", 0, 0), events)

    def test_unknown_group_permission_error_still_refuses(self):
        result, events = self.cleanup_case(mock.Mock(si_status=0), "unknown")
        self.assertIsInstance(result, PermissionError)
        self.assertIn(("signal", 0, 0), events)


if __name__ == "__main__":
    unittest.main()
