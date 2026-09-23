import contextlib
import hashlib
import importlib.util
import io
import json
import os
import subprocess
import tempfile
import unittest
import urllib.request
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "emitter_declarations.py"
STUDY = ROOT / "docs" / "emitter-declaration-check-study.md"
RUNBOOK = ROOT / "docs" / "emitter-declaration-check-runbook.md"

SPEC = importlib.util.spec_from_file_location("emitter_declarations", SCRIPT)
emitter_declarations = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(emitter_declarations)
ed = emitter_declarations

PIN = ed.PIN
TAG = ed.COMPILER_OUTPUT_REF
OTHER = "b" * 40
EMITTERS = "src/libraries/MarketEvents.sol"
EVENTS = "src/interfaces/IEvents.sol"
CALLER = "src/market/Market.sol"


def topic(signature):
    return "0x" + ed.keccak256(signature.encode()).hex()


# Synthetic Solidity written for these tests; no target source is used.
CLEAN_EMITTERS = f"""// SPDX-License-Identifier: MIT
uint256 constant Moved_size = 0x40;

function emit_Moved(address account, uint256 amount, uint256 shares) {{
  assembly {{
    mstore(0, amount)
    mstore(0x20, shares)
    log2(0, Moved_size, {topic("Moved(address,uint256,uint256)")}, account)
  }}
}}

function emit_Sent(address from, address to, uint256 value) {{
  assembly {{
    mstore(0, value)
    log3(0, 0x20, {topic("Sent(address,address,uint256)")}, from, to)
  }}
}}
"""
CLEAN_EVENTS = """// SPDX-License-Identifier: MIT
interface IEvents {
  event Moved(address indexed account, uint256 amount, uint256 shares);
  event Sent(address indexed from, address indexed to, uint256 value);
  event Unused(uint256 value);
}
"""
CALLER_SOURCE = """contract Market {
  function f(address a, uint256 b) internal { emit_Moved(a, b, b); emit_Sent(a, a, b); }
}
"""
CLEAN_ABI = [
    {"type": "event", "name": "Moved", "anonymous": False, "inputs": [
        {"name": "account", "type": "address", "indexed": True},
        {"name": "amount", "type": "uint256", "indexed": False},
        {"name": "shares", "type": "uint256", "indexed": False}]},
    {"type": "event", "name": "Sent", "anonymous": False, "inputs": [
        {"name": "from", "type": "address", "indexed": True},
        {"name": "to", "type": "address", "indexed": True},
        {"name": "value", "type": "uint256", "indexed": False}]},
]


class FakeGit:
    """An in-memory reader with the GitReader interface."""

    def __init__(self, files):
        self.files = dict(files)
        self.reads = []

    def list_sources(self, ref):
        return {p: ed.git_blob_id(d) for (r, p), d in self.files.items()
                if r == ref and p.startswith("src/") and p.endswith(".sol")}

    def read(self, ref, path):
        self.reads.append((ref, path))
        if (ref, path) not in self.files:
            raise ed.read_failure(f"{path} absent at {ref}")
        return self.files[(ref, path)]


class FakeHttps(FakeGit):
    list_sources = None


def fixture(emitters=CLEAN_EMITTERS, events=CLEAN_EVENTS, abi=None, extra=None, ref=PIN, market_emitters=None):
    sources = {EMITTERS: emitters, EVENTS: events, CALLER: CALLER_SOURCE}
    sources.update(extra or {})
    files = {(ref, p): t.encode() for p, t in sources.items()}
    market_input = {"language": "Solidity", "sources": {
        EMITTERS: {"content": market_emitters if market_emitters is not None else emitters},
        CALLER: {"content": CALLER_SOURCE}}}
    builds = {
        "WildcatMarket": (market_input, {"abi": CLEAN_ABI if abi is None else abi}),
        "HooksFactory": ({"language": "Solidity", "sources": {}}, {"abi": []}),
    }
    for contract, address in ed.DEPLOYMENTS:
        input_path, output_path = ed.deployment_paths(contract, address)
        standard_input, output = builds[contract]
        files[(TAG, input_path)] = json.dumps(standard_input).encode()
        files[(TAG, output_path)] = json.dumps(output).encode()
    return files


def build_table(**kwargs):
    reader = FakeGit(fixture(**kwargs))
    return ed.assemble(ed.read_build(reader, PIN, TAG), PIN, TAG)


def row(table, emitter):
    return next(r for r in table["rows"] if r["emitter"] == emitter)


def specimen(old, new, where="emitters"):
    source = CLEAN_EMITTERS if where == "emitters" else CLEAN_EVENTS
    if old not in source:
        raise AssertionError(f"specimen anchor {old!r} missing")
    changed = source.replace(old, new, 1)
    if where == "emitters":
        return build_table(emitters=changed, market_emitters=changed)
    return build_table(events=changed)


def run_main(argv, reader):
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        code = ed.main(argv, reader=reader)
    return code, err.getvalue()


class KeccakVectorTests(unittest.TestCase):
    def test_empty_input(self):
        self.assertEqual(
            emitter_declarations.keccak256(b"").hex(),
            "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470",
        )

    def test_erc20_transfer_signature(self):
        self.assertEqual(
            emitter_declarations.keccak256(b"Transfer(address,address,uint256)").hex(),
            "ddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",
        )

    def test_padding_boundary_vectors(self):
        # S1-R1-01: at len % 136 == 135 one padding byte remains, so the
        # suffix and the final bit share it as 0x81. Values from
        # `openssl dgst -keccak-256`.
        vectors = {
            135: "34367dc248bbd832f4e3e69dfaac2f92638bd0bbd18f2912ba4ef454919cf446",
            136: "a6c4d403279fe3e0af03729caada8374b5ca54d8065329a3ebcaeb4b60aa386e",
            271: "132f47effd6c8b1b299efa53fe68aece77ec8ae4eb2e294f668eec94f76001e1",
        }
        observed = {
            length: emitter_declarations.keccak256(b"a" * length).hex()
            for length in vectors
        }
        self.assertEqual(observed, vectors)

    def test_sponge_matches_sha3_across_three_blocks(self):
        # S1-R1-02: the sponge under SHA3's 0x06 suffix must equal hashlib's
        # SHA3-256 at every length from 0 to 409, which crosses the
        # one-byte-remaining boundary at 135, 271 and 407.
        sponge = getattr(emitter_declarations, "_sponge", None)
        self.assertIsNotNone(sponge, "no suffix-parameterised sponge to compare")
        mismatched = []
        for length in range(410):
            data = bytes(index % 251 for index in range(length))
            if sponge(data, 0x06) != hashlib.sha3_256(data).digest():
                mismatched.append(length)
        self.assertEqual(mismatched, [])


class CleanPairTests(unittest.TestCase):
    def test_clean_pair_has_no_mismatch(self):
        table = build_table()
        self.assertEqual((table["mismatches"], table["unreviewed"], table["summary"]["rows"]), ([], [], 2))

    def test_expected_topic0_comes_from_the_declaration(self):
        moved = row(build_table(), "emit_Moved")
        self.assertEqual((moved["signature"], moved["topic0"], moved["abi_checked"]),
                         ("Moved(address,uint256,uint256)", topic("Moved(address,uint256,uint256)"),
                          ["WildcatMarket"]))

    def test_reached_by_names_the_calling_build(self):
        self.assertEqual(row(build_table(), "emit_Moved")["reached_by"], ["WildcatMarket"])

    def test_declaration_without_emitter_is_listed(self):
        listed = [d["declaration"] for d in build_table()["declarations_without_emitter"]]
        self.assertEqual(listed, ["IEvents.Unused"])

    def test_source_block_binds_every_read_file(self):
        table = build_table()
        paths = sorted(f["path"] for f in table["source"]["files"])
        expected = sorted([EMITTERS, EVENTS, CALLER] + [p for c, a in ed.DEPLOYMENTS for p in ed.deployment_paths(c, a)])
        self.assertEqual(paths, expected)


class SpecimenTests(unittest.TestCase):
    """Each seeded specimen must fail for its own named class."""

    def test_topic0_specimen(self):
        literal = topic("Moved(address,uint256,uint256)")
        table = specimen(literal, literal[:-1] + ("0" if literal[-1] != "0" else "1"))
        self.assertIn("topic0", row(table, "emit_Moved")["classes"])

    def test_log_arity_specimen(self):
        table = specimen("log2(0, Moved_size, " + topic("Moved(address,uint256,uint256)") + ", account)",
                         "log1(0, Moved_size, " + topic("Moved(address,uint256,uint256)") + ")")
        self.assertIn("log-arity", row(table, "emit_Moved")["classes"])

    def test_indexed_order_specimen(self):
        table = specimen(", from, to)", ", to, from)")
        self.assertIn("indexed-order", row(table, "emit_Sent")["classes"])

    def test_data_length_specimen(self):
        table = specimen("log2(0, Moved_size,", "log2(0, 0x20,")
        self.assertIn("data-length", row(table, "emit_Moved")["classes"])

    def test_data_order_specimen(self):
        table = specimen("mstore(0, amount)\n    mstore(0x20, shares)", "mstore(0, shares)\n    mstore(0x20, amount)")
        self.assertIn("data-order", row(table, "emit_Moved")["classes"])

    def test_parameter_count_specimen(self):
        table = specimen("uint256 amount, uint256 shares);", "uint256 amount);", where="events")
        self.assertIn("parameter-count", row(table, "emit_Moved")["classes"])

    def test_anonymous_declared_specimen(self):
        table = specimen("uint256 shares);", "uint256 shares) anonymous;", where="events")
        self.assertIn("anonymous-declared", row(table, "emit_Moved")["classes"])

    def test_anonymous_indexed_order_is_not_silently_skipped(self):
        # S2-R1-01: a genuinely anonymous `logN` call reserves no topic0
        # slot, so args[2] is the first indexed value, not a signature
        # literal. Before the fix, the parser still read args[2] into
        # `topic0_literal` and dropped it from `topic_args`, so this
        # anonymous Sent emitter -- whose first topic is a stray literal
        # where `from` belongs -- lost one indexed word and its
        # `indexed-order` mismatch went undetected.
        literal = "0x" + "11" * 32
        events = CLEAN_EVENTS.replace(
            "event Sent(address indexed from, address indexed to, uint256 value);",
            "event Sent(address indexed from, address indexed to, uint256 value) anonymous;",
        )
        emitters = CLEAN_EMITTERS.replace(
            "log3(0, 0x20, " + topic("Sent(address,address,uint256)") + ", from, to)",
            f"log2(0, 0x20, {literal}, to)",
        )
        table = build_table(emitters=emitters, events=events, market_emitters=emitters)
        sent = row(table, "emit_Sent")
        self.assertEqual(sent["log_arity"], 2)
        self.assertNotIn("log-arity", sent["classes"])
        self.assertIn("indexed-order", sent["classes"])

    def test_abi_view_disagreement_is_prefixed(self):
        abi = json.loads(json.dumps(CLEAN_ABI))
        abi[0]["inputs"][1]["type"] = "uint128"
        self.assertIn("abi:WildcatMarket:topic0", row(build_table(abi=abi), "emit_Moved")["classes"])

    def test_mismatch_row_is_listed_not_dropped(self):
        table = specimen("log2(0, Moved_size,", "log2(0, 0x20,")
        self.assertEqual([m["emitter"] for m in table["mismatches"]], ["emit_Moved"])


class UnreviewedTests(unittest.TestCase):
    def reasons(self, table):
        return {u["name"]: u["reason"] for u in table["unreviewed"]}

    def test_zero_log_sites_is_unreviewed(self):
        source = CLEAN_EMITTERS.replace("log3(0, 0x20, " + topic("Sent(address,address,uint256)") + ", from, to)", "")
        self.assertEqual(self.reasons(build_table(emitters=source)).get("emit_Sent"), "0 log sites in the body")

    def test_two_log_sites_is_unreviewed(self):
        call = "log3(0, 0x20, " + topic("Sent(address,address,uint256)") + ", from, to)"
        source = CLEAN_EMITTERS.replace(call, call + "\n    " + call)
        self.assertEqual(self.reasons(build_table(emitters=source)).get("emit_Sent"), "2 log sites in the body")

    def test_log_site_outside_an_emitter_is_unreviewed(self):
        source = CLEAN_EMITTERS + "\nfunction other() { assembly { log0(0, 0) } }\n"
        kinds = [u["kind"] for u in build_table(emitters=source)["unreviewed"]]
        self.assertEqual(kinds, ["log-site"])

    def test_unresolved_parameter_type_gives_unreviewed_row(self):
        events = CLEAN_EVENTS.replace("uint256 value);\n  event Unused", "Mystery value);\n  event Unused")
        sent = row(build_table(events=events), "emit_Sent")
        self.assertEqual((sent["status"], sent["classes"], sent["signature"]), ("unreviewed", [], None))

    def test_braces_in_comments_and_strings_do_not_hide_an_emitter(self):
        source = CLEAN_EMITTERS.replace("assembly {\n    mstore(0, value)",
                                        'assembly {\n    // }} log1(\n    /* { */\n    mstore(0, value)')
        table = build_table(emitters=source)
        self.assertEqual((table["summary"]["emitters"], table["mismatches"], table["unreviewed"]), (2, [], []))

    def test_subword_value_is_a_note_not_a_class(self):
        source = CLEAN_EMITTERS.replace("address account, uint256 amount", "address account, uint32 amount")
        moved = row(build_table(emitters=source, market_emitters=source), "emit_Moved")
        self.assertEqual((moved["classes"], any("`amount` (`uint32`)" in n for n in moved["notes"])), ([], True))


class TypeMappingTests(unittest.TestCase):
    def test_canonical_type_mapping(self):
        resolver = ed.TypeResolver({"src/T.sol": """
            interface IToken {}
            contract Vault {}
            library Lib { enum Mode { A, B } struct Pair { uint a; IToken b; } }
            enum Kind { X }
            type Price is uint128;
        """})
        observed = {t: resolver.resolve(t) for t in (
            "IToken", "Vault", "Kind", "Lib.Mode", "Price", "Lib.Pair", "Price[]", "uint", "bytes32[2]", "Lib", "Missing")}
        self.assertEqual(observed, {
            "IToken": "address", "Vault": "address", "Kind": "uint8", "Lib.Mode": "uint8", "Price": "uint128",
            "Lib.Pair": "(uint256,address)", "Price[]": "uint128[]", "uint": "uint256",
            "bytes32[2]": "bytes32[2]", "Lib": None, "Missing": None})

    def test_conflicting_definitions_do_not_resolve(self):
        resolver = ed.TypeResolver({"src/A.sol": "type Amount is uint128;", "src/B.sol": "type Amount is uint64;"})
        self.assertIsNone(resolver.resolve("Amount"))


class CommandTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.table = os.path.join(self.tmp.name, "emitters.json")
        self.markdown = os.path.join(self.tmp.name, "emitters.md")

    def build(self, files):
        return run_main(["build", "--from-git", "clone", "--out", self.table, "--markdown", self.markdown],
                        FakeGit(files))

    def check(self, files, *extra):
        return run_main(["check", "--from-git", "clone", "--table", self.table, *extra], FakeGit(files))

    def test_build_writes_a_mismatch_row(self):
        changed = CLEAN_EMITTERS.replace("log2(0, Moved_size,", "log2(0, 0x20,")
        code, _err = self.build(fixture(emitters=changed, market_emitters=changed))
        with open(self.table, encoding="utf-8") as fh:
            written = json.load(fh)
        self.assertEqual((code, [m["classes"] for m in written["mismatches"]]),
                         (0, [["abi:WildcatMarket:data-length", "data-length"]]))

    def test_check_passes_on_a_regenerated_table(self):
        self.build(fixture())
        code, err = self.check(fixture(), "--markdown", self.markdown)
        self.assertEqual((code, err.strip()), (0, f"check: {self.table} regenerates exactly"))

    def test_check_exits_1_and_writes_nothing_on_a_byte_difference(self):
        self.build(fixture())
        with open(self.table, "rb") as fh:
            original = fh.read().replace(b'"emitters": 2', b'"emitters": 3')
        with open(self.table, "wb") as fh:
            fh.write(original)
        before = sorted(os.listdir(self.tmp.name))
        code, err = self.check(fixture())
        with open(self.table, "rb") as fh:
            after = fh.read()
        self.assertEqual((code, err.startswith("table-difference:"), after == original,
                          sorted(os.listdir(self.tmp.name))), (1, True, True, before))

    def test_size_mismatch_is_source_drift(self):
        self.build(fixture())
        code, err = self.check(fixture(events=CLEAN_EVENTS + "\n"))
        self.assertEqual((code, err.startswith(f"source-drift: {EVENTS} at {PIN}"), "table-difference" in err),
                         (1, True, False))

    def test_digest_mismatch_is_source_drift(self):
        self.build(fixture())
        same_size = CLEAN_EVENTS.replace("uint256 value);\n}", "uint256 valuf);\n}")
        code, err = self.check(fixture(events=same_size))
        self.assertEqual((code, len(same_size) == len(CLEAN_EVENTS), f"{EVENTS} at {PIN}: sha256" in err),
                         (1, True, True))

    def test_check_ref_override_names_moved_paths(self):
        self.build(fixture())
        files = fixture()
        files.update(fixture(ref=OTHER, events=CLEAN_EVENTS + "\n"))
        code, err = self.check(files, "--ref", OTHER)
        moved = [line for line in err.splitlines() if " at " + OTHER + ": sha256 " in line]
        self.assertEqual((code, [line.split()[1] for line in moved]), (1, [EVENTS]))

    def test_check_ref_override_with_equal_bytes_passes(self):
        self.build(fixture())
        files = fixture()
        files.update(fixture(ref=OTHER))
        self.assertEqual(self.check(files, "--ref", OTHER)[0], 0)

    def test_added_file_at_ref_is_source_drift(self):
        self.build(fixture())
        code, err = self.check(fixture(extra={"src/New.sol": "contract New {}"}))
        self.assertEqual((code, "source-drift: src/New.sol is present at" in err), (1, True))

    def test_markdown_difference_is_named(self):
        self.build(fixture())
        with open(self.markdown, "a", encoding="utf-8") as fh:
            fh.write("edited\n")
        code, err = self.check(fixture(), "--markdown", self.markdown)
        self.assertEqual((code, err.startswith("markdown-difference:")), (1, True))

    def test_markdown_is_rendered_from_the_json(self):
        self.build(fixture())
        with open(self.table, encoding="utf-8") as fh:
            rendered = ed.render_markdown(json.load(fh))
        with open(self.markdown, encoding="utf-8") as fh:
            self.assertEqual(fh.read(), rendered)

    def test_https_build_refuses_a_digest_mismatch(self):
        self.build(fixture())
        out = os.path.join(self.tmp.name, "https.json")
        code, err = run_main(["build", "--from-https", "--table", self.table, "--out", out],
                             FakeHttps(fixture(events=CLEAN_EVENTS + "\n")))
        self.assertEqual((code, err.startswith("source-drift:"), os.path.exists(out)), (1, True, False))

    def test_usage_error_exits_2(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as caught:
            ed.main(["check", "--from-git", "clone", "--table", self.table, "--ref", "not-a-commit"])
        self.assertEqual(caught.exception.code, 2)


class _Response(io.BytesIO):
    def __init__(self, data, url):
        super().__init__(data)
        self.url = url

    def geturl(self):
        return self.url


class _Opener:
    def __init__(self, data=b"x", url=None):
        self.data, self.url, self.opened = data, url, []

    def open(self, url, timeout):
        self.opened.append((url, timeout))
        return _Response(self.data, self.url or url)


class ReaderTests(unittest.TestCase):
    def test_https_url_is_fixed_host_and_pinned_commit(self):
        opener = _Opener()
        ed.HttpsReader(opener).read(PIN, EVENTS)
        self.assertEqual(opener.opened, [(f"https://raw.githubusercontent.com/wildcat-finance/v2-protocol/{PIN}/{EVENTS}",
                                          ed.HTTPS_TIMEOUT_SECONDS)])

    def test_redirect_off_host_refuses(self):
        handler = ed._HostPinnedRedirect()
        request = urllib.request.Request(ed.HttpsReader.url(PIN, EVENTS))
        with self.assertRaises(ed.Refusal):
            handler.redirect_request(request, None, 302, "Found", {}, "https://example.com/x")

    def test_response_served_off_host_refuses(self):
        with self.assertRaises(ed.Refusal):
            ed.HttpsReader(_Opener(url="https://example.com/x")).read(PIN, EVENTS)

    def test_https_size_cap_refuses(self):
        with self.assertRaises(ed.Refusal):
            ed.HttpsReader(_Opener(data=b"x" * (ed.MAX_FILE_BYTES + 1))).read(PIN, EVENTS)

    def test_git_show_argv_is_fixed_list_without_shell(self):
        completed = mock.Mock(returncode=0, stdout=b"data")
        with mock.patch.object(ed.subprocess, "run", return_value=completed) as run:
            ed.GitReader("/clone").read(PIN, EVENTS)
        args, kwargs = run.call_args
        self.assertEqual((args[0], kwargs.get("shell", False), kwargs["timeout"]),
                         (["git", "-C", os.path.abspath("/clone"), "--no-pager", "show", "--no-textconv",
                           "--end-of-options", f"{PIN}:{EVENTS}"], False, ed.GIT_TIMEOUT_SECONDS))

    def test_git_rejects_unsafe_path_before_running(self):
        with mock.patch.object(ed.subprocess, "run") as run, self.assertRaises(ed.Refusal):
            ed.GitReader("/clone").read(PIN, "src/../../etc/passwd")
        self.assertFalse(run.called)


class AtomicWriteTests(unittest.TestCase):
    def test_atomic_write_replaces_through_a_sibling_temp_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = os.path.join(tmp, "t.json")
            real = os.replace
            with mock.patch.object(ed.os, "replace", side_effect=real) as replace:
                ed.atomic_write(target, b"{}\n")
            source, destination = replace.call_args[0]
            self.assertEqual((os.path.dirname(source), destination, os.listdir(tmp)), (tmp, target, ["t.json"]))

    def test_atomic_write_failure_leaves_target_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = os.path.join(tmp, "t.json")
            with open(target, "wb") as fh:
                fh.write(b"old")
            with mock.patch.object(ed.os, "replace", side_effect=OSError("boom")), self.assertRaises(OSError):
                ed.atomic_write(target, b"new")
            with open(target, "rb") as fh:
                self.assertEqual((fh.read(), os.listdir(tmp)), (b"old", ["t.json"]))


class CommittedTableTests(unittest.TestCase):
    """Offline checks against the committed docs/kickoff/1361 table (#1361 step 3)."""

    TABLE_PATH = ROOT / "docs" / "kickoff" / "1361" / "emitters.json"
    MARKDOWN_PATH = ROOT / "docs" / "kickoff" / "1361" / "emitters.md"

    @classmethod
    def setUpClass(cls):
        with open(cls.TABLE_PATH, encoding="utf-8") as fh:
            cls.table = json.load(fh)

    def test_committed_markdown_is_byte_equal_to_its_rendering(self):
        rendered = ed.render_markdown(self.table)
        with open(self.MARKDOWN_PATH, encoding="utf-8") as fh:
            self.assertEqual(fh.read(), rendered)

    def test_table_names_the_pin_the_tag_and_both_verification_digests(self):
        source = self.table["source"]
        self.assertEqual(source["commit"], ed.PIN)
        self.assertEqual(source["compiler_output_ref"], ed.COMPILER_OUTPUT_REF)
        self.assertEqual(len(source["deployments"]), 2)
        self.assertTrue(all(len(d["standard_input_sha256"]) == 64 and len(d["output_sha256"]) == 64
                            for d in source["deployments"]))

    def test_every_emitter_appears_in_a_row_or_the_unreviewed_list(self):
        named_in_rows = {r["emitter"] for r in self.table["rows"]}
        named_unreviewed = {u["name"] for u in self.table["unreviewed"] if u["kind"] == "emitter"}
        self.assertEqual(len(named_in_rows | named_unreviewed), self.table["summary"]["emitters"])

    _WALK_SKIP_DIRS = {".git", ".hexaemeron", "tmp"}

    @classmethod
    def _sol_paths_by_walk(cls, root):
        """List every `.sol` file under `root`, skipping VCS/run-state dirs.

        Used only when a git index is unavailable (S3-R2-01): Elenchus's
        guard-check export tree is a plain file copy with no `.git`, so
        `git ls-files` cannot run there. Path names are relative to `root`.
        """
        found = []
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames
                           if d not in cls._WALK_SKIP_DIRS and not d.startswith(".")]
            for name in filenames:
                if name.endswith(".sol"):
                    full = Path(dirpath) / name
                    found.append(str(full.relative_to(root)))
        return found

    @classmethod
    def _committed_sol_paths(cls, root):
        """Return the repository's `.sol` paths, preferring the git index.

        Falls back to `_sol_paths_by_walk` when `git` cannot run (no `.git`,
        or the call itself is refused) -- never silently skips the check.
        """
        try:
            tracked = subprocess.run(["git", "ls-files"], cwd=root, capture_output=True,
                                     text=True, check=True).stdout.splitlines()
            return [p for p in tracked if p.endswith(".sol")]
        except (OSError, subprocess.CalledProcessError):
            return cls._sol_paths_by_walk(root)

    def test_no_v2_protocol_source_file_is_tracked(self):
        source_files = [f for f in self.table["source"]["files"] if f["role"] == "source"]
        source_paths = {f["path"] for f in source_files}
        source_hashes = {f["sha256"] for f in source_files}
        committed_sol = self._committed_sol_paths(ROOT)
        matched_by_path = source_paths & set(committed_sol)
        matched_by_bytes = set()
        for rel in committed_sol:
            try:
                digest = hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
            except OSError:
                continue
            if digest in source_hashes:
                matched_by_bytes.add(rel)
        self.assertEqual((matched_by_path, matched_by_bytes), (set(), set()))

    def test_the_check_falls_back_to_a_tree_walk_when_git_is_unavailable(self):
        """S3-R2-01 guard: fails on the parent, which has no fallback and lets

        `subprocess.run`'s exception propagate uncaught whenever `git` cannot
        run -- exactly Elenchus's export-tree condition (no `.git` directory).
        """
        with mock.patch("subprocess.run", side_effect=FileNotFoundError("git")):
            committed_sol = self._committed_sol_paths(ROOT)
        source_files = [f for f in self.table["source"]["files"] if f["role"] == "source"]
        source_paths = {f["path"] for f in source_files}
        self.assertGreater(len(committed_sol), 0)
        self.assertEqual(source_paths & set(committed_sol), set())

    def test_expected_figures_at_the_pin(self):
        summary = self.table["summary"]
        self.assertEqual(
            (summary["emitters"], summary["rows"], summary["abi_checked_rows"], summary["mismatch_rows"]),
            (27, 38, 32, 0))


class NotReachedSectionTests(unittest.TestCase):
    """S3-R1-01: a mismatched, unreached row must not be rendered under the

    'Not reached by any deployed build' section's 'compared cleanly' claim.
    """

    def test_a_mismatched_unreached_row_is_excluded_from_compared_cleanly(self):
        table = {
            "schema": "test", "source": {"repository": "r", "commit": "c" * 40,
                "compiler_output_ref": "x" * 40, "deployments": [], "files": []},
            "summary": {}, "mismatches": [], "unreviewed": [], "declarations_without_emitter": [],
            "rows": [{
                "emitter": "emit_Foo", "emitter_at": "a:1", "declaration": "Foo", "declared_at": "b:2",
                "signature": "Foo(uint256)", "topic0": "0x" + "1" * 64, "log_arity": 1,
                "indexed_positions": [], "data_bytes": 32, "abi_checked": [], "reached_by": [],
                "status": "mismatch", "classes": ["topic0"],
                "notes": ["called from no bound deployed build"],
            }],
        }
        rendered = ed.render_markdown(table)
        start = rendered.index("## Not reached by any deployed build")
        end = rendered.index("## Source files")
        section = rendered[start:end]
        self.assertNotIn("emit_Foo", section)
        self.assertIn("None.", section)


class SpecificationCopyTests(unittest.TestCase):
    def test_study_copy_is_committed(self):
        self.assertGreater(STUDY.stat().st_size, 0)

    def test_runbook_copy_is_committed(self):
        self.assertGreater(RUNBOOK.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
