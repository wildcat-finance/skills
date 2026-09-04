# runbook: pin RPC-boundary failures into Lazarus fixtures

This runbook derives from `.hexaemeron/study.md` at the receipted digest
`7a51a98e3948638a804106dfb620bb2cae6b82e87551c067e62e9d31a3658067`. The topic
is one procedure section in the Elenchus skill file with the one test module
that is its worked example, plus the ledger row, the version surfaces and the
committed copies that go with them, so one auditable step both scaffolds and
demonstrates it, as the Phylax P008 and Berean question-span deliveries did. A
split was considered and refused: the prose tests in the new module are red
until the section lands, so a step that shipped the module alone would hand
the next step a red tree, and a step that shipped the section without its
`elenchus-v1.3.0` row would leave a skill decision unrecorded between two pull
requests. The repository already supplies the layout, licences, Python 3.9
and 3.12 compatibility, `uv` and CI; issue #387 does not authorise touching
those, and this step verifies them rather than replacing them.

Two environment facts changed between the study and this runbook, and the
step is written against the current state. First, the study observed the
Hexaemeron suite at `1167/1168` under the Node 26 wrapper because the local
keyring lacked the public key that signed the #429 recovery commit; Fiat
imported Shoggoth's public GPG key `636EC19DE45DF10F3CE6206F57742DA1ABED6F46`
from GitHub on 2026-08-25, `git verify-commit 0fb3bcfb` now exits 0 with a
good signature, and the suite reports `1168/1168 tests passed` in 385 seconds
under `npx --yes --package=node@26.6.0 --call` with the Lazarus dependencies
supplied by `uv`. Second, the host `node` is v22.22.3, so every Hexaemeron
suite run in this step, including the one Elenchus makes on the parent
overlay, runs inside that Node 26 wrapper; without it one checker fixture
fails on the Node version and would be read as an assertion failure that has
nothing to do with this change.

## Step 1: add the RPC-boundary fixture procedure to Elenchus, guard it with the Aave v4 replay example, record elenchus-v1.3.0 and demonstrate

**Goal.** Give the Elenchus skill file one section that says how a failure at
the RPC boundary is pinned into a Lazarus fixture and reproduced offline
behind `lazarus replay`, ship the worked example as one standard-library test
module that drives the shipped Aave v4 fixture over loopback and skips by
name where Lazarus's dependencies are absent, and record the generation, the
package version and the committed study and runbook that go with the rule.

**Entry.** The clean run branch
`fiat/387-pin-rpc-boundary-failures-into-lazarus-fixtu` at
`ab611eb96a6a9bddecb57bff2416641296e0a21e`, with the Fiat study and this
runbook receipted; the root suite at 396 OK on Python 3.9.6 and 3.12.13;
`tests.test_evolution_contract` at 9 OK; `scripts/promise_machine.py check`
and `coverage --check` clean; `audit_synopsis.py --check .` exit 0 with
fourteen pairs at `committed=match`; the Lazarus suite at 414 OK under `uv run
--python 3.12.13 --with-requirements plugins/lazarus/requirements.txt`; the
Aave v4 demo and `verify` exit 0 under the same `uv` command at fixture
digest `d93cd09fcb2c6bd689a223398ebd4ae4dc480ec7d8fd8e64283b88341d0a7e49`;
the Hexaemeron suite at `1168/1168 tests passed` under
`npx --yes --package=node@26.6.0 --call` with the `uv` command above, the
keyring holding public key `636EC19DE45DF10F3CE6206F57742DA1ABED6F46`; and
`plugins/hexaemeron/skills/elenchus/SKILL.md` carrying no section on fixtures,
so `grep -c 'Pin an RPC-boundary failure' plugins/hexaemeron/skills/elenchus/SKILL.md`
prints 0. No dependency, toolchain pin or CI change enters this step.

**Exit.** `plugins/hexaemeron/skills/elenchus/SKILL.md` carries the section
`## Pin an RPC-boundary failure into a fixture` after `### 6. Verify` and
before `## Three rounds, then stop`, with the seven numbered steps the study's
section 4 gives against `lazarus-v1.2.0` behaviour, one fenced `bash` block
holding the `capture`, `verify` and `replay --port 0` commands with the
endpoint URL spelled `"$LAZARUS_RPC_URL"`, one fenced `json` block holding a
two-request plan fragment with one `required: true` and one `required: false`
request, the `required: false` rule for pinning a provider's error, the
`-32070` miss read as a failed test, the seventh step on what a fixture cannot
pin, and a closing paragraph naming
`plugins/hexaemeron/tests/test_elenchus_rpc_boundary_fixture.py` and the `uv`
command; the Reproduce step's Environment bullet gains one sentence pointing at
the section; "Before the fix is receipted" gains the item "A failure that
crossed an RPC boundary was reproduced from a verified fixture behind `lazarus
replay`, and its guard fails closed on a miss."; the frontmatter `name`,
`description`, the `## Where this sits` paragraph, the six triage steps, the
mechanical subset and the Promise Machine contract section are unchanged and
`metadata.version` reads `1.3.0`. `plugins/hexaemeron/tests/test_elenchus_rpc_boundary_fixture.py`
exists with the three classes the study names: `ProcedureTextTests`,
`LazarusDependencyGuardTests` and `ReplayGuardExampleTests`, standard library
only, loading on Python 3.9.6 and 3.12.13. `EVOLUTION.md` carries the
`elenchus-v1.3.0` generation row and current version with the frontier
revision, digest `08e77bae576b3351d6f38e60ce9da88327014bcaa7459e319b8e51d79caeda8b`
as the ledger spells it, status `mature` and `Next Fiat job: None -- mature`
byte-identical to `elenchus-v1.2.0`, the row's evidence linking
`../../tests/test_elenchus_rpc_boundary_fixture.py` and
`../../../../docs/elenchus-rpc-boundary-fixtures/study.md`. The package reads
`1.6.2` on `plugins/hexaemeron/.claude-plugin/plugin.json`,
`plugins/hexaemeron/.codex-plugin/plugin.json`, `.claude-plugin/marketplace.json`
and `.agents/plugins/marketplace.json`, with the pin in
`tests/test_version_propagation.py` moved. The study and this runbook are
committed byte-for-byte under `docs/elenchus-rpc-boundary-fixtures/`. `git
diff --stat ab611eb96a6a9bddecb57bff2416641296e0a21e -- plugins/lazarus` prints
nothing. And every command in this demo path exits zero from the repository
root, the fifth printing `1168` plus the new module's count with `skipped=0`
in its report and the first printing the replay class as skipped with the
reason naming the five import names and the `uv` command:

```bash
python3 -m unittest plugins.hexaemeron.tests.test_elenchus_rpc_boundary_fixture -v
uv run --python 3.12.13 --with-requirements plugins/lazarus/requirements.txt python -m unittest plugins.hexaemeron.tests.test_elenchus_rpc_boundary_fixture -v
uv run --python 3.12.13 --with-requirements plugins/lazarus/requirements.txt python -m unittest discover -s plugins/lazarus/tests -t plugins/lazarus
uv run --python 3.12.13 --with-requirements plugins/lazarus/requirements.txt python plugins/lazarus/examples/aave-v4-spoke-v0/demo.py
npx --yes --package=node@26.6.0 --call 'uv run --python 3.12.13 --with-requirements plugins/lazarus/requirements.txt python plugins/hexaemeron/tests/run_tests.py'
/usr/bin/python3 -B -m unittest discover -s tests
python3 -m unittest discover -s tests
python3 -m unittest tests.test_evolution_contract
python3 scripts/promise_machine.py check
python3 scripts/promise_machine.py coverage --check
python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/elenchus-rpc-boundary-fixtures/study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/elenchus-rpc-boundary-fixtures/runbook.md
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/elenchus-rpc-boundary-fixtures/study.md docs/elenchus-rpc-boundary-fixtures/runbook.md plugins/hexaemeron/skills/elenchus/SKILL.md plugins/hexaemeron/skills/elenchus/EVOLUTION.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py plugins/hexaemeron/skills/elenchus/SKILL.md
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents plugins docs
python3 plugins/horos/skills/horos/scripts/horos.py check .
git diff --check
```

**Files.** Change `plugins/hexaemeron/skills/elenchus/SKILL.md`,
`plugins/hexaemeron/skills/elenchus/EVOLUTION.md`,
`plugins/hexaemeron/.claude-plugin/plugin.json`,
`plugins/hexaemeron/.codex-plugin/plugin.json`, `.claude-plugin/marketplace.json`,
`.agents/plugins/marketplace.json` and `tests/test_version_propagation.py`;
create `plugins/hexaemeron/tests/test_elenchus_rpc_boundary_fixture.py` and
exact committed copies at `docs/elenchus-rpc-boundary-fixtures/study.md` and
`docs/elenchus-rpc-boundary-fixtures/runbook.md`; Warden appends
`fiat-audit-round/v2` records to
`audit/rounds/fiat-387-pin-rpc-boundary-failures-into-lazarus-fixtu.md` and
regenerates its `.synopsis.md` sibling in the same signed commit; regenerate
`.horos/boundary.json` only if its scan changes that tracked file. No byte
under `plugins/lazarus/` changes, `tests/promise_machine_coverage.json` is
untouched because no selector moves, and no other path is in scope without a
study amendment.

**Tests.** First write `ProcedureTextTests` and observe every assertion fail
against the unchanged skill file, recording the count: the section heading,
the `capture`, `verify` and `replay` commands, the `--port 0` spelling, the
`-32070` code, the `required: false` rule, the `LAZARUS_RPC_URL` convention,
the Environment sentence and the checklist item. Write
`LazarusDependencyGuardTests` against the probe helper with a fake finder so
the skip reason is proved to name every missing import name and the exact `uv
run` command. Write `ReplayGuardExampleTests` as the study's section 4
specifies: `setUpClass` probes `eth_hash`, `Crypto`, `jsonschema`, `rlp` and
`trie` with `importlib.util.find_spec` and raises `unittest.SkipTest` with the
fixed reason when any is missing; otherwise it starts `[sys.executable,
"plugins/lazarus/scripts/lazarus.py", "replay",
"plugins/lazarus/examples/aave-v4-spoke-v0", "--port", "0"]` with the repository
root as `cwd`, closed stdin, piped stdout and stderr, reads the first stdout
line under a thirty-second timer that kills the process, and parses the port
from the prefix `lazarus replay listening on http://127.0.0.1:`; under a
`socket.socket.connect` patch that refuses any non-loopback destination its
tests assert the slot `0x0` result byte for byte against the matching
`rpc.jsonl` record and the literal sixty-four digit word ending in `01`, the
`-32070` miss with `data.method`, `data.params` and a `capture_plan_fragment`
carrying the request's own method and parameters with `evidence:
recorded-rpc` and `required: true` for slot `0x1` and for the spelling `0x00`,
`-32601` for `eth_sendRawTransaction`, an argv with no `://` and no
`--rpc-url`, and loopback for every observed connection; `tearDownClass`
terminates, waits ten seconds, kills on timeout and closes the pipes. Observe
the class green under `uv` and skipped by name under plain `python3`. Observe
by hand, once each, and record in the audit round rather than commit: a fixture
path that does not exist ends the subprocess before the listening line and
fails the class with the captured stderr; a miss answers `-32070`. Every guard
must fail when the section is removed. The 1168 existing Hexaemeron tests plus
every new named case pass under the Node 26 wrapper with `uv`; the root suite
stays at 396 on both interpreters; the Lazarus suite stays at 414; the command
output records the final counts. Elenchus runner contract for this step, test
command
`uv run --python 3.12.13 --with-requirements plugins/lazarus/requirements.txt python plugins/hexaemeron/tests/run_tests.py {report}`,
report format `unittest-json-v1`, report file
`.elenchus/elenchus-rpc-boundary-fixtures-step-1.json`; Warden runs
`elenchus.py` inside `npx --yes --package=node@26.6.0 --call` so the pinned
Node fixture passes in the parent overlay and the only parent failures are the
prose assertions this step guards.

**Disciplines.** phylax: this step starts one subprocess from a fixed argument
list beginning with `sys.executable`, binds only loopback on an ephemeral port,
tears the server down with a bound, carries no URL or credential in the module
or its argv, and documents a capture that reads the endpoint URL from one
environment variable; the tree lint must exit 0, and where it reports the
fixed-argv subprocess the accepted form is a reason-bearing `# phylax: allow`
pragma naming the fixed argv, as `plugins/berean/tests/test_scaffold.py`
carries. ephoros: none, because nothing here runs unattended; the three
signals the study's section 8 names already exist in Lazarus and the test's
own report, and the example asserts two of them. metron: none, because the
issue makes no performance claim and the class adds under three seconds to a
suite that runs about 385 seconds here. elenchus: observe the prose assertions
red before the section lands, the replay class green under `uv` and skipped by
name under `python3`, and the two hand-observed failure modes; a round finding
follows the same order under the runner contract above. hypomnema: record the
decision that Elenchus names Lazarus as the reproduction path, the
required-or-optional rule, the fail-closed miss, the offline-half boundary and
the rejected options B to E in the `elenchus-v1.3.0` row pointing at the
committed study; `SKILL.md` owns the procedure text; the commit message carries
the package bump and its reason; a comment beside the dependency probe says
why the five import names are a constant rather than a read of
`requirements.txt`; no ADR.

Implementation order inside the step is fixed: commit the exact study and
runbook copies; write the red prose tests and preserve their failing output;
add the section, the Environment sentence and the checklist item and turn them
green; write the dependency-guard tests and the replay class and run the
module under both interpreters; move the frontmatter version, add the ledger
row and the five version surfaces; run the full demo path; then enter the Fiat
audit and prose gates. Any need for a change under `plugins/lazarus/`, a
committed fixture, a dependency, a promise clause, a different package version
or a CI workflow stops the step for a study amendment.
