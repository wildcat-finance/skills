"""An Aave V3 plan through collect, reconcile, build and check, over a constructed fixture.

`AaveScopeRefusalTests`, `AaveCollectionRefusalTests`,
`TransactionIndexSpecimenTests` and `AaveCredentialTests` are loaded by name:
the Aave conformance harness resolves `wrong-chain-or-market-refuses`,
`collection-refusal-battery`, `transaction-index-only-disagreement-declared`
and `credential-absent-from-artefacts` against them. Every other case runs the
same constructed path in process.

The fixture, `fixtures/aave-v3-interval-transport.json`, takes its subjects,
roles, creation blocks and recorded implementations from the committed
registry and constructs everything else. The tree records the seven reviewed
proxy codes by keccak-256 alone, so each case admits the keccak-256 of the
fixture's two constructed proxy codes in place of the reviewed table, as
`test_aave_v3_venue.py` does; `test_the_reviewed_table_still_refuses_the_constructed_codes`
shows the unpatched venue refusing them. The build and check invocations run
through `usdc_interval.main` in process for the same reason: a child process
would not carry that substitution. No socket is opened.
"""

import ast
import contextlib
from copy import deepcopy
import io
import json
import os
from pathlib import Path
import socket
import sys
import tempfile
import unittest
from unittest import mock
import urllib.error
import urllib.request

PLUGIN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN / "scripts"))

from alexandria_lib import aave_registry, interval  # noqa: E402
from alexandria_lib.canonical import canonical_bytes  # noqa: E402
from alexandria_lib.errors import AlexandriaError  # noqa: E402
from alexandria_lib.interval import (  # noqa: E402
    IMPLEMENTATION_SLOT,
    OPENING_CLASS,
    SUBJECT_RECEIPT_FORMAT,
    UPGRADED_TOPIC,
    OpeningRefusal,
    log_identity,
)
from alexandria_lib.venues import aave_v3  # noqa: E402
import usdc_interval  # noqa: E402
from usdc_interval import (  # noqa: E402
    BEARER_ENV,
    ENDPOINT_ENV,
    TARGETED_TRACE_GAP,
    Builder,
    Collector,
    HttpsTransport,
    Reconciler,
    check_interval,
)

from tests import test_usdc_interval as existing  # noqa: E402
from tests import test_wildcat_venue as wildcat  # noqa: E402

FIXTURE = PLUGIN / "tests" / "fixtures" / "aave-v3-interval-transport.json"
REGISTRY_PATH = PLUGIN / "examples" / "aave-v3-interval-v0" / "registry.json"
CREATED_AT = "2026-09-23T06:00:00Z"
SECOND_PROVIDER = "second constructed provider, class only"
POOL = aave_registry.MARKET["pool"]
PROVIDER = aave_registry.MARKET["addresses_provider"]
# The variable debt token proxy the registry records as created at block
# 22,824,444, inside the fixture interval, and upgraded at block 22,839,362.
TOKEN = "0x6c82c66622eb360fc973d3f492f9d8e9ea538b08"
POOL_IMPLEMENTATION = "0x947f0054faed3481ff4e76ca35f12fbe36cc665b"
LIBRARY = "0x666835b336a3a5198b2895d94109131d1b23ad11"
# An aToken proxy the registry records as created at block 22,931,583, after
# the fixture interval ends.
LATE = "0x5f4a0873a3a02f7c0cb0e13a1d4362a1ad90e751"
# The token's underlying reserve asset, which is not a subject.
ASSET = "0x1abaea1f7c830bd89acc67ec4af516284b1bc33c"
UPGRADE_BLOCK = 22839362
# The one log alone in its block and transaction, in shard 1.
SPECIMEN_SHARD = "1"
FOREIGN = "0x" + "12" * 20
EVIDENCE_COMPONENTS = ("boundary-blocks", "logs", "traces", OPENING_CLASS)
TOKEN_VALUE = "aave-test-bearer-7c1e9d24b8a3f650"
ENDPOINT = "https://aave-fixture.invalid/rpc-path-with-a-secret"


def fixture():
    if not FIXTURE.is_file():
        raise AssertionError(
            f"the Aave transport fixture is missing at {FIXTURE}; this suite proves the venue "
            "end to end and must fail rather than skip without it"
        )
    return json.loads(FIXTURE.read_text(encoding="utf-8"))["aave-v3"]


def registry():
    """The committed registry, a fresh copy each time so no case edits another's."""
    return json.loads(REGISTRY_PATH.read_bytes())


def word(address):
    return "0x" + "0" * 24 + address[2:]


def admitted_codes(state):
    """The keccak-256 of the fixture's constructed proxy codes, in the reviewed table's shape."""
    return {
        "0x" + aave_v3.keccak256(bytes.fromhex(state["code"][proxy][2:])).hex():
            (len(state["code"][proxy]) // 2 - 1, "constructed")
        for proxy in state["slots"]
    }


class AaveTransport(existing.FixtureTransport):
    """The constructed chain, with each proxy's slot as the registry's table gives it.

    `trace_transaction` also answers the fixture's `unmatched_frames` and
    `logless_frames` for their own transactions, which a blanket
    `trace_filter` fixture never carries.
    """

    def request(self, payload, label):
        envelope = json.loads(payload)
        if envelope["method"] != "eth_getStorageAt" or label in self.faults:
            return super().request(payload, label)
        self.calls.append((envelope["method"], label))
        proxy, slot, tag = envelope["params"]
        if slot != IMPLEMENTATION_SLOT or proxy not in self.state["slots"]:
            raise AssertionError(f"unexpected storage read {envelope['params']}")
        number = int(tag, 16)
        held = [implementation for block, implementation in self.state["slots"][proxy] if block <= number]
        if not held:
            raise AssertionError(f"proxy {proxy} holds no implementation at block {number}")
        return canonical_bytes({"id": envelope["id"], "jsonrpc": "2.0", "result": word(held[-1])})

    def trace_transaction(self, tx_hash):
        extra = self.state["unmatched_frames"] + self.state["logless_frames"]
        return super().trace_transaction(tx_hash) + [
            frame for frame in extra if frame["transactionHash"] == tx_hash
        ]


class SecondLogs(AaveTransport):
    """A second provider whose logs for one shard pass through `edit` first."""

    def __init__(self, state, *, shard, edit, **kwargs):
        super().__init__(state, **kwargs)
        self.shard, self.edit = shard, edit

    def logs(self, shard):
        records = super().logs(shard)
        if str(shard["index"]) == self.shard:
            self.edit(records)
        return records


class _Output(io.StringIO):
    """A stdout stand-in with the `buffer` `main` writes canonical bytes to."""

    def __init__(self):
        super().__init__()
        self.buffer = io.BytesIO()

    def text(self):
        return self.getvalue() + self.buffer.getvalue().decode("utf-8")


class AaveCase(unittest.TestCase):
    """Collect, reconcile, build and check over the constructed Aave fixture."""

    def setUp(self):
        self.state = fixture()
        self.plan = self.state["plan"]
        self.registry = registry()
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.addCleanup(self.directory.cleanup)
        patcher = mock.patch.dict(aave_v3.REVIEWED_PROXY_CODES, admitted_codes(self.state))
        patcher.start()
        self.addCleanup(patcher.stop)

    def scratch(self, name):
        root = self.root / name
        root.mkdir()
        return root

    def staged(self, name="release", state=None, second=None):
        state = state or self.state
        staging = self.scratch(f"{name}-staging")
        self.transport = AaveTransport(state)
        Collector(state["plan"], staging, self.transport, registry=self.registry).collect()
        self.document = Reconciler(
            state["plan"], staging, second or AaveTransport(state), SECOND_PROVIDER,
            registry=self.registry,
        ).reconcile()
        return staging

    def released(self, name="release", state=None, second=None):
        staging = self.staged(name, state, second)
        output = self.root / name
        release_id = Builder(
            (state or self.state)["plan"], staging, self.registry, created_at=CREATED_AT
        ).build(output)
        return output, release_id

    def captures(self, output):
        manifest = json.loads((output / "manifest.json").read_text())
        return {capture["id"]: capture for capture in manifest["captures"]}

    def edit_manifest(self, output, edit):
        path = output / "manifest.json"
        manifest = json.loads(path.read_text())
        edit({capture["id"]: capture for capture in manifest["captures"]})
        path.write_bytes(canonical_bytes(manifest))

    def check_without_verify(self, output):
        release_id = json.loads((output / "manifest.json").read_text())["release_id"]
        with mock.patch.object(usdc_interval, "verify", return_value=release_id):
            return check_interval(output)

    def files(self, plan=None):
        plan_path = self.root / "plan.json"
        registry_path = self.root / "registry.json"
        plan_path.write_bytes(canonical_bytes(plan or self.plan))
        registry_path.write_bytes(REGISTRY_PATH.read_bytes())
        return plan_path, registry_path

    def cli(self, *arguments, transport=None):
        """`usdc_interval.main` in process: the exit code, stdout and stderr."""
        out, err = _Output(), io.StringIO()
        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch.object(sys, "stdout", out))
            stack.enter_context(mock.patch.object(sys, "stderr", err))
            if transport is not None:
                stack.enter_context(mock.patch.object(
                    usdc_interval, "transport_from_environment", return_value=transport,
                ))
            code = usdc_interval.main([str(argument) for argument in arguments])
        return code, out.text(), err.getvalue()

    def build_cli(self, staging, output, plan=None):
        plan_path, registry_path = self.files(plan)
        return self.cli(
            "build", "--plan", plan_path, "--staging", staging, "--registry", registry_path,
            "--created-at", CREATED_AT, "--output", output,
        )

    def collect_cli(self, staging, transport, plan=None):
        plan_path, registry_path = self.files(plan)
        return self.cli(
            "collect", "--plan", plan_path, "--staging", staging, "--registry", registry_path,
            transport=transport,
        )

    def assertNothingInstalled(self, output):
        self.assertFalse(output.exists(), f"{output} was installed")
        self.assertEqual(
            [path.name for path in output.parent.iterdir() if path.name.startswith(f".{output.name}.")],
            [],
        )

    def assertRefused(self, result, fragment):
        code, _stdout, stderr = result
        self.assertEqual(code, 1, stderr)
        self.assertTrue(stderr.rstrip("\n").split("\n")[-1].startswith("usdc-interval: "), stderr)
        self.assertIn(fragment, stderr.rstrip("\n").split("\n")[-1])

    def receipts(self, staging, directory="receipts"):
        path = Path(staging) / directory / "errors.jsonl"
        if not path.is_file():
            return []
        return [json.loads(line) for line in path.read_bytes().splitlines() if line]


class AaveCollectorPathTests(AaveCase):
    """The Step 4 Exit's four-command path over the constructed fixture."""

    def test_collect_reconcile_build_and_check_each_exit_0(self):
        staging = self.scratch("cli-staging")
        plan_path, registry_path = self.files()
        code, stdout, stderr = self.cli(
            "collect", "--plan", plan_path, "--staging", staging, "--registry", registry_path,
            transport=AaveTransport(self.state),
        )
        self.assertEqual(code, 0, stderr)
        summary = json.loads(stdout)
        self.assertEqual(summary["record_counts"], {"boundary-blocks": 4, "logs": 11, "traces": 7})
        self.assertEqual(summary["opening_reads"], {"issued": 15, "resumed_from": 0, "total": 15})
        code, stdout, stderr = self.cli(
            "reconcile", "--plan", plan_path, "--staging", staging, "--registry", registry_path,
            "--provider-class", SECOND_PROVIDER, transport=AaveTransport(self.state),
        )
        self.assertEqual(code, 0, stderr)
        record = json.loads(stdout)["reconciliation"]
        # 4 boundary hashes, 4 transaction orders, 11 log identities, 7 trace
        # identities and 14 opening reads: the one epoch-boundary header is
        # bound by the upgrade logs and not asked again.
        self.assertEqual((record["status"], record["compared"], record["matched"]), ("agreed", 40, 40))
        output = self.root / "cli-release"
        code, stdout, stderr = self.build_cli(staging, output)
        self.assertEqual(code, 0, stderr)
        self.assertRegex(stdout, r"\Asha256:[0-9a-f]{64}\n\Z")
        release_id = stdout.strip()
        code, stdout, stderr = self.cli("check", output)
        self.assertEqual(code, 0, stderr)
        summary = json.loads(stdout)
        self.assertEqual(summary["release_id"], release_id)
        self.assertEqual(summary["receipt_semantics"], "v3-subject-positional")
        self.assertEqual(summary["reconciliation"], "agreed")
        self.assertEqual(summary["shard_statuses"], {"complete": 4})
        self.assertEqual(summary["epochs"], 7)
        # The same bytes build to the same identifier again.
        again = self.root / "cli-release-again"
        self.assertEqual(self.build_cli(staging, again)[1].strip(), release_id)

    def test_the_epoch_table_carries_proxy_and_immutable_subjects(self):
        output, _release_id = self.released()
        receipt = existing.component_document(output, "epoch-table")
        self.assertEqual(receipt["format"], SUBJECT_RECEIPT_FORMAT)
        self.assertEqual(receipt["first_code"], [])
        table = interval.subject_epoch_table(receipt["epochs"])
        start, end = self.plan["interval"]["start"], self.plan["interval"]["end"]
        entries = aave_registry.subject_entries(self.registry)
        self.assertEqual(sorted(table), sorted(set(self.plan["subjects"]) - {LATE}))
        spans = {
            subject: [
                (epoch["start_block"], epoch["start_position"]["transaction_index"],
                 epoch["start_position"]["log_index"], epoch["implementation"], epoch["end_block"])
                for epoch in epochs
            ]
            for subject, epochs in table.items()
        }
        pool_before = next(
            item["implementation"] for item in entries[POOL]["implementations"]
            if item["to_block"] == UPGRADE_BLOCK - 1
        )
        token_first = entries[TOKEN]["implementations"][0]["implementation"]
        token_next = entries[TOKEN]["implementations"][1]["implementation"]
        creation = str(entries[TOKEN]["creation_block"])
        self.assertEqual(spans, {
            POOL: [(start, None, None, pool_before, str(UPGRADE_BLOCK)),
                   (str(UPGRADE_BLOCK), 7, 31, POOL_IMPLEMENTATION, end)],
            PROVIDER: [(start, None, None, PROVIDER, end)],
            TOKEN: [(creation, None, None, token_first, str(UPGRADE_BLOCK)),
                    (str(UPGRADE_BLOCK), 7, 33, token_next, end)],
            POOL_IMPLEMENTATION: [(start, None, None, POOL_IMPLEMENTATION, end)],
            LIBRARY: [(start, None, None, LIBRARY, end)],
        })

    def test_ordinary_logs_on_both_sides_of_upgraded_are_owned_by_position(self):
        output, _release_id = self.released()
        receipt = existing.component_document(output, "epoch-table")
        rows = [
            (row["subject"], row["log_index"], row["kind"], row["epoch_index"])
            for row in receipt["log_attributions"]
            if row["block_number"] == str(UPGRADE_BLOCK)
        ]
        self.assertEqual(rows, [
            (POOL, 30, "proxy-log", 0),
            (POOL, 31, "upgrade-boundary", 1),
            (TOKEN, 32, "proxy-log", 0),
            (TOKEN, 33, "upgrade-boundary", 1),
            (TOKEN, 34, "proxy-log", 1),
            (POOL, 35, "proxy-log", 1),
        ])

    def test_each_call_site_reads_the_order_rule_from_the_venue_module(self):
        # With the collector's reading of the venue flag forced off, the same
        # fixture refuses at reconcile, at build and at check: the three
        # call sites are what admit its upgrade transaction.
        output, _release_id = self.released()
        staging = self.root / "release-staging"
        collected = self.scratch("unreconciled-staging")
        Collector(self.plan, collected, AaveTransport(self.state), registry=self.registry).collect()
        refused = "in an upgrade transaction is unsupported"
        with mock.patch.object(usdc_interval, "upgrade_transaction_order", return_value=False):
            with self.assertRaisesRegex(AlexandriaError, refused):
                Builder(self.plan, staging, self.registry, created_at=CREATED_AT).build(self.root / "off")
            self.assertNothingInstalled(self.root / "off")
            with self.assertRaisesRegex(AlexandriaError, refused):
                self.check_without_verify(output)
            document = Reconciler(
                self.plan, collected, AaveTransport(self.state), SECOND_PROVIDER, registry=self.registry,
            ).reconcile()
        self.assertEqual(document["reconciliation"]["status"], "unreconciled")
        receipt = self.receipts(collected, "reconciliation")[-1]
        self.assertEqual((receipt["shard"], receipt["class"]), (3, "second-provider"))
        self.assertIn(refused, receipt["message"])
        self.assertIs(usdc_interval.upgrade_transaction_order(aave_v3), True)
        for venue in usdc_interval.VENUES.values():
            if venue is not aave_v3:
                with self.subTest(venue=venue.VENUE):
                    self.assertIs(usdc_interval.upgrade_transaction_order(venue), False)

    def test_the_call_sites_pass_the_flag_the_venue_module_sets(self):
        tree = ast.parse((PLUGIN / "scripts" / "usdc_interval.py").read_text(encoding="utf-8"))
        values = [
            keyword.value for node in ast.walk(tree) if isinstance(node, ast.Call)
            for keyword in node.keywords if keyword.arg == "order_upgrade_transactions"
        ]
        self.assertEqual(len(values), 4)
        for value in values:
            with self.subTest(value=ast.unparse(value)):
                self.assertIsInstance(value, ast.Call)
                self.assertEqual(ast.unparse(value.func), "upgrade_transaction_order")
                self.assertEqual(len(value.args), 1)
        callers = {
            ast.unparse(node.func) for node in ast.walk(tree) if isinstance(node, ast.Call)
            and any(keyword.arg == "order_upgrade_transactions" for keyword in node.keywords)
        }
        self.assertEqual(callers, {"proxy_log_positions", "attribute_logs"})

    def test_every_capture_carries_the_field_names_a_wildcat_release_carries(self):
        def paths(value, prefix=()):
            if isinstance(value, dict):
                found = set()
                for key, item in value.items():
                    found.add(prefix + (key,))
                    found |= paths(item, prefix + (key,))
                return found
            if isinstance(value, list):
                found = set()
                for item in value:
                    found |= paths(item, prefix + ("[]",))
                return found
            return set()

        output, _release_id = self.released()
        wildcat_state = wildcat.fixture(wildcat.wildcat_v1.VENUE)
        wildcat_registry = wildcat.v1_registry()
        staging = self.scratch("wildcat-staging")
        Collector(
            wildcat_state["plan"], staging, wildcat.WildcatTransport(wildcat_state),
            registry=wildcat_registry,
        ).collect()
        Reconciler(
            wildcat_state["plan"], staging, wildcat.WildcatTransport(wildcat_state), SECOND_PROVIDER,
            registry=wildcat_registry,
        ).reconcile()
        wildcat_output = self.root / "wildcat-release"
        Builder(wildcat_state["plan"], staging, wildcat_registry, created_at=CREATED_AT).build(wildcat_output)
        ours, theirs = self.captures(output), self.captures(wildcat_output)
        self.assertEqual(sorted(ours), sorted(theirs))
        for name in sorted(ours):
            with self.subTest(component=name):
                self.assertEqual(paths(ours[name]), paths(theirs[name]))
                self.assertEqual(ours[name]["venue"], "aave-v3")

    def test_the_constructed_staging_gap_is_on_every_evidence_scope(self):
        self.assertEqual(aave_v3.PRESERVED_DEPLOYMENTS, frozenset())
        output, _release_id = self.released()
        gap = aave_v3.CONSTRUCTED_STAGING_GAP.format(deployment=self.plan["deployment"], venue="aave-v3")
        self.assertIn(self.plan["deployment"], gap)
        holders = sorted(
            name for name, capture in self.captures(output).items() if gap in capture["coverage"]["gaps"]
        )
        self.assertEqual(holders, sorted(EVIDENCE_COMPONENTS))
        for name in EVIDENCE_COMPONENTS:
            with self.subTest(component=name):
                capture = self.captures(output)[name]
                self.assertEqual(capture["coverage"]["gaps"].count(gap), 1)
                self.assertEqual(capture["coverage"]["status"], "partial")
        self.edit_manifest(output, lambda captures: captures["logs"]["coverage"]["gaps"].remove(gap))
        with self.assertRaisesRegex(AlexandriaError, "the logs coverage does not name a gap its venue owes"):
            self.check_without_verify(output)

    def test_the_reviewed_table_still_refuses_the_constructed_codes(self):
        staging = self.staged("unreviewed")
        with mock.patch.dict(aave_v3.REVIEWED_PROXY_CODES, aave_v3_reviewed(), clear=True):
            self.assertEqual(len(aave_v3.REVIEWED_PROXY_CODES), 7)
            with self.assertRaises(aave_v3.EpochRefusal) as raised:
                Builder(self.plan, staging, self.registry, created_at=CREATED_AT).build(self.root / "x")
        self.assertEqual(raised.exception.rule, aave_v3.RULE_UNREVIEWED_PROXY_CODE)
        self.assertEqual(raised.exception.subject, POOL)

    def test_the_comparison_tuple_is_unchanged(self):
        record = self.state["logs"]["0"][0]
        base = log_identity(record)
        self.assertEqual(base.count("|"), 5)
        for field, value in (
            ("blockHash", "0x" + "01" * 32), ("transactionHash", "0x" + "02" * 32),
            ("logIndex", "0x63"), ("address", FOREIGN), ("topics", ["0x" + "03" * 32]),
            ("data", "0x04"),
        ):
            with self.subTest(field=field):
                self.assertNotEqual(log_identity(dict(record, **{field: value})), base)
        for field, value in (("transactionIndex", "0x63"), ("blockNumber", "0x1"), ("removed", True)):
            with self.subTest(field=field):
                self.assertEqual(log_identity(dict(record, **{field: value})), base)


def aave_v3_reviewed():
    """The reviewed table as the module ships it, read from its source, not from the patched dict."""
    tree = ast.parse(Path(aave_v3.__file__).read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "REVIEWED_PROXY_CODES" for target in node.targets
        ):
            return ast.literal_eval(node.value)
    raise AssertionError("aave_v3.py assigns no REVIEWED_PROXY_CODES")


class AaveScopeRefusalTests(AaveCase):
    """A plan outside the ruled main market refuses at every command, before any request."""

    def refuses_everywhere(self, plan, fragment, checked):
        transport = AaveTransport(self.state)
        with self.assertRaisesRegex(AlexandriaError, fragment):
            Collector(plan, self.scratch("scope-refused"), transport, registry=self.registry)
        self.assertEqual(transport.calls, [])
        with self.assertRaisesRegex(AlexandriaError, fragment):
            Reconciler(plan, self.root / "scope-refused", transport, SECOND_PROVIDER, registry=self.registry)
        self.assertEqual(transport.calls, [])
        staging = self.staged("scope")
        output = self.root / "scope-release"
        self.assertRefused(self.build_cli(staging, output, plan), fragment)
        self.assertNothingInstalled(output)
        # A main-market release whose plan component is swapped for this one
        # does not check: its receipt's epochs no longer belong to that plan.
        good, _release_id = self.released("scope-good")
        existing.component_path(good, "interval-plan").write_bytes(canonical_bytes(plan))
        with self.assertRaises(AlexandriaError) as raised:
            self.check_without_verify(good)
        self.assertEqual(str(raised.exception), checked)

    def test_wrong_chain_refuses(self):
        plan = deepcopy(self.plan)
        plan["chain"] = "eip155:10"
        self.refuses_everywhere(
            plan, "captures the Ethereum main market on eip155:1; the plan names chain 'eip155:10'",
            "an epoch does not belong to the plan's market",
        )

    def test_wrong_market_refuses(self):
        # The main market's Pool replaced by another registry subject: the
        # plan is refused as the wrong market, not as a stray subject.
        plan = deepcopy(self.plan)
        plan["subjects"][plan["subjects"].index(POOL)] = aave_registry.MARKET["acl_manager"]
        self.refuses_everywhere(
            plan, f"does not declare the main market's Pool proxy {POOL}",
            "epoch table names an undeclared subject",
        )
        plan = deepcopy(self.plan)
        plan["subjects"].remove(PROVIDER)
        transport = AaveTransport(self.state)
        with self.assertRaisesRegex(AlexandriaError, f"main market's AddressesProvider {PROVIDER}"):
            Collector(plan, self.scratch("provider-staging"), transport, registry=self.registry)
        self.assertEqual(transport.calls, [])


class AaveCollectionRefusalTests(AaveCase):
    """The refusal battery: each fail-closed path, and what it leaves behind."""

    def test_foreign_emitter_refuses(self):
        state = deepcopy(self.state)
        state["logs"]["1"][0]["address"] = FOREIGN
        staging = self.scratch("foreign-staging")
        self.assertRefused(
            self.collect_cli(staging, AaveTransport(state)), "not emitted by a declared subject"
        )
        self.assertEqual([receipt["code"] for receipt in self.receipts(staging)], ["malformed-staged-log"])
        self.assertEqual(existing.opening_entries(staging), [])
        output = self.root / "foreign-release"
        self.assertRefused(self.build_cli(staging, output), "no committed epoch-evidence journal")
        self.assertNothingInstalled(output)

    def test_incomplete_page_refuses(self):
        # Shard 3's own answer holds exactly as many logs as the plan's page
        # limit, so it may be a truncated page and is refused as one.
        plan = deepcopy(self.plan)
        plan["provider"]["page_limit"] = len(self.state["logs"]["3"])
        state = dict(self.state, plan=plan)
        staging = self.scratch("page-staging")
        self.assertRefused(self.collect_cli(staging, AaveTransport(state), plan), "provider's limit")
        self.assertEqual([receipt["code"] for receipt in self.receipts(staging)], ["page-limit"])
        self.assertEqual(json.loads((staging / "checkpoint.json").read_text())["next_shard"], 3)
        output = self.root / "page-release"
        self.assertRefused(self.build_cli(staging, output, plan), "not completely collected")
        self.assertNothingInstalled(output)

    def test_missing_journal_refuses(self):
        staging = self.staged("missing")
        (staging / "journals" / "logs.jsonl").unlink()
        output = self.root / "missing-release"
        self.assertRefused(
            self.build_cli(staging, output), "the logs journal is shorter than its committed offset",
        )
        self.assertNothingInstalled(output)

    def test_corrupt_journal_refuses(self):
        staging = self.staged("corrupt")
        path = staging / "journals" / "logs.jsonl"
        data = path.read_bytes()
        path.write_bytes(data.replace(b'"', b"'", 1))
        self.assertEqual(len(path.read_bytes()), len(data))
        output = self.root / "corrupt-release"
        self.assertRefused(self.build_cli(staging, output), "journal logs entry is not valid JSON")
        self.assertNothingInstalled(output)

    def test_provider_failure_records_a_receipt(self):
        def fail(_envelope):
            raise usdc_interval.TransportError("shard 2 logs second provider transport failed")

        staging = self.scratch("failure-staging")
        Collector(self.plan, staging, AaveTransport(self.state), registry=self.registry).collect()
        second = AaveTransport(self.state, faults={"shard 2 logs second provider": fail})
        document = Reconciler(
            self.plan, staging, second, SECOND_PROVIDER, registry=self.registry,
        ).reconcile()
        record = document["reconciliation"]
        self.assertEqual(record["status"], "unreconciled")
        self.assertEqual(record["provider_class"], SECOND_PROVIDER)
        receipts = self.receipts(staging, "reconciliation")
        self.assertEqual(receipts, [{
            "class": "second-provider",
            "exception": "TransportError",
            "message": "shard 2 logs second provider transport failed",
            "provider_class": SECOND_PROVIDER,
            "shard": 2,
        }])
        output = self.root / "failure-release"
        Builder(self.plan, staging, self.registry, created_at=CREATED_AT).build(output)
        self.assertEqual(check_interval(output)["reconciliation"], "unreconciled")
        for name in EVIDENCE_COMPONENTS:
            with self.subTest(component=name):
                self.assertIn(
                    "the interval was not reconciled against a second provider",
                    self.captures(output)[name]["coverage"]["gaps"],
                )

    def test_provider_disagreement_is_disputed(self):
        def edit(records):
            records[0]["data"] = "0x" + "cd" * 32

        second = SecondLogs(self.state, shard=SPECIMEN_SHARD, edit=edit)
        staging = self.staged("disputed", second=second)
        record = self.document["reconciliation"]
        self.assertEqual(record["status"], "disputed")
        self.assertEqual(
            [(item["kind"], item["shard"]) for item in record["disputed"]],
            [("log-identity", 1), ("log-identity", 1)],
        )
        self.assertEqual(
            [shard["status"] for shard in self.document["shards"]],
            ["complete", "partial", "complete", "complete"],
        )
        kept = [
            json.loads(line)
            for line in (staging / "reconciliation" / "disputed.jsonl").read_bytes().splitlines()
        ]
        self.assertEqual([(item["class"], item["shard"]) for item in kept], [("logs", 1)])
        second_records = json.loads(kept[0]["response"])["result"]
        self.assertEqual(second_records[0]["data"], "0x" + "cd" * 32)
        # The primary's bytes stay in the staging journal, unchanged.
        primary = [
            json.loads(json.loads(line)["response"])["result"]
            for line in (staging / "journals" / "logs.jsonl").read_bytes().splitlines()
            if json.loads(line)["shard"] == 1
        ]
        self.assertEqual(primary, [self.state["logs"][SPECIMEN_SHARD]])
        output = self.root / "disputed"
        Builder(self.plan, staging, self.registry, created_at=CREATED_AT).build(output)
        summary = check_interval(output)
        self.assertEqual(summary["reconciliation"], "disputed")
        self.assertEqual(summary["shard_statuses"], {"complete": 3, "partial": 1})

    def test_interrupted_resume_is_byte_identical(self):
        clean = self.scratch("clean")
        Collector(self.plan, clean, AaveTransport(self.state), registry=self.registry).collect()
        expected = existing.journal_files(clean)
        self.assertEqual(len(existing.opening_entries(clean)), 15)
        for kill_at in (
            "shard 2 boundary-blocks",
            f"shard 3 traces {self.state['logs']['3'][0]['transactionHash']}",
            "opening read 3 implementation-slot block 22824001",
            "opening read 9 implementation-code block 22824001",
        ):
            with self.subTest(kill_at=kill_at):
                root = self.scratch("resumed-" + kill_at.replace(" ", "-")[:40])
                with self.assertRaises(existing._Killed):
                    Collector(
                        self.plan, root, existing_killing(self.state, kill_at), registry=self.registry,
                    ).collect()
                self.assertNotEqual(existing.journal_files(root), expected)
                Collector(self.plan, root, AaveTransport(self.state), registry=self.registry).collect()
                self.assertEqual(existing.journal_files(root), expected)

    def test_changed_boundary_hash_refuses(self):
        # Within the checkpoint's trail a changed boundary rewinds and
        # re-collects; below it the collection refuses and nothing builds.
        def interrupted(name):
            root = self.scratch(name)
            with self.assertRaises(existing._Killed):
                Collector(
                    self.plan, root, existing_killing(self.state, "shard 3 boundary-blocks"),
                    registry=self.registry,
                ).collect()
            return root

        root = interrupted("rewound")
        moved = self.plan["shards"][1]["end"]
        summary = Collector(
            self.plan, root, AaveTransport(self.state, reorg_from=moved), registry=self.registry,
        ).collect()
        self.assertEqual(summary["resumed_from"], 1)
        with mock.patch("alexandria_lib.interval.MAX_HISTORY", 2):
            root = interrupted("too-deep")
            history = json.loads((root / "checkpoint.json").read_text())["history"]
            self.assertEqual([entry["shard"] for entry in history], [1, 2])
            moved = self.plan["shards"][0]["end"]
            self.assertRefused(
                self.collect_cli(root, AaveTransport(self.state, reorg_from=moved)),
                "the reorg is deeper than the checkpoint's rewind history",
            )
        output = self.root / "too-deep-release"
        self.assertRefused(self.build_cli(root, output), "not completely collected")
        self.assertNothingInstalled(output)


def existing_killing(state, kill_at):
    """An Aave transport that stops at one request label, the way a killed process would."""

    class Killing(AaveTransport):
        def request(self, payload, label):
            if label == kill_at:
                raise existing._Killed(label)
            return super().request(payload, label)

    return Killing(state)


class TransactionIndexSpecimenTests(AaveCase):
    """Agreement over logs excludes transactionIndex, and the release says so."""

    def test_index_only_difference_still_records_agreed(self):
        def shifted(records):
            self.assertEqual(len(records), 1)
            records[0]["transactionIndex"] = "0x5"

        self.staged("clean")
        agreed = self.document["reconciliation"]
        second = SecondLogs(self.state, shard=SPECIMEN_SHARD, edit=shifted)
        self.staged("shifted", second=second)
        record = self.document["reconciliation"]
        self.assertEqual(record["status"], "agreed")
        self.assertEqual(record["disputed"], [])
        self.assertEqual((record["compared"], record["matched"]), (agreed["compared"], agreed["matched"]))
        self.assertFalse((self.root / "shifted-staging" / "reconciliation" / "disputed.jsonl").exists())
        # The specimen differs in that one field alone.
        primary = self.state["logs"][SPECIMEN_SHARD][0]
        answered = second.logs(self.plan["shards"][1])[0]
        self.assertEqual(
            sorted(key for key in primary if primary[key] != answered[key]), ["transactionIndex"],
        )

    def test_release_declares_the_positional_verification_limit(self):
        output, _release_id = self.released()
        limit = aave_v3.POSITIONAL_VERIFICATION_LIMIT
        self.assertTrue(limit.startswith("provider agreement over logs excludes transactionIndex"))
        self.assertIn("transaction-index-reconciliation", limit)
        captures = self.captures(output)
        self.assertEqual(
            sorted(name for name, capture in captures.items() if limit in capture["coverage"]["gaps"]),
            sorted(EVIDENCE_COMPONENTS),
        )
        for name in EVIDENCE_COMPONENTS:
            with self.subTest(component=name):
                self.assertEqual(captures[name]["coverage"]["gaps"].count(limit), 1)
        self.assertEqual(self.check_without_verify(output)["reconciliation"], "agreed")

    def test_check_refuses_a_release_without_the_limit(self):
        output, _release_id = self.released()
        limit = aave_v3.POSITIONAL_VERIFICATION_LIMIT
        pristine = (output / "manifest.json").read_bytes()
        for name in EVIDENCE_COMPONENTS:
            with self.subTest(component=name):
                (output / "manifest.json").write_bytes(pristine)
                self.edit_manifest(output, lambda captures: captures[name]["coverage"]["gaps"].remove(limit))
                with self.assertRaises(AlexandriaError) as raised:
                    self.check_without_verify(output)
                self.assertEqual(
                    str(raised.exception),
                    f"the {name} coverage does not declare the positional verification limit the "
                    "aave-v3 venue owes: provider agreement over logs excludes transactionIndex",
                )


class AaveCredentialTests(AaveCase):
    """No bearer value or endpoint reaches a journal, component, receipt or error string."""

    def test_bearer_credential_absent_from_every_artefact(self):
        # The credential reaches the transport through the injected mapping
        # alone; the process environment does not hold it.
        self.assertNotIn(TOKEN_VALUE, "".join(os.environ.values()))
        backing = AaveTransport(self.state)
        sent = []

        def answer(_opener, request, timeout=None):
            sent.append(dict(request.header_items()).get("Authorization"))
            return _Response(backing.request(request.data, "credential-walk"))

        staging = self.scratch("credential-staging")
        with mock.patch.object(urllib.request.OpenerDirector, "open", answer), mock.patch.object(
            socket.socket, "connect", side_effect=AssertionError("network used"),
        ):
            transport = HttpsTransport.from_environment(
                self.plan["provider"]["timeout_seconds"],
                {ENDPOINT_ENV: ENDPOINT, BEARER_ENV: TOKEN_VALUE},
            )
            Collector(self.plan, staging, transport, registry=self.registry).collect()
            Reconciler(
                self.plan, staging, transport, SECOND_PROVIDER, registry=self.registry,
            ).reconcile()
        # The credential was in play on every request, so its absence below
        # is not an absence of the credential from the run.
        self.assertTrue(sent)
        self.assertEqual(set(sent), {f"Bearer {TOKEN_VALUE}"})
        output = self.root / "credential-release"
        Builder(self.plan, staging, self.registry, created_at=CREATED_AT).build(output)
        check_interval(output)
        host = ENDPOINT.split("/")[2]
        checked = 0
        for root in (staging, output):
            for path in sorted(Path(root).rglob("*")):
                if not path.is_file():
                    continue
                content = path.read_bytes()
                for secret in (TOKEN_VALUE, ENDPOINT, host):
                    self.assertNotIn(secret.encode(), content, f"{path} carries {secret}")
                checked += 1
        self.assertGreaterEqual(checked, 10)

    def test_transport_error_text_names_no_endpoint(self):
        host = ENDPOINT.split("/")[2]
        failures = {
            "an HTTP status": lambda: _Response(b"", status=502),
            "a transport error naming the endpoint": lambda: (_ for _ in ()).throw(
                urllib.error.URLError(f"POST {ENDPOINT} with Bearer {TOKEN_VALUE} was reset")
            ),
            "a bare error naming the endpoint": lambda: (_ for _ in ()).throw(
                TimeoutError(f"{ENDPOINT} timed out for {TOKEN_VALUE}")
            ),
        }
        for label, failure in failures.items():
            with self.subTest(failure=label):
                backing = AaveTransport(self.state)

                def answer(_opener, request, timeout=None):
                    payload = json.loads(request.data)
                    if payload["method"] == "eth_getStorageAt":
                        return failure()
                    return _Response(backing.request(request.data, "error-text"))

                staging = self.scratch("error-" + label.replace(" ", "-"))
                with mock.patch.object(urllib.request.OpenerDirector, "open", answer), mock.patch.object(
                    socket.socket, "connect", side_effect=AssertionError("network used"),
                ):
                    transport = HttpsTransport.from_environment(
                        self.plan["provider"]["timeout_seconds"],
                        {ENDPOINT_ENV: ENDPOINT, BEARER_ENV: TOKEN_VALUE},
                    )
                    with self.assertRaises(AlexandriaError) as raised:
                        Collector(self.plan, staging, transport, registry=self.registry).collect()
                message = str(raised.exception)
                self.assertTrue(message.startswith("opening read 3 implementation-slot block 22824001"), message)
                receipts = (staging / "receipts" / "errors.jsonl").read_text()
                self.assertTrue(receipts)
                for text in (message, receipts):
                    for secret in (TOKEN_VALUE, ENDPOINT, host):
                        self.assertNotIn(secret, text)


class _Response:
    def __init__(self, body, status=200):
        self._body = body
        self.status = status

    def read(self, limit):
        return self._body[:limit]

    def __enter__(self):
        return self

    def __exit__(self, *_exception):
        return False


class AaveOpeningReadTests(AaveCase):
    """The opening reads the venue plans, and each answer it will not believe."""

    def phase(self, logs=None):
        return aave_v3.opening_phase(self.plan, self.registry, self.all_logs() if logs is None else logs)

    def all_logs(self):
        return [record for shard in sorted(self.state["logs"], key=int) for record in self.state["logs"][shard]]

    def accept_all(self, phase, answers=None):
        transport = AaveTransport(self.state)
        for position, read in enumerate(phase.reads()):
            envelope = json.loads(transport.request(
                usdc_interval.opening_request(self.plan, position, read), "opening",
            ))
            result = (answers or {}).get((read["kind"], read["block"]), envelope["result"])
            phase.accept(read, result)
        return phase

    def test_the_reads_follow_the_plan_in_a_fixed_order(self):
        creation = aave_registry.subject_entries(self.registry)[TOKEN]["creation_block"]
        start = int(self.plan["interval"]["start"])
        phase = self.accept_all(self.phase())
        reads = [(read["kind"], read.get("address"), read["block"]) for read in phase.reads()]
        self.assertEqual(reads[:7], [
            ("first-block-header", None, start),
            ("subject-first-block-header", None, creation),
            ("epoch-boundary-header", None, UPGRADE_BLOCK),
            ("implementation-slot", POOL, start),
            ("implementation-slot", POOL, UPGRADE_BLOCK),
            ("implementation-slot", TOKEN, creation),
            ("implementation-slot", TOKEN, UPGRADE_BLOCK),
        ])
        codes = [(address, block) for kind, address, block in reads[7:]]
        self.assertTrue(all(kind == "implementation-code" for kind, _a, _b in reads[7:]))
        entries = aave_registry.subject_entries(self.registry)
        self.assertEqual(codes, [
            (POOL, start),
            (next(i["implementation"] for i in entries[POOL]["implementations"] if i["to_block"] == UPGRADE_BLOCK - 1), start),
            (POOL_IMPLEMENTATION, start),
            (PROVIDER, start),
            (TOKEN, creation),
            (entries[TOKEN]["implementations"][0]["implementation"], creation),
            (entries[TOKEN]["implementations"][1]["implementation"], UPGRADE_BLOCK),
            (LIBRARY, start),
        ])
        self.assertEqual(phase.first_code_rows(), [])
        self.assertEqual(sorted(phase.epochs(existing.FixtureTransport(self.state)._hash(phase.end))), sorted(
            set(self.plan["subjects"]) - {LATE}
        ))

    def test_code_reads_are_not_drawn_before_every_slot_is_accepted(self):
        phase = self.phase()
        reads = phase.reads()
        for _ in range(7):
            next(reads)
        with self.assertRaisesRegex(AlexandriaError, f"slot of proxy subject {POOL} at block 22824001 was not accepted"):
            next(reads)

    def refusal(self, kind, block, answer):
        with self.assertRaises(OpeningRefusal) as raised:
            self.accept_all(self.phase(), {(kind, block): answer})
        return raised.exception

    def test_each_malformed_answer_refuses_by_its_receipt_code(self):
        start = int(self.plan["interval"]["start"])
        cases = (
            ("first-block-header", start, {"number": hex(start)}, "malformed-header", "carries no hash"),
            ("first-block-header", start, {"hash": "0x" + "ab" * 32, "number": hex(start + 1)},
             "malformed-header", "carries another block number"),
            ("epoch-boundary-header", UPGRADE_BLOCK, {"hash": "0x" + "ab" * 32, "number": hex(UPGRADE_BLOCK)},
             "upgrade-log-mismatch", "names a different block hash"),
            ("implementation-slot", start, "0x" + "ff" * 32, "slot-not-an-address", "not a left-padded address"),
            ("implementation-slot", start, "0x" + "00" * 32, "slot-not-an-address", "is the zero address"),
            ("implementation-code", start, "0x", "no-code-at-recorded-block", "has no runtime code at block"),
            ("implementation-code", start, "0xzz", "code-not-hex", "runtime code is not hexadecimal"),
        )
        for kind, block, answer, code, fragment in cases:
            with self.subTest(kind=kind, code=code, fragment=fragment):
                error = self.refusal(kind, block, answer)
                self.assertEqual((error.code, error.block), (code, block))
                self.assertIn(fragment, str(error))

    def test_an_unknown_read_kind_is_refused(self):
        phase = self.phase()
        with self.assertRaisesRegex(AlexandriaError, "unknown opening read kind 'other'"):
            phase.accept({"block": 1, "kind": "other"}, None)
        with self.assertRaisesRegex(AlexandriaError, "opening read kind 'other' is not compared"):
            phase.compare({"block": 1, "kind": "other"}, None, None)
        with self.assertRaisesRegex(AlexandriaError, "opening read kind 'epoch-boundary-header' is not compared"):
            phase.compare({"block": 1, "kind": "epoch-boundary-header"}, None, None)

    def test_the_second_provider_is_compared_by_kind(self):
        phase = self.accept_all(self.phase())
        start = int(self.plan["interval"]["start"])
        header = {"block": start, "kind": "first-block-header"}
        value = phase.hashes[start]
        self.assertEqual(phase.compare(header, value, {"hash": value, "number": hex(start)}),
                         (True, "first-block-hash", f"block {start}"))
        self.assertEqual(phase.compare(header, value, {"hash": value, "number": hex(start + 1)})[0], False)
        slot = {"address": POOL, "block": start, "kind": "implementation-slot"}
        held = interval.slot_word_address(phase.slot_words[(POOL, start)], start)
        self.assertEqual(phase.compare(slot, held, word(held)),
                         (True, "slot-word", f"implementation slot of {POOL} at block {start}"))
        self.assertEqual(phase.compare(slot, held, "0xnot-a-word")[0], False)
        code = {"address": LIBRARY, "block": start, "kind": "implementation-code"}
        digest = phase.code_digests[(LIBRARY, start)]
        self.assertEqual(phase.compare(code, digest, self.state["code"][LIBRARY]),
                         (True, "code-digest", f"code of {LIBRARY} at block {start}"))
        self.assertEqual(phase.compare(code, digest, "0x00")[0], False)
        self.assertEqual(phase.compare(code, digest, "0x")[0], False)

    def test_an_announcement_from_an_immutable_subject_refuses_before_any_read(self):
        logs = self.all_logs()
        library = dict(logs[0], address=LIBRARY, topics=[UPGRADED_TOPIC, word(POOL_IMPLEMENTATION)])
        with self.assertRaises(aave_v3.EpochRefusal) as raised:
            self.phase([library] + logs[1:])
        self.assertEqual((raised.exception.rule, raised.exception.subject),
                         (aave_v3.RULE_UPGRADE_FROM_IMMUTABLE, LIBRARY))

    def test_an_upgrade_in_the_opening_block_refuses_at_collection(self):
        state = deepcopy(self.state)
        creation = aave_registry.subject_entries(self.registry)[TOKEN]["creation_block"]
        record = state["logs"]["0"][2]
        # The record is a JSON-RPC event log; its `address` is the emitting contract.
        self.assertEqual((record["address"], int(record["blockNumber"], 16)), (TOKEN, creation))
        upgraded_to = aave_registry.subject_entries(self.registry)[TOKEN]["implementations"][1]["implementation"]
        record["topics"] = [UPGRADED_TOPIC, word(upgraded_to)]
        staging = self.scratch("opening-block")
        with self.assertRaises(aave_v3.EpochRefusal) as raised:
            Collector(state["plan"], staging, AaveTransport(state), registry=self.registry).collect()
        self.assertEqual(raised.exception.rule, aave_v3.RULE_UPGRADE_IN_OPENING_BLOCK)
        self.assertEqual([receipt["code"] for receipt in self.receipts(staging)], ["malformed-staged-log"])
        self.assertEqual(existing.opening_entries(staging), [])

    def test_a_plan_whose_opening_reads_cannot_fit_the_journal_refuses_before_any_request(self):
        transport = AaveTransport(self.state)
        with mock.patch.object(aave_v3, "MAX_JOURNAL_BYTES", 10_000):
            with self.assertRaisesRegex(AlexandriaError, r"above the 10000-byte journal limit; declare fewer subjects"):
                Collector(self.plan, self.scratch("budget"), transport, registry=self.registry)
        self.assertEqual(transport.calls, [])
        owed = aave_v3.SubjectProxyOpening(self.plan, self.registry, [])._owed()
        self.assertGreater(owed, 10_000)
        self.assertLess(owed, interval.MAX_JOURNAL_BYTES)

    def test_a_plan_with_no_subject_inside_its_interval_refuses(self):
        plan = deepcopy(self.plan)
        plan["subjects"] = [POOL, PROVIDER]
        plan["interval"] = {"end": "100", "start": "1"}
        with self.assertRaisesRegex(AlexandriaError, "no declared subject has an extent inside the interval"):
            aave_v3.opening_phase(plan, self.registry, [])


class AaveTraceCoverageTests(AaveCase):
    """What targeted traces keep, and what they declare they never asked for."""

    def test_a_frame_to_an_underlying_asset_is_dropped(self):
        unmatched = self.state["unmatched_frames"]
        self.assertEqual([frame["action"]["to"] for frame in unmatched], [ASSET])
        self.assertNotIn(ASSET, self.plan["subjects"])
        self.assertNotIn(ASSET, aave_registry.subject_entries(self.registry))
        staging = self.staged("asset")
        staged = [
            frame
            for line in (staging / "journals" / "traces.jsonl").read_bytes().splitlines()
            for frame in json.loads(json.loads(line)["response"])["result"]
        ]
        self.assertEqual(len(staged), sum(len(frames) for frames in self.state["traces"].values()))
        self.assertEqual([frame for frame in staged if frame["action"]["to"] == ASSET], [])
        # The transaction that frame belongs to was traced: the frame was
        # answered and dropped, not left unasked.
        asked = [label for method, label in self.transport.calls if method == "trace_transaction"]
        self.assertEqual(len(asked), 5)

    def test_a_logless_transaction_is_outside_trace_coverage(self):
        logless = self.state["logless_frames"]
        self.assertEqual(len(logless), 1)
        transaction = logless[0]["transactionHash"]
        named = {record["transactionHash"] for records in self.state["logs"].values() for record in records}
        self.assertNotIn(transaction, named)
        output, _release_id = self.released("logless")
        journal = (self.root / "logless-staging" / "journals" / "traces.jsonl").read_text()
        self.assertNotIn(transaction, journal)
        self.assertEqual(self.captures(output)["traces"]["coverage"]["gaps"].count(TARGETED_TRACE_GAP), 1)
        self.edit_manifest(output, lambda captures: captures["traces"]["coverage"]["gaps"].remove(TARGETED_TRACE_GAP))
        with self.assertRaisesRegex(AlexandriaError, "the traces coverage does not name the targeted trace gap"):
            self.check_without_verify(output)


class AaveOpeningOnlyDisputeTests(AaveCase):
    """An opening-only dispute follows #1831: it is recorded, and the build still refuses."""

    def test_an_opening_only_dispute_is_kept_and_does_not_build(self):
        second_state = deepcopy(self.state)
        second_state["code"][LIBRARY] = "0x60806040" + "ee" * 32
        staging = self.staged("opening-only", second=AaveTransport(second_state))
        record = self.document["reconciliation"]
        self.assertEqual(record["status"], "disputed")
        start = self.plan["interval"]["start"]
        self.assertEqual(
            record["disputed"],
            [{"identity": f"code of {LIBRARY} at block {start}", "kind": "code-digest", "shard": 4}],
        )
        self.assertEqual({shard["status"] for shard in self.document["shards"]}, {"complete"})
        kept = [
            json.loads(line)
            for line in (staging / "reconciliation" / "disputed.jsonl").read_bytes().splitlines()
        ]
        self.assertEqual([(item["class"], item["shard"]) for item in kept], [(OPENING_CLASS, 4)])
        output = self.root / "opening-only-release"
        self.assertRefused(self.build_cli(staging, output), "partial coverage must name an unsupported collection or gap")
        self.assertNothingInstalled(output)


class AaveVenueGapTests(AaveCase):
    """The venue's own gap sentences stay bounded and are re-derived by check."""

    def test_the_pre_interval_and_post_end_subjects_are_named(self):
        gaps = aave_v3.evidence_gaps(self.plan, self.registry, [])
        entries = aave_registry.subject_entries(self.registry)
        start, end = self.plan["interval"]["start"], self.plan["interval"]["end"]
        before = [s for s in self.plan["subjects"] if entries[s]["creation_block"] < int(start)]
        self.assertEqual(before, [POOL, PROVIDER, POOL_IMPLEMENTATION, LIBRARY])
        self.assertEqual(
            [gap for gap in gaps if "before the plan's start" in gap],
            [
                f"subject {subject} was created at block {entries[subject]['creation_block']}, before the "
                f"plan's start block {start}; its epoch opens at the start, its creation block is the "
                "registry's record rather than a read this collection made, and its activity before the "
                "start is outside this capture"
                for subject in before
            ],
        )
        self.assertEqual(
            [gap for gap in gaps if "after the plan's end" in gap],
            [f"subject {LATE} was created at block {entries[LATE]['creation_block']}, after the plan's end "
             f"block {end}, so it has no epoch and is outside the interval"],
        )
        self.assertEqual(len(gaps), 1 + 4 + 1)

    def test_a_large_subject_set_names_sixteen_and_counts_the_rest(self):
        plan = deepcopy(self.plan)
        entries = aave_registry.subject_entries(self.registry)
        plan["subjects"] = sorted(entries)
        gaps = aave_v3.evidence_gaps(plan, self.registry, [])
        start = int(plan["interval"]["start"])
        before = sum(1 for entry in entries.values() if entry["creation_block"] < start)
        after = sum(1 for entry in entries.values() if entry["creation_block"] > int(plan["interval"]["end"]))
        self.assertGreater(before, aave_v3.LISTED_GAPS)
        self.assertGreater(after, aave_v3.LISTED_GAPS)
        self.assertEqual(sum(1 for gap in gaps if gap.startswith("subject ") and "before the plan's start" in gap), 16)
        self.assertEqual(sum(1 for gap in gaps if gap.startswith("subject ") and "after the plan's end" in gap), 16)
        self.assertIn(
            f"{before - 16} further declared subjects, {before} in all, were created before the plan's start; "
            "each epoch opens at the start and the registry component names each creation block",
            gaps,
        )
        self.assertIn(
            f"{after - 16} further declared subjects, {after} in all, were created after the plan's end, "
            "have no epoch and are outside the interval; the plan and registry components name each",
            gaps,
        )
        self.assertEqual(len(gaps), 1 + 17 + 17)

    def test_an_admitted_deployment_drops_only_the_constructed_gap(self):
        gap = aave_v3.CONSTRUCTED_STAGING_GAP.format(deployment=self.plan["deployment"], venue="aave-v3")
        with mock.patch.object(aave_v3, "PRESERVED_DEPLOYMENTS", frozenset({self.plan["deployment"]})):
            admitted = aave_v3.evidence_gaps(self.plan, self.registry, [])
        self.assertEqual(aave_v3.evidence_gaps(self.plan, self.registry, []), [gap] + admitted)


class FixtureTests(unittest.TestCase):
    def test_the_fixture_declares_registry_subjects_and_says_it_is_constructed(self):
        state = fixture()
        entries = aave_registry.subject_entries(registry())
        self.assertEqual(state["plan"]["subjects"], [POOL, PROVIDER, TOKEN, POOL_IMPLEMENTATION, LIBRARY, LATE])
        self.assertTrue(all(subject in entries for subject in state["plan"]["subjects"]))
        self.assertIn("was not observed on any chain", state["note"])
        self.assertNotIn(state["plan"]["deployment"], aave_v3.PRESERVED_DEPLOYMENTS)
        interval.validate_plan(state["plan"])
        for proxy, table in state["slots"].items():
            with self.subTest(proxy=proxy):
                self.assertEqual(
                    table,
                    [[item["from_block"], item["implementation"]] for item in entries[proxy]["implementations"]],
                )
        self.assertEqual(sorted(state["slots"]), sorted([POOL, TOKEN]))


if __name__ == "__main__":
    unittest.main()
