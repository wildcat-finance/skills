"""`check` reads an interval release one component at a time and keeps today's refusals.

The design record's `streamed-check-keeps-every-refusal` cell loads
`RefusalOrderTests` and `SecondReadTests` by name, and runs five existing check
modules whole. Its `check-peak-independent-of-size` cell loads
`CheckPeakTests.test_the_traced_peak_does_not_grow_with_the_release`.

- `RefusalOrderTests` builds releases with two defects each and compares what
  `check` says with what the base commit's own `check` says. That `check` runs
  from a `git archive` of the base commit's `plugins/alexandria/scripts` and
  plugin manifest, as a child process with a fixed argv and no shell. Each
  case names the base message it has to reproduce, so a case that stops
  reaching its pair fails instead of passing on a coincidence.
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
from tests.test_log_attribution_parts import PartCase, V4_SEMANTICS
from tests.test_wildcat_venue import fixture as venue_fixture, v1_registry
from alexandria_lib import log_walk
from alexandria_lib.errors import AlexandriaError
from alexandria_lib.venues import wildcat_v1
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
    """A release with two defects is refused with the message the base `check` gives first."""

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
