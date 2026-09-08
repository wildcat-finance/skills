"""Step 12: a second registered implementation reads a second declared format.

The defect this step answers is a mapper that cannot tell whether the bytes it
was handed are its format. Read the three committed `AUDIT_SYNOPSIS.md` files
with the Warden implementation and it returns 31 rounds and 0 findings: a whole
corpus arrives empty, and nothing anywhere says the format was wrong. That
control is exact and is reproduced below, because it is the number the guard
exists to separate from a real 0.

The synopsis implementation reads its own header first and refuses `A079`
before a cell is read, then splits each round line on `<br>` and hands the
producer's own cells to the grammar the first implementation owns. Over the
same three files it returns 31 rounds and 41 findings, which are the same 41
findings the pilot preserves. The second corpus is therefore a second format
over one producer's records, and not a second producer.

Two things this suite does not establish. It does not establish that the
registry is unwritable after import, and it does not run the full
`fail-open-mapper` probe set or the `synopsis-cell-splitting` cases; both are
runbook step 3's.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
import unittest


PLUGIN_ROOT = Path(__file__).resolve(strict=True).parents[1]
WORKTREE = PLUGIN_ROOT.parents[1]
SCRIPT = PLUGIN_ROOT / "skills/anamnesis/scripts/anamnesis.py"

PILOT = PLUGIN_ROOT / "specimens/pilot"
ESTATE = PLUGIN_ROOT / "specimens/estate"
SYNOPSIS = PLUGIN_ROOT / "specimens/synopsis"
RELEASE = SYNOPSIS / "release"
PROJECTIONS = SYNOPSIS / "projections"

RECORD_HOME = PLUGIN_ROOT / "docs/resolved-mapper"
RECORD = RECORD_HOME / "design-evidence.json"
REPORTS = RECORD_HOME / "reports"
CONFORMANCE = "second-corpus-rebuilds-deterministically"
SELECTED = "registry-and-synopsis-mapper"
REPORT_NAME = f"{SELECTED}-{CONFORMANCE}.json"
RUN_REPORT = WORKTREE / ".hexaemeron/reports" / REPORT_NAME
RESOLVER = (
    "python3 plugins/anamnesis/skills/anamnesis/scripts/anamnesis.py "
    "verify-rebuild --specimen plugins/anamnesis/specimens/synopsis"
)

DECLARED = {"name": "fiat-audit-synopsis", "version": "1"}
WARDEN = {"name": "warden-audit-round-markdown", "version": "1"}
RULE = "A079"

# The three shipped release ids. The synopsis corpus is a third identity: it
# holds the pilot's findings, and it is not the pilot's release.
SYNOPSIS_RELEASE = "74c591e1f010868b3aadd048cdeb6db20df9ea4ac146b43f52c577a41dd6ac39"
PILOT_RELEASE = "41d640fb168049d5061e12c9d7282dafad2266343eeb0be2a078db8797c0bfbf"
ESTATE_RELEASE = "509239765f9fa2db782d3bc70fadea3b05411fc0638402fe5e0a43882f0063e3"

# Each synopsis header names the audit record it was rendered from, by digest.
# These are the digests the pilot's admission policy already records for the
# same three records, which is what makes "the same findings" mechanical.
RENDERED_FROM = {
    "hexaemeron-audit-synopsis":
        "8acff29ed567c97902941a85d72e41171c10850de6aa898b5d50564248eac28f",
    "pandects-audit-synopsis":
        "66908cb68630f3c3cbea432aec6cf6efc305bcab85ccf5fadb278c535635edf9",
    "tabularium-audit-synopsis":
        "1de310b5df5784d7e623ea9dbda83ae77e02cb1798b3aeedffc5d0c715f8e3a7",
}
PILOT_SOURCE_OF = {
    "hexaemeron-audit-synopsis": "hexaemeron-audit-rounds",
    "pandects-audit-synopsis": "pandects-audit-rounds",
    "tabularium-audit-synopsis": "tabularium-audit-rounds",
}

ROUNDS = 31
FINDINGS = 41
RECORDS = 41
BOUNDS = {"minimum": 25, "maximum": 50}

# What the specimen's own bytes may not carry. A corpus that names a machine,
# a host or a forge account cannot be rebuilt by a stranger from the repository
# alone, and the byte cap and digest re-check say nothing about that.
LOCATIONS = {
    "URL scheme": re.compile(r"[a-zA-Z][a-zA-Z0-9+.\-]*://"),
    "scp-style remote": re.compile(r"\bgit@"),
    "absolute filesystem path":
        re.compile(r"(?<![\w.])/(?:Users|home|tmp|var|private|opt|etc)/"),
    "home-relative path": re.compile(r"~/"),
    "parent-relative path": re.compile(r"(?<![\w.])\.\./"),
    "drive letter": re.compile(r"\b[A-Za-z]:[\\/]"),
    "repository slug":
        re.compile(r"\b(?:wildcat-finance|github\.com|gitlab\.com)/"),
}


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


anamnesis = load("anamnesis_synopsis", SCRIPT)


def scratch_directory(prefix: str = "anamnesis-s12-"):
    """Transient space under the ignored top-level tmp/, which git never sees."""
    scratch = WORKTREE / "tmp"
    scratch.mkdir(exist_ok=True)
    return tempfile.TemporaryDirectory(dir=scratch, prefix=prefix)


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def source_text(source_id):
    return (SYNOPSIS / "sources" / f"{source_id}.md").read_text(encoding="utf-8")


class Fixture(unittest.TestCase):
    def setUp(self) -> None:
        holder = scratch_directory()
        self.addCleanup(holder.cleanup)
        self.scratch = Path(holder.name)

    def copy_specimen(self, shipped: Path) -> Path:
        """A writable copy of a shipped specimen, without its built release."""
        target = self.scratch / shipped.name
        shutil.copytree(shipped, target)
        shutil.rmtree(target / "release")
        shutil.rmtree(target / "projections", ignore_errors=True)
        return target

    def refusal(self, call):
        with self.assertRaises(anamnesis.Refusal) as caught:
            call()
        return caught.exception


class BytesThatAreNotTheFormatAreRefused(Fixture):
    """`fail-open-mapper` at the second entry: the header decides, not the rows."""

    def test_a_wrong_or_missing_header_refuses_a079_and_returns_no_rounds(self) -> None:
        original = source_text("pandects-audit-synopsis")
        header, body = original.split("\n", 1)
        self.assertTrue(header.startswith("Synopsis schema="))
        probes = {
            "another schema": header.replace(
                anamnesis.SYNOPSIS_SCHEMA, "fiat-audit-synopsis/v2") + "\n" + body,
            "no schema field": "Synopsis source=plugins/pandects/audit/AUDIT.md\n" + body,
            "header-less": body,
            "empty": "",
        }
        for label, text in probes.items():
            with self.subTest(probe=label):
                refusal = self.refusal(
                    lambda: anamnesis.parse_synopsis(text, "pandects-audit-synopsis"))
                self.assertEqual(refusal.code, RULE)
                self.assertEqual(refusal.record, "pandects-audit-synopsis")
        # The format it does accept, so the refusals above are about the header
        # and not about the body.
        self.assertEqual(
            len(anamnesis.parse_synopsis(original, "pandects-audit-synopsis")), 16)

    def test_the_refusal_reaches_the_event_stream_it_shares_with_admission(self) -> None:
        """On-call question 3: "0 findings" and "not my format" are two answers.

        `A079` is raised inside the recorded span, so a source in the wrong
        format leaves the same durable `anamnesis.source.refused` event an
        admission refusal leaves, rather than an empty corpus and no signal.
        """
        specimen = self.copy_specimen(SYNOPSIS)
        target = specimen / "sources/hexaemeron-audit-synopsis.md"
        body = target.read_text(encoding="utf-8").split("\n", 1)[1]
        target.write_text(body, encoding="utf-8")
        policy = read(specimen / "policy.json")
        for entry in policy["sources"]:
            if entry["id"] == "hexaemeron-audit-synopsis":
                entry["bytes"] = len(body.encode("utf-8"))
                entry["sha256"] = hashlib.sha256(body.encode("utf-8")).hexdigest()
        (specimen / "policy.json").write_text(
            json.dumps(policy, indent=2) + "\n", encoding="utf-8")

        stream = self.scratch / "refused.jsonl"
        parser = anamnesis.build_parser()
        arguments = parser.parse_args([
            "curate",
            "--policy", str(specimen / "policy.json"),
            "--curation-policy", str(specimen / "curation-policy.json"),
            "--events", str(stream),
        ])
        refusal = self.refusal(lambda: arguments.handler(arguments))
        self.assertEqual(refusal.code, RULE)
        written = [json.loads(line) for line in
                   stream.read_text(encoding="utf-8").splitlines()]
        refused = [e for e in written if e["event"] == "anamnesis.source.refused"]
        self.assertEqual([e["rule"] for e in refused], [RULE])
        self.assertEqual(refused[0]["record"], "hexaemeron-audit-synopsis")
        self.assertEqual(refused[0]["policy_version"], policy["policy_version"])
        self.assertEqual(len(refused[0]["correlation_id"]), 16)


class TheControlIsExact(unittest.TestCase):
    """The two implementations over one set of bytes, and the gap between them."""

    def test_the_warden_entry_reads_thirty_one_empty_rounds_and_the_second_reads_forty_one(self) -> None:
        warden = anamnesis.resolve_mapper(WARDEN)
        synopsis = anamnesis.resolve_mapper(DECLARED)
        self.assertIsNot(warden.parse, synopsis.parse)
        counted = {}
        for entry in (warden, synopsis):
            rounds = findings = empty = 0
            for source_id in sorted(RENDERED_FROM):
                read_rounds = entry.parse(source_text(source_id), source_id)
                rounds += len(read_rounds)
                findings += sum(len(r["findings"]) for r in read_rounds)
                empty += sum(1 for r in read_rounds if not r["findings"])
            counted[entry.name] = (rounds, findings, empty)
        # The fail-open reading: every round found, every finding lost, and no
        # refusal to say the format was wrong.
        self.assertEqual(counted["warden-audit-round-markdown"], (ROUNDS, 0, ROUNDS))
        self.assertEqual(counted["fiat-audit-synopsis"], (ROUNDS, FINDINGS, 12))

    def test_each_header_names_the_digest_the_pilot_admitted_for_that_record(self) -> None:
        admitted = {
            source["id"]: source["sha256"]
            for source in read(PILOT / "policy.json")["sources"]
        }
        for source_id, digest in RENDERED_FROM.items():
            with self.subTest(source=source_id):
                header = source_text(source_id).split("\n", 1)[0]
                self.assertIn(f"source_sha256={digest}", header)
                self.assertEqual(admitted[PILOT_SOURCE_OF[source_id]], digest)

    def test_the_same_bytes_under_the_pilot_curation_policy_refuse(self) -> None:
        """A policy-level read never reaches the mapper at all.

        The pilot's declared scope names the pilot's three source ids, so the
        synopsis sources refuse `A074` at the scope check, before the declared
        implementation is handed anything. The 31 empty rounds above are what a
        direct call to the Warden implementation returns, which is the control
        this corpus exists to separate from a real result, not what the pilot
        policy admits.
        """
        events = anamnesis.Events()
        result = anamnesis.admit(str(SYNOPSIS / "policy.json"), events)
        refusal = self.assertRaises(anamnesis.Refusal)
        with refusal:
            anamnesis._admitted_within_scope(
                events, result, str(PILOT / "curation-policy.json"))
        self.assertEqual(refusal.exception.code, "A074")
        self.assertIn("warden-seed-pilot", refusal.exception.message)
        self.assertIn(refusal.exception.record, RENDERED_FROM)
        refused = [e for e in events.emitted
                   if e["event"] == "anamnesis.source.refused"]
        self.assertEqual([e["rule"] for e in refused], ["A074"])


class TheThirdCorpusRebuilds(Fixture):
    def test_two_fresh_builds_agree_and_equal_the_committed_release(self) -> None:
        specimen = self.copy_specimen(SYNOPSIS)
        release_id, components = anamnesis.verify_rebuild(str(specimen))
        self.assertEqual(release_id, SYNOPSIS_RELEASE)
        self.assertEqual(components, 7)
        manifest, _ = anamnesis.verify_release(str(RELEASE))
        self.assertEqual(manifest["release_id"], release_id)
        self.assertEqual(manifest["counts"]["rounds"], ROUNDS)
        self.assertEqual(manifest["counts"]["findings"], FINDINGS)
        self.assertEqual(manifest["counts"]["rounds_with_no_findings"], 12)
        self.assertEqual(manifest["exclusions"], [])
        # A third identity. It holds the pilot's findings and is not the pilot.
        self.assertNotIn(release_id, (PILOT_RELEASE, ESTATE_RELEASE))

    def test_the_committed_projections_equal_fresh_ones(self) -> None:
        fresh = {
            "elenchus-severity-high.json":
                anamnesis.analogues(str(RELEASE), "severity", "high"),
            "synkrisis-cohort.json": anamnesis.observations(
                str(RELEASE), "every public finding in the release"),
        }
        for name, payload in fresh.items():
            with self.subTest(projection=name):
                committed = (PROJECTIONS / name).read_text(encoding="utf-8")
                self.assertEqual(json.loads(committed), payload)
                self.assertEqual(
                    committed, json.dumps(payload, indent=2, sort_keys=True) + "\n")

    def test_both_shipped_corpora_still_rebuild_to_their_committed_ids(self) -> None:
        """`release-identity-drift`: a second entry moves neither shipped id."""
        for shipped, expected in ((PILOT, PILOT_RELEASE), (ESTATE, ESTATE_RELEASE)):
            with self.subTest(specimen=shipped.name):
                specimen = self.copy_specimen(shipped)
                release_id, _ = anamnesis.verify_rebuild(str(specimen))
                self.assertEqual(release_id, expected)
                self.assertEqual(
                    read(shipped / "curation-policy.json")["mapper"], WARDEN)


class TheThirdCorpusDeclaresWhatItHolds(Fixture):
    """`third-corpus-rights-basis` and `scope-bounds-for-the-third-corpus`."""

    def test_every_source_is_licensed_apache_and_names_no_location(self) -> None:
        policy = read(SYNOPSIS / "policy.json")
        self.assertEqual(len(policy["sources"]), 3)
        for source in policy["sources"]:
            with self.subTest(source=source["id"]):
                rights = source["rights"]
                self.assertEqual(rights["basis"], "licence")
                self.assertEqual(rights["disclosure"], "public")
                self.assertEqual(rights["holder"], "Wildcat Labs")
                self.assertIn("Apache-2.0", rights["statement"])
                self.assertIn("LICENSE", rights["statement"])
                self.assertTrue(rights["statement"].strip())
        for path in sorted(SYNOPSIS.rglob("*")):
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8")
            for label, pattern in LOCATIONS.items():
                with self.subTest(file=path.name, carries=label):
                    self.assertIsNone(pattern.search(text))
            with self.subTest(file=path.name, carries="this checkout"):
                self.assertNotIn(str(WORKTREE), text)

    def test_the_declared_bounds_hold_forty_one_and_refuse_outside_them(self) -> None:
        policy = anamnesis.load_curation_policy(str(SYNOPSIS / "curation-policy.json"))
        self.assertEqual(policy["mapper"], DECLARED)
        self.assertEqual(policy["scope"]["records"], BOUNDS)
        result = anamnesis.admit(str(SYNOPSIS / "policy.json"), anamnesis.Events())
        self.assertEqual(result["records"], RECORDS)
        self.assertEqual(result["total_bytes"], 36455)
        anamnesis.check_scope(policy, result["sources"], RECORDS)
        for count in (BOUNDS["minimum"] - 1, BOUNDS["maximum"] + 1):
            with self.subTest(records=count):
                refusal = self.refusal(
                    lambda: anamnesis.check_scope(policy, result["sources"], count))
                self.assertEqual(refusal.code, "A073")
                self.assertIn("25 to 50", refusal.message)

    def test_the_preserves_sentence_names_what_the_pilot_preserves(self) -> None:
        """Decision 3's second home, inside the release and hashed into its id."""
        preserves = read(SYNOPSIS / "curation-policy.json")["scope"]["preserves"]
        self.assertIn("the same three audit records the pilot preserves", preserves.lower())
        for name in ("Hexaemeron", "Pandects", "Tabularium"):
            with self.subTest(record=name):
                self.assertIn(name, preserves)
        self.assertIn(anamnesis.SYNOPSIS_SCHEMA, preserves)
        # It is inside the release, so it cannot be edited without moving the id.
        self.assertEqual(read(RELEASE / "policy.json")["scope"]["preserves"], preserves)
        # And the claim is mechanical: the same 41 (record, native id, round)
        # triples the pilot declares, under the synopsis source ids.
        def triples(policy, suffix):
            return {(r["source"][:-len(suffix)], r["native_id"], r["round"])
                    for r in policy["records"]}
        self.assertEqual(
            triples(read(SYNOPSIS / "policy.json"), "-audit-synopsis"),
            triples(read(PILOT / "policy.json"), "-audit-rounds"),
        )


class TheConformanceReportIsCommitted(unittest.TestCase):
    """The `step:3` cell the controller checks at this step's push."""

    def test_the_report_is_one_closed_object_standing_in_both_homes(self) -> None:
        body = (REPORTS / REPORT_NAME).read_bytes()
        report = json.loads(body.decode("utf-8"))
        self.assertEqual(set(report), {
            "schema", "candidate", "criterion", "value", "unit", "command", "exit"})
        self.assertEqual(report["schema"], "protasis-design-report/v1")
        self.assertEqual(report["candidate"], SELECTED)
        self.assertEqual(report["criterion"], CONFORMANCE)
        self.assertEqual(report["unit"], "boolean")
        self.assertIs(report["value"], True)
        self.assertEqual(report["exit"], 0)
        self.assertEqual(report["command"], RESOLVER)
        # The record's own pending cell names that resolver, so the report
        # answers the criterion the record is waiting on.
        cell = next(
            entry for entry in read(RECORD)["results"]
            if entry["candidate"] == SELECTED and entry["criterion"] == CONFORMANCE
        )
        self.assertEqual(cell["resolver"], RESOLVER)
        if RUN_REPORT.exists():
            self.assertEqual(RUN_REPORT.read_bytes(), body)

        # And the reason `resolve.py` was not re-run: the record binds the 32
        # reports step 1 receipted by digest, and a rerun would rewrite them.
        resolved = [cell for cell in read(RECORD)["results"] if cell["state"] != "pending"]
        self.assertEqual(len(resolved), 32)
        for cell in resolved:
            with self.subTest(candidate=cell["candidate"], criterion=cell["criterion"]):
                body = (RECORD_HOME / cell["report"]["path"]).read_bytes()
                self.assertEqual(
                    hashlib.sha256(body).hexdigest(), cell["report"]["sha256"])
        # Thirty-two of them, and the one this step wrote.
        self.assertEqual(len(sorted(REPORTS.glob("*.json"))), 33)


if __name__ == "__main__":
    unittest.main()
