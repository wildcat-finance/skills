"""Hold the 1374 capture record to the kickoff registry it is derived from.

``docs/kickoff/1374/capture.json`` copies three things out of
``docs/kickoff/1359``: the byte count and SHA-256 of ``targets.json`` and
``targets.md`` in its ``inputs`` array, a projection of the two Wildcat rows
and the ``aave-v3`` row in ``required_capture``, and the admitted, blocked and
deployment-less target lists in ``selection``. Each drifted once with nothing
to say so. This module recomputes each copied value from the files on disk and
compares, so the next registry change fails here until the record follows it.

It covers the kickoff-derived fields alone. It does not cover the
collector-source rows of ``inputs``, the ones naming files under
``plugins/alexandria``: those stay pinned at ``source_revision`` as a dated
observation of the collector the record was written against, and later steps
are expected to move those files without moving the rows.

The registry records a contract's Sourcify outcome in one of two places. The
Wildcat rows carry it as ``code_match.sourcify``; the ``aave-v3`` row carries
it as ``code_match.verification`` with a ``sourcify:`` prefix. The projection
reads whichever one a contract has, and refuses by name a contract that
carries both.

Nothing here is compared against a literal digest, byte count or contract
count. The expected side is always derived from ``targets.json`` or from the
file's own bytes by code in this module, never read back from the record under
test. The mutation cases copy both records into a temporary directory, first
confirm the unmodified copy is clean, then break one thing at a time in either
record and require the matching finding, so a check that passed everything
would fail here.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CAPTURE = Path("docs/kickoff/1374/capture.json")
PROSE = Path("docs/kickoff/1374/capture.md")
REGISTRY = Path("docs/kickoff/1359/targets.json")
REGISTRY_PROSE = Path("docs/kickoff/1359/targets.md")
KICKOFF_PREFIX = "docs/kickoff/1359/"
KICKOFF_INPUT_ROWS = ((0, REGISTRY.as_posix()), (1, REGISTRY_PROSE.as_posix()))
ESTATES = ("wildcat-v1-ethereum-mainnet", "wildcat-v2-ethereum-mainnet")
V1 = ESTATES[0]
AAVE = "aave-v3"
TARGETS = ESTATES + (AAVE,)
SOURCIFY_PREFIX = "sourcify:"
SOURCIFY_MATCHES = ("match", "exact_match")
COPIED = (CAPTURE, PROSE, REGISTRY, REGISTRY_PROSE)


class MalformedRow(ValueError):
    """A registry row the projection cannot read; the message is its name."""


def registry_row(registry: dict, target: str) -> dict | None:
    """Find one row by iterating the target list; the file is too deep to walk."""
    for row in registry["targets"]:
        if row["id"] == target:
            return row
    return None


def sourcify_outcome(target: str, contract: dict) -> str | None:
    """Read the Sourcify outcome from whichever field this contract uses."""
    code_match = contract["code_match"]
    verification = code_match.get("verification")
    prefixed = None
    if isinstance(verification, str) and verification.startswith(
            SOURCIFY_PREFIX):
        prefixed = verification[len(SOURCIFY_PREFIX):]
    if "sourcify" in code_match:
        if prefixed is not None:
            raise MalformedRow(
                f"sourcify-conflict:{target}:{contract['address']}")
        return code_match["sourcify"]
    return prefixed


def derive(row: dict) -> dict:
    """Project one registry row onto the fields the capture record copies."""
    target = row["id"]
    deployment = row.get("deployment")
    if deployment is None:
        raise MalformedRow(f"deployment-missing:{target}")
    contracts = [
        {
            "role": contract["role"],
            "name": contract["name"],
            "address": contract["address"],
            "code_keccak256": contract["code_keccak256"],
            "code_length": contract["code_length"],
            "sourcify": sourcify_outcome(target, contract),
            "code_match_method": contract["code_match"]["method"],
        }
        for contract in deployment["contracts"]
    ]
    return {
        "registry_status": row["status"],
        "registry_blocker": row.get("blocker"),
        "contracts": contracts,
        "contract_count": len(contracts),
        "code_hash_recorded_count": sum(
            1 for contract in contracts if contract["code_keccak256"]),
        "sourcify_match_count": sum(
            1 for contract in contracts
            if contract["sourcify"] in SOURCIFY_MATCHES),
        "unresolved": row.get("unresolved"),
    }


def derive_selection(registry: dict) -> dict:
    """Project the registry's admitted slots onto the selection lists."""
    admitted = [
        target for slot in registry["scope"]["ordered_slots"]
        for target in slot["targets"]]
    rows = [registry_row(registry, target) for target in admitted]
    for target, row in zip(admitted, rows, strict=True):
        if row is None:
            raise MalformedRow(f"admitted-row-missing:{target}")
    return {
        "admitted_targets": admitted,
        "admitted_target_count": len(admitted),
        "admitted_targets_blocked": [
            target for target, row in zip(admitted, rows, strict=True)
            if row["status"] == "blocked"],
        "admitted_targets_without_deployment": [
            target for target, row in zip(admitted, rows, strict=True)
            if row.get("deployment") is None],
    }


SELECTION_FINDINGS = {
    "admitted_targets": "selection-admitted-targets",
    "admitted_target_count": "selection-admitted-target-count",
    "admitted_targets_blocked": "selection-blocked",
    "admitted_targets_without_deployment": "selection-without-deployment",
}


def findings(root: Path) -> list[str]:
    """Name every disagreement between the records under ``root``."""
    found: list[str] = []
    capture = json.loads((root / CAPTURE).read_text(encoding="utf-8"))
    registry = json.loads((root / REGISTRY).read_text(encoding="utf-8"))
    prose = (root / PROSE).read_text(encoding="utf-8")

    kickoff_rows = tuple(
        (index, row["path"]) for index, row in enumerate(capture["inputs"])
        if row["path"].startswith(KICKOFF_PREFIX))
    if kickoff_rows != KICKOFF_INPUT_ROWS:
        found.append("kickoff-input-rows")
    for _, path in kickoff_rows:
        row = next(item for item in capture["inputs"] if item["path"] == path)
        data = (root / path).read_bytes()
        if row["bytes"] != len(data):
            found.append(f"input-bytes:{path}")
        if row["sha256"] != hashlib.sha256(data).hexdigest():
            found.append(f"input-sha256:{path}")

    # Read the rows as the list they are. Keyed by target, a stale second row
    # for one estate was dropped in favour of the last and never compared.
    rows = capture["required_capture"]
    if tuple(row["target"] for row in rows) != TARGETS:
        found.append("required-capture-targets")
    for row in rows:
        target = row["target"]
        if target not in TARGETS:
            continue
        source = registry_row(registry, target)
        if source is None:
            found.append(f"row-missing:{target}")
            continue
        try:
            derived = derive(source)
        except MalformedRow as error:
            found.append(str(error))
            continue
        for field, expected in derived.items():
            if row[field] != expected:
                found.append(f"{field}:{target}")
        if len(row["contracts"]) != row["contract_count"]:
            found.append(f"contracts-length:{target}")
        for ours, theirs in (("registry_blocker", "blocker"),
                             ("unresolved", "unresolved")):
            if (row[ours] is None) != (source.get(theirs) is None):
                found.append(f"null-parity-{ours}:{target}")
        if not re.search(
                rf"^\| `{re.escape(target)}` \| \w+ \| "
                rf"{re.escape(str(row['registry_status']))} \|$",
                prose, re.MULTILINE):
            found.append(f"prose-status:{target}")

    v1 = registry_row(registry, V1)
    if v1 is None or v1["status"] != "resolved":
        found.append("v1-registry-resolved")
    if tuple(capture["selection"]["reference_target"]) != ESTATES:
        found.append("reference-target")
    try:
        selection = derive_selection(registry)
    except MalformedRow as error:
        found.append(str(error))
    else:
        for field, expected in selection.items():
            if capture["selection"][field] != expected:
                found.append(SELECTION_FINDINGS[field])
    if f"`{capture['source_revision']}`" not in prose:
        found.append("prose-source-revision")
    return found


class CommittedRecordTests(unittest.TestCase):
    def test_the_committed_records_agree(self):
        self.assertEqual(findings(ROOT), [])

    def test_the_expected_side_is_not_empty(self):
        """An empty projection would agree with an empty record."""
        registry = json.loads((ROOT / REGISTRY).read_text(encoding="utf-8"))
        for target in TARGETS:
            with self.subTest(target=target):
                derived = derive(registry_row(registry, target))
                self.assertGreater(derived["contract_count"], 0)
                self.assertGreater(derived["sourcify_match_count"], 0)
                self.assertEqual(
                    derived["code_hash_recorded_count"],
                    derived["contract_count"])

    def test_the_resolved_aave_row_leaves_both_blocked_lists(self):
        """The drift this record carried: aave-v3 listed blocked and bare."""
        registry = json.loads((ROOT / REGISTRY).read_text(encoding="utf-8"))
        selection = derive_selection(registry)
        self.assertIn(AAVE, selection["admitted_targets"])
        self.assertNotIn(AAVE, selection["admitted_targets_blocked"])
        self.assertNotIn(AAVE, selection["admitted_targets_without_deployment"])


class MutationTests(unittest.TestCase):
    def setUp(self):
        scratch = tempfile.TemporaryDirectory()
        self.addCleanup(scratch.cleanup)
        self.root = Path(scratch.name)
        self.fresh()

    def fresh(self) -> None:
        """Restore the committed bytes, so no case inherits another's break."""
        for relative in COPIED:
            (self.root / relative).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, self.root / relative)
        self.assertEqual(findings(self.root), [])

    def edit_json(self, relative: Path, change) -> None:
        path = self.root / relative
        document = json.loads(path.read_text(encoding="utf-8"))
        change(document)
        path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")

    def edit_capture_row(self, target: str, change) -> None:
        def apply(document):
            for row in document["required_capture"]:
                if row["target"] == target:
                    change(row)
        self.edit_json(CAPTURE, apply)

    def edit_registry_row(self, target: str, change) -> None:
        self.edit_json(
            REGISTRY, lambda document: change(registry_row(document, target)))

    def test_a_same_length_edit_to_a_kickoff_input_moves_its_digest_only(self):
        for relative in (REGISTRY, REGISTRY_PROSE):
            with self.subTest(path=relative.as_posix()):
                self.fresh()
                path = self.root / relative
                data = bytearray(path.read_bytes())
                data[-1:] = b" "
                path.write_bytes(bytes(data))
                found = findings(self.root)
                self.assertIn(f"input-sha256:{relative.as_posix()}", found)
                self.assertNotIn(f"input-bytes:{relative.as_posix()}", found)

    def test_an_appended_byte_in_a_kickoff_input_moves_its_byte_count(self):
        for relative in (REGISTRY, REGISTRY_PROSE):
            with self.subTest(path=relative.as_posix()):
                self.fresh()
                with (self.root / relative).open("ab") as handle:
                    handle.write(b"\n")
                self.assertIn(
                    f"input-bytes:{relative.as_posix()}", findings(self.root))

    def test_a_wrong_recorded_byte_count_or_digest_is_found(self):
        def change(document):
            document["inputs"][0]["bytes"] += 1
            document["inputs"][1]["sha256"] = "0" * 64
        self.edit_json(CAPTURE, change)
        found = findings(self.root)
        self.assertIn(f"input-bytes:{REGISTRY.as_posix()}", found)
        self.assertNotIn(f"input-sha256:{REGISTRY.as_posix()}", found)
        self.assertIn(f"input-sha256:{REGISTRY_PROSE.as_posix()}", found)
        self.assertNotIn(f"input-bytes:{REGISTRY_PROSE.as_posix()}", found)

    def test_kickoff_input_rows_out_of_place_are_found(self):
        def swap(document):
            rows = document["inputs"]
            rows[0], rows[1] = rows[1], rows[0]
        self.edit_json(CAPTURE, swap)
        self.assertEqual(findings(self.root), ["kickoff-input-rows"])

    def test_a_third_kickoff_input_row_is_found(self):
        def add(document):
            document["inputs"].append(dict(document["inputs"][0]))
        self.edit_json(CAPTURE, add)
        self.assertIn("kickoff-input-rows", findings(self.root))

    def test_each_typed_capture_field_is_found_on_every_row(self):
        cases = {
            "registry_status": "blocked",
            "registry_blocker": "typed back in",
            "contract_count": -1,
            "code_hash_recorded_count": -1,
            "sourcify_match_count": -1,
            "unresolved": [],
        }
        for target in TARGETS:
            for field, value in cases.items():
                with self.subTest(target=target, field=field):
                    self.fresh()
                    self.edit_capture_row(
                        target,
                        lambda row, field=field, value=value: row.__setitem__(
                            field, value))
                    self.assertIn(f"{field}:{target}", findings(self.root))

    def test_a_stale_second_row_for_one_estate_is_found(self):
        """Before or after the current row, the stale one is still compared."""
        for target in TARGETS:
            for offset in (0, 1):
                with self.subTest(target=target, offset=offset):
                    self.fresh()
                    def add(document, target=target, offset=offset):
                        rows = document["required_capture"]
                        index = [row["target"] for row in rows].index(target)
                        stale = json.loads(json.dumps(rows[index]))
                        stale["registry_status"] = "blocked"
                        rows.insert(index + offset, stale)
                    self.edit_json(CAPTURE, add)
                    found = findings(self.root)
                    self.assertIn("required-capture-targets", found)
                    self.assertIn(f"registry_status:{target}", found)

    def test_a_capture_row_for_an_undeclared_target_is_found(self):
        def add(document):
            row = json.loads(json.dumps(document["required_capture"][0]))
            row["target"] = "undeclared"
            document["required_capture"].append(row)
        self.edit_json(CAPTURE, add)
        self.assertEqual(findings(self.root), ["required-capture-targets"])

    def test_capture_rows_out_of_place_are_found(self):
        self.edit_json(
            CAPTURE, lambda document: document["required_capture"].reverse())
        self.assertEqual(findings(self.root), ["required-capture-targets"])

    def test_a_capture_row_that_disappears_is_found(self):
        for index in range(len(TARGETS)):
            with self.subTest(dropped=TARGETS[index]):
                self.fresh()
                self.edit_json(
                    CAPTURE,
                    lambda document, index=index: document[
                        "required_capture"].pop(index))
                self.assertEqual(
                    findings(self.root), ["required-capture-targets"])

    def test_a_blocker_or_unresolved_typed_where_the_registry_has_none(self):
        for target in TARGETS:
            for field in ("registry_blocker", "unresolved"):
                with self.subTest(target=target, field=field):
                    self.fresh()
                    self.edit_capture_row(
                        target,
                        lambda row, field=field: row.__setitem__(field, "x"))
                    self.assertIn(
                        f"null-parity-{field}:{target}", findings(self.root))

    def test_a_blocker_or_unresolved_returning_to_the_registry_is_found(self):
        for target in TARGETS:
            for ours, theirs in (("registry_blocker", "blocker"),
                                 ("unresolved", "unresolved")):
                with self.subTest(target=target, field=ours):
                    self.fresh()
                    self.edit_registry_row(
                        target,
                        lambda row, theirs=theirs: row.__setitem__(
                            theirs, "reopened"))
                    found = findings(self.root)
                    self.assertIn(f"{ours}:{target}", found)
                    self.assertIn(f"null-parity-{ours}:{target}", found)

    def test_a_dropped_capture_contract_is_found_two_ways(self):
        for target in TARGETS:
            with self.subTest(target=target):
                self.fresh()
                self.edit_capture_row(target, lambda row: row["contracts"].pop())
                found = findings(self.root)
                self.assertIn(f"contracts:{target}", found)
                self.assertIn(f"contracts-length:{target}", found)

    def test_a_retyped_contract_address_is_found(self):
        for target in TARGETS:
            with self.subTest(target=target):
                self.fresh()
                self.edit_capture_row(
                    target,
                    lambda row: row["contracts"][-1].__setitem__(
                        "address", "0x" + "0" * 40))
                found = findings(self.root)
                self.assertIn(f"contracts:{target}", found)
                self.assertNotIn(f"contracts-length:{target}", found)

    def test_a_registry_contract_the_record_lacks_is_found(self):
        for target in TARGETS:
            with self.subTest(target=target):
                self.fresh()
                def add(row):
                    contracts = row["deployment"]["contracts"]
                    contracts.append(json.loads(json.dumps(contracts[0])))
                self.edit_registry_row(target, add)
                found = findings(self.root)
                self.assertIn(f"contracts:{target}", found)
                self.assertIn(f"contract_count:{target}", found)
                self.assertIn(f"code_hash_recorded_count:{target}", found)
                self.assertIn(f"sourcify_match_count:{target}", found)

    def test_a_registry_row_falling_back_to_blocked_is_found(self):
        for target in TARGETS:
            with self.subTest(target=target):
                self.fresh()
                self.edit_registry_row(
                    target, lambda row: row.__setitem__("status", "blocked"))
                found = findings(self.root)
                self.assertIn(f"registry_status:{target}", found)
                self.assertEqual("v1-registry-resolved" in found, target == V1)

    def test_a_registry_row_that_disappears_is_found(self):
        for target in TARGETS:
            with self.subTest(target=target):
                self.fresh()
                self.edit_registry_row(
                    target, lambda row: row.__setitem__("id", "renamed"))
                self.assertIn(f"row-missing:{target}", findings(self.root))

    def test_a_reference_target_missing_an_estate_is_found(self):
        for index in (0, 1):
            with self.subTest(dropped=ESTATES[index]):
                self.fresh()
                self.edit_json(
                    CAPTURE,
                    lambda document, index=index: document["selection"][
                        "reference_target"].pop(index))
                self.assertEqual(findings(self.root), ["reference-target"])

    def test_prose_naming_another_revision_is_found(self):
        capture = json.loads((self.root / CAPTURE).read_text(encoding="utf-8"))
        path = self.root / PROSE
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                capture["source_revision"], "0" * 40),
            encoding="utf-8")
        self.assertEqual(findings(self.root), ["prose-source-revision"])

    def test_prose_naming_another_status_is_found(self):
        capture = json.loads((self.root / CAPTURE).read_text(encoding="utf-8"))
        for row in capture["required_capture"]:
            target, status = row["target"], row["registry_status"]
            with self.subTest(target=target):
                self.fresh()
                path = self.root / PROSE
                text = path.read_text(encoding="utf-8")
                changed = re.sub(
                    rf"^(\| `{re.escape(target)}` \| \w+ \| )"
                    rf"{re.escape(status)}( \|)$",
                    r"\1another\2", text, flags=re.MULTILINE)
                self.assertNotEqual(changed, text)
                path.write_text(changed, encoding="utf-8")
                self.assertIn(f"prose-status:{target}", findings(self.root))

    def registry_contract(self, registry: dict, target: str, wanted) -> int:
        """Index of the first contract in ``target``'s row that ``wanted`` accepts."""
        contracts = registry_row(registry, target)["deployment"]["contracts"]
        for index, contract in enumerate(contracts):
            if wanted(contract["code_match"]):
                return index
        self.fail(f"no contract in {target} matches")

    def committed_registry(self) -> dict:
        return json.loads((self.root / REGISTRY).read_text(encoding="utf-8"))

    def registry_edit_findings(self) -> list[str]:
        """Findings after a registry edit, less the digest rows it must move."""
        found = findings(self.root)
        moved = (f"input-bytes:{REGISTRY.as_posix()}",
                 f"input-sha256:{REGISTRY.as_posix()}")
        self.assertIn(moved[1], found)
        return [name for name in found if name not in moved]

    def test_the_record_as_it_stood_at_entry_is_found(self):
        """No aave-v3 row, and aave-v3 still listed blocked and bare."""
        def restore(document):
            document["required_capture"] = [
                row for row in document["required_capture"]
                if row["target"] != AAVE]
            selection = document["selection"]
            selection["admitted_targets_blocked"] = list(
                selection["admitted_targets"])
            selection["admitted_targets_without_deployment"] = [AAVE] + (
                selection["admitted_targets_without_deployment"])
        self.edit_json(CAPTURE, restore)
        self.assertEqual(findings(self.root), [
            "required-capture-targets",
            "selection-blocked",
            "selection-without-deployment",
        ])

    def test_a_contract_count_disagreeing_with_its_contracts_is_found(self):
        for target in TARGETS:
            with self.subTest(target=target):
                self.fresh()
                self.edit_capture_row(
                    target,
                    lambda row: row.__setitem__(
                        "contract_count", row["contract_count"] + 1))
                self.assertEqual(findings(self.root), [
                    f"contract_count:{target}",
                    f"contracts-length:{target}",
                ])

    def test_a_verification_outside_sourcify_is_not_counted(self):
        index = self.registry_contract(
            self.committed_registry(), AAVE,
            lambda match: match.get("verification", "").startswith(
                SOURCIFY_PREFIX))
        self.edit_registry_row(
            AAVE,
            lambda row: row["deployment"]["contracts"][index][
                "code_match"].__setitem__(
                    "verification", "blockscout eth-bytecode-db:partial"))
        self.assertEqual(self.registry_edit_findings(), [
            f"contracts:{AAVE}",
            f"sourcify_match_count:{AAVE}",
        ])

    def test_an_exact_and_a_plain_sourcify_match_both_count(self):
        for before, after in (("match", "exact_match"),
                              ("exact_match", "match")):
            with self.subTest(before=before, after=after):
                self.fresh()
                index = self.registry_contract(
                    self.committed_registry(), AAVE,
                    lambda match, before=before: match.get(
                        "verification") == SOURCIFY_PREFIX + before)
                self.edit_registry_row(
                    AAVE,
                    lambda row, index=index, after=after: row["deployment"][
                        "contracts"][index]["code_match"].__setitem__(
                            "verification", SOURCIFY_PREFIX + after))
                self.assertEqual(self.registry_edit_findings(), [f"contracts:{AAVE}"])

    def test_a_contract_carrying_both_sourcify_fields_is_refused_by_name(self):
        for target in TARGETS:
            with self.subTest(target=target):
                self.fresh()
                registry = self.committed_registry()
                index = self.registry_contract(
                    registry, target,
                    lambda match: "sourcify" in match or match.get(
                        "verification", "").startswith(SOURCIFY_PREFIX))
                address = registry_row(registry, target)["deployment"][
                    "contracts"][index]["address"]
                def both(row, index=index):
                    match = row["deployment"]["contracts"][index]["code_match"]
                    match.setdefault("sourcify", "match")
                    match.setdefault("verification", SOURCIFY_PREFIX + "match")
                self.edit_registry_row(target, both)
                self.assertEqual(
                    self.registry_edit_findings(),
                    [f"sourcify-conflict:{target}:{address}"])

    def test_a_registry_row_without_a_deployment_is_refused_by_name(self):
        for target in TARGETS:
            with self.subTest(target=target):
                self.fresh()
                self.edit_registry_row(
                    target, lambda row: row.__setitem__("deployment", None))
                self.assertEqual(self.registry_edit_findings(), [
                    f"deployment-missing:{target}",
                    "selection-without-deployment",
                ])

    def test_each_selection_list_typed_in_the_record_is_found(self):
        cases = {
            "admitted_targets": lambda value: value.pop(),
            "admitted_targets_blocked": lambda value: value.append(AAVE),
            "admitted_targets_without_deployment":
                lambda value: value.append(AAVE),
        }
        for field, change in cases.items():
            with self.subTest(field=field):
                self.fresh()
                self.edit_json(
                    CAPTURE,
                    lambda document, field=field, change=change: change(
                        document["selection"][field]))
                self.assertEqual(
                    findings(self.root), [SELECTION_FINDINGS[field]])

    def test_a_typed_admitted_target_count_is_found(self):
        def change(document):
            document["selection"]["admitted_target_count"] += 1
        self.edit_json(CAPTURE, change)
        self.assertEqual(
            findings(self.root), ["selection-admitted-target-count"])

    def test_a_blocked_row_resolving_moves_the_blocked_list(self):
        target = derive_selection(
            self.committed_registry())["admitted_targets_blocked"][0]
        self.edit_registry_row(
            target, lambda row: row.__setitem__("status", "resolved"))
        self.assertEqual(self.registry_edit_findings(), ["selection-blocked"])

    def test_a_deployment_recorded_moves_the_without_deployment_list(self):
        target = derive_selection(
            self.committed_registry())["admitted_targets_without_deployment"][0]
        self.edit_registry_row(
            target,
            lambda row: row.__setitem__("deployment", {"contracts": []}))
        self.assertEqual(
            self.registry_edit_findings(), ["selection-without-deployment"])

    def test_an_admitted_slot_change_moves_the_admitted_lists(self):
        def drop(document):
            for slot in document["scope"]["ordered_slots"]:
                if AAVE in slot["targets"]:
                    slot["targets"].remove(AAVE)
        self.edit_json(REGISTRY, drop)
        self.assertEqual(self.registry_edit_findings(), [
            "selection-admitted-targets",
            "selection-admitted-target-count",
        ])

    def test_an_admitted_target_without_a_row_is_refused_by_name(self):
        def add(document):
            document["scope"]["ordered_slots"][-1]["targets"].append(
                "undeclared")
        self.edit_json(REGISTRY, add)
        self.assertEqual(
            self.registry_edit_findings(), ["admitted-row-missing:undeclared"])


if __name__ == "__main__":
    unittest.main()
