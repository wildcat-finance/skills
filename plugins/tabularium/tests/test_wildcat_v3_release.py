"""Exercise raw-byte custody and complete offline Wildcat reconstruction."""

from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
import io
import json
import os
from pathlib import Path
import shutil
import tempfile
from unittest import mock

if __package__:
    from . import support
    from .wildcat_v3_fixtures import constructed_inputs, word, log, MARKET, ACCOUNT, ASSET
else:
    import support
    from wildcat_v3_fixtures import constructed_inputs, word, log, MARKET, ACCOUNT, ASSET
import tabularium
from tabularium_lib.core import TabulariumError, canonical_json, loads_json, sha256_bytes
from tabularium_lib import verifier
from tabularium_lib.wildcat_release import build_wildcat_canonical, _physical_inventory
from tabularium_lib.wildcat_source import (
    CONSTRUCTION_FORMAT, CONSTRUCTION_GAP, _api, constructor_parameters, load_raw,
)


def constructed_release(base, venue="wildcat-v2", mutate=None):
    """Ingest labelled fixtures through the real Alexandria raw-release API."""
    contexts, records = constructed_inputs(venue, routing=True)
    document = {
        "schema": CONSTRUCTION_FORMAT, "venue": venue,
        "contexts": [{"address": address, **{key: context[key] for key in
                     ("role", "asset", "market", "abi_variant", "concrete_contract")}}
                    for address, context in sorted(contexts.items())],
        "limitations": [CONSTRUCTION_GAP],
    }
    request = {"jsonrpc": "2.0", "id": 1, "method": "eth_getLogs",
               "params": [{"address": sorted(contexts), "fromBlock": "0x64", "toBlock": "0x64"}]}
    response = {"jsonrpc": "2.0", "id": 1, "result": [raw for raw, _ in records]}
    journal = {"records": [{"request": canonical_json(request).decode(),
                            "response": canonical_json(response).decode()}]}
    scope = {"kind": "subject-scoped", "deployment": venue + "-constructed-specimen",
             "subjects": ["eip155:1:" + address for address in sorted(contexts)],
             "finality": "unknown", "interval": {"kind": "block-range", "start": "100", "end": "100"}}
    plan = {
        "format": "alexandria-capture-plan/v1",
        "release": {"name": venue + "-constructed-native", "created_at": "2026-10-04T00:00:00Z"},
        "components": [],
        "captures": [],
    }
    for name, collection, count in (("wildcat-construction", "contexts", len(contexts)), ("native-logs", "records", 1)):
        plan["components"].append({"name": name, "path": name + ".json", "media_type": "application/json",
                                   "role": "fixture", "access": "public", "redistribution": "permitted"})
        plan["captures"].append({
            "id": name, "component": name, "venue": venue, "chain": "eip155:1",
            "evidence_class": "recorded-rpc",
            "source": {"kind": "constructed-fixture", "locator_class": "local-fixture",
                       "reference": venue + "-constructed-specimen"},
            "scope": deepcopy(scope),
            "coverage": {"status": "partial", "record_count": count,
                         "collections": [{"name": collection, "selector": "/" + collection, "record_count": count}],
                         "unsupported_collections": [], "gaps": [CONSTRUCTION_GAP]},
        })
    if mutate is not None:
        mutate(document, journal, plan)
    plan["captures"][0]["coverage"]["record_count"] = len(document["contexts"])
    plan["captures"][0]["coverage"]["collections"][0]["record_count"] = len(document["contexts"])
    source = base / "fixture-source"
    source.mkdir()
    (source / "wildcat-construction.json").write_bytes(canonical_json(document))
    (source / "native-logs.json").write_bytes(canonical_json(journal))
    (source / "plan.json").write_bytes(canonical_json(plan))
    root = base / "raw"
    _api()[1].ingest(source / "plan.json", root)
    return root


class ReleaseBoundaryCases:
    """Mixin so the registered semantic resolver executes the complete boundary."""

    def test_complete_raw_copy_and_offline_rebuild(self):
        for venue, expected in (("wildcat-v1", 7), ("wildcat-v2", 10)):
            with self.subTest(venue=venue), tempfile.TemporaryDirectory() as temporary:
                base = Path(temporary).resolve()
                raw = constructed_release(base, venue)
                before = _physical_inventory(raw)
                target = base / "canonical"
                report = build_wildcat_canonical(raw, target, "constructed-" + venue)
                self.assertEqual(report.rows, expected)
                self.assertEqual(_physical_inventory(target / "source/raw-release"), before)
                shutil.rmtree(raw)
                self.assertEqual(verifier.verify(target / "coverage.json").rows, expected)
                descriptor = loads_json((target / "source.json").read_bytes())
                self.assertEqual(descriptor["scope"]["kind"], "constructed-fixture")
                self.assertEqual(descriptor["scope"]["limitations"], [CONSTRUCTION_GAP])
                self.assertEqual(len(descriptor["dispositions"]), expected + 1)

    def test_fresh_output_and_alias_guards(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            raw = constructed_release(base)
            for target in (raw, raw / "nested", base):
                with self.subTest(target=target), self.assertRaises(TabulariumError):
                    build_wildcat_canonical(raw, target, "constructed")
            alias = base / "alias"
            alias.symlink_to(raw, target_is_directory=True)
            with self.assertRaises(TabulariumError):
                build_wildcat_canonical(alias, base / "canonical", "constructed")
            self.assertFalse((base / "canonical").exists())

    def test_raw_regular_file_and_hardlink_guards(self):
        for kind in ("symlink", "hardlink", "fifo"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as temporary:
                base = Path(temporary).resolve()
                raw = constructed_release(base)
                extra = raw / "extra"
                if kind == "symlink":
                    extra.symlink_to("manifest.json")
                elif kind == "hardlink":
                    os.link(raw / "manifest.json", extra)
                else:
                    os.mkfifo(extra)
                with self.assertRaises(TabulariumError):
                    build_wildcat_canonical(raw, base / "canonical", "constructed")
                self.assertFalse((base / "canonical").exists())

    def test_raw_manifest_and_journal_mutations_refuse(self):
        def replace_result(journal, change):
            value = json.loads(journal["records"][0]["response"])
            change(value)
            journal["records"][0]["response"] = json.dumps(value)
        mutations = (
            lambda doc, journal, plan: doc.update(limitations=[]),
            lambda doc, journal, plan: doc["contexts"][0].update(role="wrapper"),
            lambda doc, journal, plan: doc["contexts"][0].update(abi_variant="undeclared"),
            lambda doc, journal, plan: doc["contexts"].append(deepcopy(doc["contexts"][0])),
            lambda doc, journal, plan: journal["records"][0].update(request={}),
            lambda doc, journal, plan: replace_result(journal, lambda value: value.update(id=2)),
            lambda doc, journal, plan: replace_result(journal, lambda value: value["result"].append(deepcopy(value["result"][0]))),
            lambda doc, journal, plan: replace_result(journal, lambda value: value["result"][0].update(blockNumber="0x65")),
            lambda doc, journal, plan: plan["captures"][0]["scope"]["interval"].update(end="101"),
            lambda doc, journal, plan: plan["captures"][0].update(evidence_class="archive-log"),
        )
        for index, mutation in enumerate(mutations):
            with self.subTest(index=index), tempfile.TemporaryDirectory() as temporary:
                base = Path(temporary).resolve()
                raw = constructed_release(base, mutate=mutation)
                with self.assertRaises(TabulariumError):
                    build_wildcat_canonical(raw, base / "canonical", "constructed")
                self.assertFalse((base / "canonical").exists())

    def test_raw_byte_damage_refuses_before_mapping(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            raw = constructed_release(base)
            admitted = load_raw(raw)
            component = admitted["manifest"]["components"][0]
            path = raw / component["object_path"]
            path.write_bytes(path.read_bytes() + b" ")
            with self.assertRaises(TabulariumError):
                build_wildcat_canonical(raw, base / "canonical", "constructed")

    def test_complete_semantic_rebuild_refuses_rehashed_tampering(self):
        # A digest-consistent descriptor/ledger mutation still lacks raw support.
        for name in ("source.json", "capture.json", "events.jsonl", "coverage.json"):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                base = Path(temporary).resolve()
                raw = constructed_release(base)
                target = base / "canonical"
                build_wildcat_canonical(raw, target, "constructed")
                path = target / name
                if name == "events.jsonl":
                    rows = [json.loads(line) for line in path.read_text().splitlines()]
                    rows[0]["parties"][0]["address"] = "0x" + "99" * 20
                    data = b"".join(canonical_json(row) + b"\n" for row in rows)
                else:
                    value = json.loads(path.read_bytes())
                    if name == "source.json":
                        value["contexts"][MARKET]["asset"] = MARKET
                    elif name == "capture.json":
                        value["scope"]["limitations"] = []
                    else:
                        value["coverage"]["included_events"] = {}
                    data = canonical_json(value) + b"\n"
                path.write_bytes(data)
                coverage_path = target / "coverage.json"
                coverage = json.loads(coverage_path.read_bytes())
                claim = {"source.json": "source", "capture.json": "capture_manifest", "events.jsonl": "canonical"}.get(name)
                if claim:
                    coverage[claim].update(sha256=sha256_bytes(data), bytes=len(data))
                    coverage_path.write_bytes(canonical_json(coverage) + b"\n")
                with self.assertRaises(TabulariumError):
                    verifier.verify(coverage_path)

    def test_release_tree_is_closed_including_empty_directories(self):
        for directory in (False, True):
            with self.subTest(directory=directory), tempfile.TemporaryDirectory() as temporary:
                base = Path(temporary).resolve()
                raw = constructed_release(base)
                target = base / "canonical"
                build_wildcat_canonical(raw, target, "constructed")
                extra = target / "extra"
                if directory:
                    extra.mkdir()
                else:
                    extra.write_text("undeclared")
                with self.assertRaises(TabulariumError):
                    verifier.verify(target / "coverage.json")

    def test_atomic_failure_leaves_no_release_or_staging_tree(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            raw = constructed_release(base)
            with mock.patch("tabularium_lib.wildcat_release.verify_wildcat_canonical", side_effect=TabulariumError("injected refusal")):
                with self.assertRaises(TabulariumError):
                    build_wildcat_canonical(raw, base / "canonical", "constructed")
            self.assertFalse((base / "canonical").exists())
            self.assertFalse(list(base.glob(".wildcat-stage-*")))

    def test_no_replace_race_preserves_occupied_output(self):
        from tabularium_lib import wildcat_release
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            raw = constructed_release(base)
            target = base / "canonical"
            original = wildcat_release._atomic_publish
            def occupied(parent_fd, stage_name, target_name):
                target.mkdir()
                (target / "owner").write_text("preexisting")
                return original(parent_fd, stage_name, target_name)
            with mock.patch.object(wildcat_release, "_atomic_publish", side_effect=occupied):
                with self.assertRaises(TabulariumError):
                    build_wildcat_canonical(raw, target, "constructed")
            self.assertEqual((target / "owner").read_text(), "preexisting")
            self.assertFalse(list(base.glob(".wildcat-stage-*")))

    def test_parent_replacement_refuses_and_preserves_foreign_stage(self):
        from tabularium_lib import wildcat_release
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            raw = constructed_release(base)
            parent = base / "output-parent"
            parent.mkdir()
            moved = base / "moved-parent"
            original = wildcat_release._outputs
            def replace(*args):
                if not moved.exists():
                    stage_name = next(parent.glob(".wildcat-stage-*")).name
                    parent.rename(moved)
                    parent.mkdir()
                    foreign = parent / stage_name
                    foreign.mkdir()
                    (foreign / "owner").write_text("foreign")
                return original(*args)
            with mock.patch.object(wildcat_release, "_outputs", side_effect=replace):
                with self.assertRaises(TabulariumError):
                    build_wildcat_canonical(raw, parent / "canonical", "constructed")
            self.assertEqual(next(parent.glob(".wildcat-stage-*/owner")).read_text(), "foreign")
            self.assertFalse((parent / "canonical").exists())
            self.assertFalse(list(moved.glob(".wildcat-stage-*")))

    def test_empty_primary_set_retains_unsupported_disposition(self):
        def unsupported(doc, journal, plan):
            response = json.loads(journal["records"][0]["response"])
            response["result"] = [log("Unrecognized(uint256)", data=(4,))]
            journal["records"][0]["response"] = json.dumps(response)
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            raw = constructed_release(base, mutate=unsupported)
            target = base / "canonical"
            report = build_wildcat_canonical(raw, target, "constructed")
            self.assertEqual(report.rows, 0)
            self.assertEqual((target / "events.jsonl").read_bytes(), b"")
            self.assertEqual(verifier.verify(target / "coverage.json").rows, 0)
            source = loads_json((target / "source.json").read_bytes())
            self.assertEqual(source["dispositions"][0]["disposition"], "unsupported-decode")

    def test_cli_build_and_verify_emit_bounded_success(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            raw = constructed_release(base)
            target = base / "canonical"
            output = io.StringIO()
            with redirect_stdout(output):
                status = tabularium.main(["wildcat-canonical", "--alexandria-release", str(raw),
                                          "--release", "constructed-cli", "--out", str(target)])
            self.assertEqual(status, 0)
            self.assertEqual(json.loads(output.getvalue())["rows"], 10)
            output = io.StringIO()
            with redirect_stdout(output):
                self.assertEqual(tabularium.main(["verify", str(target / "coverage.json")]), 0)
            self.assertIn("constructed-cli", output.getvalue())
            error = io.StringIO()
            with redirect_stderr(error):
                self.assertEqual(tabularium.main(["wildcat-canonical", "--alexandria-release", str(raw),
                                                 "--release", "constructed-cli", "--out", str(target)]), 1)
            self.assertEqual(json.loads(error.getvalue())["event"], "wildcat-canonical-refused")

    def test_constructor_widths_v1_and_v2_keep_decimals_qualification(self):
        head = [0] * 19
        head[0], head[6], head[1] = ASSET, ACCOUNT, 6
        v2 = "0x" + "".join(word(value) for value in head)
        self.assertEqual(constructor_parameters("wildcat-v2", v2)["decimals"], 6)
        head[1] = 256
        with self.assertRaises(TabulariumError):
            constructor_parameters("wildcat-v2", "0x" + "".join(word(value) for value in head))
        with self.assertRaises(TabulariumError):
            constructor_parameters("wildcat-v2", v2 + "00")
        v1_head = [0] * 16
        v1_head[0], v1_head[3], v1_head[4] = ASSET, ACCOUNT, MARKET
        v1_head[1], v1_head[2] = 512, 576
        # Independently encoded two dynamic strings occupy 64 bytes each.
        tails = word(1) + "61" + "00" * 31 + word(1) + "62" + "00" * 31
        v1 = "0x" + word(32) + "".join(word(value) for value in v1_head) + tails
        self.assertIsNone(constructor_parameters("wildcat-v1", v1)["decimals"])
        self.assertEqual(len(bytes.fromhex(v1[2:])), 672)
        for changed in (v1 + "00", "0x" + word(64) + v1[66:]):
            with self.assertRaises(TabulariumError):
                constructor_parameters("wildcat-v1", changed)
