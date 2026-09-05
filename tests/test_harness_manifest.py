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
ADR-076 puts that enforcement in the probe's classifier, and these are the cases
that hold it there.

``ClassifierTests`` sweeps the input matrix for a shape that reaches an earned
class without a recorded client run. ``SubprocessTests`` holds the command
boundary: a fixed argv, no shell, nothing read out of a manifest, and a client
that goes quiet recorded as unread rather than as absent. ``CredentialTests``
feeds the probe a client output fixture carrying a token and sweeps both the
manifest and the log for it. ``KilledProbeTests`` kills a real child process
between the temporary write and the rename, and is the resolver for the
``killed-probe-recovery`` gate; it writes that gate's report on the way out.
"""

from __future__ import annotations

import importlib.util
import itertools
import json
import os
from pathlib import Path
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
        "auth_configured": False,
        "launcher_contract": "documented deep link, not exercised here",
        "blocker": "absent from this host and unauthenticated",
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

    def test_every_harness_entry_requires_the_five_observation_fields(self):
        required = self.harness["required"]
        for field in OBSERVATION_FIELDS:
            with self.subTest(field=field):
                self.assertIn(field, required)
        self.assertFalse(self.harness["additionalProperties"])
        document = manifest()
        self.assertEqual(len(document["harnesses"]), len(HARNESSES))
        self.assert_valid(document)

    def test_a_harness_entry_missing_any_observation_field_is_refused(self):
        for field in OBSERVATION_FIELDS:
            with self.subTest(field=field):
                # Document level: being listed in `required` is the mechanism
                # that turns the omission below into a refusal.
                self.assertIn(field, self.harness["required"])
                record = entry("Cline")
                del record[field]
                self.assert_refused(manifest(record))

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
    passed: set[str] = set()

    @classmethod
    def tearDownClass(cls):
        """Write the gate's report, or leave it alone in a tree without one."""
        directory = cls.REPORT_PATH.parent
        if not directory.is_dir():
            return
        resolved = cls.passed == set(cls.CASES)
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
                with self.subTest(mode=mode):
                    self.kill_during_write(root, target, mode)
                    self.assertEqual(target.read_bytes(), before)
                    self.assertEqual(
                        probe_harnesses.read_manifest(target)["harnesses"][0]["name"],
                        "GitHub Copilot",
                    )
        self.passed.add(self._testMethodName)

    def test_a_killed_probe_leaves_nothing_where_there_was_no_manifest(self):
        for mode in ("rename", "flush"):
            with self.subTest(mode=mode):
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    target = root / "harness-classification.json"
                    self.kill_during_write(root, target, mode)
                    self.assertFalse(target.exists())
                    self.assertEqual(list(root.glob("*.json")), [])
        self.passed.add(self._testMethodName)

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
                with self.subTest(leftover=leftover.name):
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
        self.passed.add(self._testMethodName)

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
        self.passed.add(self._testMethodName)


if __name__ == "__main__":
    unittest.main()
