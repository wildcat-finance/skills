"""The Aave V3 venue's pinned 356-subject registry and the plan scope it enforces.

`AaveRegistryConformanceTests` is loaded by name: the Aave conformance harness
resolves `registry-reproduces-recorded-subject-set` and
`registry-pin-change-refuses` against it. No case here reads the two full
records the aave-v3 row pins; they are not in this repository. The committed
registry is checked against the in-tree row, generator inputs are constructed
temporary files, and the derivation is exercised over documents rebuilt from
the committed registry itself.
"""

import ast
import contextlib
from copy import deepcopy
import hashlib
import io
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


PLUGIN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN / "scripts"))

from alexandria_lib import aave_registry, interval, wildcat_registry  # noqa: E402
from alexandria_lib.canonical import canonical_bytes  # noqa: E402
from alexandria_lib.errors import AlexandriaError  # noqa: E402
from alexandria_lib.venues import VENUES, aave_v3  # noqa: E402
import usdc_interval  # noqa: E402

REPO_ROOT = PLUGIN.parents[1]
EXAMPLE = PLUGIN / "examples" / "aave-v3-interval-v0"
REGISTRY = EXAMPLE / "registry.json"
TARGETS = REPO_ROOT / "docs" / "kickoff" / "1359" / "targets.json"
EVIDENCE = REPO_ROOT / "docs" / "kickoff" / "1359" / "evidence" / "ethereum-mainnet-1591.json"
WILDCAT_V2_PLAN = PLUGIN / "examples" / "wildcat-v2-interval-v0" / "plan.json"
OVERLAP = "0x102633152313c81cd80419b6ecf66d14ad68949a"
WETH = "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"
POOL = "0x87870bca3f3fd6335c3f4ce8392d69350b4fa4e2"
PROVIDER = "0x2f39d218133afab8f2b819b1066c7e434ad94e9e"
# A Pool address of another Aave V3 market, used only as a stand-in.
OTHER_POOL = "0x4e033931ad43597d96d6bcc25c280717730b58b1"


def row():
    """The aave-v3 row, re-read by iterating the target list, never by walking it."""
    document = json.loads(TARGETS.read_bytes())
    matches = [item for item in document["targets"] if item.get("id") == "aave-v3"]
    assert len(matches) == 1, "targets.json carries no single aave-v3 row"
    return matches[0]


def registry():
    """The committed registry, a fresh copy each time so no case edits another's."""
    return json.loads(REGISTRY.read_bytes())


def entries(document=None):
    return {entry["address"]: entry for entry in (document or registry())["entries"]}


def rebuilt_records(document=None):
    """Observation and source-match documents carrying exactly what the registry records.

    They hold only the fields `derive_registry` reads, projected back from the
    committed registry, so a derivation over them must reproduce it byte for
    byte and a mutation of one field exercises one refusal.
    """
    document = document or registry()
    by_address = entries(document)
    observed = document["observed_block"]["number"]
    market = document["market"]
    token_roles = {"aToken-proxy", "variableDebtToken-proxy", "stableDebtToken-proxy"}
    reserves = [
        dict(reserve, interest_rate_strategy_epochs=[]) for reserve in document["reserves"]
    ]
    reserves[0]["interest_rate_strategy_epochs"] = [
        {"strategy": address} for address, entry in by_address.items()
        if entry["role"] == "interest-rate-strategy"
    ]

    def table(epochs):
        return [
            {key if key != "transaction" else "tx": value for key, value in epoch.items()}
            for epoch in epochs
        ]

    observations = {
        "chain_id": 1,
        "code": [
            {
                "address": address,
                "block_number": observed,
                "code_keccak256": entry["code_keccak256"],
                "code_length": entry["code_length"],
            }
            for address, entry in by_address.items()
        ],
        "creation": {
            address: {"block": entry["creation_block"], "tx": entry["creation_transaction"]}
            for address, entry in by_address.items()
        },
        "implementation_revisions": {
            address: {"role": entry["role"]} for address, entry in by_address.items()
            if entry["role"] in aave_registry.IMPLEMENTATION_ROLES
        },
        "library_links": {
            market["pool"]: {
                address: "Library" for address, entry in by_address.items() if entry["role"] == "library"
            }
        },
        "market": {
            "acl_manager": market["acl_manager"],
            "addresses_provider": market["addresses_provider"],
            "pool_configurator_proxy": market["pool_configurator"],
            "pool_proxy": market["pool"],
        },
        "periphery_not_subjects": {
            "mock_stable_debt": OVERLAP,
            "others": list(document["periphery"]["excluded"]),
        },
        "pool_configurator_implementation_epochs": table(
            by_address[market["pool_configurator"]]["implementations"]
        ),
        "pool_implementation_epochs": table(by_address[market["pool"]]["implementations"]),
        "reserves": reserves,
        "summary": {"by_role": dict(document["subject_set"]["by_role"])},
        "token_proxy_implementation_epochs": {
            address: table(entry["implementations"]) for address, entry in by_address.items()
            if entry["role"] in token_roles
        },
    }
    sets = {}
    for address, entry in by_address.items():
        sets.setdefault(entry["source_set"], []).append(address)
    source_match = {
        "source_sets": [
            {"id": set_id, "reproduction": {"members": members}}
            for set_id, members in sorted(sets.items())
        ]
    }
    return observations, source_match


def plan(subjects=None, **changes):
    """A v2 interval plan over the Aave venue that the shared plan check accepts."""
    document = json.loads(WILDCAT_V2_PLAN.read_bytes())
    document.update({
        "deployment": "aave-v3-constructed",
        "subjects": list(subjects or [POOL, PROVIDER]),
        "venue": aave_v3.VENUE,
    })
    document.update(changes)
    return document


class AaveRegistryConformanceTests(unittest.TestCase):
    """The committed registry reproduces the row, and a changed pin refuses by name."""

    def test_registry_reproduces_the_recorded_subject_set_digest(self):
        document = registry()
        recorded = row()["deployment"]["full_subject_set"]
        addresses = [entry["address"] for entry in document["entries"]]
        # Recomputed here from the committed bytes under the row's recorded
        # form, not read back from the registry or asserted as a literal.
        digest = hashlib.sha256(
            ("\n".join(sorted(address.lower() for address in addresses)) + "\n").encode("utf-8")
        ).hexdigest()
        self.assertEqual(digest, recorded["sha256"])
        self.assertEqual(len(set(addresses)), recorded["count"])
        self.assertEqual(recorded["count"], 356)
        counts = {}
        for entry in document["entries"]:
            counts[entry["role"]] = counts.get(entry["role"], 0) + 1
        self.assertEqual(counts, recorded["by_role"])
        self.assertEqual(document["subject_set"]["sha256"], digest)
        self.assertEqual(REGISTRY.read_bytes(), canonical_bytes(document))
        aave_registry.validate_registry(document)

    def test_listed_contracts_match_the_merged_row(self):
        document = registry()
        by_address = entries(document)
        contracts = row()["deployment"]["contracts"]
        self.assertEqual(len(contracts), 22)
        for contract in contracts:
            with self.subTest(contract=contract["address"]):
                entry = by_address[contract["address"]]
                self.assertEqual(entry["role"], contract["role"])
                self.assertEqual(entry["code_length"], contract["code_length"])
                self.assertEqual(entry["code_keccak256"], contract["code_keccak256"])
                self.assertEqual(entry["creation_block"], contract["code_match"]["deployment_block"])
        aave_registry.check_row_agreement(document, row())

    def test_changed_registry_pin_refuses_by_name(self):
        # One subject changed in a field the shape check does not constrain:
        # only the pinned digest separates it from the reviewed registry.
        changed = registry()
        entry = changed["entries"][0]
        entry["creation_transaction"] = "0x" + "ab" * 32
        aave_registry._validate_shape(changed)
        actual = hashlib.sha256(canonical_bytes(changed)).hexdigest()
        with self.assertRaises(AlexandriaError) as raised:
            aave_registry.validate_registry(changed)
        message = str(raised.exception)
        self.assertIn("AAVE_V3_REGISTRY_SHA256", message)
        self.assertIn(actual, message)
        self.assertIn(aave_registry.AAVE_V3_REGISTRY_SHA256, message)
        # A changed pin refuses the committed registry the same way.
        moved = "0" * 64
        with mock.patch.object(aave_registry, "AAVE_V3_REGISTRY_SHA256", moved):
            with self.assertRaises(AlexandriaError) as raised:
                aave_v3.validate_registry(registry())
        self.assertIn(moved, str(raised.exception))
        self.assertIn(hashlib.sha256(REGISTRY.read_bytes()).hexdigest(), str(raised.exception))
        # A subject swapped for another address fails the subject-set digest.
        swapped = registry()
        swapped["entries"][-1]["address"] = "0x" + "f" * 40
        with self.assertRaises(AlexandriaError) as raised:
            aave_registry.validate_registry(swapped)
        self.assertIn(aave_registry.SUBJECT_SET_SHA256, str(raised.exception))
        self.assertIn("subjects hash to", str(raised.exception))

    def test_changed_source_row_refuses_by_name(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / aave_registry.TARGETS_PATH
            target.parent.mkdir(parents=True)
            document = json.loads(TARGETS.read_bytes())
            target.write_bytes(TARGETS.read_bytes())
            self.assertEqual(aave_registry.read_row(root)["id"], "aave-v3")
            # Another row changing leaves the pinned row readable.
            other = next(item for item in document["targets"] if item.get("id") != "aave-v3")
            other["label"] = "edited for this case"
            target.write_text(json.dumps(document), encoding="utf-8")
            self.assertEqual(aave_registry.read_row(root)["id"], "aave-v3")
            aave = next(item for item in document["targets"] if item.get("id") == "aave-v3")
            aave["deployment"]["full_subject_set"]["count"] = 355
            target.write_text(json.dumps(document), encoding="utf-8")
            with self.assertRaises(AlexandriaError) as raised:
                aave_registry.read_row(root)
        message = str(raised.exception)
        self.assertIn("row aave-v3 does not match its pin", message)
        self.assertIn(aave_registry.row_digest(aave), message)
        self.assertIn(dict(aave_registry.ROW_PINS)["aave-v3"], message)


class AaveRegistryContentTests(unittest.TestCase):
    """What each subject carries, and what stays out of the subject set."""

    def test_the_fourteen_role_counts(self):
        counts = registry()["subject_set"]["by_role"]
        self.assertEqual(len(counts), 14)
        self.assertEqual(counts, row()["deployment"]["full_subject_set"]["by_role"])
        self.assertEqual(counts, aave_registry.EXPECTED_ROLE_COUNTS)
        self.assertEqual(sum(counts.values()), 356)

    def test_each_subject_carries_role_creation_and_proxy_implementations(self):
        by_address = entries()
        proxies = [e for e in by_address.values() if e["role"] in aave_registry.PROXY_ROLES]
        others = [e for e in by_address.values() if e["role"] not in aave_registry.PROXY_ROLES]
        self.assertEqual((len(proxies), len(others)), (172, 184))
        for entry in by_address.values():
            self.assertIsInstance(entry["creation_block"], int)
            self.assertRegex(entry["creation_transaction"], r"^0x[0-9a-f]{64}$")
        for entry in others:
            self.assertIsNone(entry["implementations"])
        tokens = [e for e in proxies if e["role"] not in ("pool-proxy", "pool-configurator-proxy")]
        self.assertEqual(sum(len(e["implementations"]) for e in tokens), 489)
        pool = by_address[POOL]["implementations"]
        self.assertEqual(len(pool), 11)
        self.assertEqual(len(by_address[aave_registry.MARKET["pool_configurator"]]["implementations"]), 7)
        for entry in proxies:
            for epoch in entry["implementations"]:
                self.assertEqual(by_address[epoch["implementation"]]["role"], aave_registry.PROXY_ROLES[entry["role"]])

    def test_weth_stable_debt_token_overlap_is_recorded(self):
        document = registry()
        self.assertEqual(entries(document)[OVERLAP]["role"], "stableDebtToken-proxy")
        self.assertEqual(
            document["periphery"]["overlap"],
            [{"address": OVERLAP, "periphery": "mock_stable_debt", "role": "stableDebtToken-proxy"}],
        )
        weth = [reserve for reserve in document["reserves"] if reserve["asset"] == WETH]
        self.assertEqual(len(weth), 1)
        self.assertEqual(weth[0]["stable_debt_token"], OVERLAP)
        self.assertEqual(len(aave_v3.gaps(document)), 1)
        self.assertIn(OVERLAP, aave_v3.gaps(document)[0])
        self.assertIn("mock_stable_debt", aave_v3.gaps(document)[0])

    def test_no_periphery_address_from_the_merged_evidence_is_a_subject(self):
        periphery = json.loads(EVIDENCE.read_bytes())["periphery_not_subjects"]
        addresses = []
        for value in periphery.values():
            addresses.extend(value if isinstance(value, list) else [value])
        self.assertEqual(len(addresses), 10)
        subjects = set(entries())
        admitted = sorted(set(addresses) & subjects)
        # The one overlap stays a subject and is recorded; nothing else enters.
        self.assertEqual(admitted, [OVERLAP])
        self.assertEqual(sorted(set(addresses) - {OVERLAP}), registry()["periphery"]["excluded"])

    def test_no_underlying_asset_is_a_subject(self):
        document = registry()
        assets = {reserve["asset"] for reserve in document["reserves"]}
        self.assertEqual(len(assets), 67)
        self.assertIn(WETH, assets)
        self.assertFalse(assets & set(entries(document)))


class AaveRegistryGeneratorInputTests(unittest.TestCase):
    """A generator input refuses unless its bytes equal the row's pin, with no out-of-tree file."""

    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.sha256, self.size = aave_registry.full_record_pins(row())["observations"]

    def refusal(self, path):
        with self.assertRaises(AlexandriaError) as raised:
            aave_registry.read_full_record(path, "observations", self.sha256, self.size)
        return str(raised.exception)

    def test_byte_count_differing_from_the_pin_refuses_by_name(self):
        path = self.root / "short.json"
        path.write_bytes(b"{}\n")
        message = self.refusal(path)
        self.assertIn("full record observations does not match the aave-v3 row's pin", message)
        self.assertIn("3 bytes hashing to " + hashlib.sha256(b"{}\n").hexdigest(), message)
        self.assertIn(f"{self.size} bytes hashing to {self.sha256}", message)

    def test_digest_differing_from_the_pin_at_the_pinned_length_refuses_by_name(self):
        path = self.root / "same-length.json"
        data = b" " * self.size
        path.write_bytes(data)
        message = self.refusal(path)
        self.assertIn("full record observations does not match", message)
        self.assertIn(f"{self.size} bytes hashing to {hashlib.sha256(data).hexdigest()}", message)
        self.assertIn(self.sha256, message)

    def test_symlinked_input_refuses(self):
        target = self.root / "target.json"
        target.write_bytes(b"{}\n")
        link = self.root / "link.json"
        os.symlink(target, link)
        self.assertIn("must not be a symbolic link", self.refusal(link))

    def test_directory_missing_and_oversized_inputs_refuse(self):
        self.assertIn("must be a regular file", self.refusal(self.root))
        self.assertIn("cannot open full record observations", self.refusal(self.root / "absent.json"))
        large = self.root / "large.json"
        with open(large, "wb") as handle:
            handle.truncate(aave_registry.MAX_FULL_RECORD_BYTES + 1)
        self.assertIn("exceeds the", self.refusal(large))

    def test_a_platform_without_no_follow_opens_refuses(self):
        path = self.root / "record.json"
        path.write_bytes(b"{}\n")
        with mock.patch.object(os, "O_NOFOLLOW", 0):
            self.assertIn("cannot open a full record without following a link", self.refusal(path))

    def test_generate_refuses_a_constructed_input_before_the_second_is_read(self):
        wrong = self.root / "observations.json"
        wrong.write_bytes(b"{}\n")
        with mock.patch.object(aave_registry, "read_full_record", wraps=aave_registry.read_full_record) as read:
            with self.assertRaises(AlexandriaError) as raised:
                aave_registry.generate(REPO_ROOT, wrong, self.root / "never-read.json")
        self.assertIn("full record observations", str(raised.exception))
        self.assertEqual(read.call_count, 1)

    def test_command_refusal_exits_one_and_writes_nothing(self):
        wrong = self.root / "observations.json"
        wrong.write_bytes(b"{}\n")
        output = self.root / "registry.json"
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr), contextlib.redirect_stdout(io.StringIO()):
            status = aave_registry.main([
                "--observations", str(wrong), "--source-match", str(wrong),
                "--output", str(output), "--repo-root", str(REPO_ROOT),
            ])
        self.assertEqual(status, 1)
        self.assertIn("aave-registry: full record observations does not match", stderr.getvalue())
        self.assertFalse(output.exists())

    def test_generator_imports_no_subprocess_or_network_module(self):
        tree = ast.parse(Path(aave_registry.__file__).read_text(encoding="utf-8"))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                imported.add(node.module.split(".")[0])
        self.assertFalse(imported & {"subprocess", "socket", "urllib", "http", "ssl", "asyncio"})

    def test_derivation_opens_no_socket_and_starts_no_process(self):
        observations, source_match = rebuilt_records()
        refuse = mock.Mock(side_effect=AssertionError("the derivation reached a socket or process"))
        with mock.patch.object(socket, "socket", refuse), mock.patch.object(subprocess, "Popen", refuse):
            aave_registry.derive_registry(row(), observations, source_match)
        refuse.assert_not_called()


class AaveRegistryDerivationTests(unittest.TestCase):
    """Each cross-record check of the derivation refuses by name."""

    def test_rebuilt_records_reproduce_the_committed_registry(self):
        observations, source_match = rebuilt_records()
        derived = aave_registry.derive_registry(row(), observations, source_match)
        self.assertEqual(canonical_bytes(derived), REGISTRY.read_bytes())

    def refuses(self, change, fragment, target="observations"):
        observations, source_match = rebuilt_records()
        merged = row()
        change({"observations": observations, "source_match": source_match, "row": merged}[target])
        with self.assertRaises(AlexandriaError) as raised:
            aave_registry.derive_registry(merged, observations, source_match)
        self.assertIn(fragment, str(raised.exception))

    def test_each_cross_record_refusal(self):
        library = next(a for a, e in entries().items() if e["role"] == "library")
        strategy = next(a for a, e in entries().items() if e["role"] == "interest-rate-strategy")
        cases = [
            ("chain", lambda d: d.update(chain_id=5), "are not Ethereum mainnet", "observations"),
            ("market", lambda d: d["market"].update(pool_proxy=OTHER_POOL), "names another pool_proxy", "observations"),
            ("repeat", lambda d: d["code"].append(dict(d["code"][0])), "repeats", "observations"),
            ("block", lambda d: d["code"][0].update(block_number=1), "not read at the row's observed block", "observations"),
            ("unassigned", lambda d: d["code"].append(dict(d["code"][0], address="0x" + "e" * 40)), "carry no role", "observations"),
            ("outside", lambda d: d["code"].pop(0), "outside the code array", "observations"),
            ("two roles", lambda d: d["reserves"][0]["interest_rate_strategy_epochs"].append({"strategy": library}), "both role", "observations"),
            ("revision role", lambda d: d["implementation_revisions"].update({strategy: {"role": "library"}}), "carries no implementation role", "observations"),
            ("summary", lambda d: d["summary"]["by_role"].update(library=69), "summary counts other roles", "observations"),
            ("derived counts", lambda d: (d["library_links"][POOL].pop(library), d["reserves"][0]["interest_rate_strategy_epochs"].append({"strategy": library})), "derived roles do not match", "observations"),
            ("token tables", lambda d: d["token_proxy_implementation_epochs"].pop(OVERLAP), "do not name exactly the token proxy subjects", "observations"),
            ("set id", lambda d: d["source_sets"][0].update(id="set-x"), "carries no set identifier", "source_match"),
            ("foreign member", lambda d: d["source_sets"][0]["reproduction"]["members"].append("0x" + "e" * 40), "which is not a subject", "source_match"),
            ("two sets", lambda d: d["source_sets"][1]["reproduction"]["members"].append(d["source_sets"][0]["reproduction"]["members"][0]), "member of two source sets", "source_match"),
            ("no set", lambda d: d["source_sets"][0]["reproduction"]["members"].pop(0), "belong to no source set", "source_match"),
            ("periphery", lambda d: d["periphery_not_subjects"].update(extra=library), "periphery overlap is not the reviewed one", "observations"),
            ("asset", lambda d: d["reserves"][0].update(asset=library), "is a subject", "observations"),
            ("unpinned row", lambda d: d["deployment"]["contracts"][0].update(code_keccak256="0x" + "0" * 64), "row aave-v3 does not match its pin", "row"),
        ]
        for name, change, fragment, target in cases:
            with self.subTest(case=name):
                self.refuses(change, fragment, target)

    def test_malformed_epoch_evidence_and_reserve_fields_refuse_by_name(self):
        # S2-R1-01 and S2-R1-02: a missing or non-string `via` was coerced to
        # text, and a reserve without its stable debt token key raised
        # KeyError. Any other exception fails the case rather than erroring,
        # so the unfixed tree reports an assertion.
        for name, change, fragment in (
            ("via absent", lambda d: d["pool_implementation_epochs"][0].pop("via"), "pool_implementation_epochs 0 names no evidence"),
            ("via null", lambda d: next(iter(d["token_proxy_implementation_epochs"].values()))[0].update(via=None), "names no evidence"),
            ("via number", lambda d: d["pool_configurator_implementation_epochs"][0].update(via=7), "names no evidence"),
            ("stable key", lambda d: d["reserves"][0].pop("stable_debt_token"), "reserve 0 carries no stable_debt_token field"),
            ("aToken key", lambda d: d["reserves"][0].pop("a_token"), "reserve 0 carries no a_token field"),
        ):
            with self.subTest(case=name):
                observations, source_match = rebuilt_records()
                change(observations)
                try:
                    aave_registry.derive_registry(row(), observations, source_match)
                except AlexandriaError as error:
                    self.assertIn(fragment, str(error))
                except Exception as error:  # noqa: BLE001 -- the defect under guard
                    self.fail(f"{name} raised {type(error).__name__} rather than a named refusal")
                else:
                    self.fail(f"{name} was accepted")

    def test_every_refusal_is_an_alexandria_error_on_malformed_types(self):
        for name, change, fragment in (
            ("code", lambda d: d.update(code={}), "observations code has an unknown shape"),
            ("market", lambda d: d.update(market=[]), "observations market has an unknown shape"),
            ("reserve", lambda d: d["reserves"].__setitem__(0, "reserve"), "reserve 0 has an unknown shape"),
            ("epoch", lambda d: d["pool_implementation_epochs"].__setitem__(0, 7), "pool_implementation_epochs 0 has an unknown shape"),
            ("creation", lambda d: d["creation"].update({POOL: None}), f"creation of {POOL} has an unknown shape"),
            ("links", lambda d: d["library_links"].update({POOL: ["library"]}), "library links of"),
        ):
            with self.subTest(case=name):
                observations, source_match = rebuilt_records()
                change(observations)
                with self.assertRaises(AlexandriaError) as raised:
                    aave_registry.derive_registry(row(), observations, source_match)
                self.assertIn(fragment, str(raised.exception))


class AaveRowAgreementTests(unittest.TestCase):
    """A registry that disagrees with the merged row refuses, naming the field."""

    def test_each_row_field_disagreement_refuses_by_name(self):
        deployment = lambda d: d["deployment"]  # noqa: E731
        contract = lambda d: d["deployment"]["contracts"][0]  # noqa: E731
        cases = [
            ("market", lambda d: deployment(d)["market"].update(pool=OTHER_POOL), "another market"),
            ("start", lambda d: deployment(d)["start_block"].update(number=1), "start_block is not"),
            ("observed", lambda d: deployment(d)["observed_block"].update(hash="0x" + "0" * 64), "observed_block is not"),
            ("form", lambda d: deployment(d)["full_subject_set"].update(form="x"), "subject-set form"),
            ("count", lambda d: deployment(d)["full_subject_set"].update(count=355), "declares 356 subjects"),
            ("digest", lambda d: deployment(d)["full_subject_set"].update(sha256="0" * 64), "subject set hashes to"),
            ("by role", lambda d: deployment(d)["full_subject_set"]["by_role"].update(library=69), "role counts"),
            ("pins", lambda d: d["full_records"]["observations"].update(bytes=1), "full-record pins"),
            ("absent", lambda d: contract(d).update(address="0x" + "e" * 40), "is not a registry subject"),
            ("role", lambda d: contract(d).update(role="library"), "role"),
            ("length", lambda d: contract(d).update(code_length=1), "code length"),
            ("keccak", lambda d: contract(d).update(code_keccak256="0x" + "0" * 64), "code keccak"),
            ("observed block", lambda d: contract(d).update(observed_block_number=1), "observed block"),
            ("deployment block", lambda d: contract(d)["code_match"].update(deployment_block=1), "deployment block"),
            ("pool epochs", lambda d: next(e for e in d["source"]["deployed_source_epochs"] if e["proxy"] == "Pool").update(to_block=1), "Pool epochs"),
            ("configurator epochs", lambda d: next(e for e in d["source"]["deployed_source_epochs"] if e["proxy"] == "PoolConfigurator").update(transaction="0x" + "0" * 64), "PoolConfigurator epochs"),
        ]
        for name, change, fragment in cases:
            with self.subTest(case=name):
                merged = row()
                change(merged)
                with self.assertRaises(AlexandriaError) as raised:
                    aave_registry.check_row_agreement(registry(), merged)
                self.assertIn(fragment, str(raised.exception))

    def test_full_record_pins_and_row_lookup_refuse_by_name(self):
        for name, change, fragment in (
            ("sha", lambda d: d["full_records"]["source_match"].update(sha256="x"), "pins no SHA-256 for its source_match"),
            ("bytes", lambda d: d["full_records"]["observations"].update(bytes=True), "pins no bounded byte count"),
            ("records", lambda d: d.update(full_records=[]), "full_records has an unknown shape"),
        ):
            with self.subTest(case=name):
                merged = row()
                change(merged)
                with self.assertRaises(AlexandriaError) as raised:
                    aave_registry.full_record_pins(merged)
                self.assertIn(fragment, str(raised.exception))
        for document, fragment in (
            ({}, "carries no target list"),
            ({"targets": []}, "carries no single aave-v3 row"),
            ({"targets": [row(), row()]}, "carries no single aave-v3 row"),
        ):
            with self.subTest(fragment=fragment):
                with self.assertRaises(AlexandriaError) as raised:
                    aave_registry.find_row(document)
                self.assertIn(fragment, str(raised.exception))


class AaveRegistryShapeTests(unittest.TestCase):
    """Each document-only check refuses a constructed registry with one thing changed."""

    def test_each_shape_refusal(self):
        first = lambda d: d["entries"][0]  # noqa: E731
        by_role = lambda d, role: next(e for e in d["entries"] if e["role"] == role)  # noqa: E731
        pool = lambda d: next(e for e in d["entries"] if e["address"] == POOL)  # noqa: E731
        token = lambda d: by_role(d, "aToken-proxy")  # noqa: E731
        cases = [
            ("type", lambda d: d.clear(), "format is unknown"),
            ("format", lambda d: d.update(format="alexandria-wildcat-v2-registry/v1"), "format is unknown"),
            ("fields", lambda d: d.update(extra=1), "unknown shape"),
            ("venue", lambda d: d.update(venue="wildcat-v2"), "another venue or chain"),
            ("chain", lambda d: d.update(chain_id=5), "another venue or chain"),
            ("market", lambda d: d["market"].update(pool=OTHER_POOL), "another market"),
            ("block shape", lambda d: d["start_block"].update(extra=1), "start_block has an unknown shape"),
            ("block hash", lambda d: d["observed_block"].update(hash="0x"), "observed_block hash"),
            ("block order", lambda d: d["start_block"].update(number=d["observed_block"]["number"] + 1), "starts after"),
            ("count", lambda d: d["entries"].pop(), "must contain 356 subjects"),
            ("entry shape", lambda d: first(d).update(extra=1), "entry has an unknown shape"),
            ("address", lambda d: first(d).update(address=first(d)["address"].upper()), "lowercase EVM address"),
            ("order", lambda d: d["entries"].reverse(), "out of order or repeated"),
            ("role", lambda d: first(d).update(role="oracle"), "unknown role"),
            ("keccak", lambda d: first(d).update(code_keccak256="0x"), "code keccak"),
            ("length", lambda d: first(d).update(code_length=-1), "code length"),
            ("created", lambda d: first(d).update(creation_block=True), "creation block"),
            ("created late", lambda d: first(d).update(creation_block=d["observed_block"]["number"] + 1), "created after the observed block"),
            ("created tx", lambda d: first(d).update(creation_transaction=None), "creation transaction"),
            ("source set", lambda d: first(d).update(source_set=1), "names no source set"),
            ("impl on immutable", lambda d: by_role(d, "library").update(implementations=[]), "implementations against its role"),
            ("counts", lambda d: by_role(d, "library").update(role="interest-rate-strategy"), "roles do not match"),
            ("market role", lambda d: (pool(d).update(role="pool-configurator-proxy"), by_role(d, "pool-configurator-proxy").update(role="pool-proxy")), "main market's pool as pool-proxy"),
            ("set shape", lambda d: d["subject_set"].update(extra=1), "subject set has an unknown shape"),
            ("set form", lambda d: d["subject_set"].update(canonical_form="compact-sorted-json"), "another canonical form"),
            ("set counts", lambda d: d["subject_set"].update(count=355), "counts are not the pinned ones"),
            ("set digest", lambda d: d["subject_set"].update(sha256="0" * 64), "subjects hash to"),
            ("epochs bound", lambda d: token(d).update(implementations=[]), "no bounded implementation table"),
            ("epoch shape", lambda d: token(d)["implementations"][0].update(extra=1), "has an unknown shape"),
            ("epoch target", lambda d: token(d)["implementations"][0].update(implementation=POOL), "which is not a aToken-implementation subject"),
            ("epoch open", lambda d: token(d)["implementations"][0].update(from_block=1), "does not open where"),
            ("epoch tx", lambda d: token(d)["implementations"][0].update(transaction="x"), "transaction"),
            ("epoch via", lambda d: token(d)["implementations"][0].update(via=""), "names no evidence"),
            ("epoch closed", lambda d: token(d)["implementations"][-1].update(to_block=1), "last epoch and is closed"),
            ("epoch reversed", lambda d: pool(d)["implementations"][0].update(to_block=0), "closes before it opens"),
            ("impl unnamed", lambda d: pool(d).update(implementations=[dict(pool(d)["implementations"][0], to_block=None)]), "named by no proxy epoch"),
            ("reserves", lambda d: d.update(reserves={}), "reserves have an unknown shape"),
            ("reserve shape", lambda d: d["reserves"][0].update(extra=1), "reserve has an unknown shape"),
            ("reserve order", lambda d: d["reserves"].reverse(), "out of order or repeated"),
            ("reserve asset", lambda d: d["reserves"][0].update(asset=POOL), "is a subject"),
            ("reserve token", lambda d: d["reserves"][0].update(a_token=POOL), "is not a aToken-proxy subject"),
            ("reserve twice", lambda d: d["reserves"][1].update(a_token=d["reserves"][0]["a_token"]), "serves two reserves"),
            ("reserve cover", lambda d: next(r for r in d["reserves"] if r["stable_debt_token"]).update(stable_debt_token=None), "do not name every stableDebtToken-proxy"),
            ("periphery shape", lambda d: d["periphery"].update(extra=1), "periphery has an unknown shape"),
            ("overlap", lambda d: d["periphery"].update(overlap=[]), "overlap is not the reviewed one"),
            ("excluded", lambda d: d["periphery"]["excluded"].reverse(), "not a sorted address list"),
            ("excluded subject", lambda d: d["periphery"].update(excluded=sorted(d["periphery"]["excluded"] + [POOL])), "is a subject"),
            ("source", lambda d: d["source"].update(row_sha256="0" * 64), "source does not name"),
        ]
        for name, change, fragment in cases:
            with self.subTest(case=name):
                document = registry()
                change(document)
                with self.assertRaises(AlexandriaError) as raised:
                    aave_registry.validate_registry(document)
                self.assertIn(fragment, str(raised.exception))

    def test_a_non_mapping_registry_refuses(self):
        for value in (None, [], "registry"):
            with self.assertRaises(AlexandriaError):
                aave_registry.validate_registry(value)


class AaveVenueScopeTests(unittest.TestCase):
    """The registered venue refuses a plan outside the main market, through dispatch."""

    def dispatch(self, document, registry_document=None):
        return usdc_interval.opening_phase(
            document, [], registry=registry() if registry_document is None else registry_document
        )

    def test_the_registry_digest_is_written_in_the_generator_and_nowhere_else(self):
        literal = aave_registry.AAVE_V3_REGISTRY_SHA256
        holders = sorted(
            str(path.relative_to(PLUGIN))
            for path in PLUGIN.rglob("*")
            if path.is_file() and path.suffix in (".py", ".json", ".md")
            and literal in path.read_text(encoding="utf-8", errors="replace")
        )
        self.assertEqual(holders, ["scripts/alexandria_lib/aave_registry.py"])

    def test_the_venue_is_registered_and_reexports_the_pins(self):
        self.assertIs(VENUES["aave-v3"], aave_v3)
        self.assertIs(aave_v3.validate_registry, aave_registry.validate_registry)
        self.assertEqual(aave_v3.AAVE_V3_REGISTRY_SHA256, aave_registry.AAVE_V3_REGISTRY_SHA256)
        self.assertEqual(aave_v3.ROW_PINS, aave_registry.ROW_PINS)
        self.assertNotEqual(aave_v3.EPOCH_MODEL, usdc_interval.EIP1967_MODEL)
        # No interval plan field can carry a registry digest: the plan shape is closed.
        with self.assertRaises(AlexandriaError):
            interval.validate_plan(plan(registry_sha256=aave_registry.AAVE_V3_REGISTRY_SHA256))

    def test_constructed_plan_passes_the_shared_plan_check(self):
        interval.validate_plan(plan())

    def test_wrong_chain_refuses(self):
        with self.assertRaises(AlexandriaError) as raised:
            self.dispatch(plan(chain="eip155:10"))
        self.assertIn("eip155:1", str(raised.exception))
        self.assertIn("eip155:10", str(raised.exception))

    def test_wrong_pool_refuses(self):
        with self.assertRaises(AlexandriaError) as raised:
            self.dispatch(plan([OTHER_POOL, PROVIDER]))
        self.assertIn(f"main market's Pool proxy {POOL}", str(raised.exception))

    def test_wrong_addresses_provider_refuses(self):
        with self.assertRaises(AlexandriaError) as raised:
            self.dispatch(plan([POOL, aave_registry.MARKET["acl_manager"]]))
        self.assertIn(f"main market's AddressesProvider {PROVIDER}", str(raised.exception))

    def test_unlisted_subject_and_missing_or_foreign_registry_refuse(self):
        with self.assertRaises(AlexandriaError) as raised:
            self.dispatch(plan([POOL, PROVIDER, "0x" + "e" * 40]))
        self.assertIn("which the aave-v3 registry does not list", str(raised.exception))
        with self.assertRaises(AlexandriaError) as raised:
            aave_v3.opening_phase(plan(), None, [])
        self.assertIn("none was supplied", str(raised.exception))
        wildcat = json.loads((PLUGIN / "examples" / "wildcat-v2-interval-v0" / "registry.json").read_bytes())
        with self.assertRaises(AlexandriaError) as raised:
            self.dispatch(plan(), wildcat)
        self.assertIn("Aave V3 registry format is unknown", str(raised.exception))
        single = plan()
        del single["subjects"]
        with self.assertRaises(AlexandriaError) as raised:
            aave_v3.opening_phase(single, registry(), [])
        self.assertIn("single-proxy plan names none", str(raised.exception))

    def test_in_scope_plan_reaches_its_opening_phase(self):
        self.assertEqual(aave_v3.validate_plan_scope(plan(), registry()), [POOL, PROVIDER])
        self.assertIsInstance(self.dispatch(plan()), aave_v3.SubjectProxyOpening)
        gaps = aave_v3.evidence_gaps(plan(), registry(), [])
        self.assertEqual(
            gaps[0],
            aave_v3.CONSTRUCTED_STAGING_GAP.format(deployment="aave-v3-constructed", venue="aave-v3"),
        )
        self.assertEqual(len(gaps), 3)


class WildcatRegistriesUnchangedTests(unittest.TestCase):
    """Registering Aave leaves both Wildcat registries and their row pins as they were."""

    def test_wildcat_row_pins_are_unchanged(self):
        self.assertEqual(
            wildcat_registry.ROW_PINS,
            (
                ("wildcat-v2-ethereum-mainnet", "8cd1272ef8e5b790e10228ee041e480d569f6ba7696f9afc3a9dffc80f510317"),
                ("wildcat-v1-ethereum-mainnet", "549f02f46cfdb00769ccf87085d8e49d6272c946643ae31fcd6613f8cd55651a"),
            ),
        )

    def test_wildcat_registries_validate_unchanged(self):
        v2 = PLUGIN / "examples" / "wildcat-v2-interval-v0" / "registry.json"
        v1 = PLUGIN / "examples" / "wildcat-v1-interval-v0" / "registry.json"
        self.assertEqual(wildcat_registry.registry_bytes(REPO_ROOT), v2.read_bytes())
        wildcat_registry.validate_registry(json.loads(v2.read_bytes()))
        wildcat_registry.validate_v1_registry(json.loads(wildcat_registry.registry_v1_bytes(REPO_ROOT)))
        # Each generator still yields the bytes its own module's constant pins;
        # the digests are not restated here, since each is written in one place.
        self.assertEqual(
            hashlib.sha256(wildcat_registry.registry_bytes(REPO_ROOT)).hexdigest(),
            wildcat_registry.WILDCAT_V2_REGISTRY_SHA256,
        )
        self.assertEqual(
            hashlib.sha256(wildcat_registry.registry_v1_bytes(REPO_ROOT)).hexdigest(),
            wildcat_registry.WILDCAT_V1_REGISTRY_SHA256,
        )
        self.assertIs(VENUES["wildcat-v2"].validate_registry, wildcat_registry.validate_registry)
        self.assertEqual(json.loads(v1.read_bytes())["format"], wildcat_registry.V1_REGISTRY_FORMAT)
        for document in (json.loads(v2.read_bytes()), json.loads(wildcat_registry.registry_v1_bytes(REPO_ROOT))):
            with self.assertRaises(AlexandriaError):
                aave_v3.validate_registry(document)


if __name__ == "__main__":
    unittest.main()
