# Study: Elenchus emits the fixed-and-guarded result as a structured record

Topic: `elenchus emits the fixed-and-guarded result as a structured record`.
Task issue: [skills#1275](https://github.com/wildcat-finance/skills/issues/1275).
Starting ref: `0fefcc986107ed66ff43c6572b7aa1c7351f12f4` on `main`.

## Assumptions

Proceeding on these unless corrected.

1. The interpreter is the exact version in `.python-version`, which reads
   `3.14.6` at the starting ref, and the emitter uses the standard library
   only. Every other script under `plugins/hexaemeron/skills/*/scripts/` does.
2. The axis is generation, not evolution. The issue is labelled `wish`, so
   `elenchus-v1.3.0` becomes `elenchus-v1.4.0` and the frontier revision
   `observed-failure-root-cause`, its digest
   `08e77bae576b3351d6f38e60ce9da88327014bcaa7459e319b8e51d79caeda8b`, the
   `mature` status and `Next Fiat job: None -- mature` are all retained byte
   for byte. Rows `elenchus-v1.2.0` and `elenchus-v1.3.0` did exactly this.
3. `Fiat-Required: 1` on the issue is authoritative, so the run owes the
   generation row and the package re-pin that goes with it: Hexaemeron moves
   from `1.6.24` on both plugin manifests and both marketplace listings.
4. No Solidity is in scope, so the Pashov suite and `fizz` are waived for
   every step.
5. [skills#1222](https://github.com/wildcat-finance/skills/issues/1222) has
   landed nothing. It is `OPEN`, `Fiat-Required: 0`, and no commit, branch or
   file in this checkout references it. There is therefore no agreed record
   shape to adopt, and this study proposes the one its own producer can fill.
6. The emitted record is written by whoever closed the failure, from evidence
   already in hand. Nothing in this delivery reads a corpus, writes to one, or
   runs after the fix is receipted.

## 1. Problem statement

Elenchus reproduces a failure, localises it to a mechanism, repairs the
mechanism and leaves a guard, then hands that result back as prose. The
`elenchus-fixed-and-guarded` Promise already names every part of the claim, and
the skill already holds every part in order to make it. None of it survives the
run in a form anything can read.

**What is built.** One emitter and one schema. The emitter takes the fields the
operator holds and the guard evidence `elenchus.py` already produces, and
writes one closed `elenchus-fixed-and-guarded/v1` object beside the prose
hand-back. It refuses a record it cannot fill.

**For whom.** Whoever closes a failure under Elenchus. That is three callers,
not one: Mason when implementation breaks, Warden inside a Fiat audit round,
and a person at a terminal with a red test. The prose record serves all three
today and the structured record has to as well.

**What a working prototype means here.** A repaired failure in a scratch
repository produces a record that a checker accepts; the same record with any
one evidence field removed, or with a verdict other than `guarded`, is refused
with the rule and the field named.

**The nine fields, and where each comes from.** The set is derived from the
Promise's own two clauses and from nothing else.

The Evidence clause reads: "The reproduction command and output, causal
account, minimal case where useful, fix diff, detached-parent guard report,
fixed-tree report and both relevant suite results." That is seven.

The Boundary clause reads: "The result covers the reproduced failure and named
guard; it does not prove the surrounding system defect-free or turn an
inconclusive, zero-test or infrastructure-failed comparison into a guard." That
clause turns on which guard was named, and on which of the four states the
comparison reached. Those are the other two.

| Field | Carries | Held by |
| --- | --- | --- |
| `reproduction` | the exact command, and the digest and byte count of its observed output | the operator |
| `causal_mechanism` | the account as a mechanism, and the `path:line` where it starts | the operator |
| `minimal_case` | the reduced case, or `null` where none was useful | the operator |
| `repair` | the commit that repaired the mechanism, and the files it touched | the operator |
| `guard` | the regression test's file, and the test name inside it | `elenchus.py` `tests`, and the operator |
| `unfixed_parent` | the parent commit, and its normalised report counts | `elenchus.py`, and one `git rev-parse` |
| `fixed_tree` | the fixed commit, and its normalised report counts | the operator's rerun |
| `suites` | each suite command and its exit code | the operator |
| `verdict` | one of the four states, and the runner contract that produced it | `elenchus.py` |

`elenchus.py --format json` already prints `ref`, `tests`, `status`, `detail`
and, when a report parsed, `report` with `complete`, `executed`,
`assertion_failures`, `errors` and `skipped`. `unfixed_parent` and `verdict`
come straight out of that, and `guard` takes its file from `tests`. The rest is
what the operator had to establish before the Promise could be claimed at all,
and `fixed_tree` is the rerun the skill's own Verify step already demands.

One field needs a sentence. `elenchus.py` resolves the parent in `parent_of`
and runs the comparison against it, but its printed result carries `ref` and
not the parent, so the emitter re-derives it with `git rev-parse <ref>^`, the
same call `elenchus.py` makes. That keeps the constraint that every field is
one Elenchus already holds, and it adds no evidence-gathering step to the
skill's procedure. Printing the parent from `elenchus.py` instead would change
the file this delivery is committed to leaving alone.

**Demo path.** The last step runs the whole path end to end against a scratch
repository the test harness builds, in the shape
`plugins/hexaemeron/tests/test_elenchus_checker.py` already builds one:

```bash
python3 plugins/hexaemeron/skills/elenchus/scripts/fixed_and_guarded.py \
  --result .elenchus/result.json \
  --draft .elenchus/draft.json \
  --out .elenchus/fixed-and-guarded.json
python3 plugins/hexaemeron/skills/elenchus/scripts/fixed_and_guarded.py \
  --check .elenchus/fixed-and-guarded.json
```

**Success criteria.** Each names a command.

1. The emitter writes a record from a `guarded` result and a complete draft:
   `python3 -m unittest plugins.hexaemeron.tests.test_elenchus_fixed_and_guarded`
   passes, and the demo path above exits 0 twice.
2. A record missing any one of the nine evidence fields is refused, and so is a
   record whose `verdict.status` is `passed`, `unguarded` or `inconclusive`:
   covered by named cases in the same module.
3. `elenchus.py` is unchanged in behaviour:
   `python3 -m unittest plugins.hexaemeron.tests.test_elenchus_checker` passes
   with no case edited.
4. The ledger row is a generation row:
   `python3 -m unittest plugins.hexaemeron.tests.test_evolution` passes, and
   `git diff` on `EVOLUTION.md` shows the frontier revision, digest, status and
   next job unchanged.
5. Both suites are green:
   `python3 plugins/hexaemeron/tests/run_tests.py` and
   `python3 tests/run_tests.py`.
6. Every shipped document scores no defect:
   `python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py <file>`.

## 2. Prior art

### In this repository

`plugins/hexaemeron/skills/elenchus/scripts/elenchus.py` is the only script the
skill ships. It overlays a fix's changed test files onto the detached parent,
runs a declared command there, reads a fresh runner-owned report in one of
three formats, and classifies the result as `guarded`, `passed`, `unguarded` or
`inconclusive`. `--format json` prints the whole result dict. It is the source
of two of the nine fields and part of a third, and this delivery changes none
of its behaviour.

`plugins/hexaemeron/tests/test_elenchus_checker.py`, 841 lines, is the
convention a new checker follows here: a `Fixture` class that builds a scratch
git repository, one test class per report format, and a `ReportValidation`
class for the refusals. `plugins/hexaemeron/skills/protasis/scripts/design_evidence.py`
is the convention a closed-record checker follows: stable finding codes, one
strict-JSON reader with a byte cap and a duplicate-key refusal, symlink-free
path resolution below a fixed root, and `--format text|json`.

`tests/run_tests.py` writes an `elenchus.unittest.v1` report and was added by
[PR #744](https://github.com/wildcat-finance/skills/pull/744) for exactly this
reason: a runner contract needs a producer before an audit round can read one.
Its refusal set is the closest prior art for the emitter's write boundary. It
refuses a `..` component, an absolute path outside the worktree, an existing
regular file, an existing symlink, a parent component that is a regular file,
and two report paths in one invocation.

`plugins/anamnesis/skills/anamnesis/SKILL.md` models the parts separately:
submissions, adjudicated findings, occurrences, remediation attempts and
verifications. A fixed-and-guarded result is one of each. `reproduction` and
`causal_mechanism` are the finding; the mechanism at its site in this
repository at this commit is the occurrence; `repair` is the remediation
attempt; the guard observed red on the parent and green on the fixed tree is
the verification. The field set below is chosen so each part has a source.
Anamnesis's own rule that `applied` is as far as any status string reaches is
why `verdict` stays the four-state Elenchus value and gains nothing.

Two directions must not be confused. Anamnesis's outbound `analogues` view has
no field a verdict could occupy, so a past `guarded` cannot travel into a
present case. This is inbound and carries the verdict, because the verdict is
what the present run observed.

### The last two merged pull requests that changed the subject

[PR #636](https://github.com/wildcat-finance/skills/pull/636) and
[PR #635](https://github.com/wildcat-finance/skills/pull/635), both merged
2026-08-26, have identical file sets and are the run and step pair for
`elenchus-v1.3.0`. `git log --oneline -12 -- plugins/hexaemeron/skills/elenchus/`
finds nothing later that touches the directory. Their body carries three items
forward. Each is answered here:

1. *The study and runbook count fourteen synopsis pairs where
   `audit_synopsis.py --check .` listed thirteen at that base tree.* Closed by
   time rather than by work. The check at this run's base lists 66 sources and
   every one reads `committed=match`, so the count that was in dispute no
   longer exists in either document.
2. *The loopback guard's `ipaddress.ip_address(address[0])` raises `ValueError`
   rather than the intended `AssertionError` for a non-numeric host.* Stays
   open, and stays out of scope. It lives in
   `plugins/hexaemeron/tests/test_elenchus_rpc_boundary_fixture.py`, which this
   delivery does not touch, and the round that raised it recorded that either
   outcome is a non-pass.
3. *A miss fragment whose params carry a moving block tag is schema-valid yet
   refused by `capture` at plan validation.* Stays open, and stays out of
   scope. It is a Lazarus plan-validation question with no bearing on emission.

### Audit records read

`python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .`
exits 0 at the starting ref, and all 66 reported sources read
`committed=match`. The whole-set currency check therefore passes, so a verified
synopsis is the normal reading view.

In scope are the audit records of the skills this delivery changes or has to
agree with: Elenchus, whose skill directory is under `plugins/hexaemeron/`,
and Anamnesis, whose record model the emitted shape answers to. That is the root
`audit/AUDIT.md`, the plugin record `plugins/hexaemeron/audit/AUDIT.md`, and
three of the 58 per-run records under `audit/rounds/`. The other 55 belong to
deliveries this one neither changes nor reads. Each in-scope source is named
below with the view actually read.

| In-scope source | Read | Evidence for the choice |
| --- | --- | --- |
| `audit/AUDIT.md` | source, at the two `Elenchus structured reports` and seven `Elenchus audit-round verdict` headings, and not at the other 416 of its 425 rounds | the synopsis renders each round as one line with `<br>` joins; the leads carried across these nine name issues by number, and the source is the readable form |
| `plugins/hexaemeron/audit/AUDIT.md` | synopsis `plugins/hexaemeron/audit/AUDIT_SYNOPSIS.md` | `committed=match` at this ref; both rounds are Step 0 plugin rounds on `hexctl.py` and `hook_gate.py`, neither in scope here |
| `audit/rounds/fiat-387-pin-rpc-boundary-failures-into-lazarus-fixtu.md` | synopsis `...synopsis.md` | `committed=match` at this ref; the record is one round with zero findings across 19 register ids, and the synopsis keeps every id, the `Not checked` text, the `null` verdict and the four leads |
| `audit/rounds/fiat-anamnesis-source-bound-curation-and-release-of-a.md` | synopsis | `committed=match`; read for the corpus record model, not for a finding |
| `audit/rounds/fiat-admit-the-anamnesis-corpus-projection-into-a-syn.md` | synopsis | `committed=match`; read for the projection boundary ADR-005 records |

Findings and statuses retained from those sources: the `fiat-387` round is
zero findings, all 19 register ids `reviewed`, `Elenchus verdict: null`, and
four leads not pursued, three of which PR #636 also carried forward and which
are answered above. The fourth is that on a 3.9 interpreter carrying the
Lazarus dependencies the replay subprocess would fail at Lazarus's 3.11 floor
and the class would error rather than skip, which the round recorded as a
fail-closed outcome no interpreter here reaches. The two plugin-level rounds in
`plugins/hexaemeron/audit/AUDIT.md` carry ten findings `F-01` to `F-10`, nine
`fixed` and `F-10` `accepted`, all on `hexctl.py` and `hook_gate.py`; every one
of them predates the audit schema, so `Covered`, `Not checked` and
`Elenchus verdict` read `[missing legacy field: ...]` and stay unknown. The
`Elenchus audit-round verdict` rounds carry no unfixed finding and one standing
lead named repeatedly: `issue 453`'s report-byte binding and production
`guarded` gate.

That lead is the closest thing to a competing claim on this work, and it is
answered by boundary rather than by scope. Issue 453 is `OPEN`. It owns binding
a *Fiat receipt* to the report bytes behind a verdict. This delivery binds
nothing to a receipt: the emitter writes a file, and the record establishes
what the run recorded. The two do not overlap and neither blocks the other.

### In the organisation

[skills#1222](https://github.com/wildcat-finance/skills/issues/1222) asks
Warden for the same emission from an audit round. It is `OPEN` and
`Fiat-Required: 0`, and nothing in this checkout references it, so there is no
landed shape to agree with. Its own field list is the round's identity, each
finding's id, severity, subject and status, the remediation commit, the
verification result, and the leads with their dispositions. Four of the nine
fields here overlap it by meaning: `repair` is its remediation commit,
`verdict` is its verification result, and `unfixed_parent` and `fixed_tree`
are the two trees behind that result. A later producer can carry those four
under the same key names; this study does not oblige it to, because the
producer that has not been written cannot be held to a contract.

[skills#1212](https://github.com/wildcat-finance/skills/issues/1212) moves
closed audit history behind a digest manifest and splits `Evidence:` out of
`Leads not pursued`. It changes the audit record grammar. It has no bearing
here, and that is the point: a producer that reads no prose is not exposed to a
prose grammar changing under it.

[skills#429](https://github.com/wildcat-finance/skills/issues/429) is `CLOSED`,
merged 2026-08-25; it gave the audit record its schema, timestamp and synopsis,
which is why `fiat-audit-round/v2` exists to compare against.

`plugins/hexaemeron/docs/elenchus-audit-round-verdict/study.md` rejected
"Option D: store the complete Elenchus JSON report" inside the Fiat audit
round, because it "duplicates Elenchus's schema, expands state and downstream
formats, and takes the evidence-binding work from issue 453". That rejection
stands and this study does not reopen it. The subject there was the controller
storing the report in receipted state. The subject here is Elenchus writing a
file of its own, which adds nothing to state, nothing to any receipt, and
nothing to a downstream format.

### Outside the organisation

SARIF (OASIS, `sarif-schema-2.1.0`) is the nearest external analogue: a tool
writes its findings as a closed structured object beside whatever it prints for
a person, and consumers read the object. The shape it settled on that matters
here is that a result carries its own rule identity and its own location rather
than a pointer into the human report. This record does the same by carrying the
mechanism's `path:line` and the guard's test name.

The in-toto attestation predicate model, which this repository already
implements under `plugins/ariadne/`, is the other reference: a statement names its subject
by digest and says what it does and does not establish. `reproduction` stores
its output's digest and byte count rather than the bytes for the same reason
Ariadne stores subjects by digest.

## 3. Constraints and non-goals

### Constraints

1. Starting ref `0fefcc986107ed66ff43c6572b7aa1c7351f12f4`, branch
   `fiat/1275-elenchus-emits-the-fixed-and-guarded-result`.
2. Python `3.14.6` from `.python-version`, standard library only, stdlib
   `unittest` for tests.
3. The generation axis of `plugins/hexaemeron/skills/VERSIONING.md`. The row
   `elenchus-v1.4.0` retains the frontier revision, the digest, `mature` and
   `None -- mature` byte for byte, and links its evidence.
4. Hexaemeron re-pins from `1.6.24` on `plugins/hexaemeron/.claude-plugin/plugin.json`,
   `plugins/hexaemeron/.codex-plugin/plugin.json`, `.claude-plugin/marketplace.json`
   and `.agents/plugins/marketplace.json`, so an installed copy is offered the
   changed skill file.
5. `elenchus.py`'s command-line interface, defaults and four state strings do
   not change. `test_elenchus_checker.py` passes with no case edited.
6. No Solidity, so the Pashov suite and `fizz` are waived on every step.
7. Every field in the record is one Elenchus already holds. The delivery adds
   no evidence-gathering step to the skill's procedure.

### Non-goals

1. No resolver. Nothing joins one record to another, and the schema carries no
   field that could point at another record.
2. No corpus admission. What Anamnesis preserves beyond its 41-finding pilot
   seed is its own held `corpus-scope` frontier and is untouched here.
3. No recurrence claim. Two records naming a similar mechanism establish that
   two runs recorded a similar mechanism, and the schema says so in its own
   boundary text.
4. No change to the four-state classification, its adapters or its report
   formats.
5. No controller change. No receipt field, no state key, no `hexctl`
   subcommand, no audit record grammar change.
6. No emission from Warden. That producer is issue 1222's, and writing it here
   would settle a contract for a caller that has not been specified.

### Explicit unknowns

1. Whether issue 1222's producer will adopt these key names is unknown and
   unknowable from here, because that producer does not exist. This study
   states the overlap and leaves the choice to whoever writes it.
2. Whether Anamnesis will admit this record is unknown. Its `corpus-scope` job
   decides admission and has not run.

## 4. Design options

Four candidate constructions were compared. The prose below explains what each
one is and the trade it makes; the selection is made by
`.hexaemeron/design-evidence.json` from checked gates and measured values, not
from this prose.

### Candidate `skill-emitter`

A new script `plugins/hexaemeron/skills/elenchus/scripts/fixed_and_guarded.py`
beside `elenchus.py`, with a matching test module and one new section in
`SKILL.md`. It reads a draft holding the operator-held fields and an
`elenchus.py --format json` result holding the guard evidence, and writes one
closed record. A `--check` mode validates a record on its own.

The trade: two scripts under one skill instead of one, and a second
command-line surface to keep. Against that, the file that Warden invokes on
every audit round does not change at all, and the emitter's write boundary is
reviewed on its own rather than folded into a checker whose job is to spawn
worktrees and subprocesses.

### Candidate `checker-subcommand`

`elenchus.py` gains an emission mode: the flags for the operator-held fields,
and a `--record PATH` output. Nothing new is added to the skill directory.

The trade: one file, one command, no second surface. Against that, it widens
the interface Warden's brief names by exact flag set, it puts a filesystem
write boundary inside the process that already runs an arbitrary operator
command in a detached worktree, and every change to it obliges the 841-line
`test_elenchus_checker.py` to be re-run and re-reviewed.

### Candidate `warden-receipt`

The record is emitted from the Fiat audit round: `hexctl audit-round` takes the
fields and writes the structured record beside the Markdown one, in the same
signed commit.

The trade: the record arrives already joined to a run, a step and a receipt.
Against that, it is issue 1222's producer and issue 1222's file, it changes the
audit record grammar that issue 1212 is already changing, and a fix Mason makes
during implementation or a person makes at a terminal emits nothing at all,
because there is no round. Most of the nine fields have no home in the round's
own grammar and would have to be read back out of its Markdown table.

### Candidate `prose-block`

A fenced `fixed-and-guarded` block in the Elenchus hand-back prose, with a
parser that lifts it into JSON when something asks.

The trade: the smallest text change of the four, and no new command at all.
Against that, the record is produced by parsing prose, which is the defect
issue 1222 names in its own opening line, and a fence terminated early parses
as a complete record with fields absent rather than as a truncated one.

### The record

`.hexaemeron/design-evidence.json` holds four candidates, seven criteria and
the complete 28-cell matrix under schema `protasis-design-evidence/v1`. Five
criteria are selection evidence and are resolved; two are conformance evidence
and are pending against `step:2` and `integration`.

Resolved by `python3 .hexaemeron/reports/resolve.py <criterion>` at the
starting ref, on this host:

| Criterion | `skill-emitter` | `checker-subcommand` | `warden-receipt` | `prose-block` |
| --- | --- | --- | --- | --- |
| `prose-parsed-fields` (= 0) | 0 | 0 | 7 | 9 |
| `covers-every-close` (= true) | true | true | false | true |
| `interrupted-emit-leaves-nothing` (= true) | true | true | true | false |
| `published-surface-bytes` (min) | 514 | 2985 | 10238 | 514 |
| `obliged-existing-suite-ms` (min) | 226 | 10314 | 898332 | 226 |

`warden-receipt` and `prose-block` each fail a selection gate and leave the
frontier before any measurement is weighed. Of the two that remain,
`skill-emitter` is lower on both comparative metrics, so the non-dominated
frontier holds one candidate and the rule is `unique-frontier`.

Two of those numbers deserve their derivation stated, because both are
measurements over declared change sets rather than over running code.

`published-surface-bytes` counts the bytes of already-published contract text
each candidate must rewrite, measured by summing named `##` sections:
`## Hand back` in the Elenchus skill file is 514 bytes,
`## The mechanical subset` is 2471, and `## One round` in
`plugins/hexaemeron/skills/fiat/references/audit-loop.md` is 7253. Adding a new
section rewrites nothing; changing a command rewrites the section that
documents it.

`obliged-existing-suite-ms` times the existing test modules that already bind
the files each candidate changes, run from the repository root under the pinned
interpreter. Every candidate adds the ledger row and edits the skill prose, so
every candidate owes `plugins.hexaemeron.tests.test_evolution` and the
Imprimatur lint on `SKILL.md`. `checker-subcommand` additionally owes
`plugins.hexaemeron.tests.test_elenchus_checker`, and `warden-receipt`
additionally owes `plugins.hexaemeron.tests.test_hexctl`. New tests are outside
this metric, and each candidate needs a comparable number of them against the
same nine-field shape.

The numbers are one measurement each on this host, a 2026 Darwin 25.5.0
machine reporting 18 CPUs. They are host-bound, and a different machine would
report different values. The ordering they produce is not close.

## 5. Risk register seed

```risk-register
record-overclaims-verdict | the emitted verdict field and the four Elenchus states | verdict.status is one of the four exact strings taken from the result without translation, and the round reads every shipped field for a claim the prose record does not already make
partial-record-write | the emitter's output path during a write | the record is staged and renamed into place, so a killed emitter leaves no file the checker would accept
output-path-escape | the operator-supplied output and draft paths | each is a relative worktree descendant with no symlink component, and a tracked or existing destination is refused
draft-input-untrusted | the draft JSON and the elenchus.py result the emitter reads | both are parsed as bounded strict JSON with a closed key set and a duplicate-key refusal; no value is executed, interpolated into a command or followed as a URL
secret-in-reproduction-output | the reproduction command's captured output | the record stores that output's SHA-256 and byte count and never its bytes, so an RPC credential in a stack trace cannot reach the record
mechanism-recurrence-claim | the causal_mechanism field read across two records | the schema's key set is closed and holds no cross-record identifier, so a record carrying one is refused by the same rule that refuses any unknown key
frontier-drift | the elenchus EVOLUTION.md row this run adds | the frontier revision, digest, status and next job are byte-identical to elenchus-v1.3.0 and test_evolution passes
checker-interface-drift | elenchus.py's command-line interface and its four state strings | no flag, default or state string changes, and test_elenchus_checker passes with no case edited
unbounded-record-size | the draft's free-text fields | every text field carries a byte cap and a printable-character rule, and an over-cap or non-printable draft is refused
guard-name-unbound | the guard field and the tests the parent comparison actually ran | the guard names a test file present in the fix commit's changed test files, and a name absent from that list is refused
```

## 6. Glossary seeds

- **Fixed-and-guarded result.** The claim the `elenchus-fixed-and-guarded`
  Promise authorises: one reproduced failure, localised to a mechanism,
  repaired there, and covered by a test seen red on the parent and green on the
  fixed tree.
- **Structured record.** One closed `elenchus-fixed-and-guarded/v1` JSON
  object holding the nine evidence fields, written beside the prose hand-back
  and never in place of it.
- **Draft.** The operator-supplied JSON holding what `elenchus.py` cannot
  know: `reproduction`, `causal_mechanism`, `minimal_case`, `repair`,
  `fixed_tree`, `suites`, and the test name inside `guard`.
- **Result.** The JSON `elenchus.py --format json` prints, holding `ref`,
  `tests`, `status`, `detail` and, when a report parsed, `report`.
- **Verdict.** One of `guarded`, `passed`, `unguarded`, `inconclusive`, taken
  from the result without translation.
- **Emission.** Writing the record. Not admission, not curation, not
  resolution, and not a claim about any other record.
- **Generation row.** A `EVOLUTION.md` history row that changes behaviour
  without advancing the frontier, retaining the prior frontier revision and
  digest byte for byte.

## 7. Sources

1. `plugins/hexaemeron/skills/elenchus/SKILL.md` at
   `0fefcc98`, in particular `## The mechanical subset`, `## Before the fix is
   receipted`, `## Hand back` and the `### elenchus-fixed-and-guarded` contract.
2. `plugins/hexaemeron/skills/elenchus/scripts/elenchus.py`, functions
   `check`, `classify`, `read_report` and `main`.
3. `plugins/hexaemeron/skills/elenchus/EVOLUTION.md`, rows `elenchus-v1.1.0`
   through `elenchus-v1.3.0`.
4. `plugins/hexaemeron/skills/VERSIONING.md`, `## Frontier discipline` and
   `## What every frontier run owes`.
5. `plugins/anamnesis/skills/anamnesis/SKILL.md`, `### curate` and
   `## Reading the records`.
6. `plugins/hexaemeron/tests/test_elenchus_checker.py` and
   `tests/test_root_elenchus_runner.py` for the test and refusal conventions.
7. `plugins/hexaemeron/skills/protasis/scripts/design_evidence.py` for the
   closed-record checker convention.
8. `tests/run_tests.py`, the root Elenchus report writer, and its
   `--elenchus-report` refusal set.
9. `plugins/hexaemeron/docs/elenchus-audit-round-verdict/study.md`, section 4,
   for the rejection of storing the report inside the audit round.
10. `docs/elenchus-rpc-boundary-fixtures/study.md` and
    `audit/rounds/fiat-387-pin-rpc-boundary-failures-into-lazarus-fixtu.md`
    for the previous generation's evidence and leads.
11. [skills#1275](https://github.com/wildcat-finance/skills/issues/1275),
    [skills#1222](https://github.com/wildcat-finance/skills/issues/1222),
    [skills#1212](https://github.com/wildcat-finance/skills/issues/1212),
    [skills#453](https://github.com/wildcat-finance/skills/issues/453),
    [skills#429](https://github.com/wildcat-finance/skills/issues/429).
12. [PR #636](https://github.com/wildcat-finance/skills/pull/636),
    [PR #635](https://github.com/wildcat-finance/skills/pull/635) and
    [PR #744](https://github.com/wildcat-finance/skills/pull/744) bodies.
13. OASIS SARIF 2.1.0, the `result` object's `ruleId` and `locations` members,
    for the external analogue of a tool emitting structured findings beside
    human output.

## 8. Signals, and the questions behind them

The emitter is a terminal command that runs once at the end of a diagnosis. It
holds no state, opens no socket and runs nothing unattended, so it has no alert
and no metric. It still has to answer two questions at three in the morning,
and both are answered by what it writes rather than by what it logs.

1. *Which run wrote this record, and against which trees?* Answered by the
   record itself: `repair.commit`, `unfixed_parent.commit` and
   `fixed_tree.commit` are three full hexadecimal commit identifiers, so a
   reader can check out all three. Emitted by the step that ships the emitter.
2. *Why was this record refused?* Answered by the refusal, which names the
   stable finding code and the field, in the style `design_evidence.py` uses
   for `D000` to `D008`. Emitted by the same step, and covered by the refusal
   cases in `test_elenchus_fixed_and_guarded.py`.

No structured event stream, no counter and no correlation identifier is added.
`plugins/hexaemeron/skills/ephoros/SKILL.md` owns what a signal must carry, and
the condition it exists for, an unattended path whose behaviour nobody can
reconstruct afterwards, is absent here: the command's whole output is one file
and one exit code, both in front of the person who ran it.

## 9. Boundaries, per capability

Four boundaries open, and each has a control.
`plugins/hexaemeron/skills/phylax/SKILL.md` owns the boundary list and the
controls; these are the instances.

1. **Reading the draft.** The draft is operator-supplied JSON. Worth taking is
   a record whose operator-held fields are typed rather than parsed out of
   prose. The control is a bounded strict-JSON read: a byte cap, a closed key
   set, a duplicate-key refusal, printable text only, and a per-field byte cap.
   No value is executed, interpolated into a command line, or followed as a
   URL. This is the same posture `elenchus.py` already takes toward error
   output, and the same reader shape `design_evidence.py` uses.
2. **Reading the result.** The `elenchus.py --format json` result carries
   `output`, which is up to 4000 characters of text from an arbitrary command
   and is untrusted by the skill's own rule. The control is that `output` is
   never copied into the record and never read for meaning; only `status`,
   `ref`, `tests` and the five integer report counts cross into the record.
3. **Writing the record.** One file inside the worktree. The control is the
   refusal set `tests/run_tests.py` already proved: a relative descendant with
   no `..` component, no symlink component, a parent that is a directory, a
   destination that does not already exist and is not tracked, and one output
   path per invocation. The write is staged and renamed.
4. **The reproduction output.** A stack trace can hold an RPC credential, and
   the skill already forbids leaving instrumentation that prints one. The
   control is that the record stores the output's SHA-256 and byte count and
   never its bytes, so the credential has nowhere in the record to land.

No network is reached, no subprocess is started, and no dependency is added.

## 10. The budget, or its absence

No budget is declared, and the reason is the shape of the work: the emitter
reads two JSON files under a byte cap and writes one, so its cost is bounded by
the cap rather than by anything a change could regress.

That absence is recorded rather than assumed. The baseline command a later run
would declare a budget against, if one is ever wanted, is
`python3 plugins/hexaemeron/skills/elenchus/scripts/fixed_and_guarded.py
--check <record>` timed over the demo record.
`plugins/hexaemeron/skills/metron/SKILL.md` owns what a budget carries and how
it is checked, and its own rule is that a change to performance needs a
recorded measurement first. Nothing here changes performance: the file
`elenchus.py`, which does the expensive work of building a worktree and running
a suite, is not touched.

One measurement is recorded for a different purpose. The design record's
`obliged-existing-suite-ms` criterion timed
`plugins.hexaemeron.tests.test_elenchus_checker` and
`plugins.hexaemeron.tests.test_hexctl` on this host to compare the audit cost
of the candidates. Those are selection evidence, not a budget, and no step is
held to them.

## 11. The fail-closed posture

What stops the run: any refusal exits non-zero and names the rule and the
field. No default value is substituted for a missing field, no field is
inferred from another, and no partial record reaches the destination.

Four refusals decide whether a record exists at all, and each follows from the
Promise's own clauses rather than from taste. A record is refused when any of
the nine evidence fields is absent, because the Evidence clause requires
all of them. A record is refused when `verdict.status` is `passed`,
`unguarded` or `inconclusive`, because the Boundary clause says the result does
not turn an inconclusive, zero-test or infrastructure-failed comparison into a
guard. A record is refused when `guard` names a test absent from the fix
commit's changed test files, because the Boundary covers the *named* guard. A
record is refused when the draft is not one closed bounded object.

The guard-test convention every fix in this delivery follows is Elenchus's own:
write the test that fails on the old code and passes on the new one, run it
against the unfixed tree first, and name it after the failure rather than after
the fix. `plugins/hexaemeron/skills/elenchus/SKILL.md` owns the triage order
and the guard rule, and this delivery's audit rounds use the runner contract
each runbook step declares. Because the skill under change is
Elenchus itself, one extra care applies: a fix to the emitter is guarded by the
emitter's own test module, and `test_elenchus_checker.py` is left alone so the
classifier the guard check depends on is never modified in the same commit as a
guard that depends on it.

## 12. Decisions and their homes

Two decisions here are expensive to reverse, because a record written under one
of them exists afterwards and a reader will read it.

1. **The nine-field shape and its derivation from the Promise's two clauses.**
   Once records exist, the field set is what every reader parses, and adding or
   removing a field afterwards splits the population. This earns a decision
   record under `docs/decisions/`, and it also states what the record does not
   establish, so the boundary travels with the shape rather than living only in
   this study.
2. **Emitting rather than resolving.** That the schema carries no cross-record
   identifier is a choice, not an omission, and the next person to want
   recurrence will read the absence as a gap unless the reason is written down.
   It belongs in the same record as the shape it constrains.

Both go in one file. Under
`docs/decisions/ADR-077-assign-adr-numbers-at-merge-not-at-authoring.md`
the number is assigned at merge rather than at authoring, so the runbook step
picks it against the default branch immediately before pushing; `ADR-080` is
the highest present at the starting ref.

The generation row in `plugins/hexaemeron/skills/elenchus/EVOLUTION.md` is the
ledger's own record and is not an ADR.
`plugins/hexaemeron/skills/hypomnema/SKILL.md` owns which decisions earn a
record and where each one lives; nothing else here meets its bar, because the
emitter's flags, its refusal codes and its test layout are all cheap to change
while no record has been written to a shared place.

## Boundaries this study states

**Always.** Run both suites before a commit:
`python3 plugins/hexaemeron/tests/run_tests.py` and
`python3 tests/run_tests.py`. Run
`python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py` on every
shipped document. Make every new guard test fail against the unfixed tree
before keeping it.

**Ask first.** Adding any dependency outside the standard library. Changing
`elenchus.py`'s command-line interface, its defaults or its four state strings.
Changing the audit record grammar. Touching CI. Changing a released digest or a
committed release under `plugins/anamnesis/specimens/`.

**Never.** Commit an RPC credential or key material, including inside a
reproduction output. Edit `plugins/lazarus/` or any vendored Pashov skill.
Delete or weaken a failing test to make a suite pass. Edit an existing audit
record. Claim a command ran when it did not.

### Amendment -- 2026-09-05

**What changed.** Two sentences described the shipped emitter incorrectly. Section 9's closing sentence "No network is reached, no subprocess is started, and no dependency is added" is replaced by: no network is reached and no dependency is added, and the emitter starts two fixed-argv `git` subprocesses in emit mode, `git rev-parse <ref>^` to derive the parent and `git ls-files --error-unmatch` to refuse a tracked destination, with no shell, no interpolated value and neither call reached by `--check`. The field table's `verdict` row, "one of the four states, and the runner contract that produced it", is replaced by: one of the four states and the runner-report account that produced it, both taken from the `elenchus.py --format json` result without translation. The nine-field set, its derivation and every boundary the record carries are unchanged.

**Why.** Warden findings S1-R1-01 and S1-R1-05 in round 1 of step 1. The study's own field table requires the `git rev-parse` call and section 9's third boundary requires the `git ls-files` call, so the closing sentence contradicted the document that contains it. The `elenchus.py --format json` result prints `ref`, `tests`, `status`, `detail` and `report`, and carries no runner contract; taking one would have moved the field out of the column the table assigns it to, or widened the operator draft past its stated key set. The emitter follows the study's substance in both cases, so the wording is what was wrong.

**Steps touched.** Step 1.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds.

### Amendment -- 2026-09-05

**What changed.** Section 11 now names six refusals rather than four. The two added ones are: a record whose `unfixed_parent.commit` equals its `fixed_tree.commit` is refused by `--check` as well as on emit, because a guard observed red and green on one commit is not the two trees the Evidence clause names; and a record whose `verdict.status` is `guarded` while its own `unfixed_parent.report` shows zero assertion failures and zero errors is refused, because the Promise's Refuses clause names a guard that never failed without the fix. Both are decided from fields the record already carries, and neither reads anything outside it. Section 1's parent-derivation rendering `git rev-parse <ref>^` is replaced by the exact shipped argv `git rev-parse <ref>^{commit} <ref>^`, which peels an annotated tag before taking the parent, and the tracked-destination call is `git ls-files --error-unmatch -- <path>`; these two renderings supersede the ones the 2026-09-05 amendment above gave. The nine-field set and its derivation are unchanged.

**Why.** Warden findings S1-R2-03, S1-R2-04 and S1-R2-06 in round 2 of step 1. Round 2 demonstrated that `--check` accepted a record whose parent and fixed tree were one commit, the exact shape round 1 had demonstrated on the emit path, and accepted a `guarded` record whose own parent report showed nothing had failed. The round declined to close either in code, because section 11 authorised four refusals and writing a fifth and sixth ahead of the study is what produced finding S1-R1-01. The renderings were incomplete rather than wrong in substance: round 1's fix added the `--` operand and round 2's added the `^{commit}` peel, and the study still described the call as it stood before both.

**Steps touched.** Step 1.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds.
