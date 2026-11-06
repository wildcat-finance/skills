"""The Wildcat V1 emitter-declaration checker (#1962).

Every case below except CommittedTableTests runs on synthetic Solidity, a
synthetic registry row and synthetic Sourcify records written for these
tests; no wildcat-protocol source is read or committed.
"""

import contextlib
import hashlib
import importlib.util
import io
import json
import os
import stat
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "emitter_declarations_v1.py"
SPEC = importlib.util.spec_from_file_location("emitter_declarations_v1", SCRIPT)
v1 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(v1)
core = v1.core

PIN = "1" * 40
OTHER = "2" * 40
COMPILER = "0.8.22+commit.4fc1097e"
EMITTERS, SPHEREX = v1.EMITTER_FILES
A = {role: "0x" + f"{n:040x}" for n, role in enumerate(
    ("market", "controller", "factory", "registry", "sanctions-sentinel", "lens", "market-2"), start=1)}


def topic(signature):
    return "0x" + core.keccak256(signature.encode()).hex()


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
CLEAN_SPHEREX = f"""// SPDX-License-Identifier: MIT
function emit_Changed(address oldValue, address newValue) {{
  assembly {{
    mstore(0, oldValue)
    mstore(0x20, newValue)
    log1(0, 0x40, {topic("Changed(address,address)")})
  }}
}}
"""
SOURCES = {
    EMITTERS: CLEAN_EMITTERS,
    SPHEREX: CLEAN_SPHEREX,
    "src/interfaces/IEvents.sol": textwrap.dedent("""\
        interface IEvents {
          event Moved(address indexed account, uint256 amount, uint256 shares);
          event Sent(address indexed from, address indexed to, uint256 value);
          event Changed(address oldValue, address newValue);
        }
        """),
    "src/Base.sol": "abstract contract Base {\n  function _change(address a) internal { emit_Changed(a, a); }\n}\n",
    "src/market/Market.sol": textwrap.dedent("""\
        contract Market is Base {
          function f(address a, uint256 b) internal { emit_Moved(a, b, b); emit_Sent(a, a, b); }
        }
        """),
    "src/Controller.sol": "contract Controller is Base {}\n",
    "src/Factory.sol": textwrap.dedent("""\
        contract Factory is Base {
          event Created(address market);
          function make() external { emit Created(address(0)); }
        }
        """),
    "src/interfaces/IFactory.sol": "interface IFactory {\n  event Created();\n}\n",
    "src/Arch.sol": "contract Arch is Base {}\n",
    "src/Sentinel.sol": textwrap.dedent("""\
        // SPDX-License-Identifier: MIT
        contract Sentinel {
          event Flagged(address account);
          function flag(address a) external { emit Flagged(a); }
        }
        """),
    "src/Lens.sol": "contract Lens {}\n",
}


def event(name, *inputs):
    return {"type": "event", "name": name, "anonymous": False,
            "inputs": [{"name": n, "type": t, "indexed": i} for n, t, i in inputs]}


MOVED = event("Moved", ("account", "address", True), ("amount", "uint256", False), ("shares", "uint256", False))
SENT = event("Sent", ("from", "address", True), ("to", "address", True), ("value", "uint256", False))
CHANGED = event("Changed", ("oldValue", "address", False), ("newValue", "address", False))
MARKET_FILES = (EMITTERS, SPHEREX, "src/interfaces/IEvents.sol", "src/Base.sol", "src/market/Market.sol")
BUILDS = {
    "market": ("src/market/Market.sol", "Market", MARKET_FILES, [MOVED, SENT, CHANGED]),
    "controller": ("src/Controller.sol", "Controller", (SPHEREX, "src/Base.sol", "src/Controller.sol"), [CHANGED]),
    "factory": ("src/Factory.sol", "Factory", MARKET_FILES + ("src/Factory.sol",),
                [CHANGED, event("Created", ("market", "address", False))]),
    "registry": ("src/Arch.sol", "Arch", (SPHEREX, "src/Base.sol", "src/Arch.sol"), [CHANGED]),
    "sanctions-sentinel": ("src/Sentinel.sol", "Sentinel", ("src/Sentinel.sol",),
                           [event("Flagged", ("account", "address", False))]),
    "lens": ("src/Lens.sol", "Lens", (EMITTERS, "src/Lens.sol"), []),
}
PINNED_ROLES = ("factory", "registry", "sanctions-sentinel")


def sources(**changes):
    result = dict(SOURCES)
    result.update(changes)
    return {p: t for p, t in result.items() if t is not None}


def records(git=None, build_changes=None, abi_changes=None):
    """Sourcify records built from the git sources, with per-role overrides."""
    git = git or SOURCES
    out = {}
    for role, (path, name, files, abi) in BUILDS.items():
        contents = {p: git[p] for p in files}
        contents.update((build_changes or {}).get(role, {}))
        out[A[role]] = {
            "address": A[role], "chainId": "1", "match": "match",
            "compilation": {"fullyQualifiedName": f"{path}:{name}", "compilerVersion": COMPILER},
            "stdJsonInput": {"language": "Solidity", "settings": {},
                             "sources": {p: {"content": c} for p, c in contents.items()}},
            "stdJsonOutput": {"contracts": {path: {name: {"abi": (abi_changes or {}).get(role, abi)}}}},
        }
    return out


def registry(recs, pins=None, emitter_paths=None):
    names = {role: BUILDS[role][1] for role in BUILDS}
    build_inputs = [{"compilation_target": names[role],
                     "sha256": (pins or {}).get(role, hashlib.sha256(v1.canonical(recs[A[role]]["stdJsonInput"])).hexdigest())}
                    for role in PINNED_ROLES]
    contracts = [{"role": role, "name": names[role], "address": A[role], "code_match": {"source_commit": PIN}}
                 for role in BUILDS]
    return {"targets": [{"id": v1.REGISTRY_ROW, "source": {
        "repository": f"https://github.com/{v1.REPOSITORY}", "commit": PIN, "compiler": {"solc": COMPILER},
        "build_inputs": build_inputs,
        "emitter_paths": [{"path": p} for p in (emitter_paths or v1.EMITTER_FILES)],
    }, "deployment": {"contracts": contracts,
                      "instances": {"markets": [A["market"], A["market-2"]], "controllers": [A["controller"]]}}}]}


class FakeGit:
    list_sources_enabled = True

    def __init__(self, by_ref):
        self.by_ref = {ref: {p: t.encode() for p, t in files.items()} for ref, files in by_ref.items()}

    def list_sources(self, ref):
        return {p: core.git_blob_id(d) for p, d in self.by_ref.get(ref, {}).items()}

    def read(self, ref, path):
        try:
            return self.by_ref[ref][path]
        except KeyError:
            raise core.read_failure(f"{path} absent at {ref}") from None


class FakeHttps(FakeGit):
    list_sources = None


class FakeSourcify:
    def __init__(self, recs):
        self.recs = recs

    def record(self, address):
        if address not in self.recs:
            raise core.read_failure(f"no Sourcify record for {address}")
        return json.loads(json.dumps(self.recs[address]))


class Estate:
    """A temporary registry root plus the table paths a command writes."""

    def __init__(self, test, recs=None, reg=None):
        self.tmp = tempfile.TemporaryDirectory()
        test.addCleanup(self.tmp.cleanup)
        self.root = self.tmp.name
        self.recs = recs or records()
        self.write_registry(reg or registry(self.recs))
        self.table = os.path.join(self.root, "emitters.json")
        self.markdown = os.path.join(self.root, "emitters.md")

    def write_registry(self, reg):
        path = os.path.join(self.root, v1.REGISTRY_PATH)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(reg, fh)

    def run(self, argv, reader, recs=None):
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            code = v1.main(argv, reader=reader, sourcify=FakeSourcify(recs or self.recs), root=self.root)
        return code, err.getvalue()

    def build(self, git=None, recs=None):
        return self.run(["build", "--from-git", "clone", "--out", self.table, "--markdown", self.markdown],
                        FakeGit({PIN: git or SOURCES}), recs)

    def check(self, by_ref=None, recs=None, *extra):
        return self.run(["check", "--from-git", "clone", "--table", self.table, *extra],
                        FakeGit(by_ref or {PIN: SOURCES}), recs)

    def load(self):
        with open(self.table, encoding="utf-8") as fh:
            return json.load(fh)


def build_table(test, git=None, recs=None, reg=None):
    estate = Estate(test, recs=recs, reg=reg)
    code, err = estate.build(git=git)
    test.assertEqual(code, 0, err)
    return estate.load()


def row(table, emitter, declaration=None):
    return next(r for r in table["rows"] if r["emitter"] == emitter
                and (declaration is None or r["declaration"] == declaration))


class CleanEstateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        scope = unittest.TestCase()
        scope.addCleanup = cls.addClassCleanup
        cls.table = build_table(scope)

    def test_clean_estate_has_no_mismatch_and_checks_every_row_against_an_abi(self):
        s = self.table["summary"]
        self.assertEqual((s["emitters"], s["rows"], s["mismatch_rows"], s["abi_checked_rows"], s["unreviewed"]),
                         (3, 3, 0, 3, 0))

    def test_reach_is_contract_level_not_build_level(self):
        # The factory's input carries the market sources, as V1's does, but
        # the factory never calls a market emitter.
        self.assertEqual(row(self.table, "emit_Moved")["reached_by"], ["Market"])
        self.assertEqual(row(self.table, "emit_Changed")["reached_by"],
                         ["Arch", "Controller", "Factory", "Market"])

    def test_builds_carry_registry_pins_and_instance_counts(self):
        builds = {d["role"]: d for d in self.table["source"]["deployments"]}
        self.assertEqual((builds["market"]["instances"], builds["market"]["address"]), (2, A["market"]))
        self.assertEqual(sorted(r for r, d in builds.items() if d["registry_build_input"]), sorted(PINNED_ROLES))
        self.assertTrue(all(d["source_commit"] == PIN and d["compiler"] == COMPILER for d in builds.values()))

    def test_disagreeing_same_named_declarations_are_listed_with_what_emits_them(self):
        [group] = self.table["declaration_disagreements"]
        variants = {v["declaration"]: v for v in group["variants"]}
        self.assertEqual(group["name"], "Created")
        self.assertEqual((variants["Factory.Created"]["solidity_emit_sites"], variants["Factory.Created"]["in_abi_of"]),
                         (["src/Factory.sol:3"], ["Factory"]))
        self.assertEqual((variants["IFactory.Created"]["solidity_emit_sites"], variants["IFactory.Created"]["in_abi_of"]),
                         ([], []))

    def test_an_emit_site_is_attributed_only_through_inheritance(self):
        without = {d["declaration"]: d["solidity_emit_sites"] for d in self.table["declarations_without_emitter"]}
        self.assertEqual(without["IFactory.Created"], [])
        self.assertEqual(without["Sentinel.Flagged"], ["src/Sentinel.sol:4"])
        self.assertEqual(self.table["summary"]["non_emitting_declarations"], 1)

    def test_every_read_file_is_bound_to_every_build(self):
        files = {f["path"]: f["in_builds"] for f in self.table["source"]["files"]}
        self.assertEqual(files[EMITTERS]["Market"], "equal")
        self.assertEqual(files[EMITTERS]["Sentinel"], "absent")
        self.assertEqual(len(files), len(SOURCES))

    def test_markdown_is_rendered_from_the_json(self):
        estate = Estate(self)
        estate.build()
        with open(estate.markdown, encoding="utf-8") as fh:
            self.assertEqual(fh.read(), v1.render_markdown(estate.load()))


class RejectionTests(unittest.TestCase):
    """The four rejection cases #1962 names, and their neighbours."""

    def test_wrong_topic_is_a_preserved_mismatch_row(self):
        wrong = CLEAN_EMITTERS.replace(topic("Moved(address,uint256,uint256)"), topic("Moved(address,uint256)"))
        git = sources(**{EMITTERS: wrong})
        table = build_table(self, git=git, recs=records(git))
        self.assertEqual(row(table, "emit_Moved")["classes"], ["abi:Market:topic0", "topic0"])
        self.assertEqual([m["emitter"] for m in table["mismatches"]], ["emit_Moved"])

    def test_wrong_arity_is_a_preserved_mismatch_row(self):
        wrong = CLEAN_EMITTERS.replace("log3(0, 0x20,", "log2(0, 0x20,").replace(", from, to)", ", from)")
        git = sources(**{EMITTERS: wrong})
        table = build_table(self, git=git, recs=records(git))
        self.assertIn("log-arity", row(table, "emit_Sent")["classes"])
        self.assertIn("abi:Market:log-arity", row(table, "emit_Sent")["classes"])

    def test_changed_source_is_refused_before_regeneration(self):
        estate = Estate(self)
        estate.build()
        changed = sources(**{"src/interfaces/IEvents.sol": SOURCES["src/interfaces/IEvents.sol"] + "\n"})
        code, err = estate.check({PIN: SOURCES, OTHER: changed}, None, "--ref", OTHER)
        self.assertEqual(code, 1)
        self.assertTrue(err.startswith(f"source-drift: src/interfaces/IEvents.sol at {OTHER}: sha256"), err)
        self.assertNotIn("table-difference", err)

    def test_omitted_row_is_a_table_difference(self):
        estate = Estate(self)
        estate.build()
        table = estate.load()
        table["rows"].pop()
        with open(estate.table, "wb") as fh:
            fh.write(core.serialize(table))
        code, err = estate.check()
        self.assertEqual((code, err.startswith("table-difference:")), (1, True), err)

    def test_added_file_at_the_ref_is_source_drift(self):
        estate = Estate(self)
        estate.build()
        code, err = estate.check({PIN: sources(**{"src/New.sol": "contract New {}\n"})})
        self.assertEqual((code, "source-drift: src/New.sol is present at" in err), (1, True))

    def test_a_changed_sourcify_abi_is_source_drift(self):
        estate = Estate(self)
        estate.build()
        drifted = records(abi_changes={"lens": [CHANGED]})
        code, err = estate.check(None, drifted)
        self.assertEqual(code, 1)
        self.assertIn(f"source-drift: build Lens at {A['lens']}: abi_sha256", err)

    def test_a_sourcify_input_the_registry_does_not_pin_is_refused(self):
        recs = records()
        estate = Estate(self, recs=recs, reg=registry(recs, pins={"factory": "0" * 64}))
        code, err = estate.build()
        self.assertEqual(code, 1)
        self.assertTrue(err.startswith("source-drift: Sourcify input for Factory"), err)
        self.assertFalse(os.path.exists(estate.table))

    def test_a_registry_emitter_path_the_checker_does_not_scan_is_refused(self):
        recs = records()
        reg = registry(recs, emitter_paths=v1.EMITTER_FILES + ("src/libraries/OtherEvents.sol",))
        code, err = Estate(self, recs=recs, reg=reg).build()
        self.assertEqual((code, err.startswith("registry-difference:")), (1, True), err)

    def test_markdown_difference_is_named(self):
        estate = Estate(self)
        estate.build()
        with open(estate.markdown, "a", encoding="utf-8") as fh:
            fh.write("edited\n")
        code, err = estate.check(None, None, "--markdown", estate.markdown)
        self.assertEqual((code, err.startswith("markdown-difference:")), (1, True))

    def test_https_check_reads_the_table_paths_and_refuses_drift(self):
        estate = Estate(self)
        estate.build()
        ok = estate.run(["check", "--from-https", "--table", estate.table], FakeHttps({PIN: SOURCES}))
        changed = sources(**{"src/Lens.sol": "contract Lens { }\n"})
        bad = estate.run(["check", "--from-https", "--table", estate.table], FakeHttps({PIN: changed}))
        self.assertEqual((ok[0], bad[0], bad[1].startswith("source-drift: src/Lens.sol")), (0, 1, True))


class BindingAndScopeTests(unittest.TestCase):
    def test_comment_only_difference_is_told_apart_from_a_code_difference(self):
        recs = records(build_changes={
            "sanctions-sentinel": {"src/Sentinel.sol": SOURCES["src/Sentinel.sol"].replace("MIT", "Apache-2.0")},
            "lens": {EMITTERS: "// SPDX-License-Identifier: Apache-2.0\n" + CLEAN_EMITTERS,
                     "src/Lens.sol": "contract Lens { uint256 x; }\n"},
        })
        table = build_table(self, recs=recs)
        files = {f["path"]: f["in_builds"] for f in table["source"]["files"]}
        self.assertEqual((files["src/Sentinel.sol"]["Sentinel"], files[EMITTERS]["Lens"], files["src/Lens.sol"]["Lens"]),
                         ("comments-only", "comments-only", "differs"))
        self.assertEqual(table["summary"]["binding_differs"], ["src/Lens.sol"])

    def test_log_site_outside_the_emitter_paths_is_unreviewed(self):
        git = sources(**{"src/Arch.sol": "contract Arch is Base {\n  function g() internal { assembly { log0(0, 0) } }\n}\n"})
        table = build_table(self, git=git, recs=records(git))
        self.assertIn({"kind": "log-site", "name": "log0", "at": "src/Arch.sol:2",
                       "reason": "log site outside the registry's emitter paths"}, table["unreviewed"])

    def test_emitter_function_outside_the_emitter_paths_is_unreviewed(self):
        git = sources(**{"src/Lens.sol": "function emit_Hidden(uint256 v) {}\ncontract Lens {}\n"})
        table = build_table(self, git=git, recs=records(git))
        self.assertIn("emit_Hidden", [u["name"] for u in table["unreviewed"] if u["kind"] == "emitter"])

    def test_a_library_call_site_is_named_not_attributed(self):
        helper = "library Helper {\n  function h(address a) internal { emit_Changed(a, a); }\n}\n"
        git = sources(**{"src/Helper.sol": helper})
        recs = records(git, build_changes={"registry": {"src/Helper.sol": helper}})
        table = build_table(self, git=git, recs=recs)
        changed = row(table, "emit_Changed")
        self.assertIn("src/Helper.sol:2 in Arch's input", changed["notes"][-1])
        self.assertIn(("reach", "emit_Changed"), [(u["kind"], u["name"]) for u in table["unreviewed"]])

    def test_an_emit_site_that_resolves_to_nothing_is_unreviewed(self):
        git = sources(**{"src/Lens.sol": "contract Lens {\n  function g() external { emit Missing(1); }\n}\n"})
        table = build_table(self, git=git, recs=records(git))
        self.assertIn({"kind": "emit-site", "name": "Missing", "at": "src/Lens.sol:2",
                       "reason": "resolves to 0 declarations under src/"}, table["unreviewed"])

    def test_an_unresolved_base_in_a_build_is_unreviewed(self):
        recs = records(build_changes={"controller": {"src/Controller.sol": "contract Controller is Base, Gone {}\n"}})
        table = build_table(self, recs=recs)
        self.assertIn({"kind": "reach", "name": "Controller", "at": "build Controller",
                       "reason": "inheritance names Gone do not resolve to one definition"}, table["unreviewed"])


class _Response(io.BytesIO):
    def __init__(self, data, url):
        super().__init__(data)
        self.url = url

    def geturl(self):
        return self.url


class _Opener:
    def __init__(self, data, url=None):
        self.data, self.url, self.opened = data, url, []

    def open(self, url, timeout):
        self.opened.append(url)
        return _Response(self.data, self.url or url)


class ReaderTests(unittest.TestCase):
    RECORD = json.dumps({"address": A["market"], "chainId": "1"}).encode()

    def test_sourcify_url_is_the_fixed_host_and_the_named_address(self):
        opener = _Opener(self.RECORD)
        v1.SourcifyReader(opener).record(A["market"])
        self.assertEqual(opener.opened, [f"https://sourcify.dev/server/v2/contract/1/{A['market']}"
                                         "?fields=stdJsonInput,stdJsonOutput,compilation"])

    def test_a_record_served_off_host_is_refused(self):
        opener = _Opener(self.RECORD, url="https://example.org/x")
        with self.assertRaises(core.Refusal) as caught:
            v1.SourcifyReader(opener).record(A["market"])
        self.assertIn("served from example.org", str(caught.exception))

    def test_an_unsafe_address_is_refused_before_any_read(self):
        opener = _Opener(self.RECORD)
        for address in ("0xABC", "../etc/passwd", "0x" + "A" * 40):
            with self.subTest(address=address), self.assertRaises(core.Refusal):
                v1.SourcifyReader(opener).record(address)
        self.assertEqual(opener.opened, [])

    def test_a_record_over_the_cap_is_refused(self):
        opener = _Opener(b" " * (v1.MAX_RECORD_BYTES + 1))
        with self.assertRaises(core.Refusal) as caught:
            v1.SourcifyReader(opener).record(A["market"])
        self.assertIn("cap", str(caught.exception))

    def test_directory_reader_reads_address_named_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, A["market"] + ".json"), "wb") as fh:
                fh.write(self.RECORD)
            self.assertEqual(v1.DirectorySourcifyReader(tmp).record(A["market"])["chainId"], "1")

    def test_a_record_for_another_contract_is_refused(self):
        spec = {"role": "market", "address": A["market"], "instances": 1, "registry_name": "m", "source_commit": PIN}
        record = records()[A["controller"]]
        with self.assertRaises(core.Refusal):
            v1.parse_record(spec, record, {"pinned_inputs": {}})

    def test_https_source_url_names_wildcat_protocol_at_the_commit(self):
        self.assertEqual(v1.HttpsReader.url(PIN, EMITTERS),
                         f"https://raw.githubusercontent.com/wildcat-finance/wildcat-protocol/{PIN}/{EMITTERS}")


FAKE_SOLC = """#!{python}
import json, sys
ABIS = json.loads({abis!r})
VERSION = {version!r}
if sys.argv[1:] == ["--version"]:
    print("solc, the solidity compiler commandline interface")
    print("Version: " + VERSION + ".Linux.g++")
    sys.exit(0)
request = json.load(sys.stdin)
contracts = {{}}
for path in request["sources"]:
    for name, abi in ABIS.get(path, {{}}).items():
        contracts.setdefault(path, {{}})[name] = {{"abi": abi}}
json.dump({{"contracts": contracts}}, sys.stdout)
"""


class CrosscheckTests(unittest.TestCase):
    def solc(self, estate, version=COMPILER, market_abi=None):
        abis = {path: {name: abi} for path, name, _files, abi in BUILDS.values()}
        if market_abi is not None:
            abis["src/market/Market.sol"]["Market"] = market_abi
        path = os.path.join(estate.root, "solc")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(FAKE_SOLC.format(python=sys.executable, abis=json.dumps(abis), version=version))
        os.chmod(path, os.stat(path).st_mode | stat.S_IXUSR)
        return path

    def run_crosscheck(self, estate, solc):
        return estate.run(["crosscheck", "--solc", solc], None)

    def test_agreeing_abis_pass_and_uncovered_builds_are_named(self):
        estate = Estate(self)
        code, err = self.run_crosscheck(estate, self.solc(estate))
        self.assertEqual(code, 0, err)
        self.assertIn("Market ABI from the Factory input", err)
        self.assertIn("Lens is compiled by no registry-pinned input; not cross-checked", err)

    def test_a_differing_abi_fails(self):
        estate = Estate(self)
        code, err = self.run_crosscheck(estate, self.solc(estate, market_abi=[MOVED]))
        self.assertEqual(code, 1)
        self.assertIn("abi-crosscheck: Market ABI from the Factory input", err.splitlines()[-1])

    def test_another_compiler_version_is_refused(self):
        estate = Estate(self)
        code, err = self.run_crosscheck(estate, self.solc(estate, version="0.8.25+commit.b61c2a91"))
        self.assertEqual((code, "not the registry's 0.8.22+commit.4fc1097e" in err), (1, True))


class CommittedTableTests(unittest.TestCase):
    """Offline checks against the committed docs/kickoff/1962 table."""

    TABLE_PATH = ROOT / v1.TABLE_PATH
    MARKDOWN_PATH = ROOT / v1.MARKDOWN_PATH

    @classmethod
    def setUpClass(cls):
        with open(cls.TABLE_PATH, encoding="utf-8") as fh:
            cls.table = json.load(fh)
        cls.registry = v1.load_registry(str(ROOT))

    def test_committed_markdown_is_byte_equal_to_its_rendering(self):
        with open(self.MARKDOWN_PATH, encoding="utf-8") as fh:
            self.assertEqual(fh.read(), v1.render_markdown(self.table))

    def test_the_table_still_describes_the_registry_row(self):
        source = self.table["source"]
        self.assertEqual(source["registry"], {k: self.registry[k] for k in
                                              ("path", "row", "commit", "compiler", "emitter_paths")})
        self.assertEqual(source["commit"], self.registry["commit"])
        committed = [(d["role"], d["address"], d["instances"], d["source_commit"]) for d in source["deployments"]]
        expected = [(b["role"], b["address"], b["instances"], b["source_commit"]) for b in self.registry["builds"]]
        self.assertEqual(committed, expected)

    def test_every_pinned_build_input_equals_the_registry_pin(self):
        pins = self.registry["pinned_inputs"]
        pinned = {d["contract"]: d["standard_input_sha256"] for d in self.table["source"]["deployments"]
                  if d["registry_build_input"]}
        self.assertEqual(pinned, {name: pins[name] for name in pinned})
        self.assertEqual(sorted(pinned), sorted(pins))

    def test_every_emitter_appears_in_a_row_or_the_unreviewed_list(self):
        named = {r["emitter"] for r in self.table["rows"]}
        named |= {u["name"] for u in self.table["unreviewed"] if u["kind"] == "emitter"}
        self.assertEqual(len(named), self.table["summary"]["emitters"])

    def test_expected_figures_at_the_pin(self):
        s = self.table["summary"]
        self.assertEqual(
            (s["emitters"], s["rows"], s["abi_checked_rows"], s["mismatch_rows"], s["unreviewed"],
             s["unreached_rows"], s["declaration_disagreements"], s["non_emitting_declarations"], s["binding_differs"]),
            (26, 37, 37, 0, 0, 0, 4, 10, []))

    def test_no_wildcat_protocol_source_file_is_tracked(self):
        digests = {f["sha256"] for f in self.table["source"]["files"]}
        try:
            listed = subprocess.run(["git", "ls-files", "-z", "--", "*.sol"], cwd=ROOT, capture_output=True,
                                    check=True).stdout.decode("utf-8").split("\0")
            tracked = [ROOT / p for p in listed if p]
        except (OSError, subprocess.CalledProcessError):
            tracked = [p for p in ROOT.rglob("*.sol") if ".git" not in p.parts]
        found = [str(p) for p in tracked
                 if p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest() in digests]
        self.assertEqual(found, [])


if __name__ == "__main__":
    unittest.main()
