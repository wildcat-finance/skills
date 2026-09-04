"""Checks for harness-classification/v1 and the probe that writes it.

The roster schema is the contract three generated wording surfaces will be
rendered from, so ``SchemaTests`` holds the two things that are expensive to
reverse once prose exists: the four classification names, and the observation
fields every harness entry has to carry.

``jsonschema`` is a Lazarus dependency rather than a root one, so no case here
may depend on it being installed. Each case asserts against the schema document
itself, which always runs, and then asserts the same rule behaviourally when the
library happens to be importable. A host without the library still checks the
declared rule; it does not quietly skip.

The other four classes hold ``scripts/probe_harnesses.py``. The schema fixes
the roster's vocabulary and refuses an unknown name, and its own description
says so, but it will admit an earned class on an entry that never ran a client.
ADR-077 puts that enforcement in the probe's classifier, and these are the cases
that hold it there.

``ClassifierTests`` sweeps the input matrix for a shape that reaches an earned
class without a recorded client run. ``SubprocessTests`` holds the command
boundary: a fixed argv, no shell, nothing read out of a manifest, and a client
that goes quiet recorded as unread rather than as absent. ``CredentialTests``
feeds the probe a client output fixture carrying a token and sweeps both the
manifest and the log for it. ``KilledProbeTests`` kills a real child process
between the temporary write and the rename, and is the resolver for the
``killed-probe-recovery`` gate; it writes that gate's report on the way out.
``GateReportTests`` holds that report to the run that earned it in both
directions: a partial selection of the class cannot report a failure nothing
observed, and a case that failed cannot report success. The second direction is
the dangerous one, because ``subTest`` swallows a failure and lets the rest of
the case run, including the statement where it flags itself passed.
"""

from __future__ import annotations

import contextlib
import importlib.util
import itertools
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas/harness-classification-v1.json"
PROBE_PATH = ROOT / "scripts/probe_harnesses.py"
SCHEMA_ID = "harness-classification/v1"

_SPEC = importlib.util.spec_from_file_location("probe_harnesses", PROBE_PATH)
probe_harnesses = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = probe_harnesses
_SPEC.loader.exec_module(probe_harnesses)

CLASSIFICATIONS = (
    "Atlas launcher",
    "tested local route",
    "manual route",
    "unsupported",
)

# The two classes a harness only reaches by a recorded client run.
EARNED_CLASSIFICATIONS = ("Atlas launcher", "tested local route")

OBSERVATION_FIELDS = (
    "client_present",
    "client_version",
    "auth_configured",
    "launcher_contract",
    "blocker",
)

# `version_read` is derived rather than read off the host, and it is what the
# schema tells a reader to consult instead of recognising the `unread`
# sentinel. That instruction only means something if every entry carries the
# field, because one that sits in `properties` alone constrains its value where
# a producer supplies one and compels nothing where it does not.
DERIVED_FIELDS = ("version_read",)

REQUIRED_ENTRY_FIELDS = OBSERVATION_FIELDS + DERIVED_FIELDS

# ADR-077 names these two optional in as many words, so the schema may not
# quietly start requiring them. A tightening here is a decision the record
# owns, not an audit fix.
OPTIONAL_ENTRY_FIELDS = ("testable_here", "probe")

# The six harnesses issue #856 asks about. Named here so a missing-field case
# removes a field from a realistic record rather than from a stub.
HARNESSES = (
    "GitHub Copilot",
    "Cursor",
    "Gemini CLI",
    "Windsurf",
    "Cline",
    "Roo Code",
)


def load_schema():
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def validator():
    """A Draft 2020-12 validator, or None where the library is absent."""
    try:
        import jsonschema
    except ImportError:
        return None
    schema = load_schema()
    jsonschema.Draft202012Validator.check_schema(schema)
    return jsonschema.Draft202012Validator(schema)


def entry(name, **overrides):
    record = {
        "name": name,
        "classification": "manual route",
        "client_present": False,
        "client_version": None,
        "version_read": False,
        "auth_configured": False,
        "launcher_contract": "documented deep link, not exercised here",
        "blocker": "absent from this host and unauthenticated",
        "testable_here": False,
    }
    record.update(overrides)
    return record


def shaped(classification):
    """Entry overrides that keep a record coherent with the class it carries.

    An earned class is only ever written against a recorded client run, so the
    two earned names get one here. The schema does not enforce that pairing --
    the probe's classifier does -- and this helper exists so that no case in
    this file asserts an unearned earned class is a valid record.
    """
    if classification not in EARNED_CLASSIFICATIONS:
        return {"classification": classification}
    return {
        "classification": classification,
        "client_present": True,
        "client_version": "2026.8.1",
        "version_read": True,
        "auth_configured": True,
        "launcher_contract": "deep link exercised on this host",
        "blocker": None,
        "testable_here": True,
        "probe": {"command": ["cursor", "--version"], "result": "2026.8.1"},
    }


def manifest(*entries):
    return {
        "schema": SCHEMA_ID,
        "recorded": {
            "host": "darwin-arm64",
            "date": "2026-09-04",
            "base_ref": "8dc3aca54adeca49387a2bdfc174cf6e72d02a11",
        },
        "harnesses": list(entries) or [entry(name) for name in HARNESSES],
    }


class SchemaTests(unittest.TestCase):
    def setUp(self):
        self.schema = load_schema()
        self.validator = validator()
        self.harness = self.schema["$defs"]["harness"]

    def assert_valid(self, document):
        if self.validator is None:
            return
        self.assertEqual([e.message for e in self.validator.iter_errors(document)], [])

    def assert_refused(self, document):
        if self.validator is None:
            return
        self.assertNotEqual(list(self.validator.iter_errors(document)), [])

    def test_the_schema_is_the_published_roster_contract(self):
        self.assertEqual(self.schema["properties"]["schema"]["const"], SCHEMA_ID)
        self.assertEqual(
            self.schema["$id"],
            "https://wildcat.finance/schemas/harness-classification-v1.json",
        )
        self.assert_valid(manifest())

    def test_the_four_classification_names_are_exactly_these_four(self):
        declared = self.schema["$defs"]["classification"]["enum"]
        self.assertEqual(tuple(declared), CLASSIFICATIONS)

    def test_each_classification_name_is_admitted(self):
        declared = self.schema["$defs"]["classification"]["enum"]
        for name in CLASSIFICATIONS:
            with self.subTest(classification=name):
                # Document level, so this case still checks something on a host
                # without jsonschema: the enum carries the name, which is what
                # makes any validator reading this schema admit it.
                self.assertIn(name, declared)
                self.assert_valid(manifest(entry("Cursor", **shaped(name))))

    def test_an_unknown_classification_name_is_refused(self):
        declared = self.schema["$defs"]["classification"]
        # A closed enum is what refuses the unknown name. A type keyword beside
        # it would admit any string the enum forgot.
        self.assertEqual(set(declared), {"enum", "description"})
        for unknown in ("tested", "Atlas Launcher", "supported", ""):
            with self.subTest(classification=unknown):
                self.assertNotIn(unknown, declared["enum"])
                self.assert_refused(
                    manifest(entry("Cursor", classification=unknown))
                )

    def test_every_harness_entry_requires_every_observed_and_derived_field(self):
        required = self.harness["required"]
        for field in REQUIRED_ENTRY_FIELDS:
            with self.subTest(field=field):
                self.assertIn(field, required)
        self.assertFalse(self.harness["additionalProperties"])
        document = manifest()
        self.assertEqual(len(document["harnesses"]), len(HARNESSES))
        self.assert_valid(document)

    def test_every_declared_field_is_either_required_or_named_optional(self):
        # ADR-077 enumerates this entry and states which two fields are
        # optional, so the schema and the record can be read against each
        # other. A field added to `properties` without landing in `required`
        # or in the optional pair is the drift that put a required
        # `version_read` outside the record's enumeration in the first place.
        declared = set(self.harness["properties"])
        required = set(self.harness["required"])
        self.assertEqual(
            declared - required,
            set(OPTIONAL_ENTRY_FIELDS),
            "a declared field is neither required nor one ADR-077 calls optional",
        )
        self.assertEqual(
            required,
            {"name", "classification"} | set(REQUIRED_ENTRY_FIELDS),
        )

    def test_a_harness_entry_missing_any_required_field_is_refused(self):
        for field in REQUIRED_ENTRY_FIELDS:
            with self.subTest(field=field):
                # Document level: being listed in `required` is the mechanism
                # that turns the omission below into a refusal. A field that
                # sits in `properties` alone constrains its value where a
                # producer supplies one and compels nothing where it does not,
                # which is what makes an optional `version_read` no better than
                # the sentinel it was added to replace.
                self.assertIn(field, self.harness["required"])
                record = entry("Cline")
                del record[field]
                self.assert_refused(manifest(record))

    def test_the_fields_adr_076_calls_optional_stay_optional(self):
        # ADR-077 enumerates the entry and calls `testable_here` and `probe`
        # optional in as many words. Requiring either would put the schema at
        # odds with the record that pins it, so the omission has to keep
        # validating even though the generator always writes `testable_here`.
        for field in OPTIONAL_ENTRY_FIELDS:
            with self.subTest(field=field):
                self.assertIn(field, self.harness["properties"])
                self.assertNotIn(field, self.harness["required"])
        record = entry("Cline")
        for field in OPTIONAL_ENTRY_FIELDS:
            record.pop(field, None)
        self.assert_valid(manifest(record))

    def test_version_read_and_client_version_may_not_disagree(self):
        # The `client_version` description tells a reader to consult
        # `version_read` rather than recognise the sentinel. That instruction
        # is only worth following if the document cannot say both things at
        # once, so the pairing is a schema rule and not a generator habit.
        for label, overrides in (
            (
                "a read version that is the sentinel",
                {"client_present": True, "client_version": "unread", "version_read": True},
            ),
            (
                "a read version that is absent",
                {"client_present": False, "client_version": None, "version_read": True},
            ),
            (
                "an unread version carrying a real version",
                {"client_present": True, "client_version": "2026.8.1", "version_read": False},
            ),
        ):
            with self.subTest(contradiction=label):
                self.assert_refused(manifest(entry("Cursor", **overrides)))
        # Both coherent pairings stand.
        self.assert_valid(
            manifest(
                entry("Cursor", client_present=True, client_version="unread", version_read=False)
            )
        )
        self.assert_valid(
            manifest(
                entry(
                    "Cursor",
                    client_present=True,
                    client_version="2026.8.1",
                    version_read=True,
                    auth_configured=True,
                    testable_here=True,
                )
            )
        )

    def test_a_null_client_version_is_admitted_when_the_client_is_absent(self):
        # Document level: the union type admits null, and the conditional that
        # withdraws it is keyed on client_present being true, so it does not
        # fire for an absent client.
        self.assertIn("null", self.harness["properties"]["client_version"]["type"])
        self.assertEqual(
            self.harness["allOf"][0]["if"]["properties"]["client_present"]["const"],
            True,
        )
        self.assert_valid(
            manifest(entry("Gemini CLI", client_present=False, client_version=None))
        )

    def test_a_null_client_version_is_refused_when_the_client_is_present(self):
        conditional = self.harness["allOf"][0]
        self.assertEqual(conditional["if"]["properties"]["client_present"]["const"], True)
        self.assertIn("client_version", conditional["then"]["properties"])
        self.assert_refused(
            manifest(entry("Cursor", client_present=True, client_version=None))
        )
        self.assert_valid(
            manifest(
                entry(
                    "Cursor",
                    client_present=True,
                    client_version="2026.8.1",
                    # A record carrying a version says a version was read. The
                    # default here is False, for the absent client the helper
                    # describes, and leaving it False beside a real version
                    # would be the contradiction the pairing rule refuses.
                    version_read=True,
                    classification="manual route",
                )
            )
        )


# --------------------------------------------------------------------------
# The probe.


BASE_REF = "8dc3aca54adeca49387a2bdfc174cf6e72d02a11"

# A client output fixture that carries a credential. Every case that feeds the
# probe real-looking output uses this one, so the sweeps are always run against
# something that would fail them if the allowlist leaked.
LEAKING_CLIENT_OUTPUT = (
    "cursor-agent 2026.8.1\n"
    "signed in as someone@example.org\n"
    "bearer: ghp_wxyz1234567890abcdefghijklmnopqrstuv\n"
)
# The case that feeds this to the probe is the evidence that no real one gets
# through, so the fixture has to look like the thing it stands in for.
# phylax: allow a fabricated token this file exists to prove the sweep catches
LEAKED_SECRET = "ghp_wxyz1234567890abcdefghijklmnopqrstuv"


def observation(**overrides):
    """One Observation, defaulting to the shape every client on this host has."""
    record = {
        "name": "Cursor",
        "client_present": False,
        "client_version": None,
        "auth_configured": False,
        "launcher_contract": "none published, so the prompt is moved by hand",
        "launcher_published": False,
        "product_withdrawn": False,
        "standing_blocker": "absent from this host and unauthenticated",
        "probe": None,
    }
    record.update(overrides)
    return probe_harnesses.Observation(**record)


def probe_record(status, version=None, command=("cursor-agent", "--version")):
    results = {
        probe_harnesses.STATUS_ANSWERED: probe_harnesses.RESULT_ANSWERED.format(
            version=version
        ),
        probe_harnesses.STATUS_ABSENT: probe_harnesses.RESULT_ABSENT.format(
            binary=command[0]
        ),
        probe_harnesses.STATUS_UNREAD: probe_harnesses.RESULT_TIMEOUT.format(
            binary=command[0], seconds="10"
        ),
    }
    return probe_harnesses.ProbeRecord(command, results[status], status, version)


ANSWERED = probe_record(probe_harnesses.STATUS_ANSWERED, "2026.8.1")
ABSENT = probe_record(probe_harnesses.STATUS_ABSENT)
UNREAD = probe_record(probe_harnesses.STATUS_UNREAD)

# Every boolean combination the classifier reads, so a case can sweep the input
# space rather than sample it.
FLAG_NAMES = ("client_present", "auth_configured", "launcher_published", "product_withdrawn")
FLAG_MATRIX = tuple(
    dict(zip(FLAG_NAMES, values)) for values in itertools.product((False, True), repeat=4)
)


class RecordingRunner:
    """A stand-in for the probe's default runner that records what it was handed.

    It never spawns anything, so a case can drive the whole roster as if every
    client were installed without this host having one.
    """

    def __init__(self, stdout="cursor-agent 2026.8.1\n", stderr="", returncode=0, raises=None):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode
        self.raises = raises
        self.calls = []

    def __call__(self, argv, timeout):
        self.calls.append((argv, timeout))
        if self.raises is not None:
            raise self.raises(cmd=list(argv), timeout=timeout)
        return subprocess.CompletedProcess(
            list(argv), self.returncode, self.stdout, self.stderr
        )


def present_everywhere(name):
    return f"/usr/local/bin/{name}"


def absent_everywhere(_name):
    return None


class ClassifierTests(unittest.TestCase):
    """No input shape may reach an earned class without a recorded client run."""

    def test_no_input_without_a_recorded_client_run_reaches_an_earned_class(self):
        # A recorded client run is a probe that answered on a client that was
        # found present, so every other pairing belongs in this sweep,
        # including an answered probe on an entry claiming the client is absent.
        probes = (None, ABSENT, UNREAD)
        for flags, probe in itertools.product(FLAG_MATRIX, probes):
            with self.subTest(probe=None if probe is None else probe.status, **flags):
                got = probe_harnesses.classify(observation(probe=probe, **flags))
                self.assertNotIn(got, probe_harnesses.EARNED_CLASSIFICATIONS)
                self.assertIn(got, ("manual route", "unsupported"))
        for flags in FLAG_MATRIX:
            if flags["client_present"]:
                continue
            with self.subTest(probe="answered but not present", **flags):
                got = probe_harnesses.classify(observation(probe=ANSWERED, **flags))
                self.assertNotIn(got, probe_harnesses.EARNED_CLASSIFICATIONS)

    def test_a_recorded_client_run_with_authentication_earns_a_class(self):
        earned = observation(
            probe=ANSWERED,
            client_present=True,
            client_version="2026.8.1",
            auth_configured=True,
        )
        self.assertEqual(probe_harnesses.classify(earned), "tested local route")
        with_launcher = observation(
            probe=ANSWERED,
            client_present=True,
            client_version="2026.8.1",
            auth_configured=True,
            launcher_published=True,
        )
        self.assertEqual(probe_harnesses.classify(with_launcher), "Atlas launcher")
        # An earned class is the one shape that carries no blocker.
        self.assertIsNone(probe_harnesses.blocker_for(earned, "tested local route"))

    def test_a_recorded_client_run_without_authentication_stays_a_manual_route(self):
        unauthenticated = observation(
            probe=ANSWERED,
            client_present=True,
            client_version="2026.8.1",
            auth_configured=False,
            launcher_published=True,
        )
        self.assertEqual(probe_harnesses.classify(unauthenticated), "manual route")
        blocker = probe_harnesses.blocker_for(unauthenticated, "manual route")
        self.assertIn(probe_harnesses.NO_AUTH_SIGNAL.lower(), blocker.lower())
        # The reader is told the run happened as well as why it earned nothing.
        self.assertIn("reported version 2026.8.1", blocker)

    def test_a_withdrawn_product_is_unsupported_whatever_else_it_carries(self):
        for probe, present, auth in (
            (None, False, False),
            (ABSENT, False, False),
            (UNREAD, True, False),
            (ANSWERED, True, True),
        ):
            with self.subTest(probe=None if probe is None else probe.status):
                withdrawn = observation(
                    probe=probe,
                    client_present=present,
                    client_version="2026.8.1" if present else None,
                    auth_configured=auth,
                    launcher_published=True,
                    product_withdrawn=True,
                )
                self.assertEqual(probe_harnesses.classify(withdrawn), "unsupported")

    def test_absence_and_a_failed_authentication_never_collapse(self):
        absent = probe_harnesses.entry_document(observation(probe=ABSENT))
        unread = probe_harnesses.entry_document(
            observation(probe=UNREAD, client_present=True, client_version="unread")
        )
        present = probe_harnesses.entry_document(
            observation(
                probe=ANSWERED, client_present=True, client_version="2026.8.1"
            )
        )
        self.assertEqual(
            [absent["client_present"], unread["client_present"], present["client_present"]],
            [False, True, True],
        )
        # All three are unauthenticated, and all three say so, yet no two of the
        # records are the same. That is the collapse the separate fields refuse.
        self.assertEqual(
            {record["auth_configured"] for record in (absent, unread, present)}, {False}
        )
        self.assertEqual(len({json.dumps(r, sort_keys=True) for r in (absent, unread, present)}), 3)
        self.assertEqual(
            [absent["client_version"], unread["client_version"], present["client_version"]],
            [None, "unread", "2026.8.1"],
        )
        for record in (absent, unread, present):
            with self.subTest(name=record["client_version"]):
                self.assertNotIn(record["classification"], probe_harnesses.EARNED_CLASSIFICATIONS)
                self.assertTrue(record["blocker"])

    def test_version_read_carries_the_unread_encoding_as_a_field(self):
        # The schema requires a non-null client_version wherever the client is
        # present, so a present client that never answered carries the sentinel
        # rather than null. A sentinel is prose, and a reader that has to
        # recognise the literal "unread" to tell a version from the absence of
        # one is a reader the schema has not told the truth to. This is the
        # boolean that keeps the fact machine-readable.
        cases = (
            (ABSENT, False, None, False),
            (UNREAD, True, probe_harnesses.UNREAD_VERSION, False),
            (ANSWERED, True, "2026.8.1", True),
        )
        for probe, present, version, expected in cases:
            with self.subTest(probe=probe.status):
                record = probe_harnesses.entry_document(
                    observation(probe=probe, client_present=present, client_version=version)
                )
                self.assertEqual(record["client_version"], version)
                self.assertIn("version_read", record)
                self.assertEqual(record.get("version_read"), expected)
        # The field says exactly what the sentinel says, and never disagrees
        # with it, so neither can drift away from the other unnoticed.
        for flags, probe in itertools.product(FLAG_MATRIX, (None, ABSENT, UNREAD, ANSWERED)):
            observed = observation(probe=probe, **flags)
            record = probe_harnesses.entry_document(observed)
            with self.subTest(probe=None if probe is None else probe.status, **flags):
                self.assertEqual(
                    record.get("version_read"),
                    record["client_version"] not in (None, probe_harnesses.UNREAD_VERSION),
                )

    def test_a_probe_written_document_validates_against_the_schema(self):
        # entry_document is the only writer of a harnesses entry and the schema
        # closes additionalProperties, so a field added on one side and not the
        # other is a manifest the published contract refuses. This case is the
        # join: it validates what the probe actually writes.
        recorder = probe_harnesses.Recorder("00000000")
        observations = probe_harnesses.probe_roster(
            recorder=recorder,
            runner=RecordingRunner(),
            path_lookup=present_everywhere,
            environ={},
            home=Path(tempfile.gettempdir()),
        )
        document = probe_harnesses.manifest_document(
            observations, host="darwin-arm64", date="2026-09-04", base_ref=BASE_REF
        )
        declared = set(load_schema()["$defs"]["harness"]["properties"])
        for record in document["harnesses"]:
            with self.subTest(harness=record["name"]):
                self.assertEqual(set(record) - declared, set())
        checker = validator()
        if checker is None:
            self.skipTest("jsonschema is a Lazarus dependency and is not installed")
        self.assertEqual([e.message for e in checker.iter_errors(document)], [])

    def test_every_class_the_classifier_returns_is_one_of_the_schema_names(self):
        declared = tuple(load_schema()["$defs"]["classification"]["enum"])
        self.assertEqual(declared, probe_harnesses.CLASSIFICATIONS)
        returned = set()
        for flags, probe in itertools.product(FLAG_MATRIX, (None, ABSENT, UNREAD, ANSWERED)):
            returned.add(probe_harnesses.classify(observation(probe=probe, **flags)))
        self.assertTrue(returned.issubset(set(declared)))
        # The sweep reaches all four, so this is coverage rather than a subset
        # that happens to hold because three names are unreachable.
        self.assertEqual(returned, set(declared))


class SubprocessTests(unittest.TestCase):
    """The command boundary: fixed argv, no shell, bounded, manifest-blind."""

    def test_every_declared_argv_is_a_fixed_list_and_no_shell_is_used(self):
        for harness in probe_harnesses.ROSTER:
            with self.subTest(harness=harness.name):
                argv = harness.probe_argv
                self.assertIsInstance(argv, tuple)
                for word in argv:
                    self.assertIsInstance(word, str)
                    self.assertTrue(word)
                    self.assertFalse(set(word) & set(" \t\n;|&$`<>()*?![]{}'\"\\"))
                if argv:
                    self.assertNotIn("/", argv[0])
                    self.assertFalse(argv[0].startswith("-"))
        source = PROBE_PATH.read_text(encoding="utf-8")
        for forbidden in (
            "shell=True",
            "os.system",
            "os.popen",
            "subprocess.getoutput",
            "subprocess.getstatusoutput",
            "subprocess.call(",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)

    def test_the_default_runner_passes_argv_as_a_list_with_no_shell(self):
        # Two of these words would be swallowed or re-read by a shell. Passed as
        # a list they are one argument, and the version comes back intact.
        harness = probe_harnesses.Harness(
            name="fixture",
            probe_argv=(sys.executable, "-c", "print('fixture 1.2.3 && echo pwned')"),
            auth_env=(),
            auth_files=(),
            launcher_contract="none",
            launcher_published=False,
            product_withdrawn=False,
            standing_blocker="fixture",
        )
        record = probe_harnesses.probe_client(
            harness, timeout=30.0, path_lookup=present_everywhere
        )
        self.assertEqual(record.status, "answered")
        self.assertEqual(record.version, "1.2.3")
        self.assertNotIn("pwned", record.result)
        self.assertEqual(record.command, harness.probe_argv)

    def test_no_probe_argument_is_read_from_a_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "harness-classification.json"
            evidence = root / "hostile-command-ran"
            # A manifest already sitting at the destination, carrying a command
            # somebody would very much like the probe to run.
            hostile = manifest(
                entry(
                    "Cursor",
                    probe={
                        "command": ["sh", "-c", f"touch {evidence}"],
                        "result": "run me",
                    },
                )
            )
            target.write_text(json.dumps(hostile), encoding="utf-8")
            runner = RecordingRunner()
            recorder = probe_harnesses.Recorder("00000000")
            observations = probe_harnesses.probe_roster(
                recorder=recorder,
                runner=runner,
                path_lookup=present_everywhere,
                environ={},
                home=root,
            )
            declared = {h.probe_argv for h in probe_harnesses.ROSTER if h.probe_argv}
            self.assertEqual({argv for argv, _timeout in runner.calls}, declared)
            for argv, _timeout in runner.calls:
                with self.subTest(argv=argv):
                    self.assertNotIn("sh", argv)
                    self.assertNotIn("-c", argv)
                    self.assertNotIn(str(evidence), argv)
            self.assertFalse(evidence.exists())
            document = probe_harnesses.manifest_document(
                observations, host="darwin-arm64", date="2026-09-04", base_ref=BASE_REF
            )
            probe_harnesses.write_manifest(target, document, recorder)
            written = probe_harnesses.read_manifest(target)
            self.assertNotIn(
                ["sh", "-c", f"touch {evidence}"],
                [h.get("probe", {}).get("command") for h in written["harnesses"]],
            )

    def test_a_client_that_goes_quiet_is_recorded_unread_with_its_reason(self):
        harness = probe_harnesses.ROSTER[1]
        runner = RecordingRunner(raises=subprocess.TimeoutExpired)
        record = probe_harnesses.probe_client(
            harness, timeout=10.0, runner=runner, path_lookup=present_everywhere
        )
        self.assertEqual(record.status, "unread")
        self.assertIn("did not answer within 10s", record.result)
        self.assertIn("unread rather than absent", record.result)
        quiet = probe_harnesses.observe(
            harness, timeout=10.0, runner=runner, path_lookup=present_everywhere, environ={}
        )
        # Present, unread and unauthenticated, and not one of those three
        # collapses into another.
        self.assertTrue(quiet.client_present)
        self.assertEqual(quiet.client_version, probe_harnesses.UNREAD_VERSION)
        entry_record = probe_harnesses.entry_document(quiet)
        self.assertEqual(entry_record["classification"], "manual route")
        self.assertIn("did not answer within 10s", entry_record["blocker"])
        self.assertIn("did not answer within 10s", entry_record["probe"]["result"])

    def test_a_client_that_fails_never_answers_however_its_error_reads(self):
        # VERSION_TOKEN matches any dotted number, and a failing client prints
        # plenty of them. Each of these is one real client failure whose error
        # text carries something version-shaped: a loopback address, a library
        # version in a stack trace, an expiry date, a docs URL. None of them is
        # the client reporting its version, so none may reach `answered`, and
        # none may earn a class on a host where the client is installed and an
        # API key happens to be set.
        failures = (
            ("Error: connect ECONNREFUSED 127.0.0.1:8080\n", 1),
            ("node:internal/errors 4.18.2 unhandled rejection\n", 1),
            ("fatal: credentials expired at 2026.09.04\n", 1),
            ("unknown flag --version; see cursor.com/cli/0.1.2\n", 2),
        )
        harness = probe_harnesses.ROSTER[1]
        for stderr, code in failures:
            with self.subTest(code=code, stderr=stderr.strip()[:40]):
                runner = RecordingRunner(stdout="", stderr=stderr, returncode=code)
                record = probe_harnesses.probe_client(
                    harness, runner=runner, path_lookup=present_everywhere
                )
                self.assertEqual(record.status, "unread")
                self.assertIsNone(record.version)
                self.assertIn(f"exited {code}", record.result)
                self.assertIn("unread rather than absent", record.result)
                # Nothing the client printed rode along into the record.
                self.assertNotIn("127.0.0.1", record.result)
                self.assertNotIn("2026.09.04", record.result)
                # And the class the whole design turns on stays unearned even
                # with the client present and authentication configured.
                observed = probe_harnesses.observe(
                    harness,
                    runner=runner,
                    path_lookup=present_everywhere,
                    environ={"CURSOR_API_KEY": "set"},
                )
                self.assertTrue(observed.client_present)
                self.assertEqual(observed.client_version, probe_harnesses.UNREAD_VERSION)
                self.assertTrue(observed.auth_configured)
                self.assertNotIn(
                    probe_harnesses.classify(observed),
                    probe_harnesses.EARNED_CLASSIFICATIONS,
                )

    def test_a_zero_exit_client_still_answers_with_its_version(self):
        # The other half of the rule above: reading the exit status first must
        # not stop a client that succeeded from being recorded as answering.
        runner = RecordingRunner(stdout="cursor-agent 2026.8.1\n", returncode=0)
        record = probe_harnesses.probe_client(
            probe_harnesses.ROSTER[1], runner=runner, path_lookup=present_everywhere
        )
        self.assertEqual(record.status, "answered")
        self.assertEqual(record.version, "2026.8.1")

    def test_a_version_cut_in_half_by_the_output_bound_is_never_recorded(self):
        # The bound on how much client output is read can land inside the token
        # itself, and half of a version is not the version the client
        # reported. `1.234` recorded for a client that said `1.23456789` is the
        # same defect as a token scraped out of a failure: a `client_version`
        # nobody reported, under a schema description that calls it exact.
        cap = probe_harnesses.MAX_CLIENT_OUTPUT_CHARS
        version = "1.23456789"
        cut = "x" * (cap - 6) + " " + version
        self.assertGreater(len(cut), cap)
        self.assertIsNone(probe_harnesses.recognise_version(cut))

        # A whole token inside the bound is still read, wherever it sits, and a
        # client whose version is followed by more output is unaffected.
        self.assertEqual(probe_harnesses.recognise_version(f"cursor-agent {version}"), version)
        self.assertEqual(
            probe_harnesses.recognise_version(f"cursor-agent {version}\n" + "x" * cap), version
        )
        # A cut that landed on a newline left every line it kept intact, so the
        # guard must not withhold a version that was never truncated.
        self.assertEqual(
            probe_harnesses.recognise_version(f"cursor-agent {version}\n" + "x" * cap + "\ntail"),
            version,
        )
        # And the fixture the rest of this class uses stays exact.
        self.assertEqual(probe_harnesses.recognise_version("cursor-agent 2026.8.1\n"), "2026.8.1")

    def test_only_a_cut_that_could_extend_the_token_withholds_it(self):
        # Which side of the bound a character falls on does not decide whether
        # a version is whole; what the cut removed does. Deciding it on the
        # match reaching the end of the line withheld `1.2.3` from a client
        # whose only truncated character was the newline after it.
        cap = probe_harnesses.MAX_CLIENT_OUTPUT_CHARS
        head = "x" * (cap - 6) + " 1.2.3"
        self.assertEqual(len(head), cap)

        for tail, expected in (
            ("4", None),          # a digit extends the last group
            (".4", None),         # a dot opens another group
            ("-rc1", None),       # a dash opens the build suffix
            ("+build", None),     # so does a plus
            ("\n", "1.2.3"),      # a newline cannot extend anything
            (" ", "1.2.3"),
            (")", "1.2.3"),
            (",", "1.2.3"),
        ):
            with self.subTest(dropped=tail[:1]):
                stream = head + tail
                self.assertGreater(len(stream), cap)
                self.assertEqual(probe_harnesses.recognise_version(stream), expected)

        # Nothing was truncated at all, so the token stands whatever it abuts.
        self.assertEqual(probe_harnesses.recognise_version(head), "1.2.3")

    def test_the_default_runner_really_bounds_the_timeout(self):
        harness = probe_harnesses.Harness(
            name="fixture",
            probe_argv=(sys.executable, "-c", "import time; time.sleep(60)"),
            auth_env=(),
            auth_files=(),
            launcher_contract="none",
            launcher_published=False,
            product_withdrawn=False,
            standing_blocker="fixture",
        )
        record = probe_harnesses.probe_client(
            harness, timeout=0.75, path_lookup=present_everywhere
        )
        self.assertEqual(record.status, "unread")
        self.assertIn("did not answer within 0.75s", record.result)
        for bad in (0, -1.0, probe_harnesses.MAX_TIMEOUT_SECONDS + 1):
            with self.subTest(timeout=bad):
                # A bound the operator can set to anything is not a bound.
                with self.assertRaises(probe_harnesses.ProbeError):
                    probe_harnesses._checked_timeout(bad)

    def test_an_absent_binary_is_recorded_absent_and_its_command_is_never_run(self):
        runner = RecordingRunner()
        record = probe_harnesses.probe_client(
            probe_harnesses.ROSTER[1], runner=runner, path_lookup=absent_everywhere
        )
        self.assertEqual(runner.calls, [])
        self.assertEqual(record.status, "absent")
        self.assertIn("was not run", record.result)
        gone = probe_harnesses.observe(
            probe_harnesses.ROSTER[1],
            runner=runner,
            path_lookup=absent_everywhere,
            environ={},
        )
        self.assertFalse(gone.client_present)
        self.assertIsNone(gone.client_version)
        # A left-behind configuration directory is residue, not presence, and
        # the roster declaring no local authentication signal says so.
        self.assertFalse(gone.auth_configured)


class CredentialTests(unittest.TestCase):
    """Nothing shaped like a credential reaches the manifest or the probe log."""

    def run_leaking_probe(self, root):
        recorder = probe_harnesses.Recorder("00000000")
        observations = probe_harnesses.probe_roster(
            recorder=recorder,
            runner=RecordingRunner(stdout=LEAKING_CLIENT_OUTPUT),
            path_lookup=present_everywhere,
            environ={},
            home=root,
        )
        document = probe_harnesses.manifest_document(
            observations, host="darwin-arm64", date="2026-09-04", base_ref=BASE_REF
        )
        return recorder, document

    def test_a_token_in_client_output_never_reaches_the_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            recorder, document = self.run_leaking_probe(root)
            target = probe_harnesses.write_manifest(
                root / "harness-classification.json", document, recorder
            )
            text = target.read_text(encoding="utf-8")
            self.assertNotIn(LEAKED_SECRET, text)
            self.assertNotIn("someone@example.org", text)
            self.assertEqual(probe_harnesses.credential_findings(text), [])
            # The useful half survived: the allowlist kept the version and
            # dropped everything around it.
            self.assertIn('"client_version": "2026.8.1"', text)

    def test_the_same_output_never_reaches_the_probe_log(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            recorder, _document = self.run_leaking_probe(root)
            lines = recorder.lines()
            self.assertNotIn(LEAKED_SECRET, lines)
            self.assertNotIn("someone@example.org", lines)
            self.assertEqual(probe_harnesses.credential_findings(lines), [])
            written = probe_harnesses.write_log(root / "probe.log", recorder)
            self.assertEqual(
                probe_harnesses.credential_findings(written.read_text(encoding="utf-8")), []
            )

    def test_the_sweep_recognises_every_declared_shape(self):
        fixtures = {
            "token": "authorization bearer = ghp_wxyz1234567890abcdefghijkl",
            "key": "api_key: AKIAIOSFODNN7EXAMPLE",
            "cookie": "Set-Cookie: sid=abcdefghijklmnop",
            "session": "session_token=abcdefghijklmnop",
        }
        self.assertEqual(
            sorted(fixtures), list(probe_harnesses.CREDENTIAL_SHAPES)
        )
        for shape, text in fixtures.items():
            with self.subTest(shape=shape):
                self.assertIn(shape, probe_harnesses.credential_findings(text))
        for clean in (
            "",
            "absent: cursor-agent did not resolve on PATH",
            "ghapp://session/new with repo, pr, branch, prompt and mode",
            json.dumps(manifest(), sort_keys=True),
        ):
            with self.subTest(clean=clean[:40]):
                self.assertEqual(probe_harnesses.credential_findings(clean), [])

    def test_every_refusal_the_reader_can_meet_is_one_refusal_type(self):
        # `read_manifest` is the oracle step 3's renderer reads through, and its
        # docstring promises a refusal. A renderer catching `ProbeError` -- the
        # only refusal type the rest of the module raises -- would otherwise
        # miss the two cases it is likeliest to meet, an absent manifest and an
        # unreadable one, because those arrive from the filesystem instead.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for label, target in (
                ("absent", root / "absent.json"),
                ("a directory", root),
            ):
                with self.subTest(target=label):
                    # Caught broadly and then asserted on, rather than
                    # `assertRaises(ProbeError)`. On a tree that does not
                    # convert the filesystem error, the narrow form lets the
                    # OSError escape as an uncaught error, and the mechanical
                    # guard check reads an error as broken infrastructure
                    # rather than as a guard that failed.
                    with self.assertRaises(Exception) as caught:
                        probe_harnesses.read_manifest(target)
                    self.assertIsInstance(caught.exception, probe_harnesses.ProbeError)

    def test_an_output_path_the_filesystem_rejects_exits_one_without_a_traceback(self):
        # `main` reports operator-facing failures as one line and exit 1. A
        # destination that is a directory reaches `os.replace` rather than any
        # of the checks above it, so it arrived as an uncaught OSError and a
        # traceback carrying the path back out.
        with tempfile.TemporaryDirectory() as directory:
            # The escape is turned into an assertion for the same reason as
            # above: an uncaught OSError here would read as broken
            # infrastructure rather than as this guard doing its job.
            try:
                outcome = probe_harnesses.main(["--out", directory])
            except OSError as error:
                self.fail(
                    f"main let {type(error).__name__} escape instead of returning 1"
                )
            self.assertEqual(outcome, 1)
            # The neighbouring case already refused cleanly, and still does.
            self.assertEqual(
                probe_harnesses.main(["--out", str(Path(directory) / "absent" / "m.json")]), 1
            )

    def test_a_planted_leak_fails_the_write_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "harness-classification.json"
            good = manifest()
            probe_harnesses.write_manifest(target, good)
            before = target.read_bytes()
            planted = manifest(
                entry("Cursor", launcher_contract=f"bearer: {LEAKED_SECRET}")
            )
            with self.assertRaises(probe_harnesses.CredentialLeak):
                probe_harnesses.write_manifest(target, planted)
            # Fail closed: the previous manifest stands and no temporary file
            # is left behind for a reader to find.
            self.assertEqual(target.read_bytes(), before)
            self.assertEqual(list(root.glob(f"{probe_harnesses.TEMPORARY_PREFIX}*")), [])
            with self.assertRaises(probe_harnesses.CredentialLeak):
                probe_harnesses.Recorder("00000000").record(
                    "harness_probe_done", result=f"bearer: {LEAKED_SECRET}"
                )


CHILD_SOURCE = '''
"""Write a manifest and die at the point the parent names."""

import importlib.util
import os
import signal
import sys

script, target, home, mode = sys.argv[1:5]
spec = importlib.util.spec_from_file_location("probe_harnesses", script)
probe = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = probe
spec.loader.exec_module(probe)


def die(*_arguments, **_keywords):
    os.kill(os.getpid(), signal.SIGKILL)


if mode == "rename":
    probe.os.replace = die
    probe.os.rename = die
elif mode == "flush":
    probe.os.fsync = die
else:
    raise SystemExit(f"unknown mode {mode}")

recorder = probe.Recorder("00000000")
observations = probe.probe_roster(
    recorder=recorder, path_lookup=lambda _name: None, environ={}, home=home
)
document = probe.manifest_document(
    observations, host="darwin-arm64", date="2026-09-04", base_ref="0" * 40
)
probe.write_manifest(target, document)
print("the write completed without reaching the kill point")
'''


class KilledProbeTests(unittest.TestCase):
    """A probe killed mid-write must not leave a manifest anybody would read.

    This class is the resolver for the ``killed-probe-recovery`` gate. It runs a
    real child process and sends it ``SIGKILL`` between the temporary write and
    the rename, because that is the moment the atomic write exists to survive.
    Remove the rename from ``_atomic_write_text`` and the child never reaches
    the kill point: it completes, the destination changes, and every case here
    goes red.
    """

    REPORT_PATH = ROOT / ".hexaemeron/reports/probe-manifest-killed-probe-recovery.json"
    CASES = (
        "test_a_killed_probe_leaves_the_previous_manifest_intact",
        "test_a_killed_probe_leaves_nothing_where_there_was_no_manifest",
        "test_a_killed_probe_leaves_no_partial_file_the_reader_would_accept",
        "test_the_temporary_file_is_written_beside_the_target_and_renamed",
    )
    attempted: set[str] = set()
    passed: set[str] = set()
    failed: set[str] = set()

    def setUp(self):
        self.attempted.add(self._testMethodName)

    @contextlib.contextmanager
    def checked_subtest(self, **parameters):
        """A ``subTest`` whose failure is remembered as well as reported.

        ``subTest`` swallows the failure so the loop can carry on, which means
        the statement after the loop runs either way -- and that statement is
        where a case flags itself passed. An unremembered subtest failure
        therefore lets a red run write ``value: true``, which is the inversion
        of the partial-run defect the ``attempted`` gate closes, and the worse
        direction of the two: it admits a broken atomic write at ``step:3``
        rather than blocking a sound one.
        """
        with self.subTest(**parameters):
            try:
                yield
            except unittest.SkipTest:
                raise
            except Exception:
                self.failed.add(self._testMethodName)
                raise

    def _passed(self):
        """Flag this case, unless something inside it failed.

        A case that raises never reaches its call to this. A case whose failure
        was confined to a ``checked_subtest`` does reach it, and this is what
        stops it speaking for the gate anyway.
        """
        if self._testMethodName not in self.failed:
            self.passed.add(self._testMethodName)

    @classmethod
    def tearDownClass(cls):
        """Write the gate's report, or leave it alone in a tree without one."""
        directory = cls.REPORT_PATH.parent
        if not directory.is_dir():
            return
        # A partial selection is not a failed gate. Running one case by name,
        # or filtering with -k, would otherwise write `value: false` and
        # `exit: 1` for a run in which nothing failed and nothing exited 1 --
        # and Fiat's design checker reads this file at the step:3 transition.
        # Only a run that attempted every case may speak for the gate.
        if cls.attempted != set(cls.CASES):
            return
        # Two conditions, because each catches the other's blind spot. Every
        # case has to have flagged itself, and nothing may have failed along
        # the way -- a case whose failure was confined to a subtest would
        # otherwise still be holding its flag.
        resolved = cls.passed == set(cls.CASES) and not cls.failed
        report = {
            "candidate": "probe-manifest",
            "command": "python3 -m unittest tests.test_harness_manifest.KilledProbeTests",
            "criterion": "killed-probe-recovery",
            "exit": 0 if resolved else 1,
            "schema": "protasis-design-report/v1",
            "unit": "boolean",
            "value": resolved,
        }
        cls.REPORT_PATH.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    def kill_during_write(self, root, target, mode):
        """Run the probe in a child that dies at `mode`, and prove it died."""
        child = root / "killed_write.py"
        child.write_text(CHILD_SOURCE, encoding="utf-8")
        completed = subprocess.run(
            [sys.executable, str(child), str(PROBE_PATH), str(target), str(root), mode],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        self.assertEqual(
            completed.returncode,
            -9,
            msg=(
                "the child was expected to be killed at the "
                f"{mode} point, not to finish: {completed.stdout}{completed.stderr}"
            ),
        )
        return completed

    def test_a_killed_probe_leaves_the_previous_manifest_intact(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "harness-classification.json"
            probe_harnesses.write_manifest(target, manifest())
            before = target.read_bytes()
            for mode in ("rename", "flush"):
                with self.checked_subtest(mode=mode):
                    self.kill_during_write(root, target, mode)
                    self.assertEqual(target.read_bytes(), before)
                    self.assertEqual(
                        probe_harnesses.read_manifest(target)["harnesses"][0]["name"],
                        "GitHub Copilot",
                    )
        self._passed()

    def test_a_killed_probe_leaves_nothing_where_there_was_no_manifest(self):
        for mode in ("rename", "flush"):
            with self.checked_subtest(mode=mode):
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    target = root / "harness-classification.json"
                    self.kill_during_write(root, target, mode)
                    self.assertFalse(target.exists())
                    self.assertEqual(list(root.glob("*.json")), [])
        self._passed()

    def test_a_killed_probe_leaves_no_partial_file_the_reader_would_accept(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "harness-classification.json"
            probe_harnesses.write_manifest(target, manifest())
            good = target.read_bytes()
            self.kill_during_write(root, target, "flush")

            # Whatever the killed child left in the directory, the destination
            # still holds the finished manifest and nothing else answers to a
            # renderer looking for JSON.
            self.assertEqual(target.read_bytes(), good)
            self.assertEqual(list(root.glob("*.json")), [target])
            for leftover in root.glob(f"{probe_harnesses.TEMPORARY_PREFIX}*"):
                with self.checked_subtest(leftover=leftover.name):
                    self.assertTrue(leftover.name.startswith("."))
                    self.assertTrue(leftover.name.endswith(probe_harnesses.TEMPORARY_SUFFIX))
                    self.assertNotEqual(leftover, target)

            # And the reader has teeth: a torn file is refused rather than
            # half-read, so "never a partial file it would accept" is a claim
            # about the reader as well as about the write.
            torn = root / "torn.json"
            torn.write_bytes(good[: len(good) // 2])
            with self.assertRaises(probe_harnesses.ProbeError):
                probe_harnesses.read_manifest(torn)
            other = root / "other.json"
            other.write_text(json.dumps({"schema": "something-else/v1"}), encoding="utf-8")
            with self.assertRaises(probe_harnesses.ProbeError):
                probe_harnesses.read_manifest(other)
        self._passed()

    def test_the_temporary_file_is_written_beside_the_target_and_renamed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "harness-classification.json"
            seen = []
            real = os.replace

            def capture(source, destination):
                seen.append((Path(source), Path(destination)))
                return real(source, destination)

            with mock.patch.object(probe_harnesses.os, "replace", capture):
                probe_harnesses.write_manifest(target, manifest())

            self.assertEqual(len(seen), 1)
            temporary, destination = seen[0]
            self.assertEqual(destination, target)
            # Same directory, so the rename is a same-filesystem operation,
            # which is the whole reason it is atomic.
            self.assertEqual(temporary.parent, target.parent)
            self.assertTrue(temporary.name.startswith(probe_harnesses.TEMPORARY_PREFIX))
            self.assertTrue(temporary.name.endswith(probe_harnesses.TEMPORARY_SUFFIX))
            self.assertFalse(temporary.exists())
            self.assertEqual(list(root.glob("*.json")), [target])
        self._passed()


class GateReportTests(unittest.TestCase):
    """The gate report may only speak for a run that attempted and passed every case.

    ``KilledProbeTests`` writes the ``killed-probe-recovery`` report on its way
    out, and Fiat's design checker reads that file at the ``step:3``
    transition. A run that selects one case by name passes it, so a report
    saying ``value: false`` and ``exit: 1`` would describe a failure nothing
    observed and block the step on it. The inverse costs more: a case whose
    failure was confined to a ``subTest`` still runs the statement that flags
    it passed, so a red run would report ``value: true`` and let a broken
    atomic write through the gate.

    These cases drive ``KilledProbeTests.tearDownClass`` directly rather than
    through a real kill, so they cost nothing and cannot disturb the real
    class's own bookkeeping.
    """

    def write_report(self, attempted, passed, root, failed=()):
        target = root / "gate.json"
        with mock.patch.multiple(
            KilledProbeTests,
            REPORT_PATH=target,
            attempted=set(attempted),
            passed=set(passed),
            failed=set(failed),
        ):
            KilledProbeTests.tearDownClass()
        return target

    def test_a_partial_selection_writes_no_report_at_all(self):
        for selected in ((), KilledProbeTests.CASES[:1], KilledProbeTests.CASES[:3]):
            with self.subTest(attempted=len(selected)):
                with tempfile.TemporaryDirectory() as directory:
                    # Every selected case passed. The only thing missing is the
                    # rest of the class, and that is not a failed gate.
                    target = self.write_report(selected, selected, Path(directory))
                    self.assertFalse(target.exists())

    def test_a_complete_run_writes_the_resolved_report(self):
        with tempfile.TemporaryDirectory() as directory:
            target = self.write_report(
                KilledProbeTests.CASES, KilledProbeTests.CASES, Path(directory)
            )
            report = json.loads(target.read_text(encoding="utf-8"))
            self.assertEqual(report["criterion"], "killed-probe-recovery")
            self.assertEqual(report["candidate"], "probe-manifest")
            self.assertIs(report["value"], True)
            self.assertEqual(report["exit"], 0)

    def test_a_complete_run_with_a_failure_writes_the_unresolved_report(self):
        with tempfile.TemporaryDirectory() as directory:
            target = self.write_report(
                KilledProbeTests.CASES, KilledProbeTests.CASES[:-1], Path(directory)
            )
            report = json.loads(target.read_text(encoding="utf-8"))
            self.assertIs(report["value"], False)
            self.assertEqual(report["exit"], 1)

    def test_a_case_that_failed_cannot_leave_the_report_resolved(self):
        # The inverse of the partial-selection rule, and the worse direction:
        # a partial run that reports failure blocks a sound step, while a
        # failed run that reports success admits a broken atomic write.
        with tempfile.TemporaryDirectory() as directory:
            target = self.write_report(
                KilledProbeTests.CASES,
                KilledProbeTests.CASES,
                Path(directory),
                failed=KilledProbeTests.CASES[:1],
            )
            report = json.loads(target.read_text(encoding="utf-8"))
            self.assertIs(report["value"], False)
            self.assertEqual(report["exit"], 1)

    def test_a_failing_subtest_stops_a_case_reporting_itself_passed(self):
        """``subTest`` swallows the failure, so the flag has to know about it.

        Without this, every statement after a ``subTest`` loop runs on a failed
        case, including the one that flags it passed -- and four of this file's
        gate cases end in exactly that statement.
        """

        class Sample(unittest.TestCase):
            passed: set[str] = set()
            failed: set[str] = set()
            checked_subtest = KilledProbeTests.checked_subtest
            _passed = KilledProbeTests._passed

            def test_one_mode_of_two_fails(self):
                for mode in ("rename", "flush"):
                    with self.checked_subtest(mode=mode):
                        self.assertEqual(mode, "flush")
                self._passed()

        with open(os.devnull, "w", encoding="utf-8") as sink:
            result = unittest.TextTestRunner(stream=sink, verbosity=0).run(
                unittest.TestLoader().loadTestsFromTestCase(Sample)
            )

        # The run is red, the failure was remembered, and the case did not
        # flag itself even though execution reached the flag.
        self.assertFalse(result.wasSuccessful())
        self.assertEqual(Sample.failed, {"test_one_mode_of_two_fails"})
        self.assertEqual(Sample.passed, set())

    def test_every_case_the_report_speaks_for_is_a_real_test_method(self):
        # The gate's case list is the report's denominator, so a renamed or
        # deleted case must not leave it claiming coverage it no longer has.
        for name in KilledProbeTests.CASES:
            with self.subTest(case=name):
                self.assertTrue(callable(getattr(KilledProbeTests, name, None)))
        declared = {
            name for name in vars(KilledProbeTests) if name.startswith("test_")
        }
        self.assertEqual(declared, set(KilledProbeTests.CASES))


MANIFEST_PATH = ROOT / "docs/harness-classification.json"
RENDERER_PATH = ROOT / "scripts/render_harness_roster.py"
README_PATH = ROOT / "README.md"
GUIDE_PATH = ROOT / "docs/how-to-help-shoggoth.md"
PDF_PATH = ROOT / "docs/pdf/how-to-help-shoggoth.pdf"

# A PDF this repository already ships that carries no harness page, used to
# prove the check reads the page rather than accepting any file it is handed.
OTHER_PDF_PATH = ROOT / "docs/pdf/the-promise-machine-explained-properly.pdf"

_RENDER_SPEC = importlib.util.spec_from_file_location(
    "render_harness_roster", RENDERER_PATH
)
render_harness_roster = importlib.util.module_from_spec(_RENDER_SPEC)
sys.modules[_RENDER_SPEC.name] = render_harness_roster
_RENDER_SPEC.loader.exec_module(render_harness_roster)


def landed():
    """The manifest this host's probe actually wrote and the tree carries."""
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


class RecordTests(unittest.TestCase):
    """The landed record, held to what a probe on this host may claim.

    ``SchemaTests`` holds the contract in the abstract, against constructed
    documents. These cases hold the one document three wording surfaces are
    generated from: it validates, it names every harness the probe declares,
    it awards no class a client run did not earn, and nothing it could not run
    is left without a stated reason.
    """

    def setUp(self):
        self.document = landed()

    def test_the_landed_manifest_validates_against_the_schema(self):
        schema = load_schema()
        self.assertEqual(self.document["schema"], schema["properties"]["schema"]["const"])
        required = set(schema["$defs"]["harness"]["required"])
        for record in self.document["harnesses"]:
            with self.subTest(harness=record["name"]):
                self.assertTrue(required.issubset(record), required - set(record))
        checker = validator()
        if checker is None:
            self.skipTest("jsonschema is a Lazarus dependency and is absent here")
        checker.validate(self.document)

    def test_the_landed_manifest_names_every_declared_harness(self):
        # The probe's own ROSTER is the declaration; a manifest that dropped or
        # reordered a row would generate three surfaces missing a harness and
        # nothing else would notice.
        declared = [harness.name for harness in probe_harnesses.ROSTER]
        self.assertEqual([record["name"] for record in self.document["harnesses"]], declared)
        self.assertEqual(sorted(declared), sorted(HARNESSES))

    def test_no_landed_entry_carries_an_earned_class(self):
        # Not one client is installed or authenticated on this host, so an
        # earned class here would mean the classifier was bypassed rather than
        # that a harness improved.
        for record in self.document["harnesses"]:
            with self.subTest(harness=record["name"]):
                self.assertIn(record["classification"], CLASSIFICATIONS)
                self.assertNotIn(record["classification"], EARNED_CLASSIFICATIONS)
                self.assertFalse(record["version_read"])

    def test_every_untestable_entry_carries_a_blocker(self):
        untestable = [
            record for record in self.document["harnesses"]
            if not record.get("testable_here", False)
        ]
        self.assertEqual(len(untestable), len(self.document["harnesses"]))
        for record in untestable:
            with self.subTest(harness=record["name"]):
                self.assertIsInstance(record["blocker"], str)
                self.assertTrue(record["blocker"].strip())

    def test_the_recorded_block_is_the_staleness_signal(self):
        # Host, date and base ref are what a later reader compares a surface
        # against, so each has to be present and shaped rather than merely
        # truthy.
        recorded = self.document["recorded"]
        self.assertEqual(set(recorded), {"host", "date", "base_ref"})
        self.assertTrue(probe_harnesses.HOST_PATTERN.match(recorded["host"]))
        self.assertTrue(probe_harnesses.DATE_PATTERN.match(recorded["date"]))
        self.assertTrue(probe_harnesses.BASE_REF_PATTERN.match(recorded["base_ref"]))


class RenderTests(unittest.TestCase):
    """The three surfaces, held to the manifest they are generated from.

    Every case works on a staged copy of the four files rather than on the
    repository's own, so a case that fails leaves the tree exactly as it found
    it and no case can pass by rewriting the thing it is checking.

    The PDF is compared as the harness page's shown text rather than as bytes.
    Two cases hold that from both directions: a file whose creation timestamp
    was changed still passes, and a file that never carried the roster still
    fails. Comparing whole bytes would invert both.
    """

    def stage(self, directory):
        """Copies of the four files, and the keyword arguments to check them."""
        root = Path(directory)
        (root / "docs" / "pdf").mkdir(parents=True)
        (root / "scripts").mkdir()
        staged = {
            "manifest": root / "docs/harness-classification.json",
            "readme": root / "README.md",
            "guide": root / "docs/how-to-help-shoggoth.md",
            "pdf": root / "docs/pdf/how-to-help-shoggoth.pdf",
        }
        for key, source in (
            ("manifest", MANIFEST_PATH),
            ("readme", README_PATH),
            ("guide", GUIDE_PATH),
            ("pdf", PDF_PATH),
        ):
            staged[key].write_bytes(source.read_bytes())
        return staged

    def drift(self, staged):
        _, lines = render_harness_roster.check(**staged)
        return lines

    def test_two_renders_of_one_manifest_produce_the_same_bytes(self):
        # Nothing in the renderer reads a clock or an environment, so a second
        # render has to be the first one. Without this the check below would be
        # a diff of two build times rather than a drift test.
        document = landed()
        again = landed()
        for name, render in (
            ("readme", render_harness_roster.readme_block),
            ("guide", render_harness_roster.guide_block),
        ):
            with self.subTest(surface=name):
                self.assertEqual(render(document), render(again))
        self.assertEqual(
            render_harness_roster.pdf_expectations(document),
            render_harness_roster.pdf_expectations(again),
        )

    def test_check_passes_on_the_surfaces_the_renderer_wrote(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(self.drift(self.stage(directory)), [])

    def test_one_changed_character_in_a_written_surface_fails_the_check(self):
        for surface in ("readme", "guide"):
            with self.subTest(surface=surface):
                with tempfile.TemporaryDirectory() as directory:
                    staged = self.stage(directory)
                    target = staged[surface]
                    text = target.read_text(encoding="utf-8")
                    # One character, inside the generated region, in a name the
                    # manifest supplied. Neither surface mentions a harness
                    # before its markers, so the first occurrence is the
                    # generated one.
                    edited = text.replace("Windsurf", "Windsurg", 1)
                    self.assertNotEqual(edited, text)
                    target.write_text(edited, encoding="utf-8")
                    lines = self.drift(staged)
                    self.assertEqual(len(lines), 1, lines)
                    self.assertIn(str(target), lines[0])

    def test_one_changed_character_in_the_manifest_reaches_every_surface(self):
        # The manifest is the source, so a single character changed there has to
        # show up as drift in all three surfaces at once. This is what proves
        # the PDF is genuinely compared rather than assumed to agree.
        with tempfile.TemporaryDirectory() as directory:
            staged = self.stage(directory)
            raw = staged["manifest"].read_text(encoding="utf-8")
            edited = raw.replace('"name": "Cline"', '"name": "Clins"', 1)
            self.assertNotEqual(edited, raw)
            staged["manifest"].write_text(edited, encoding="utf-8")
            lines = self.drift(staged)
            self.assertEqual(len(lines), 3, lines)
            for surface in ("readme", "guide", "pdf"):
                with self.subTest(surface=surface):
                    self.assertTrue(
                        any(str(staged[surface]) in line for line in lines), lines
                    )

    def test_a_changed_creation_timestamp_does_not_fail_the_pdf_check(self):
        # The point of reading the page rather than the file. The replacement
        # is the same length as what it replaces, so only the timestamp moves.
        with tempfile.TemporaryDirectory() as directory:
            staged = self.stage(directory)
            original = staged["pdf"].read_bytes()
            found = re.search(rb"/CreationDate \(D:\d{14}", original)
            self.assertIsNotNone(found, "the guide PDF carries no creation date")
            stamped = original.replace(found.group(0), b"/CreationDate (D:20310607081533", 1)
            self.assertNotEqual(stamped, original)
            self.assertEqual(len(stamped), len(original))
            staged["pdf"].write_bytes(stamped)
            self.assertEqual(self.drift(staged), [])

    def test_a_pdf_without_a_harness_page_fails_the_check(self):
        with tempfile.TemporaryDirectory() as directory:
            staged = self.stage(directory)
            staged["pdf"].write_bytes(OTHER_PDF_PATH.read_bytes())
            lines = self.drift(staged)
            self.assertEqual(len(lines), 1, lines)
            self.assertIn(render_harness_roster.PDF_PAGE_MARKER, lines[0])

    def test_a_missing_manifest_fails_the_check(self):
        with tempfile.TemporaryDirectory() as directory:
            staged = self.stage(directory)
            staged["manifest"].unlink()
            with self.assertRaises(render_harness_roster.RenderError):
                render_harness_roster.check(**staged)
            # And the command line answers the same way, without a traceback
            # carrying the path back out. Its refusal line is not the subject
            # here, so it goes to the bin rather than into the suite's output.
            with open(os.devnull, "w", encoding="utf-8") as sink:
                with contextlib.redirect_stderr(sink):
                    exit_code = render_harness_roster.main(
                        ["--check", "--manifest", str(staged["manifest"])]
                    )
            self.assertEqual(exit_code, 1)

    def test_a_credential_in_the_manifest_never_reaches_a_surface(self):
        # The probe sweeps what a client printed. This is the same sweep one
        # boundary later: a token typed into the manifest afterwards would
        # otherwise be published in three surfaces at once. Feeding it hostile
        # input is what makes the control established rather than asserted.
        with tempfile.TemporaryDirectory() as directory:
            staged = self.stage(directory)
            document = json.loads(staged["manifest"].read_text(encoding="utf-8"))
            document["harnesses"][0]["blocker"] = f"bearer: {LEAKED_SECRET}"
            staged["manifest"].write_text(json.dumps(document, indent=2), encoding="utf-8")
            before = {key: path.read_bytes() for key, path in staged.items()}
            with self.assertRaises(render_harness_roster.RenderError) as refused:
                render_harness_roster.write(**staged)
            self.assertIn("token", str(refused.exception))
            # Nothing was written at all, which is the probe's rule as well.
            for key, path in staged.items():
                with self.subTest(surface=key):
                    self.assertEqual(path.read_bytes(), before[key])

    def test_a_credential_refuses_before_any_surface_is_written(self):
        # S3-R2-02. The sweep used to run as each surface's turn came round,
        # so the refusal was only as early as the surface carrying the token.
        # A blocker reaches the guide body and no other, and a blocker is
        # where captured client output lands, so a token there refused after
        # the README had already been rewritten.
        #
        # The case above cannot catch that. It plants the token in a blocker
        # and changes nothing else, so the README it renders is byte-identical
        # to the staged one and goes unwritten whichever order the sweep runs
        # in; its "nothing was written" assertion is vacuous for the README.
        # This one moves the README body too, which is what a real re-render
        # does, and no token reaches disk either way -- what is at stake is
        # one surface regenerated against two left stale.
        with tempfile.TemporaryDirectory() as directory:
            staged = self.stage(directory)
            document = json.loads(staged["manifest"].read_text(encoding="utf-8"))
            document["recorded"]["base_ref"] = "0" * 40
            document["harnesses"][0]["blocker"] = f"bearer: {LEAKED_SECRET}"
            staged["manifest"].write_text(json.dumps(document, indent=2), encoding="utf-8")
            # The precondition that makes this a real hole: the README body
            # does move, so the old order wrote it before it refused.
            self.assertNotIn(
                render_harness_roster.readme_block(document),
                staged["readme"].read_text(encoding="utf-8"),
            )
            before = {key: path.read_bytes() for key, path in staged.items()}
            with self.assertRaises(render_harness_roster.RenderError) as refused:
                render_harness_roster.write(**staged)
            self.assertIn("token", str(refused.exception))
            for key, path in staged.items():
                with self.subTest(surface=key):
                    self.assertEqual(path.read_bytes(), before[key])

    def test_an_operator_path_the_renderer_rejects_exits_one(self):
        with open(os.devnull, "w", encoding="utf-8") as sink:
            with contextlib.redirect_stderr(sink):
                for option in ("--manifest", "--readme", "--guide", "--pdf"):
                    with self.subTest(option=option):
                        self.assertEqual(
                            render_harness_roster.main(["--check", option, ""]), 1
                        )

    def test_every_harness_the_manifest_names_reaches_every_surface(self):
        document = landed()
        readme = render_harness_roster.readme_block(document)
        guide = render_harness_roster.guide_block(document)
        shown = render_harness_roster.harness_page_text(PDF_PATH)
        for record in document["harnesses"]:
            with self.subTest(harness=record["name"]):
                self.assertIn(record["name"], readme)
                self.assertIn(record["name"], guide)
                self.assertIn(record["name"], shown)
                # And the guide carries the exact reason, not a summary of it.
                self.assertIn(record["blocker"], guide)

    def test_a_page_showing_a_longer_roster_than_the_manifest_is_drift(self):
        # S3-R1-02. The PDF half of `check` compares by containment, and the
        # roster line is names joined by a separator, so dropping the FIRST or
        # LAST name leaves the shorter line contained in the page's longer one.
        # Both ends are driven here; the tail case is the one the committed
        # page actually admitted before the delimiter guard existed.
        document = landed()
        shown = render_harness_roster.harness_page_text(PDF_PATH)
        self.assertEqual(render_harness_roster.pdf_drift(document, shown), [])
        manual = render_harness_roster.names_in_class(
            document, render_harness_roster.MANUAL_ROUTE
        )
        self.assertGreater(len(manual), 2, manual)
        for dropped in (manual[0], manual[-1]):
            with self.subTest(dropped=dropped):
                trimmed = json.loads(json.dumps(document))
                trimmed["harnesses"] = [
                    record for record in trimmed["harnesses"]
                    if record["name"] != dropped
                ]
                shorter = render_harness_roster.pdf_roster_line(trimmed)
                # The precondition that makes this a real hole rather than a
                # hypothetical one: the shorter line IS still contained.
                self.assertIn(render_harness_roster._normalise(shorter), shown)
                self.assertEqual(
                    len(render_harness_roster.pdf_drift(trimmed, shown)), 1
                )

    def test_a_manifest_rendering_an_empty_roster_line_is_drift(self):
        # An empty expectation is contained in every page ever written, so
        # containment alone would report a clean check against a page that says
        # nothing at all. Reachable whenever no harness holds `manual route`.
        document = landed()
        for record in document["harnesses"]:
            record["classification"] = render_harness_roster.UNSUPPORTED
        self.assertEqual(render_harness_roster.pdf_roster_line(document), "")
        shown = render_harness_roster.harness_page_text(PDF_PATH)
        drift = render_harness_roster.pdf_drift(document, shown)
        self.assertTrue(any("empty string" in line for line in drift), drift)

    def test_a_page_showing_an_unsupported_list_the_manifest_dropped_is_drift(self):
        # S3-R2-01, the containment hole S3-R1-02 closed on the roster line,
        # one field over. The unsupported clause is optional, so dropping the
        # LAST unsupported harness removes it rather than shortening it, and
        # the manifest's detail becomes a strict prefix of the page's. Nothing
        # else moves -- an unsupported entry is in neither the roster line nor
        # the label -- so every other expectation still matched and the whole
        # check exited 0 on a page still advertising the harness that left.
        document = landed()
        shown = render_harness_roster.harness_page_text(PDF_PATH)
        self.assertEqual(render_harness_roster.pdf_drift(document, shown), [])
        unsupported = render_harness_roster.names_in_class(
            document, render_harness_roster.UNSUPPORTED
        )
        self.assertEqual(len(unsupported), 1, unsupported)
        trimmed = json.loads(json.dumps(document))
        trimmed["harnesses"] = [
            record for record in trimmed["harnesses"]
            if record["classification"] != render_harness_roster.UNSUPPORTED
        ]
        # The precondition that makes this a hole rather than a hypothetical:
        # every expectation IS still contained, and the other two are byte
        # for byte what they were.
        for expected in render_harness_roster.pdf_expectations(trimmed):
            with self.subTest(expected=expected):
                self.assertIn(render_harness_roster._normalise(expected), shown)
        self.assertEqual(
            render_harness_roster.pdf_roster_line(trimmed),
            render_harness_roster.pdf_roster_line(document),
        )
        self.assertEqual(
            render_harness_roster.pdf_label(trimmed),
            render_harness_roster.pdf_label(document),
        )
        self.assertEqual(len(render_harness_roster.pdf_drift(trimmed, shown)), 1)
        # Dropping one of several was already caught, because the list is
        # comma-separated and full-stopped: `Unsupported: A.` is not a prefix
        # of `Unsupported: A, B.`. Only the fall to zero hid, which is why the
        # case above drops the only one there is.
        two = json.loads(json.dumps(document))
        two["harnesses"][0]["classification"] = render_harness_roster.UNSUPPORTED
        one = json.loads(json.dumps(two))
        one["harnesses"] = [
            record for record in one["harnesses"] if record["name"] != unsupported[0]
        ]
        self.assertNotIn(
            render_harness_roster.pdf_detail(one),
            render_harness_roster.pdf_detail(two),
        )

    def test_a_recorded_date_that_is_not_a_calendar_date_is_refused(self):
        # S3-R1-04, handed here by step 2's round 4. `manifest_document`
        # matches the shape and nothing more, so an operator `--date` of
        # `2026-13-45` reaches a written manifest. This is the last gate before
        # that string is published in three surfaces at once.
        for bad in ("2026-13-45", "2026-02-31", "0000-00-00"):
            with self.subTest(date=bad):
                document = landed()
                document["recorded"]["date"] = bad
                # The shape check the probe applies still passes it, which is
                # what makes this refusal load-bearing rather than redundant.
                self.assertTrue(probe_harnesses.DATE_PATTERN.match(bad))
                for render in (
                    render_harness_roster.readme_block,
                    render_harness_roster.guide_block,
                    render_harness_roster.pdf_label,
                ):
                    with self.assertRaises(render_harness_roster.RenderError):
                        render(document)
        # A real date still renders, so the guard refuses the calendar and not
        # the field.
        self.assertIn("2026-09-04", render_harness_roster.pdf_label(landed()))

    def test_the_readme_states_how_many_clients_answered(self):
        # S3-R1-03. The sentence used to claim the probe "read every client
        # below"; no client was read on this host. The count is derived from
        # `version_read`, so it cannot drift from the manifest.
        document = landed()
        self.assertFalse(any(record["version_read"] for record in document["harnesses"]))
        block = render_harness_roster.readme_block(document)
        self.assertIn("no client answered there", block)
        self.assertNotIn("read every client", block)
        answered = json.loads(json.dumps(document))
        answered["harnesses"][0]["version_read"] = True
        answered["harnesses"][0]["client_version"] = "1.2.3"
        self.assertIn(
            f"1 of the {len(answered['harnesses'])} clients answered there",
            render_harness_roster.readme_block(answered),
        )

    def test_neither_surface_names_a_roster_harness_outside_the_markers(self):
        # The provenance comment published in both files makes this claim, so
        # something has to hold it. Codex and Claude Code are named outside the
        # markers on purpose and are not in the roster; the comment now says
        # exactly that rather than claiming no harness name appears at all.
        names = [record["name"] for record in landed()["harnesses"]]
        self.assertNotIn("Codex", names)
        self.assertNotIn("Claude Code", names)
        for label, path in (("README", README_PATH), ("guide", GUIDE_PATH)):
            text = path.read_text(encoding="utf-8")
            head, _, tail = render_harness_roster.split_surface(text, path)
            outside = head + tail
            for name in names:
                with self.subTest(surface=label, harness=name):
                    self.assertNotIn(name, outside)


if __name__ == "__main__":
    unittest.main()
