"""Worked example for the Elenchus procedure that pins an RPC-boundary failure.

`plugins/hexaemeron/skills/elenchus/SKILL.md` says how a failure that needs a
live JSON-RPC endpoint's answer is captured into a Lazarus fixture and
reproduced offline behind `lazarus replay`. This module is the guard half of
that procedure, run against the fixture Lazarus ships at
`plugins/lazarus/examples/goldfinch-v0`, whose `verify` digest is
`d93cd09fcb2c6bd689a223398ebd4ae4dc480ec7d8fd8e64283b88341d0a7e49`. The digest
is named here rather than asserted, so a Lazarus recapture that keeps the
recorded answers keeps this example green.

Three classes. `ProcedureTextTests` holds the skill file to the section's
commands and rules, and fails by assertion when the section is missing.
`LazarusDependencyGuardTests` proves the dependency probe names every missing
import and the `uv` command that supplies them. `ReplayGuardExampleTests`
starts `lazarus replay` on an ephemeral loopback port from a fixed argument
list, asserts the recorded slot value exactly, asserts that an uncaptured
request is a `-32070` miss and that a write method is refused, and stops the
server. It skips by name where the Lazarus dependencies are not importable
from the running interpreter, and never passes without running.

Standard library only, on Python 3.9 and 3.12.
"""

import http.client
import importlib.util
import ipaddress
import json
from pathlib import Path
import socket
import subprocess
import sys
import threading
import unittest
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[3]
SKILL_FILE = REPO_ROOT / "plugins" / "hexaemeron" / "skills" / "elenchus" / "SKILL.md"
RPC_RECORDS = (
    REPO_ROOT / "plugins" / "lazarus" / "examples" / "goldfinch-v0" / "rpc.jsonl"
)

SECTION_HEADING = "## Pin an RPC-boundary failure into a fixture"
NEXT_HEADING = "## Three rounds, then stop"
LAZARUS_COMMAND = "python3 plugins/lazarus/scripts/lazarus.py"
UV_COMMAND = (
    'uv run --no-project --python "$(cat .python-version)" '
    "--with-requirements plugins/lazarus/requirements.txt"
)
EXAMPLE_MODULE = "plugins/hexaemeron/tests/test_elenchus_rpc_boundary_fixture.py"
ENVIRONMENT_SENTENCE = (
    "A failure that needs a live endpoint's answer to appear belongs in a "
    'fixture; "Pin an RPC-boundary failure into a fixture" below says how.'
)
CHECKLIST_ITEM = (
    "- [ ] A failure that crossed an RPC boundary was reproduced from a "
    "verified fixture behind `lazarus replay`, and its guard fails closed on "
    "a miss."
)

# The import names that the four exact pins in plugins/lazarus/requirements.txt
# provide: eth-hash[pycryptodome] imports as eth_hash and Crypto; jsonschema,
# rlp and trie import as themselves. They are a constant rather than a read of
# that file because a requirement name is not an import name (one pin is two
# modules, neither spelled like the pin), and because the probe must say what
# is missing without parsing anything.
LAZARUS_IMPORTS = ("eth_hash", "Crypto", "jsonschema", "rlp", "trie")

# The replay server's argument list is fixed: an interpreter, a script path,
# a fixture path and an ephemeral port. It carries no URL because replay takes
# none, and it runs with the repository root as the working directory.
REPLAY_ARGV = [
    sys.executable,
    "plugins/lazarus/scripts/lazarus.py",
    "replay",
    "plugins/lazarus/examples/goldfinch-v0",
    "--port",
    "0",
]
LISTENING_PREFIX = "lazarus replay listening on http://127.0.0.1:"
FIRST_LINE_SECONDS = 30.0
STOP_SECONDS = 10.0

MISS_ERROR = -32070
METHOD_NOT_FOUND = -32601
ADDRESS = "0x8bbd80f88e662e56b918c353da635e210ece93c6"
BLOCK_NUMBER = "0xc7da16"
SLOT_ZERO_WORD = "0x" + "00" * 31 + "01"


def fixture_section(text):
    """The section's text, or an empty string when its heading is absent."""
    start = text.find(SECTION_HEADING)
    if start < 0:
        return ""
    end = text.find(NEXT_HEADING, start)
    return text[start:end] if end > start else text[start:]


def between(flat, first, second):
    """The whitespace-normalised text between two headings that always exist."""
    return flat[flat.index(first):flat.index(second)]


def missing_lazarus_imports(find_spec=importlib.util.find_spec):
    """The names in LAZARUS_IMPORTS the running interpreter cannot import."""
    return [name for name in LAZARUS_IMPORTS if find_spec(name) is None]


def skip_reason(missing, executable=sys.executable):
    """The fixed skip text: the interpreter, the missing names, the uv command."""
    return (
        "Lazarus dependencies are not importable from "
        + executable
        + ": "
        + ", ".join(missing)
        + "; run under "
        + UV_COMMAND
    )


def recorded_outcome(method, params):
    """The outcome of the Goldfinch record whose method and params match exactly."""
    with RPC_RECORDS.open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            if record["method"] == method and record["params"] == params:
                return record["outcome"]
    raise AssertionError("no Goldfinch record for " + method + " " + repr(params))


class ProcedureTextTests(unittest.TestCase):
    """Every case fails by assertion on a skill file without the section."""

    @classmethod
    def setUpClass(cls):
        cls.text = SKILL_FILE.read_text(encoding="utf-8")
        cls.section = fixture_section(cls.text)
        cls.flat = " ".join(cls.text.split())

    def test_section_sits_after_verify_and_before_three_rounds(self):
        self.assertIn(SECTION_HEADING, self.text)
        verify = self.text.find("### 6. Verify")
        heading = self.text.find(SECTION_HEADING)
        three_rounds = self.text.find(NEXT_HEADING)
        self.assertTrue(
            0 <= verify < heading < three_rounds, (verify, heading, three_rounds)
        )

    def test_capture_command_takes_the_url_from_the_environment(self):
        self.assertIn(LAZARUS_COMMAND + " capture --plan", self.section)
        self.assertIn('--rpc-url "$LAZARUS_RPC_URL"', self.section)
        self.assertIn("--anchor-rpc-env SOURCE_ID=ENV_VAR", self.section)

    def test_verify_command_supplies_the_digest_for_the_docstring(self):
        self.assertIn(LAZARUS_COMMAND + " verify", self.section)
        self.assertIn("docstring", self.section)

    def test_replay_command_binds_an_ephemeral_loopback_port(self):
        self.assertIn(LAZARUS_COMMAND + " replay", self.section)
        self.assertIn("--port 0", self.section)
        self.assertIn(LISTENING_PREFIX + "<port>", self.section)

    def test_miss_code_is_a_failed_test_and_never_a_zero(self):
        self.assertIn("`-32070`", self.section)
        self.assertIn("never as a zero", self.section)

    def test_optional_request_rule_pins_a_provider_error(self):
        self.assertIn("`required: true`", self.section)
        self.assertIn("`required: false`", self.section)
        self.assertIn("`provider request failed`", self.section)
        self.assertIn("`-32000`", self.section)

    def test_plan_fragment_carries_one_required_and_one_optional_request(self):
        self.assertIn("```json", self.section)
        self.assertEqual(self.section.count('"required": true'), 1)
        self.assertEqual(self.section.count('"required": false'), 1)

    def test_environment_bullet_points_at_the_section(self):
        self.assertIn(SECTION_HEADING, self.text)
        reproduce = between(self.flat, "### 1. Reproduce", "### 2. Localise")
        self.assertIn(ENVIRONMENT_SENTENCE, reproduce)

    def test_checklist_names_the_fixture_guard(self):
        self.assertIn(SECTION_HEADING, self.text)
        checklist = between(
            self.flat, "## Before the fix is receipted", "## Hand back"
        )
        self.assertIn(CHECKLIST_ITEM, checklist)

    def test_closing_paragraph_names_the_example_and_the_uv_command(self):
        self.assertIn(EXAMPLE_MODULE, self.section)
        self.assertIn(
            UV_COMMAND
            + " python -m unittest"
            + " plugins.hexaemeron.tests.test_elenchus_rpc_boundary_fixture",
            self.section,
        )


class LazarusDependencyGuardTests(unittest.TestCase):
    """The probe and its skip reason, exercised with a fake finder."""

    def test_probe_names_every_missing_import_in_declared_order(self):
        present = {"jsonschema", "rlp"}

        def find_spec(name):
            return object() if name in present else None

        self.assertEqual(
            missing_lazarus_imports(find_spec), ["eth_hash", "Crypto", "trie"]
        )

    def test_probe_reports_nothing_missing_when_every_import_is_found(self):
        self.assertEqual(missing_lazarus_imports(lambda name: object()), [])

    def test_probe_asks_for_exactly_the_five_import_names(self):
        asked = []

        def find_spec(name):
            asked.append(name)
            return None

        self.assertEqual(missing_lazarus_imports(find_spec), list(LAZARUS_IMPORTS))
        self.assertEqual(asked, ["eth_hash", "Crypto", "jsonschema", "rlp", "trie"])

    def test_skip_reason_names_the_missing_imports_and_the_uv_command(self):
        self.assertEqual(
            skip_reason(["eth_hash", "trie"], executable="/opt/py/bin/python"),
            "Lazarus dependencies are not importable from /opt/py/bin/python: "
            'eth_hash, trie; run under uv run --no-project --python '
            '"$(cat .python-version)" '
            "--with-requirements plugins/lazarus/requirements.txt",
        )
        reason = skip_reason(list(LAZARUS_IMPORTS))
        for name in LAZARUS_IMPORTS:
            self.assertIn(name, reason)
        self.assertIn(sys.executable, reason)


class ReplayGuardExampleTests(unittest.TestCase):
    """Drive the shipped Goldfinch fixture through `lazarus replay` on loopback."""

    process = None
    port = None

    @classmethod
    def setUpClass(cls):
        missing = missing_lazarus_imports()
        if missing:
            raise unittest.SkipTest(skip_reason(missing))
        cls.process = subprocess.Popen(
            REPLAY_ARGV,
            cwd=str(REPO_ROOT),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        deadline = threading.Timer(FIRST_LINE_SECONDS, cls.process.kill)
        deadline.start()
        try:
            first_line = cls.process.stdout.readline()
        finally:
            deadline.cancel()
        if not first_line.startswith(LISTENING_PREFIX):
            stderr = cls.stop()
            raise AssertionError(
                "lazarus replay did not print its listening line; first line "
                + repr(first_line)
                + "; stderr:\n"
                + stderr
            )
        cls.port = int(first_line[len(LISTENING_PREFIX):].strip())

    @classmethod
    def tearDownClass(cls):
        cls.stop()

    @classmethod
    def stop(cls):
        """Terminate the server, wait with a bound, kill on timeout, close pipes."""
        process = cls.process
        if process is None:
            return ""
        cls.process = None
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=STOP_SECONDS)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=STOP_SECONDS)
        stderr = process.stderr.read()
        process.stdout.close()
        process.stderr.close()
        return stderr

    def setUp(self):
        self.destinations = []
        destinations = self.destinations
        real_connect = socket.socket.connect

        def guarded_connect(sock, address):
            destinations.append(address)
            if not ipaddress.ip_address(address[0]).is_loopback:
                raise AssertionError("outbound replay connection: " + repr(address))
            return real_connect(sock, address)

        patcher = mock.patch.object(socket.socket, "connect", guarded_connect)
        patcher.start()
        self.addCleanup(patcher.stop)

    def rpc(self, method, params, identifier):
        """One JSON-RPC 2.0 request on its own loopback connection."""
        body = json.dumps(
            {"jsonrpc": "2.0", "id": identifier, "method": method, "params": params}
        )
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        try:
            connection.request(
                "POST", "/", body=body, headers={"Content-Type": "application/json"}
            )
            response = connection.getresponse()
            payload = response.read()
        finally:
            connection.close()
        self.assertEqual(response.status, 200)
        self.assertTrue(self.destinations, "no connection was observed")
        self.assertTrue(
            all(ipaddress.ip_address(item[0]).is_loopback for item in self.destinations),
            self.destinations,
        )
        parsed = json.loads(payload)
        self.assertEqual(parsed["jsonrpc"], "2.0")
        self.assertEqual(parsed["id"], identifier)
        return parsed

    def test_recorded_slot_zero_replays_byte_for_byte(self):
        params = [ADDRESS, "0x0", BLOCK_NUMBER]
        outcome = recorded_outcome("eth_getStorageAt", params)
        response = self.rpc("eth_getStorageAt", params, 1)
        self.assertNotIn("error", response)
        self.assertEqual(response["result"], outcome["result"])
        self.assertEqual(response["result"], SLOT_ZERO_WORD)

    def test_uncaptured_slot_one_is_a_miss_carrying_a_plan_fragment(self):
        params = [ADDRESS, "0x1", BLOCK_NUMBER]
        response = self.rpc("eth_getStorageAt", params, 2)
        self.assertNotIn("result", response)
        error = response["error"]
        self.assertEqual(error["code"], MISS_ERROR)
        self.assertEqual(error["data"]["method"], "eth_getStorageAt")
        self.assertEqual(error["data"]["params"], params)
        fragment = error["data"]["capture_plan_fragment"]
        self.assertEqual(fragment["method"], "eth_getStorageAt")
        self.assertEqual(fragment["params"], params)
        self.assertEqual(fragment["evidence"], "recorded-rpc")
        self.assertIs(fragment["required"], True)

    def test_zero_padded_spelling_of_slot_zero_is_a_miss(self):
        response = self.rpc("eth_getStorageAt", [ADDRESS, "0x00", BLOCK_NUMBER], 3)
        self.assertNotIn("result", response)
        self.assertEqual(response["error"]["code"], MISS_ERROR)

    def test_write_method_is_refused(self):
        response = self.rpc("eth_sendRawTransaction", ["0x00"], 4)
        self.assertNotIn("result", response)
        self.assertEqual(response["error"]["code"], METHOD_NOT_FOUND)

    def test_replay_argv_carries_no_url_and_no_rpc_url_flag(self):
        self.assertEqual(REPLAY_ARGV[0], sys.executable)
        self.assertNotIn("--rpc-url", REPLAY_ARGV)
        for argument in REPLAY_ARGV:
            self.assertNotIn("://", argument)


if __name__ == "__main__":
    unittest.main()
