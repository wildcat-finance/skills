"""Hold the constructed public specimens to native meanings and copied bytes."""

from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest

if __package__:
    from . import support
    from .test_wildcat_v3_release import constructed_release
    from .wildcat_v3_public_fixtures import build_main_release, release_id
    from .wildcat_v3_registry_fixture import build_registry_release
    from .wildcat_v3_fixtures import ACCOUNT, ASSET, DEBTOR, ESCROW, MARKET, OTHER, PAYER, WRAPPER, log, word
else:
    import support
    from test_wildcat_v3_release import constructed_release
    from wildcat_v3_public_fixtures import build_main_release, release_id
    from wildcat_v3_registry_fixture import build_registry_release
    from wildcat_v3_fixtures import ACCOUNT, ASSET, DEBTOR, ESCROW, MARKET, OTHER, PAYER, WRAPPER, log, word

from tabularium_lib import verifier
from tabularium_lib.core import TabulariumError, canonical_json
from tabularium_lib.wildcat_release import build_wildcat_canonical
from tabularium_lib.wildcat_source import CONSTRUCTION_GAP, load_raw


VENUES = ("wildcat-v1", "wildcat-v2")
ROOTS = ("release", "registry-context/release")
REGISTRY_MARKETS = {
    "wildcat-v1": "0x5850afc80561932b0abb63dd13cdc129395323a3",
    "wildcat-v2": "0x20632bd54e16fcbcd35dcb2c8882a8a8802ad38d",
}


def _document(root, name):
    return json.loads((root / name).read_bytes())


def _rows(root):
    return [json.loads(line) for line in (root / "events.jsonl").read_text().splitlines()]


def _file_bytes(root):
    return {path.relative_to(root).as_posix(): path.read_bytes()
            for path in root.rglob("*") if path.is_file()}


def _write_document(root, name, value):
    (root / name).write_bytes(canonical_json(value) + b"\n")


def _rebind(root, name):
    """Keep top-level byte claims coherent while leaving semantics unsupported."""
    data = (root / name).read_bytes()
    claim = {"source.json": "source", "capture.json": "capture_manifest",
             "events.jsonl": "canonical"}[name]
    coverage = _document(root, "coverage.json")
    coverage[claim].update(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
    if name == "source.json":
        capture = _document(root, "capture.json")
        capture["source"].update(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
        _write_document(root, "capture.json", capture)
        _rebind(root, "capture.json")
        coverage = _document(root, "coverage.json")
        coverage[claim].update(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
    elif name == "events.jsonl":
        rows = _rows(root)
        coverage["canonical"]["rows"] = len(rows)
        coverage["coverage"]["included_events"] = dict(Counter(
            row["action"].split(".", 1)[1] for row in rows))
    _write_document(root, "coverage.json", coverage)


def _public(venue, name):
    return support.EXAMPLES / (venue + "-v0") / name


def _copy_public(base, venue, name):
    root = base / "release"
    shutil.copytree(_public(venue, name), root)
    for path in root.rglob("*"):
        if path.is_file():
            path.chmod(0o600)
    return root


class ReleaseSpecimenTests(unittest.TestCase):
    """Independent economic oracles, full-file reproduction and refusal copies."""

    def test_all_four_fresh_releases_match_every_public_file_and_move(self):
        for venue in VENUES:
            for name in ROOTS:
                with self.subTest(venue=venue, root=name), tempfile.TemporaryDirectory() as temporary:
                    base = Path(temporary).resolve()
                    target = base / "fresh"
                    registry = name != "release"
                    builder = build_registry_release if registry else build_main_release
                    coverage = builder(target, venue, release_id(venue, registry))
                    self.assertEqual(coverage, target / "coverage.json")
                    # Actual file bytes are compared, independently of digest inventories.
                    self.assertEqual(_file_bytes(target), _file_bytes(_public(venue, name)))
                    self.assertEqual(verifier.verify(coverage).schema_version, 3)
                    moved = base / "moved"
                    target.rename(moved)
                    self.assertFalse(target.exists())
                    for path in moved.rglob("*"):
                        if path.is_file():
                            path.chmod(0o444)
                    self.assertEqual(verifier.verify(moved / "coverage.json").rows,
                                     2 if registry else (7 if venue == "wildcat-v1" else 10))

    def test_main_market_parties_and_amounts_have_independent_oracles(self):
        expected = {
            "deposit": ([("depositor", ACCOUNT), ("minted-token-account", ACCOUNT)],
                        [("assets", "100", ASSET), ("scaled-claims", "90", None)]),
            "withdrawal-queued": ([("withdrawing-account", ACCOUNT)],
                                  [("normalized-claims", "80", MARKET), ("scaled-claims", "70", None)]),
            "withdrawal-executed": ([("beneficiary", ACCOUNT), ("escrow-recipient", ESCROW)],
                                    [("assets", "50", ASSET)]),
            "transfer": ([("from", ACCOUNT), ("to", OTHER)], [("market-token-claims", "30", MARKET)]),
            "borrow": ([("pool", MARKET)], [("assets", "75", ASSET)]),
            "debt-repaid": ([("payer", PAYER), ("pool", MARKET)], [("assets", "25", ASSET)]),
            "market-closed": ([("pool", MARKET)], []),
        }
        for venue in VENUES:
            rows = {row["action"].split(".", 1)[1]: row for row in _rows(_public(venue, "release"))}
            for action, (parties, amounts) in expected.items():
                with self.subTest(venue=venue, action=action):
                    row = rows[action]
                    self.assertEqual([(p["role"], p["address"]) for p in row["parties"]], parties)
                    self.assertEqual([(a["kind"], a["base_units"], a["asset"]) for a in row["amounts"]], amounts)
                    self.assertEqual(row["instrument"]["id"], MARKET)
            self.assertEqual(set(rows), set(expected) | ({"wrapper-deposit", "wrapper-withdrawal", "wrapper-transfer"}
                                                       if venue == "wildcat-v2" else set()))

    def test_wrapper_amounts_are_market_tokens_and_wrapper_shares(self):
        expected = {
            "wrapper-deposit": ([("caller", PAYER), ("owner", ACCOUNT)],
                                [("market-token-assets", "100", MARKET), ("wrapper-shares", "80", WRAPPER)]),
            "wrapper-withdrawal": ([("caller", PAYER), ("receiver", OTHER), ("owner", ACCOUNT)],
                                   [("market-token-assets", "60", MARKET), ("wrapper-shares", "45", WRAPPER)]),
            "wrapper-transfer": ([("from", ACCOUNT), ("to", OTHER)], [("wrapper-shares", "5", WRAPPER)]),
        }
        rows = {row["action"].split(".", 1)[1]: row for row in _rows(_public("wildcat-v2", "release"))}
        for action, (parties, amounts) in expected.items():
            with self.subTest(action=action):
                row = rows[action]
                self.assertEqual(row["instrument"]["id"], WRAPPER)
                self.assertEqual([(p["role"], p["address"]) for p in row["parties"]], parties)
                self.assertEqual([(a["kind"], a["base_units"], a["asset"]) for a in row["amounts"]], amounts)
                self.assertNotIn(ASSET, [a["asset"] for a in row["amounts"]])

    def test_main_synthetic_context_and_capture_classes_stay_qualified(self):
        for venue in VENUES:
            root = _public(venue, "release")
            source = _document(root, "source.json")
            self.assertEqual(source["scope"]["kind"], "constructed-fixture")
            self.assertEqual(source["scope"]["limitations"], [CONSTRUCTION_GAP])
            for context in source["contexts"].values():
                self.assertNotIn("borrower_context", context)
                self.assertEqual([item["class"] for item in context["source"]], ["declared-constructed-context"])
            for capture in source["scope"]["raw_captures"]:
                self.assertEqual(capture["source"]["kind"], "constructed-fixture")
                self.assertEqual(capture["source"]["locator_class"], "local-fixture")
                self.assertEqual(capture["scope"]["finality"], "unknown")
                self.assertEqual(capture["coverage"]["gaps"], [CONSTRUCTION_GAP])
            self.assertEqual(_document(root, "capture.json")["scope"], source["scope"])

    def test_registry_inference_keeps_observed_payer_separate_and_synthetic_gaps(self):
        for venue in VENUES:
            with self.subTest(venue=venue):
                root = _public(venue, "registry-context/release")
                source = _document(root, "source.json")
                market = REGISTRY_MARKETS[venue]
                context = source["contexts"][market]
                self.assertEqual({item["class"] for item in context["source"]},
                                 {"checked-registry-context", "checked-positional-epoch-context",
                                  "inferred-deployment-asset", "registry-inferred-debtor"})
                self.assertEqual(context["borrower_context"]["class"], "registry-inferred")
                self.assertEqual(context["borrower_context"]["borrower"], DEBTOR)
                self.assertEqual(context["borrower_context"]["rule"],
                                 "v1-NewController-and-MarketDeployed" if venue == "wildcat-v1"
                                 else "v2-factory-return-and-MarketDeployed")
                rows = {row["action"].split(".", 1)[1]: row for row in _rows(root)}
                self.assertEqual(set(rows), {"borrow", "debt-repaid"})
                self.assertEqual(rows["borrow"]["parties"], [{"role": "pool", "address": market}])
                self.assertEqual(rows["debt-repaid"]["parties"],
                                 [{"role": "payer", "address": PAYER}, {"role": "pool", "address": market}])
                self.assertNotEqual(PAYER, DEBTOR)
                for action, amount in (("borrow", "75"), ("debt-repaid", "25")):
                    self.assertEqual(rows[action]["amounts"],
                                     [{"kind": "assets", "base_units": amount, "asset": ASSET}])
                self.assertEqual(source["scope"]["kind"], "recorded-interval")
                self.assertEqual(source["scope"]["wrapper_native_coverage"], "not-established")
                captures = {c["component"]: c for c in source["scope"]["raw_captures"]}
                for component in ("boundary-blocks", "epoch-evidence", "logs", "traces"):
                    capture = captures[component]
                    self.assertEqual(capture["evidence_class"], "recorded-rpc")
                    self.assertIn("constructed fixture", capture["source"]["reference"])
                    self.assertTrue(any("declared constructed" in gap and "not preserved chain evidence" in gap
                                        for gap in capture["coverage"]["gaps"]))

    def test_native_disposition_denominators_and_every_raw_selector(self):
        for venue in VENUES:
            for name in ROOTS:
                with self.subTest(venue=venue, root=name):
                    root = _public(venue, name)
                    source = _document(root, "source.json")
                    rows = _rows(root)
                    count = (7 if venue == "wildcat-v1" else 10) if name == "release" else 2
                    expected = ({"primary": count, "supporting-routing": 1,
                                 "unsupported-canonical-meaning": 1, "unsupported-decode": 1}
                                if name == "release" else
                                {"primary": 2, "unsupported-canonical-meaning": 2 if venue == "wildcat-v1" else 1})
                    self.assertEqual(Counter(d["disposition"] for d in source["dispositions"]), expected)
                    self.assertEqual(len(source["mapping_records"]), sum(expected.values()))
                    self.assertEqual(len(rows), count)
                    mappings = {m["source_selector"]: m for m in source["mapping_records"]}
                    self.assertEqual(len(mappings), sum(expected.values()))
                    self.assertEqual({d["source_selector"] for d in source["dispositions"]}, set(mappings))
                    self.assertEqual({row["provenance"]["source_selector"] for row in rows},
                                     {key for key, mapping in mappings.items() if mapping["disposition"] == "primary"})
                    manifest = _document(root / "source/raw-release", "manifest.json")
                    components = {item["name"]: item for item in manifest["components"]}
                    for mapping in mappings.values():
                        reference = mapping["reference"]
                        journal = _document(root / "source/raw-release", components[reference["component"]]["object_path"])
                        response = json.loads(journal["records"][int(reference["journal_selector"].split("/")[2])]["response"])
                        self.assertEqual(mapping["native_record"], response["result"][int(reference["selector"].split("/")[2])])
                        self.assertEqual(mapping["evidence_class"], "directly-observed")
                        self.assertEqual(reference["evidence_class"], "recorded-rpc")
                    for row in rows:
                        self.assertEqual(row["native_record"], mappings[row["provenance"]["source_selector"]]["native_record"])
                    coverage = _document(root, "coverage.json")
                    self.assertEqual(coverage["canonical"]["rows"], count)
                    self.assertEqual(coverage["coverage"]["included_events"],
                                     dict(Counter(row["action"].split(".", 1)[1] for row in rows)))

    def test_routing_has_two_selectors_and_one_cash_withdrawal(self):
        for venue in VENUES:
            root = _public(venue, "release")
            source = _document(root, "source.json")
            executions = [row for row in _rows(root) if row["action"] == venue + ".withdrawal-executed"]
            self.assertEqual(len(executions), 1)
            event = executions[0]
            mapping = next(m for m in source["mapping_records"] if m["signature"] == "WithdrawalExecuted(uint256,address,uint256)")
            route = next(m for m in source["mapping_records"] if m["disposition"] == "supporting-routing")
            self.assertEqual(mapping["join"]["evidence_class"], "join-inference")
            self.assertEqual(mapping["join"]["primary_selector"], event["provenance"]["source_selector"])
            self.assertEqual(mapping["join"]["companion_selector"], route["source_selector"])
            self.assertIn(route["source_selector"], event["provenance"]["supporting_selectors"])
            self.assertNotEqual(mapping["join"]["primary_selector"], mapping["join"]["companion_selector"])
            self.assertEqual(event["amounts"], [{"kind": "assets", "base_units": "50", "asset": ASSET}])
            self.assertEqual(_document(root, "coverage.json")["coverage"]["included_events"]["withdrawal-executed"], 1)
            unsupported = [m for m in source["mapping_records"] if m["disposition"].startswith("unsupported")]
            self.assertEqual({m["signature"] for m in unsupported}, {"Approval(address,address,uint256)", None})

    def test_rehashed_canonical_mutations_refuse_semantic_rebuild(self):
        for venue in VENUES:
            for name in ROOTS:
                for change in ("party", "amount", "selector", "rule", "drop-row", "duplicate-cash"):
                    with self.subTest(venue=venue, root=name, change=change), tempfile.TemporaryDirectory() as temporary:
                        root = _copy_public(Path(temporary).resolve(), venue, name)
                        rows = _rows(root)
                        if change == "party":
                            next(r for r in rows if r["action"].endswith(".debt-repaid"))["parties"][0]["address"] = DEBTOR
                        elif change == "amount":
                            rows[0]["amounts"][0]["base_units"] = "101"
                        elif change == "selector":
                            rows[0]["provenance"]["source_selector"] = "wildcat-journal:" + "0" * 64
                        elif change == "rule":
                            rows[0]["provenance"]["mapping_rule"] = venue + ".debt-repaid.v1"
                        elif change == "drop-row":
                            rows.pop()
                        else:
                            row = deepcopy(next(r for r in rows if r["action"].endswith(".withdrawal-executed"))
                                           if name == "release" else rows[-1])
                            row["id"] += ":unsupported-copy"
                            rows.append(row)
                        (root / "events.jsonl").write_bytes(b"".join(canonical_json(row) + b"\n" for row in rows))
                        _rebind(root, "events.jsonl")
                        with self.assertRaisesRegex(TabulariumError, "events.jsonl differs from its offline semantic rebuild"):
                            verifier.verify(root / "coverage.json")

    def test_rehashed_source_mapping_class_context_and_disposition_mutations_refuse(self):
        for venue in VENUES:
            for name in ROOTS:
                for change in ("class", "mapping", "context", "drop-disposition"):
                    with self.subTest(venue=venue, root=name, change=change), tempfile.TemporaryDirectory() as temporary:
                        root = _copy_public(Path(temporary).resolve(), venue, name)
                        source = _document(root, "source.json")
                        if change == "class":
                            source["mapping_records"][0]["evidence_class"] = "proved"
                        elif change == "mapping":
                            source["mapping_records"][0]["signature"] = "Borrow(address,uint256)"
                        elif change == "context":
                            market = MARKET if name == "release" else REGISTRY_MARKETS[venue]
                            source["contexts"][market]["borrower_context"] = {"class": "registry-inferred", "borrower": OTHER}
                        else:
                            source["dispositions"].pop()
                        _write_document(root, "source.json", source)
                        _rebind(root, "source.json")
                        with self.assertRaisesRegex(TabulariumError, "source.json differs from its offline semantic rebuild"):
                            verifier.verify(root / "coverage.json")

    def test_rehashed_capture_and_stale_coverage_mutations_refuse(self):
        for venue in VENUES:
            for name in ROOTS:
                for change in ("capture", "coverage"):
                    with self.subTest(venue=venue, root=name, change=change), tempfile.TemporaryDirectory() as temporary:
                        root = _copy_public(Path(temporary).resolve(), venue, name)
                        if change == "capture":
                            document = _document(root, "capture.json")
                            document["scope"]["kind"] = "full-dataset"
                            _write_document(root, "capture.json", document)
                            _rebind(root, "capture.json")
                            reason = "capture.json"
                        else:
                            document = _document(root, "coverage.json")
                            document["coverage"]["included_events"]["borrow"] = 2
                            _write_document(root, "coverage.json", document)
                            reason = "coverage.json"
                        with self.assertRaisesRegex(TabulariumError, reason + " differs from its offline semantic rebuild"):
                            verifier.verify(root / "coverage.json")

    def test_rebound_new_raw_source_cannot_bless_stale_interpretation(self):
        def change_payer(document, journal, plan):
            response = json.loads(journal["records"][0]["response"])
            raws = response["result"]
            raws.extend((log("Approval(address,address,uint256)", (ACCOUNT, OTHER), (9,), index=len(raws)),
                         log("Unrecognized(uint256)", data=(4,), index=len(raws) + 1)))
            raws[5]["topics"][1] = "0x" + word(OTHER)
            journal["records"][0]["response"] = canonical_json(response).decode()

        for venue in VENUES:
            with self.subTest(venue=venue), tempfile.TemporaryDirectory() as temporary:
                base = Path(temporary).resolve()
                root = _copy_public(base, venue, "release")
                expected_raws = deepcopy([raw for raw, reference in load_raw(root / "source/raw-release")["records"]])
                expected_raws[5]["topics"][1] = "0x" + word(OTHER)
                inputs = base / "changed-inputs"
                inputs.mkdir()
                changed_raw = constructed_release(inputs, venue, change_payer)
                admitted = load_raw(changed_raw)
                self.assertEqual([raw for raw, reference in admitted["records"]], expected_raws)
                shutil.rmtree(root / "source/raw-release")
                shutil.copytree(changed_raw, root / "source/raw-release")
                source = _document(root, "source.json")
                source["raw_release"].update(release_id=admitted["release_id"], inventory=admitted["inventory"])
                _write_document(root, "source.json", source)
                _rebind(root, "source.json")
                # The replacement raw release itself is admitted; old mappings still refuse.
                self.assertEqual(load_raw(root / "source/raw-release")["release_id"], admitted["release_id"])
                with self.assertRaisesRegex(TabulariumError, "source.json differs from its offline semantic rebuild"):
                    verifier.verify(root / "coverage.json")

    def test_constructed_inputs_cannot_hide_qualification_or_wrong_wrapper_asset(self):
        def mutate_kind(document, journal, plan):
            for capture in plan["captures"]:
                capture["source"].update(kind="json-rpc", locator_class="provider-endpoint")

        def mutate_gap(document, journal, plan):
            document["limitations"] = []

        def mutate_capture_gap(document, journal, plan):
            for capture in plan["captures"]:
                capture["coverage"]["gaps"] = ["a different gap does not qualify these synthetic bytes"]

        def mutate_wrapper(document, journal, plan):
            next(context for context in document["contexts"] if context["role"] == "wrapper")["asset"] = ASSET

        mutations = ((mutate_kind, "constructed Wildcat capture labels conflict"),
                     (mutate_gap, "constructed Wildcat context has missing source qualifications"),
                     (mutate_capture_gap, "constructed Wildcat capture labels conflict"),
                     (mutate_wrapper, "constructed wrapper lacks its declared market-token asset context"))
        for mutation, reason in mutations:
            with self.subTest(change=mutation.__name__), tempfile.TemporaryDirectory() as temporary:
                base = Path(temporary).resolve()
                raw = constructed_release(base, "wildcat-v2", mutation)
                output = base / "canonical"
                with self.assertRaisesRegex(TabulariumError, reason):
                    build_wildcat_canonical(raw, output, "constructed-hostile")
                self.assertFalse(output.exists())
                self.assertFalse(list(base.glob(".wildcat-stage-*")))

    def test_malformed_primary_abi_refuses_while_unknown_topic_stays_unsupported(self):
        for venue in VENUES:
            for malformed in (False, True):
                with self.subTest(venue=venue, malformed=malformed), tempfile.TemporaryDirectory() as temporary:
                    base = Path(temporary).resolve()

                    def mutate(document, journal, plan):
                        response = json.loads(journal["records"][0]["response"])
                        first = response["result"][0]
                        if malformed:
                            first["data"] = "0x" + word(100)
                        else:
                            first["topics"][0] = "0x" + "ab" * 32
                        journal["records"][0]["response"] = canonical_json(response).decode()

                    raw = constructed_release(base, venue, mutate)
                    target = base / "canonical"
                    if malformed:
                        with self.assertRaises(TabulariumError):
                            build_wildcat_canonical(raw, target, "constructed-malformed-primary")
                        self.assertFalse(target.exists())
                    else:
                        build_wildcat_canonical(raw, target, "constructed-unknown-topic")
                        self.assertEqual(verifier.verify(target / "coverage.json").rows,
                                         6 if venue == "wildcat-v1" else 9)
                        dispositions = _document(target, "source.json")["dispositions"]
                        self.assertEqual(Counter(d["disposition"] for d in dispositions)["unsupported-decode"], 1)

    def test_existing_public_output_cannot_be_overwritten(self):
        for venue in VENUES:
            with self.subTest(venue=venue), tempfile.TemporaryDirectory() as temporary:
                base = Path(temporary).resolve()
                target = _copy_public(base, venue, "release")
                before = _file_bytes(target)
                builder = build_main_release
                with self.assertRaisesRegex(TabulariumError, "output directory must be fresh"):
                    builder(target, venue, release_id(venue))
                self.assertEqual(_file_bytes(target), before)
                self.assertFalse(list(base.glob(".wildcat-stage-*")))

    def test_each_closed_root_refuses_extras_and_missing_copied_raw_files(self):
        for venue in VENUES:
            for name in ROOTS:
                for change in ("file", "directory", "missing-raw"):
                    with self.subTest(venue=venue, root=name, change=change), tempfile.TemporaryDirectory() as temporary:
                        root = _copy_public(Path(temporary).resolve(), venue, name)
                        if change == "file":
                            (root / "undeclared").write_text("extra")
                        elif change == "directory":
                            (root / "undeclared").mkdir()
                        else:
                            source = _document(root, "source.json")
                            relative = next(path for path in source["raw_release"]["inventory"] if path.startswith("objects/"))
                            (root / "source/raw-release" / relative).unlink()
                        with self.assertRaises(TabulariumError):
                            verifier.verify(root / "coverage.json")
