"""`check` reads an interval release one component at a time and keeps today's refusals.

The design record's `streamed-check-keeps-every-refusal` cell loads
`RefusalOrderTests` and `SecondReadTests` by name, and runs five existing check
modules whole. Its `check-peak-independent-of-size` cell loads
`CheckPeakTests.test_the_traced_peak_does_not_grow_with_the_release`.

- `RefusalOrderTests` builds releases with one or two defects each and
  compares what `check` says with what the base commit's own `check` says.
  That `check` runs
  from a `git archive` of the base commit's `plugins/alexandria/scripts` and
  plugin manifest, as a child process with a fixed argv and no shell. Each
  case names the base message it has to reproduce, so a case that stops
  reaching its pair fails instead of passing on a coincidence.
- `OpeningLimitTests` lowers the opening-log limit below the one opening log
  the constructed release preserves and expects the refusal that names it.
- `SecondReadTests` changes a part, and a logs journal the walk reads a second
  time, between the two reads, and expects the refusal that names it.
- `CheckPeakTests` traces `check` with `tracemalloc` on a generated release and
  on one four times larger, from the committed synthetic generator.

Only the base `check`, `git` and the generator start a child process. No case
opens a socket.
"""

from contextlib import redirect_stderr, redirect_stdout
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import tracemalloc
import unittest
from unittest import mock

from tests import test_usdc_interval as existing
from tests import test_usdc_interval_live_demo as live
from tests.test_log_attribution_parts import PartCase, V4_SEMANTICS, replanned
from tests.test_wildcat_venue import fixture as venue_fixture, v1_registry
from alexandria_lib import interval, log_walk
from alexandria_lib.errors import AlexandriaError
from alexandria_lib.venues import wildcat_v1, wildcat_v2
import usdc_interval
from usdc_interval import PART_CLASS, check_interval

BASE = "150943da240837040478a76c3611d150fa04f2b6"
BASE_PATHS = ("plugins/alexandria/scripts", "plugins/alexandria/.claude-plugin")
OTHER_HASH = "0x" + "ab" * 32
GENERATOR = (
    Path(__file__).resolve().parents[1] / "docs" / "bounded-memory-interval" / "design"
    / "synthetic_interval.py"
)
# The traced-peak bound the study states: a release four times larger may
# raise `check`'s traced peak by at most this much plus 16 bytes a log.
PEAK_ALLOWANCE = 8_388_608
PEAK_BYTES_PER_LOG = 16
# Four shards and sixteen of 1,500 generated logs each: 6,000 and 24,000 logs.
PEAK_SHARDS = (4, 16)
PEAK_LOGS_PER_SHARD = 1_500
# Two shards of 600 logs, four to a transaction: 300 transactions, more than a
# one-byte key has values, so narrowed keys are certain to collide.
COLLIDING_LOGS_PER_SHARD = 600


def repository_root() -> Path:
    """The checkout holding this module, found by its marketplace manifest rather than by depth."""
    here = Path(__file__).resolve()
    for candidate in here.parents:
        if (
            (candidate / ".claude-plugin" / "marketplace.json").is_file()
            and (candidate / "plugins" / "alexandria" / "tests" / here.name).is_file()
        ):
            return candidate
    raise AssertionError(
        f"no directory above {here} holds both .claude-plugin/marketplace.json and this module"
    )


def child_environment() -> dict:
    """PATH and HOME for a child interpreter, and nothing else this process carries."""
    environment = {
        "PATH": os.environ.get("PATH", os.defpath), "NO_COLOR": "1",
        "PYTHONDONTWRITEBYTECODE": "1", "LC_ALL": "C",
    }
    if "HOME" in os.environ:
        environment["HOME"] = os.environ["HOME"]
    return environment


def extract_base(destination: Path) -> Path:
    """The base commit's `check`, from a `git archive` of its scripts and plugin manifest."""
    home = tempfile.mkdtemp(prefix="alexandria-streamed-check-git-")
    try:
        environment = {key: value for key, value in os.environ.items()
                       if not key.startswith("GIT_")}
        environment.update(HOME=home, XDG_CONFIG_HOME=home, GIT_CONFIG_NOSYSTEM="1",
                           GIT_CONFIG_GLOBAL=os.devnull, LC_ALL="C")
        result = subprocess.run(  # phylax: allow subprocess: fixed git argv archiving the base commit's scripts, no shell
            ["git", "-c", "color.ui=never", "-C", str(repository_root()), "archive",
             "--format=tar", BASE, *BASE_PATHS],
            capture_output=True, timeout=120, env=environment, check=False,
        )
    finally:
        shutil.rmtree(home, ignore_errors=True)
    if result.returncode != 0:
        raise AssertionError(
            f"git could not archive the base commit {BASE}: "
            + result.stderr.decode("utf-8", "replace").strip()[:300]
        )
    with tarfile.open(fileobj=io.BytesIO(result.stdout), mode="r:") as archive:
        archive.extractall(destination, filter="data")
    script = destination / "plugins" / "alexandria" / "scripts" / "usdc_interval.py"
    if not script.is_file():
        raise AssertionError(f"the base commit's archive holds no {script.name}")
    return script


def generate(root, name, shards, logs_per_shard) -> dict:
    """Generate and build one release with the committed synthetic generator."""
    output = Path(root) / name
    result = subprocess.run(  # phylax: allow subprocess: the committed generator, fixed argv, no shell
        [sys.executable, str(GENERATOR), "--output", str(output), "--shards", str(shards),
         "--logs-per-shard", str(logs_per_shard), "--build"],
        capture_output=True, text=True, check=False, cwd=root,
        env=child_environment(), timeout=600,
    )
    if result.returncode != 0:
        raise AssertionError(f"the generator refused: {result.stderr[-2000:]}")
    return json.loads(result.stdout)


def current_outcome(release) -> tuple:
    """What the working tree's `check` command prints for one release, and its exit status."""
    stdout, stderr = io.BytesIO(), io.StringIO()
    wrapper = io.TextIOWrapper(stdout, encoding="utf-8")
    with redirect_stdout(wrapper), redirect_stderr(stderr):
        code = usdc_interval.main(["check", str(release)])
        wrapper.flush()
    return code, stdout.getvalue(), stderr.getvalue()


class BaseCheckCase(PartCase):
    """Runs the base commit's `check` beside the working tree's."""

    base_script = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._base_directory = tempfile.TemporaryDirectory(prefix="alexandria-base-check-")
        cls.addClassCleanup(cls._base_directory.cleanup)
        cls.base_script = extract_base(Path(cls._base_directory.name))

    def base_outcome(self, release) -> tuple:
        result = subprocess.run(  # phylax: allow subprocess: the base commit's own check, fixed argv, no shell
            [sys.executable, str(self.base_script), "check", str(release)],
            capture_output=True, timeout=600, env=child_environment(), check=False,
            cwd=str(self.root),
        )
        return result.returncode, result.stdout, result.stderr.decode("utf-8", "replace")

    def assert_as_base(self, release, expected=None):
        """The working tree's `check` prints what the base's prints; `expected` names the refusal."""
        base = self.base_outcome(release)
        self.assertNotIn("Traceback", base[2])
        if expected is not None:
            self.assertEqual(base[0], 1, base[2])
            self.assertRegex(base[2], f"^usdc-interval: {expected}\n$")
        self.assertEqual(current_outcome(release), base)


def records(documents, name):
    """One journal component's records, for an edit."""
    return documents[name]["records"]


def rewrite_result(record, edit):
    """Re-encode one journal record's response after `edit(result)` changes its result."""
    envelope = json.loads(record["response"])
    edit(envelope["result"])
    record["response"] = json.dumps(envelope, separators=(",", ":"), sort_keys=True)


def unorder_logs(name):
    def edit(documents):
        for record in records(documents, name):
            if len(json.loads(record["response"])["result"]) >= 2:
                rewrite_result(record, lambda result: result.insert(0, result.pop(1)))
                return
        raise AssertionError(f"{name} holds no record with two logs to swap")
    return edit


def wrong_boundary_hash(name):
    def edit(documents):
        rewrite_result(records(documents, name)[0], lambda result: result.update(hash=OTHER_HASH))
    return edit


def forged_epoch(documents):
    epochs = documents["epoch-table"]["epochs"]
    first = epochs[0]["epochs"][0] if isinstance(epochs[0], dict) and "subject" in epochs[0] else epochs[0]
    first["start_hash"] = OTHER_HASH


def altered_part_row(name=f"{PART_CLASS}.0"):
    def edit(documents):
        documents[name]["rows"][0]["transaction_hash"] = OTHER_HASH
    return edit


def altered_receipt_row(documents):
    documents["epoch-table"]["log_attributions"][0]["transaction_hash"] = OTHER_HASH


def wrong_code_digest(documents):
    documents["epoch-table"]["implementation_code"]["sha256"] = "0" * 64


def unknown_receipt_field(documents):
    documents["epoch-table"]["unrecorded"] = 1


def altered_request(name):
    def edit(documents):
        record = records(documents, name)[0]
        record["request"] = record["request"].replace('"jsonrpc"', '"jsonrpc" ', 1)
    return edit


def both(*edits):
    def edit(documents):
        for step in edits:
            step(documents)
    return edit


class RefusalOrderTests(BaseCheckCase):
    """A release with one or two defects is refused with the base `check`'s first message."""

    # A known ordering residual, kept by decision and not guarded here: under
    # a venue's own epoch model the opening phase attributes only the opening
    # logs, so an attribution refusal on an opening log comes before one on a
    # log of a subject that appears earlier. Attribution refusals name no log,
    # so the first message differs from the base only when one is "proxy log
    # has no positional epoch owner" and the other "proxy log hash contradicts
    # its epoch boundary".

    def split_release(self):
        output, _plan = self.split("split")
        self.assertEqual(check_interval(output)["receipt_semantics"], V4_SEMANTICS)
        return output

    def case(self, source, name, expected, *, edit=None, raw=None, captures=None):
        release = self.reissued(source, name, edit=edit, raw=raw, captures=captures)
        with self.subTest(case=name):
            self.assert_as_base(release, expected)

    def test_a_forged_epoch_table_is_reported_before_its_rows(self):
        epoch = "the epoch table does not match the epochs the preserved opening reads derive"
        self.case(self.split_release(), "forged-split", epoch,
                  edit=both(forged_epoch, altered_part_row()))
        twin, _plan = self.split("twin", parts=False)
        self.case(twin, "forged-unsplit", epoch, edit=both(forged_epoch, altered_receipt_row))

    def test_a_wrong_boundary_hash_is_reported_before_an_unordered_log(self):
        self.case(
            self.split_release(), "boundary-and-order",
            r"shard 1 declares boundary hash 0x[0-9a-f]{64}, which its preserved boundary read "
            r"does not carry; that read carries 0x(ab){32}",
            edit=both(unorder_logs("logs.2"), wrong_boundary_hash("boundary-blocks.1")),
        )

    def test_a_wrong_code_digest_is_reported_before_a_row_mismatch(self):
        code = (r"the epoch table names implementation-code digest 0{64} but the component's "
                r"bytes hash to [0-9a-f]{64}")
        self.case(self.split_release(), "code-and-rows", code,
                  edit=both(wrong_code_digest, altered_part_row(f"{PART_CLASS}.2")))
        twin, _plan = self.split("twin", parts=False)
        self.case(twin, "code-and-receipt-rows", code,
                  edit=both(wrong_code_digest, altered_receipt_row))

    def test_an_unordered_log_is_reported_before_the_code_digest(self):
        self.case(
            self.split_release(), "order-and-code",
            r"proxy log position \(\d+, \d+, \d+\) is duplicated or unordered",
            edit=both(unorder_logs("logs.2"), wrong_code_digest),
        )

    def test_a_journal_rule_is_reported_before_an_unordered_log(self):
        self.case(
            self.split_release(), "order-and-request",
            "the traces.3 record filed under shard 3 is not the read the plan names there",
            edit=both(unorder_logs("logs.0"), altered_request("traces.3")),
        )

    def test_a_row_mismatch_is_reported_before_a_scope(self):
        def scope(by_id):
            by_id["logs.0"]["scope"]["interval"]["start_hash"] = OTHER_HASH

        self.case(
            self.split_release(), "rows-and-scope",
            re.escape(
                f"component {PART_CLASS}.1 (shards 1 to 1) does not hold the rows "
                "attribute_logs derives from the preserved logs of its shards"
            ),
            edit=altered_part_row(f"{PART_CLASS}.1"), captures=scope,
        )

    def test_an_unreadable_component_is_reported_before_every_rule(self):
        output = self.split_release()
        self.case(
            output, "part-and-receipt",
            re.escape(f"component {PART_CLASS}.3 (shards 3 to 3) is not valid JSON"),
            edit=unknown_receipt_field, raw={f"{PART_CLASS}.3": b"{\n"},
        )
        self.case(
            output, "journal-and-request", re.escape("component traces.3 is not valid JSON"),
            edit=altered_request("logs.0"), raw={"traces.3": b"{\n"},
        )
        # A journal named before a part is refused first, though `check`
        # reads the parts before the journals.
        self.case(
            output, "two-unreadable", re.escape("component boundary-blocks.1 is not valid JSON"),
            raw={"boundary-blocks.1": b"{\n", f"{PART_CLASS}.2": b"{\n"},
        )

    def test_the_wildcat_v1_path_keeps_the_same_order(self):
        self.registry = v1_registry()
        output, _release_id = self.released("v1", venue_fixture(wildcat_v1.VENUE))
        # The V1 fixture preserves no logs, so its venue is handed no opening
        # log and the walk no log at all.
        self.case(
            output, "v1-boundary-and-code",
            r"shard 0 declares boundary hash 0x[0-9a-f]{64}, which its preserved boundary read "
            r"does not carry; that read carries 0x(ab){32}",
            edit=both(wrong_boundary_hash("boundary-blocks"), wrong_code_digest),
        )
        self.case(
            output, "v1-code-and-epoch",
            r"the epoch table names implementation-code digest 0{64} but the component's "
            r"bytes hash to [0-9a-f]{64}",
            edit=both(wrong_code_digest, forged_epoch),
        )

    def test_a_block_only_release_is_not_held_to_log_positions(self):
        # Base `check` never applied the position rules to a v1 receipt's
        # logs, and the walk is not run under one: the release is judged as
        # before, whatever the order of its logs.
        summary = live.demo().build(self.root / "legacy")
        release = self.root / "legacy" / "release"
        self.assertEqual(check_interval(release)["receipt_semantics"], "v1-block-only")
        self.assert_as_base(release)
        manifest = json.loads((release / "manifest.json").read_text(encoding="utf-8"))
        names = [item["name"] for item in manifest["components"]]
        self.assertIn("logs", names, summary)

        def reverse(documents):
            for record in records(documents, "logs"):
                rewrite_result(record, lambda result: result.reverse())

        self.assert_as_base(self.reissued(release, "legacy-reversed", edit=reverse))


    def single_proxy_release(self, name):
        """A positional single-proxy release, built from the collector's own fixture."""
        state = existing.fixture()
        plan = state["plan"]
        staging = self.root / f"{name}-staging"
        staging.mkdir()
        usdc_interval.Collector(plan, staging, existing.FixtureTransport(state)).collect()
        usdc_interval.Reconciler(
            plan, staging, existing.FixtureTransport(state), "second archive endpoint, class only",
        ).reconcile()
        output = self.root / name
        usdc_interval.Builder(
            plan, staging, existing.registry(), created_at=existing.CREATED_AT,
        ).build(output)
        self.assertEqual(check_interval(output)["receipt_semantics"], "v2-positional")
        return output

    def test_a_single_proxy_forged_table_reports_a_log_its_derivation_refuses(self):
        # `discover_epochs` attributed every preserved log to the table it
        # derives before that table was compared with the receipt's, so a log
        # the derived table cannot own is refused before the forged table.
        def edit(documents):
            first = documents["interval-plan"]["interval"]["start"]
            touched = 0
            for name in sorted(documents):
                if name != "logs" and not name.startswith("logs."):
                    continue
                for record in records(documents, name):
                    def rehash(result):
                        nonlocal touched
                        for entry in result:
                            if int(entry["blockNumber"], 16) == int(first):
                                entry["blockHash"] = OTHER_HASH
                                touched += 1
                    rewrite_result(record, rehash)
            self.assertGreater(touched, 0, "the fixture preserves no log at its first block")
            documents["epoch-table"]["epochs"][0]["start_hash"] = "0x" + "cd" * 32

        self.case(
            self.single_proxy_release("single"), "single-hash-and-epoch",
            re.escape("proxy log hash contradicts its epoch boundary"), edit=edit,
        )

    def test_a_venue_keeps_the_first_repeated_transaction_among_every_log(self):
        # The walk holds a repeated transaction hash for the opening replay. A
        # venue's phase then checked positions over every preserved log, so the
        # refusal names the first repeat in plan order, not the first repeat
        # among the opening logs.
        expected = []

        def edit(documents):
            names = sorted(
                (name for name in documents if name.startswith("logs.")),
                key=lambda name: int(name.split(".")[1]),
            )
            logs = [
                (name, position, index, entry)
                for name in names
                for position, record in enumerate(records(documents, name))
                for index, entry in enumerate(json.loads(record["response"])["result"])
            ]

            def transaction(entry):
                return entry["blockNumber"], entry["transactionIndex"]

            first = logs[0][3]
            opening = next(
                item for item in logs
                if item[3]["topics"][0] == wildcat_v2.MARKET_DEPLOYED_TOPIC
                and transaction(item[3]) != transaction(first)
            )
            between = next(
                item for item in logs[:logs.index(opening)]
                if transaction(item[3]) not in (transaction(first), transaction(opening[3]))
            )
            moved = {transaction(between[3]), transaction(opening[3])}
            for name in names:
                for record in records(documents, name):
                    def edit_result(result):
                        for entry in result:
                            if transaction(entry) in moved:
                                entry["transactionHash"] = first["transactionHash"]
                    rewrite_result(record, edit_result)
            # The first log becomes an opening log too, so two opening logs share
            # the repeated hash; the log between them repeats it first.
            name, position, index, _entry = logs[0]
            rewrite_result(
                records(documents, name)[position],
                lambda result: result[index]["topics"].__setitem__(
                    0, wildcat_v2.MARKET_DEPLOYED_TOPIC,
                ),
            )
            # Each shard's trace request names its own logs' transactions.
            by_shard = {}
            for name in names:
                for record in records(documents, name):
                    by_shard[record["shard"]] = json.loads(record["response"])["result"]
            for name in sorted(documents):
                if not name.startswith("traces."):
                    continue
                for record in records(documents, name):
                    record["request"] = usdc_interval.request_bytes(
                        usdc_interval.request_identifier(record["shard"], "traces"),
                        "trace_transaction",
                        usdc_interval.subject_transaction_hashes(by_shard.get(record["shard"], [])),
                    ).decode()
            entry = between[3]
            expected.append(
                f"proxy log position ({int(entry['blockNumber'], 16)}, "
                f"{int(entry['transactionIndex'], 16)}, {int(entry['logIndex'], 16)}) has "
                "contradictory transaction hash/index pairs"
            )

        release = self.reissued(self.split_release(), "venue-repeat", edit=edit)
        with self.subTest(case="venue-repeat"):
            self.assert_as_base(release, re.escape(expected[0]))

    def test_a_log_the_table_cannot_own_is_refused_after_the_table_matches(self):
        # The receipt's table is the derived one, so the attribution refusal a
        # row found against it stands, ahead of the row comparison it spoils.
        def edit(documents):
            first = int(documents["interval-plan"]["interval"]["start"])
            for name in sorted(documents):
                if name == "logs" or name.startswith("logs."):
                    for record in records(documents, name):
                        rewrite_result(record, lambda result: [
                            entry.update(blockHash=OTHER_HASH) for entry in result
                            if int(entry["blockNumber"], 16) == first
                        ])

        self.case(
            self.single_proxy_release("single-owner"), "single-hash",
            re.escape("proxy log hash contradicts its epoch boundary"), edit=edit,
        )

    def test_a_log_without_a_transaction_hash_refuses_at_its_trace_record(self):
        # The trace request a shard's logs derive is kept as its refusal when
        # it cannot be derived, and that refusal is raised at the trace record.
        def edit(documents):
            rewrite_result(
                records(documents, "logs.1")[0],
                lambda result: result[0].update(transactionHash="0x12"),
            )

        self.case(
            self.split_release(), "trace-derivation",
            re.escape("a log entry carries no transaction hash"), edit=edit,
        )

    def test_a_block_only_release_keeps_its_upgrade_limit(self):
        # Under a block-only receipt only the `Upgraded(address)` logs are
        # kept, up to one past the epoch limit, so the limit still refuses.
        live.demo().build(self.root / "legacy-limit")
        release = self.root / "legacy-limit" / "release"
        limit = interval.MAX_EPOCHS

        def edit(documents):
            plan = documents["interval-plan"]
            proxy = plan["proxy"]
            record = records(documents, "logs")[0]
            shard = plan["shards"][record["shard"]]
            added = [
                {"address": proxy, "blockNumber": hex(shard["start"]),
                 "topics": [usdc_interval.UPGRADED_TOPIC]}
                for _ in range(limit + 1)
            ]
            rewrite_result(record, lambda result: result.extend(added))
            for table in (documents["epoch-table"]["shards"], documents["reconciliation"]["shards"]):
                table[record["shard"]]["record_counts"]["logs"] += len(added)

        self.case(
            release, "legacy-upgrade-limit",
            re.escape(f"more than {limit} upgrade logs were staged"), edit=edit,
        )

    def test_a_part_capture_is_reported_after_the_reconciliation(self):
        # A part's capture is compared while its document is in hand on the
        # first read, and its refusal waits for the capture rules' point.
        def reconciliation(documents):
            documents["reconciliation"]["plan_sha256"] = "sha256:" + "0" * 64

        def capture(by_id):
            gaps = by_id[f"{PART_CLASS}.1"]["coverage"]["gaps"]
            gaps[:] = [gap.replace("part 1 of", "part one of") for gap in gaps]

        self.case(
            self.split_release(), "capture-and-reconciliation",
            re.escape("the reconciliation record belongs to a different plan"),
            edit=reconciliation, captures=capture,
        )

    def test_every_part_is_read_after_a_part_rule_refuses(self):
        # A part rule's refusal does not stop the reads: a later part that
        # cannot be read is still refused first, in component-name order.
        def index(documents):
            documents[f"{PART_CLASS}.0"]["part"] = 1

        self.case(
            self.split_release(), "part-rule-and-unreadable-part",
            re.escape(f"component {PART_CLASS}.3 (shards 3 to 3) is not valid JSON"),
            edit=index, raw={f"{PART_CLASS}.3": b"{\n"},
        )

    def test_a_venue_checks_its_registry_before_a_held_position_refusal(self):
        # A venue's phase validated its registry before it checked the
        # positions of the logs it was handed, so a changed registry is
        # reported before an unordered log.
        def registry(documents):
            documents["registry"]["entries"][0]["source_commit"] = "0" * 40

        self.case(
            self.split_release(), "registry-and-order",
            re.escape("Wildcat V2 registry bytes do not match the pinned registry"),
            edit=both(unorder_logs("logs.2"), registry),
        )

    def test_a_part_whose_range_preserves_no_logs_holds_no_rows(self):
        # A plan that declares parts without the logs class derives no row, so
        # every part is compared with the empty list its range derives.
        source = self.split_release()
        row = self.document(source, f"{PART_CLASS}.0")["rows"][0]
        state = replanned(self.state, 1)
        state["plan"]["evidence_classes"] = [
            name for name in state["plan"]["evidence_classes"] if name not in ("logs", "traces")
        ]
        output, _release_id = self.released("no-logs", state)
        self.assertEqual(check_interval(output)["receipt_semantics"], V4_SEMANTICS)

        def edit(documents):
            documents[f"{PART_CLASS}.0"]["rows"] = [row]
            documents["epoch-table"]["log_attribution_parts"][0]["rows"] = 1

        self.case(
            output, "no-logs-fabricated-row",
            re.escape(
                f"component {PART_CLASS}.0 (shards 0 to 0) does not hold the rows "
                "attribute_logs derives from the preserved logs of its shards"
            ),
            edit=edit,
        )

    def test_an_unsplit_receipt_with_a_trailing_row_refuses(self):
        def edit(documents):
            rows = documents["epoch-table"]["log_attributions"]
            rows.append(dict(rows[-1]))

        twin, _plan = self.split("twin", parts=False)
        self.case(
            twin, "trailing-receipt-row",
            re.escape("log attributions do not match ownership derived from preserved logs"),
            edit=edit,
        )


class OpeningLimitTests(PartCase):
    """`check` refuses by name a release holding more opening logs than the walk keeps."""

    def test_opening_logs_above_the_limit_refuse_by_name(self):
        output, _plan = self.split("opening-limit")
        self.assertEqual(check_interval(output)["receipt_semantics"], V4_SEMANTICS)
        # The constructed V2 release preserves one MarketDeployed log, so a
        # limit of none puts it above the limit.
        with mock.patch.object(log_walk, "MAX_OPENING_LOGS", 0), \
                self.assertRaises(AlexandriaError) as caught:
            check_interval(output)
        self.assertEqual(
            str(caught.exception),
            "the preserved logs hold 1 opening logs, above the 0-log opening-log limit",
        )


class SecondReadTests(PartCase):
    """A component `check` reads twice has to carry the verified bytes both times."""

    def reads_of(self, output, names):
        """Patch `check`'s confined reads to count each named component's reads by object path."""
        manifest = json.loads((Path(output) / "manifest.json").read_text(encoding="utf-8"))
        paths = {item["object_path"]: item["name"] for item in manifest["components"]
                 if item["name"] in names}
        counts = {name: 0 for name in names}
        real = usdc_interval.read_confined_file

        def counted(root, value, label, *, max_bytes):
            data = real(root, value, label, max_bytes=max_bytes)
            if value in paths:
                counts[paths[value]] += 1
            return data

        return counts, mock.patch.object(usdc_interval, "read_confined_file", counted)

    def changed_after(self, output, name, reads):
        """Patch `check`'s reads to rewrite one component once it has been read `reads` times."""
        path = existing.component_path(output, name)
        saved = path.read_bytes()
        target = str(path.relative_to(output))
        seen = []
        real = usdc_interval.read_confined_file

        def changing(root, value, label, *, max_bytes):
            data = real(root, value, label, max_bytes=max_bytes)
            if value == target:
                seen.append(value)
                if len(seen) == reads:
                    # The same document, indented: every value is unchanged,
                    # so only the binding tells these bytes from the verified ones.
                    path.write_bytes(json.dumps(json.loads(saved), indent=2).encode())
            return data

        self.addCleanup(path.write_bytes, saved)
        return seen, mock.patch.object(usdc_interval, "read_confined_file", changing)

    def test_each_part_is_read_twice_and_bound_both_times(self):
        output, plan = self.split("twice")
        parts = usdc_interval.attribution_parts(plan)
        counts, patch = self.reads_of(output, parts)
        with patch:
            self.assertEqual(check_interval(output)["receipt_semantics"], V4_SEMANTICS)
        self.assertEqual(counts, {name: 2 for name in parts})

    def test_a_part_changed_between_its_two_reads_refuses_by_name(self):
        output, _plan = self.split("changed-part")
        seen, patch = self.changed_after(output, f"{PART_CLASS}.1", 1)
        with patch, self.assertRaises(AlexandriaError) as caught:
            check_interval(output)
        self.assertEqual(len(seen), 2)
        self.assertEqual(
            str(caught.exception),
            f"component {PART_CLASS}.1 (shards 1 to 1) changed between check's two reads of "
            "it: the second read does not carry the size and SHA-256 the verified manifest "
            "records",
        )

    def generated(self):
        """A generated release of two shards whose 300 transactions must share one-byte keys."""
        result = generate(self.root, "generated", 2, COLLIDING_LOGS_PER_SHARD)
        return Path(result["release"])

    def test_colliding_transaction_keys_cost_one_more_read_of_the_logs(self):
        output = self.generated()
        logs = ["logs.0", "logs.1"]
        counts, patch = self.reads_of(output, logs)
        with patch:
            self.assertEqual(check_interval(output)["receipt_semantics"], V4_SEMANTICS)
        self.assertEqual(counts, {name: 1 for name in logs})
        # One-byte keys: 300 transactions cannot have 300 distinct first
        # bytes, so the walk reads the logs a second time and admits the same
        # release.
        counts, patch = self.reads_of(output, logs)
        with patch, mock.patch.object(log_walk, "KEY_BYTES", 1):
            self.assertEqual(check_interval(output)["receipt_semantics"], V4_SEMANTICS)
        self.assertEqual(counts, {name: 2 for name in logs})

    def test_a_logs_journal_changed_before_its_second_read_refuses_by_name(self):
        output = self.generated()
        seen, patch = self.changed_after(output, "logs.0", 1)
        with patch, mock.patch.object(log_walk, "KEY_BYTES", 1), \
                self.assertRaises(AlexandriaError) as caught:
            check_interval(output)
        self.assertEqual(len(seen), 2)
        self.assertEqual(
            str(caught.exception),
            "component logs.0 changed between check's two reads of it: the second read does "
            "not carry the size and SHA-256 the verified manifest records",
        )


class CheckPeakTests(unittest.TestCase):
    """`check`'s traced peak on a release four times larger stays within the stated bound."""

    def traced_peak(self, release) -> int:
        """`check`'s traced peak, counted from its own manifest read onwards.

        `verify` and `check` each read the manifest into a buffer sized for
        the 128 MiB manifest ceiling before any component is held, and that
        buffer alone sets the peak of a small release, whatever `check` holds
        later. The peak is reset once `check` has read the manifest, so what
        is compared is what `check` holds while it reads the components.
        """
        real = usdc_interval.read_manifest_bytes

        def manifest_read(*args, **kwargs):
            data = real(*args, **kwargs)
            tracemalloc.reset_peak()
            return data

        with mock.patch.object(usdc_interval, "read_manifest_bytes", manifest_read):
            tracemalloc.start()
            try:
                summary = check_interval(release)
                peak = tracemalloc.get_traced_memory()[1]
            finally:
                tracemalloc.stop()
        self.assertEqual(summary["receipt_semantics"], V4_SEMANTICS)
        return peak

    def test_the_traced_peak_does_not_grow_with_the_release(self):
        with tempfile.TemporaryDirectory(prefix="alexandria-check-peak-") as directory:
            small, large = (
                generate(directory, f"shards-{shards}", shards, PEAK_LOGS_PER_SHARD)
                for shards in PEAK_SHARDS
            )
            # Four times the shards and the logs, and so nearly four times the
            # bytes: the fixed components do not grow.
            self.assertGreaterEqual(10 * large["release_bytes"], 39 * small["release_bytes"])
            # One untraced run first, so imports and caches are not counted
            # against the first release.
            check_interval(small["release"])
            peaks = [self.traced_peak(run["release"]) for run in (small, large)]
        added_logs = (PEAK_SHARDS[1] - PEAK_SHARDS[0]) * PEAK_LOGS_PER_SHARD
        bound = PEAK_ALLOWANCE + PEAK_BYTES_PER_LOG * added_logs
        self.assertLessEqual(
            peaks[1] - peaks[0], bound,
            f"check's traced peak rose from {peaks[0]} to {peaks[1]} bytes over {added_logs} "
            f"added logs, above the {bound}-byte bound",
        )


if __name__ == "__main__":
    unittest.main()
