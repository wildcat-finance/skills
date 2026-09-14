# Runbook: make the declared mapper select the implementation that reads a source

Derived from the study receipted at `.hexaemeron/study.md` and committed beside
this file as `resolved-mapper-study.md`. The selected design is
`registry-and-synopsis-mapper`: a module-level registry maps `(name, version)`
to an implementation, `curate` and `ingest` resolve `policy["mapper"]` through
it and refuse by rule when it does not resolve, every assertion records the
resolved registry entry, and a second implementation reading
`fiat-audit-synopsis/v1` admits a third specimen over the three committed
`AUDIT_SYNOPSIS.md` files.

Four steps. Step 1 commits the design records, admits this run's step numbers to
the guard runner and adds the registry with its unresolved-mapper refusal. Step
2 adds the synopsis mapper, builds the third corpus and produces the conformance
report the design record's one pending cell names. Step 3 records the decisions
and closes the guards the risk register still owes. Step 4 advances the ledger,
corrects the declared input, reconciles the prose and runs the demo path.

## Where the design checker runs, measured

`hexctl.py` at `done push` computes its next design transition from the first
step still marked `pending`. The step being pushed is `open`, not `pending`, so
at step N's push the transition checked is `step:N+1`. `_prepare_design_transition`
fails the push when the checker reports a finding, and `_due` in
`design_evidence.py` treats a cell blocking `step:K` as due at every transition
`step:J` where `K <= J`, and at `integration`.

The schedule that follows: `done study` receipted `design-lock`; `done runbook`
receipts `step:1`; step 1's push receipts `step:2`; **step 2's push receipts
`step:3`**; step 3's push receipts `step:4`; step 4's push receipts nothing
because no step remains pending; and `integrate` receipts `integration`.

The design record's one conformance criterion,
`second-corpus-rebuilds-deterministically`, carries `blocks` `step:3`. That is
the transition by which its report must exist, not the step that produces it.
The report is therefore due at the end of step 2, and step 2 both writes it and
proves the boundary.

Measured against the receipted record at `f0ef9266`: `--transition design-lock`,
`--transition step:1` and `--transition step:2` each print `clean` and exit 0;
`--transition step:3`, `--transition step:4` and `--transition integration` each
exit 1 with `D008 registry-and-synopsis-mapper/second-corpus-rebuilds-deterministically
report is unavailable or outside the record directory`.

The record holds four pending cells, one per candidate, all blocking `step:3`.
The checker enforces only the selected candidate's, so this run owes exactly one
report: `reports/registry-and-synopsis-mapper-second-corpus-rebuilds-deterministically.json`,
resolved against the record's own directory, which is `.hexaemeron/`.

## How to read the step numbers

The Elenchus guard runner is `plugins/anamnesis/tests/elenchus.py`. It numbers
steps by the plugin's own history, not by this run's, and its `STEPS` tuple
today admits 1 to 10. Anamnesis numbering continues from 10, so this run's Fiat
step N is the plugin's step 10 + N:

| Fiat step | Anamnesis step | Suite the runner discovers |
| --- | --- | --- |
| 1 | 11 | `plugins/anamnesis/tests/test_s11_registry.py` |
| 2 | 12 | `plugins/anamnesis/tests/test_s12_synopsis.py` |
| 3 | 13 | `plugins/anamnesis/tests/test_s13_guards.py` |
| 4 | 14 | `plugins/anamnesis/tests/test_s14_ledger.py` |

The runner refuses a step whose `test_sN_*.py` pattern discovers nothing, so
each step creates its own suite. Step 1 extends `STEPS` to 1 through 14 once,
for the whole run. Each step's `Tests` field names the exact runner command, so
Warden takes its argument from there and does not infer one from the heading.

## Which step owes each risk-register entry

Study section 5 seeds ten concerns. Each one is a named obligation of exactly
one step, so a gate is checked where it is incurred rather than argued about in
the audit loop:

| Register id | Step that owes its check |
| --- | --- |
| `unresolved-mapper-writes-records` | 1 |
| `declared-not-resolved-in-assertion` | 1 |
| `release-identity-drift` | 1, and rechecked in 2, 3 and 4 |
| `program-digest-repin` | 1, and again in 2 |
| `third-corpus-rights-basis` | 2 |
| `scope-bounds-for-the-third-corpus` | 2 |
| `registry-mutability` | 3 |
| `synopsis-cell-splitting` | 3 |
| `mapper-backtracking` | 3 |
| `fail-open-mapper` | 2 raises the refusal, 3 proves it against every probe |

## The exit command every step names

The root check runner is `python3 scripts/run_checks.py --base origin/main`.
Three lints are not CI, and no step exit is satisfied by the plugin suite alone.
Every step runs it from a clean detached snapshot of that step's committed head,
taken with `git worktree add --detach`, because the run worktree's own
`.hexaemeron/` directory reddens two root tests that read that path
([skills#1228](https://github.com/wildcat-finance/skills/issues/1228)).

Every commit is preceded by
`python3 plugins/horos/skills/horos/scripts/horos.py scan . --write` and
`python3 plugins/horos/skills/horos/scripts/horos.py scan . --census --write`
over the staged tree, because the boundary counts tracked paths and the census
counts bytes, and any tracked-file edit moves the census.

## Two refusal codes this run allocates

`anamnesis.py` uses `A001` through `A077`, `A080`, and the `A100` and above
bands. `A078` and `A079` are unused, and this run takes both: `A078` for a
declared mapper that does not resolve, `A079` for bytes handed to the synopsis
mapper without its declared schema header.

```design-lock
schema | protasis-design-evidence/v1
sha256 | 36170cc03cbd3ce3fab6b4d0ae2cec31bcc2f2024ba5ad397881a17815e54228
candidate | registry-and-synopsis-mapper
```

## Step 1: Commit the design records and resolve the declared mapper through a registry

**Goal.** Land the study, this runbook, the design record, its 32 reports and
their resolver under `plugins/anamnesis/docs/`, admit this run's step numbers to
the Elenchus runner, and make `curate` and `ingest` resolve `policy["mapper"]`
through a module-level registry that refuses `A078` before any record is written
and records the resolved entry on every assertion.

This step carries the Protasis scaffolding fixed point and one product change
together. The registry cannot wait: the synopsis mapper in step 2 is a second
registry entry, and the conformance report step 2 owes is due at step 2's push.

**Entry.** The run branch `fiat/1464-make-the-declared-mapper-select-the-impleme`
at `f0ef92663484c548c5fee26f2964628349a03892`, with `.hexaemeron/study.md`,
`.hexaemeron/design-evidence.json`, its 32 reports and `.hexaemeron/reports/resolve.py`
receipted and this runbook receipted;
`python3 plugins/hexaemeron/skills/protasis/scripts/design_evidence.py .hexaemeron/design-evidence.json --transition step:1`
exits zero.

**Exit.** `plugins/anamnesis/docs/resolved-mapper-study.md` and
`plugins/anamnesis/docs/resolved-mapper-runbook.md` are byte-identical to
`.hexaemeron/study.md` and `.hexaemeron/runbook.md` as those stand at this step's
head, including any amendment the controller appended during the step, and step
4 re-syncs both after any later amendment;
`plugins/anamnesis/docs/resolved-mapper/design-evidence.json` has SHA-256
`36170cc03cbd3ce3fab6b4d0ae2cec31bcc2f2024ba5ad397881a17815e54228`;
`plugins/anamnesis/docs/resolved-mapper/reports/` holds the 32 receipted report
objects and `resolve.py` with the receipted bytes;
`plugins/anamnesis/tests/elenchus.py` admits steps 1 through 14 and
`python3 plugins/anamnesis/tests/elenchus.py --step 11 .hexaemeron/elenchus/anamnesis-step-11.json`
exits zero;
`anamnesis.py` holds one module-level registry mapping
`("warden-audit-round-markdown", "1")` to the implementation `parse_source`
already is, and the unreferenced `MAPPER` constant is gone; `curate` and
`cmd_ingest` resolve `policy["mapper"]` by exact `(name, version)` lookup with
no fallback, no default and no partial match; an unresolved declaration raises
`A078` inside `refusals_recorded` before any assertion, quarantine entry or
release directory exists, and emits the existing `anamnesis.source.refused`
JSONL event carrying the rule, the record, the policy version and the
correlation id; `_assertion` writes the resolved registry entry's identity
rather than the policy string, and for a policy whose mapper resolves that
object is byte-identical to the declared one, which is the hard gate this step
turns on;
`plugins/anamnesis/tests/fixtures/unknown-mapper-policy.json` declares
`{"name": "a-mapper-that-does-not-exist", "version": "9"}` and both shipped
`curation-policy.json` files are byte-unchanged;
`python3 plugins/anamnesis/skills/anamnesis/scripts/anamnesis.py verify-rebuild --specimen plugins/anamnesis/specimens/pilot`
exits zero on release id `41d640fb` and the same command on
`plugins/anamnesis/specimens/estate` exits zero on `50923976`;
`plugins/anamnesis/skills/anamnesis/DEMONSTRATION.md` re-pins its `program`
source `sha256` to the new digest of `anamnesis.py` and carries exactly one new
`generation` row `anamnesis-demo-v0.4.0`, with the demo frontier revision
`second-preserved-audit-corpus` and its digest
`04859403f738c0e6c358e794307f9db5abecd53f5ec8ec2dd7a2863886086374` unchanged and
the header bullet and the record's `frontier.version` both reading
`anamnesis-demo-v0.4.0`; the root `README.md` front-door card `digest=` value
equals `record_digest` of that record; the program digest is carried by
`DEMONSTRATION.md` and no other tracked file;
`python3 scripts/demonstrations.py check --root .` and
`python3 scripts/check_public_front_door.py` exit zero;
`python3 -m unittest plugins.anamnesis.tests.test_s8_scope` is green, including
`TheRebuiltCountSeesArtefactsAndNotGuards` rerunning all four recorded
`pilot-artefacts-rebuilt` values;
`python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py plugins/anamnesis/docs/resolved-mapper-study.md plugins/anamnesis/docs/resolved-mapper-runbook.md`
exits zero;
`python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/anamnesis/docs/resolved-mapper-study.md plugins/anamnesis/docs/resolved-mapper-runbook.md`
exits zero;
`python3 -m unittest discover -s plugins/anamnesis/tests -t plugins/anamnesis`
is green; `python3 scripts/run_checks.py --base origin/main` exits zero from a
clean detached snapshot of the committed head;
`python3 plugins/horos/skills/horos/scripts/horos.py check .` exits zero;
`git diff --check` is clean; and
`python3 plugins/hexaemeron/skills/protasis/scripts/design_evidence.py .hexaemeron/design-evidence.json --transition step:2`
exits zero before the pull request is ready.

**Files.** Create `plugins/anamnesis/docs/resolved-mapper-study.md`,
`plugins/anamnesis/docs/resolved-mapper-runbook.md`,
`plugins/anamnesis/docs/resolved-mapper/design-evidence.json`,
`plugins/anamnesis/docs/resolved-mapper/reports/` (32 report objects and
`resolve.py`), `plugins/anamnesis/tests/test_s11_registry.py` and
`plugins/anamnesis/tests/fixtures/unknown-mapper-policy.json`. Change
`plugins/anamnesis/tests/elenchus.py` (`STEPS`),
`plugins/anamnesis/skills/anamnesis/scripts/anamnesis.py`,
`plugins/anamnesis/skills/anamnesis/DEMONSTRATION.md`,
`plugins/anamnesis/skills/anamnesis/SKILL.md` (the curation `Refuses` line and
the sentence describing what a mapper declaration does), root `README.md` (the
card digest), `.horos/boundary.json` and `.horos/census.json`.

**Tests.** Add `plugins/anamnesis/tests/test_s11_registry.py`.

Over the committed design record: it parses as one closed
`protasis-design-evidence/v1` object naming four candidates and nine criteria
that cover `correctness`, `time`, `space`, `compatibility` and `recovery`; it
selects `registry-and-synopsis-mapper` under `unique-frontier`, with
`registry-and-red-team-mapper` and `registry-only` each failing exactly
`second-format-declares-its-own-schema` and `per-source-mapper` failing exactly
`shipped-release-policies-changed` at a measured value of 2; each of its 32
resolved cells names a report whose recorded SHA-256 equals the committed bytes,
whose `exit` is 0 and whose `command` names the committed `resolve.py`; its four
pending cells, one per candidate, each name a resolver, a future report path and
the stop point `step:3`, and the selected candidate's names the report path
`reports/registry-and-synopsis-mapper-second-corpus-rebuilds-deterministically.json`;
the two committed documents equal the artefacts at this step's head byte for
byte; and `elenchus.py` admits every step from 1 to 14.

Over the registry: the estate specimen under `fixtures/unknown-mapper-policy.json`
refuses `A078` from `curate` and from `ingest`, leaving no assertion, no
quarantine entry and no release directory, where at the parent commit that same
input exited 0, produced 17 findings, wrote the false name into all 55
assertions and released `8bae874752c55b9f`; the refusal writes one
`anamnesis.source.refused` event carrying rule `A078`, the record, the policy
version and the correlation id; every assertion in a fresh pilot build carries
the identity of the registry entry that ran, checked by resolving that entry
directly and comparing it with the assertion, and by a source check that
`_assertion` takes the resolved entry as an argument instead of reading
`policy["mapper"]`; a declared object that resolves produces an assertion object
byte-identical to the declaration, so neither shipped release id moves; the
token `MAPPER` no longer appears in the module; the pilot rebuilds to `41d640fb`
and the estate to `50923976`; both shipped curation policies are byte-unchanged;
and `DEMONSTRATION.md` names the current program digest while the committed root
card digest equals `demonstrations.record_digest` of the ledger record.

The audit runner contract is
`python3 plugins/anamnesis/tests/elenchus.py --step 11 {report}`, its format is
`elenchus.unittest.v1`, and Warden writes
`.hexaemeron/elenchus/anamnesis-step-11.json`. Also run both shipped rebuilds,
`python3 -m unittest plugins.anamnesis.tests.test_s8_scope`, the anamnesis suite
from the repository root, the root suite from a clean snapshot, and
`git diff --check`. Expected new focused tests: 18.

**Disciplines.** phylax: this step opens the boundary in study section 9 item 2,
a value in a policy file deciding which code runs, and the controls are the
module-level constant map, exact `(name, version)` lookup with no fallback or
default, refusal on a miss, and no path by which a policy or a source registers
an entry; `unresolved-mapper-writes-records`, `declared-not-resolved-in-assertion`,
`release-identity-drift` and `program-digest-repin` are this step's register
obligations, and step 3 proves the registry is unwritable after import.
ephoros: `curate` already sits inside `refusals_recorded`, so `A078` emits the
existing `anamnesis.source.refused` event with rule, record, policy version and
correlation id, which is the study's on-call question 1; no new event kind, sink
or counter, because the existing stream already answers it. metron: none, no
budget is declared and no change here is motivated by speed; the design record's
`acceptance-check-ms` is a recorded baseline at 1 millisecond for all four
candidates. elenchus: the estate probe in study section 1 is the failure in
hand, its policy becomes the fixture the guard runs against, and the guard is
run at the parent commit to show it fails there. hypomnema: the registry as the
resolution mechanism, the mapper's home staying in the curation policy rather
than moving per source, and the committed home and names of this run's design
records are all expensive to reverse; the first two are decided here and
recorded in the decision record step 3 lands, and the third is settled here
because the ledger row in step 4 cites those paths.

## Step 2: Add the synopsis mapper, build the third corpus, produce the conformance report

**Goal.** Register a second implementation that refuses bytes without the
`fiat-audit-synopsis/v1` header and reads that format, build
`plugins/anamnesis/specimens/synopsis` over the three committed
`AUDIT_SYNOPSIS.md` files, and write the conformance report the design record's
`step:3` cell names, so the boundary the controller checks at this step's push
is already clean.

Decision 3 of study section 12, that the second corpus preserves the same
findings the pilot preserves, has two homes. This step writes the second one:
the `scope.preserves` sentence in the synopsis curation policy, which sits
inside the release and is hashed into its id. The decision record carrying all
three decisions is written in step 3.

**Entry.** Step 1's exit state;
`python3 plugins/hexaemeron/skills/protasis/scripts/design_evidence.py .hexaemeron/design-evidence.json --transition step:2`
exits zero.

**Exit.** The registry carries a second entry `("fiat-audit-synopsis", "1")`
whose implementation reads the header line, requires
`schema=fiat-audit-synopsis/v1`, and raises `A079` for a missing, malformed or
non-matching header before reading any round, so it never returns an empty or
partial round set from bytes it did not accept; each round line is split on
`<br>` into the producer's own cells and the round-field and finding-row grammar
the first mapper owns is applied to those cells;
`plugins/anamnesis/specimens/synopsis/` holds `policy.json` naming three sources
at digests `2e919d920cd952a837bee6069251b710a9543df37514d7248a996d61766138cd`,
`ecde800e07ed8b1bc94b5a55714e3b01fbe0dfb1283bdafc88be170357dd32f1` and
`2432d6fd11be15a838d62ab067a190314a1a63011a67e106682f700cc3447e6c`, each with
rights basis `licence`, Apache-2.0, holder Wildcat Labs and a statement naming
the repository `LICENSE` the way the pilot's three sources do;
`curation-policy.json` declaring mapper `fiat-audit-synopsis` version 1, a scope
whose `preserves` sentence states that this corpus renders the same three audit
records the pilot preserves, the three source ids and record bounds 25 to 50;
`sources/` holding the three files at 36,455 bytes in total; and `release/`,
`projections/` and `events/`;
`python3 plugins/anamnesis/skills/anamnesis/scripts/anamnesis.py demo --specimen plugins/anamnesis/specimens/synopsis`
exits zero with two fresh builds agreeing byte for byte on 41 findings across 31
rounds, 12 of them with no findings; the same three sources read under the pilot
curation policy refuse rather than returning the 31 empty rounds they return at
the parent commit; the pilot rebuilds to `41d640fb` and the estate to `50923976`,
and both shipped curation policies stay byte-unchanged;
`python3 plugins/anamnesis/skills/anamnesis/scripts/anamnesis.py verify-rebuild --specimen plugins/anamnesis/specimens/synopsis`
exits zero and its result is written by hand as one closed
`protasis-design-report/v1` object at
`.hexaemeron/reports/registry-and-synopsis-mapper-second-corpus-rebuilds-deterministically.json`
whose `candidate` is `registry-and-synopsis-mapper`, `criterion` is
`second-corpus-rebuilds-deterministically`, `unit` is `boolean`, `value` is
`true`, `command` is that exact resolver string and `exit` is `0`, with the same
bytes committed under `plugins/anamnesis/docs/resolved-mapper/reports/`, which
then holds 33 report objects; the committed `resolve.py` is not re-run, because
a rerun would rewrite the 32 receipted reports the design record binds by digest;
`plugins/anamnesis/skills/anamnesis/DEMONSTRATION.md` re-pins its `program`
source `sha256` to the new digest and carries exactly one new `generation` row
`anamnesis-demo-v0.5.0`, demo frontier revision and digest unchanged, and the
root `README.md` card `digest=` is re-pinned to `record_digest` of that record,
with the program digest still carried by `DEMONSTRATION.md` and no other tracked
file;
`python3 scripts/demonstrations.py check --root .` and
`python3 scripts/check_public_front_door.py` exit zero;
`python3 -m unittest plugins.anamnesis.tests.test_s8_scope` is green, including
`TheRebuiltCountSeesArtefactsAndNotGuards` rerunning all four recorded values;
`python3 plugins/anamnesis/tests/elenchus.py --step 12 .hexaemeron/elenchus/anamnesis-step-12.json`
exits zero; `python3 scripts/run_checks.py --base origin/main` exits zero from a
clean detached snapshot of the committed head;
`python3 plugins/horos/skills/horos/scripts/horos.py check .` exits zero;
`git diff --check` is clean; and
`python3 plugins/hexaemeron/skills/protasis/scripts/design_evidence.py .hexaemeron/design-evidence.json --transition step:3`
exits zero, which is the boundary `done push` checks immediately after this
step and the reason the report is due here.

**Files.** Change `plugins/anamnesis/skills/anamnesis/scripts/anamnesis.py`,
`plugins/anamnesis/skills/anamnesis/DEMONSTRATION.md`,
`plugins/anamnesis/skills/anamnesis/SKILL.md` (the mapper paragraph and the
curation `Refuses` line), `plugins/anamnesis/README.md` (the specimen list),
root `README.md` (the card digest), `.horos/boundary.json` and
`.horos/census.json`. Create `plugins/anamnesis/specimens/synopsis/policy.json`,
`curation-policy.json`, three files under `sources/`, `release/`, `projections/`
and `events/admit.jsonl`;
`plugins/anamnesis/docs/resolved-mapper/reports/registry-and-synopsis-mapper-second-corpus-rebuilds-deterministically.json`;
and `plugins/anamnesis/tests/test_s12_synopsis.py`.

**Tests.** Add `plugins/anamnesis/tests/test_s12_synopsis.py`: the synopsis
mapper raises `A079` and returns no rounds on a file whose header declares
another schema and on a header-less file; the same three synopsis sources read
by the Warden mapper return 31 rounds and 0 findings while read by the synopsis
mapper they return 31 rounds and 41 findings, so the control is exact; each
synopsis source's header `source_sha256` equals the digest the pilot's admission
policy records for the same audit record, at
`8acff29ed567c97902941a85d72e41171c10850de6aa898b5d50564248eac28f`,
`66908cb68630f3c3cbea432aec6cf6efc305bcab85ccf5fadb278c535635edf9` and
`1de310b5df5784d7e623ea9dbda83ae77e02cb1798b3aeedffc5d0c715f8e3a7`; two fresh
builds agree byte for byte and equal the committed release, whose id differs from
both `41d640fb` and `50923976`; the committed projections equal fresh ones; every
synopsis source's `rights` are `licence`, Apache-2.0, holder Wildcat Labs with a
non-empty statement, and no synopsis source or policy byte carries a local path
prefix, a URL scheme or a repository slug; the declared record bounds are 25 to
50, the corpus holds 41, and a record count outside those bounds refuses `A073`;
the curation policy's `scope.preserves` sentence names the same three audit
records the pilot preserves; the committed conformance report parses as one
closed `protasis-design-report/v1` object with `value` `true` and `exit` `0`, its
bytes equal the copy under `.hexaemeron/reports/`, and the 32 report objects
committed in step 1 are byte-unchanged; and the pilot rebuilds to `41d640fb`
and the estate to `50923976`. The audit runner contract is
`python3 plugins/anamnesis/tests/elenchus.py --step 12 {report}`, its format is
`elenchus.unittest.v1`, and Warden writes
`.hexaemeron/elenchus/anamnesis-step-12.json`. Also run the synopsis demo, both
shipped rebuilds, `python3 -m unittest plugins.anamnesis.tests.test_s8_scope`,
the anamnesis suite from the repository root, the root suite from a clean
snapshot, and `git diff --check`. Expected new focused tests: 12.

**Disciplines.** phylax: this step opens the boundary in study section 9 item 1,
a second parser over untrusted preserved bytes, and the existing
`MAX_SOURCE_BYTES_CEILING` read cap, the digest re-check at curation and
`resolve_within`'s no-symlink resolution all apply unchanged; the new control is
the schema-header check that runs before any row is read;
`third-corpus-rights-basis` and `scope-bounds-for-the-third-corpus` are closed
here, and `synopsis-cell-splitting`, `mapper-backtracking` and the full
`fail-open-mapper` probe set are step 3's. ephoros: `A079` is raised inside
`refusals_recorded`, so it emits the existing `anamnesis.source.refused` event,
which is the study's on-call question 3 and is what stops "0 findings" and "not
my format" being the same observation; no new event kind. metron: none, no
budget is declared and `demo` prints duration and peak resident memory as
baselines; the step records the 36,455 added source bytes against the
packaged-payload cap in
[#1467](https://github.com/wildcat-finance/skills/issues/1467) rather than
budgeting them. elenchus: the fail-open reading of 31 rounds and 0 findings is
the failure in hand, its guard is the refusal case above, and the guard is run at
the parent commit to show it fails there. hypomnema: decision 3 of study section
12 gets its second home here, the `scope.preserves` sentence the release id
hashes, and the decision record carrying all three lands in step 3.

## Step 3: Record the decisions and close the risk register's guards

**Goal.** Write one decision record carrying the three decisions in study
section 12, and add the four guards the risk register still owes: registry
immutability at import time, the `synopsis-cell-splitting` cases, the
`mapper-backtracking` bound or the restated absence of one, and
`fail-open-mapper` fed both Warden Markdown and the pilot's own bytes.

**Entry.** Step 2's exit state;
`python3 plugins/hexaemeron/skills/protasis/scripts/design_evidence.py .hexaemeron/design-evidence.json --transition step:3`
exits zero.

**Exit.** One decision record under `plugins/anamnesis/docs/decisions/` carries
the three decisions in study section 12, cites the measured
`shipped-release-policies-changed` value of 2 as the reason `per-source-mapper`
was rejected, carries the five sections and a dated status, and its number is
chosen against the default branch immediately before the pull request is pushed
rather than when the file is written, because numbers collide before merge;
`python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py <the decision record>`
and
`python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py <the decision record>`
exit zero;
the registry rejects every write attempted after import and no policy field,
source byte or environment variable reaches it;
a producer cell containing the `<br>` separator, an unterminated finding row and
a file whose final line is truncated each refuse or round-trip verbatim and are
never silently shortened;
the synopsis mapper's patterns are run over the widest cell any admitted source
produces and the outcome is recorded either as a measured bound or as the source
byte cap restated as the only bound claimed, with the choice stated in the
decision record's consequences section;
the synopsis mapper raises `A079` and returns no rounds on Warden Markdown and
on each of the pilot's three source files;
if this step changes `anamnesis.py` bytes, `DEMONSTRATION.md` re-pins its
`program` source `sha256` and carries exactly one new `generation` row
`anamnesis-demo-v0.6.0` with the demo frontier revision and digest unchanged, the
root `README.md` card `digest=` is re-pinned to that record's `record_digest`,
and the program digest stays carried by `DEMONSTRATION.md` and no other tracked
file; if it does not, both files stay byte-unchanged;
either way `python3 scripts/demonstrations.py check --root .` and
`python3 scripts/check_public_front_door.py` exit zero;
the pilot rebuilds to `41d640fb` and the estate to `50923976`, and both shipped
curation policies stay byte-unchanged;
`python3 -m unittest plugins.anamnesis.tests.test_s8_scope` is green, including
`TheRebuiltCountSeesArtefactsAndNotGuards` rerunning all four recorded values;
`python3 plugins/anamnesis/tests/elenchus.py --step 13 .hexaemeron/elenchus/anamnesis-step-13.json`
exits zero; `python3 scripts/run_checks.py --base origin/main` exits zero from a
clean detached snapshot of the committed head;
`python3 plugins/horos/skills/horos/scripts/horos.py check .` exits zero;
`git diff --check` is clean; and
`python3 plugins/hexaemeron/skills/protasis/scripts/design_evidence.py .hexaemeron/design-evidence.json --transition step:4`
exits zero before the pull request is ready.

**Files.** Create one decision record under
`plugins/anamnesis/docs/decisions/` and
`plugins/anamnesis/tests/test_s13_guards.py`. Change `.horos/boundary.json` and
`.horos/census.json`, and, only if the backtracking bound needs a pattern
change, `plugins/anamnesis/skills/anamnesis/scripts/anamnesis.py`,
`plugins/anamnesis/skills/anamnesis/DEMONSTRATION.md` and root `README.md`.

**Tests.** Add `plugins/anamnesis/tests/test_s13_guards.py`: assigning into the
registry, replacing it, and deleting an entry each fail after import, and a
source that declares an implementation, a policy field that names a module path
and an environment variable naming one all fail to reach it; a synopsis source
whose producer cell contains `<br>`, one with an unterminated finding row and one
whose final line is truncated each refuse by rule or round-trip verbatim, checked
against the source bytes rather than against a rendering; the widest cell any
admitted synopsis source produces is fed to every pattern the synopsis mapper
runs and the recorded outcome is either a measured bound or the byte cap
restated, with the test failing if neither is recorded; the synopsis mapper
raises `A079` and returns no rounds on Warden Markdown and on each of the
pilot's three source files, so the control covers both the format the first
mapper owns and the exact bytes the pilot preserves; the committed decision
record exists under `plugins/anamnesis/docs/decisions/`, carries the five
sections and a dated status, names all three decisions from study section 12,
and cites the value 2; and the pilot rebuilds to `41d640fb` and the estate to
`50923976`. The audit runner contract is
`python3 plugins/anamnesis/tests/elenchus.py --step 13 {report}`, its format is
`elenchus.unittest.v1`, and Warden writes
`.hexaemeron/elenchus/anamnesis-step-13.json`. Also run both shipped rebuilds,
`python3 -m unittest plugins.anamnesis.tests.test_s8_scope`, the anamnesis suite
from the repository root, the root suite from a clean snapshot, and
`git diff --check`. Expected new focused tests: 10.

**Disciplines.** phylax: no boundary opens here, and the step exists to prove the
controls study section 9 named for the two boundaries steps 1 and 2 opened;
`registry-mutability`, `synopsis-cell-splitting`, `mapper-backtracking` and
`fail-open-mapper` are this step's register obligations, and the last of them is
fed Warden Markdown and the pilot's bytes because those are the two inputs a
fail-open mapper would silently accept. ephoros: none, no refusal path changes
and no event kind, sink or counter is added; the two rules this run introduced
already emit on the existing stream. metron: none, no budget is declared, and
the backtracking outcome is a recorded measurement or a restated cap rather than
a budget, which is the position study section 10 takes. elenchus: this is the
step where study section 11's guard convention is discharged, so each guard
names the exact specimen or bytes that reproduce its concern and is run against
the parent commit to show it fails there. hypomnema: all three decisions in
study section 12 land here in one record, and decision 3's second home, the
synopsis curation policy's `scope.preserves` sentence, was written in step 2 and
is cited rather than restated.

## Step 4: Advance the ledger, correct the declared input, run the demo path

**Goal.** Record the completed frontier job in Anamnesis's evolution ledger,
replace the stale declared-input row, re-sync the committed study and runbook
copies, reconcile every mutable first-party marketplace prose surface from a cold
read, and run the study's demo path.

**Entry.** Step 3's exit state;
`python3 plugins/hexaemeron/skills/protasis/scripts/design_evidence.py .hexaemeron/design-evidence.json --transition step:4`
exits zero.

**Exit.** `plugins/anamnesis/skills/anamnesis/EVOLUTION.md` carries exactly one
new row valid under the versioning contract: evolution incremented once to
`anamnesis-v5.1.0`, generation and epoch retained, the prior revision
`declared-scope` and digest
`13c730d9f26091188d16c8c640632c21943fe3f85b2c9363c70b8e0ed499965e` preserved in
the `v4.1.0` row, the header bullets and the row naming the same version, the new
frontier revision `resolved-mapper`, the frontier digest recomputed over the
exact `{status}|{frontier revision}|{current frontier}|{next Fiat job}` line
including its final newline, Evidence citing the step 3 decision record and the
step 12 and step 13 suites, and one evidenced next job, which is the successor
study section 12 names: admit a corpus whose findings a party other than this
repository produced, under a per-source mapper declaration so one corpus can hold
both; the `declared-inputs` block replaces the `foreign-format-corpus` row with
one row `second-producer-findings | corpus | absent | <note>` whose note names a
second producer's findings with a rights basis to redistribute them and stays
within 200 bytes, so the block still holds four non-empty pipe-separated fields
and opens with no hyphen, pipe or backtick;
`plugins/anamnesis/docs/resolved-mapper-study.md` and
`plugins/anamnesis/docs/resolved-mapper-runbook.md` are byte-identical to the
receipted `.hexaemeron/study.md` and `.hexaemeron/runbook.md` including every
amendment appended during the run; `SKILL.md` frontmatter reads `5.1.0`; the
marketplace-context blocks in `plugins/anamnesis/README.md`,
`plugins/anamnesis/AGENTS.md` and
`plugins/anamnesis/skills/anamnesis/SKILL.md`, the front-door status block and
the `Next Fiat job` paragraph in `plugins/anamnesis/README.md`, and the root
`README.md` describe the resolved mapper and the new held job, and no
first-party document under `plugins/anamnesis/` still says the resolver always
runs one mapper or that an assertion records the declared name; the study's three
demo commands each behave as the study states, with the unresolved-mapper curate
exiting non-zero and writing nothing, the synopsis demo agreeing on two fresh
builds over 41 findings across 31 rounds with 12 empty, and the pilot
verify-rebuild returning `41d640fb`;
`python3 scripts/check_public_front_door.py`,
`python3 scripts/demonstrations.py check --root .` and
`python3 scripts/promise_machine.py sync --check` exit zero;
`python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py` over every
document this step changed exits zero;
`python3 plugins/anamnesis/tests/elenchus.py --step 14 .hexaemeron/elenchus/anamnesis-step-14.json`
exits zero;
`python3 -m unittest plugins.anamnesis.tests.test_s8_scope` is green;
`python3 scripts/run_checks.py --base origin/main` exits zero from a clean
detached snapshot of the committed head;
`python3 plugins/horos/skills/horos/scripts/horos.py check .` exits zero;
`git diff --check` is clean; and
`python3 plugins/hexaemeron/skills/protasis/scripts/design_evidence.py .hexaemeron/design-evidence.json --transition integration`
exits zero, which no push checks because no step remains pending, and which the
step runs anyway so the integrate phase cannot wedge on evidence.

**Files.** Change `plugins/anamnesis/skills/anamnesis/EVOLUTION.md`,
`plugins/anamnesis/skills/anamnesis/SKILL.md`, `plugins/anamnesis/README.md`,
`plugins/anamnesis/AGENTS.md`, root `README.md`,
`plugins/anamnesis/docs/resolved-mapper-study.md`,
`plugins/anamnesis/docs/resolved-mapper-runbook.md`,
`plugins/anamnesis/tests/test_s10_ledger.py` (the `v4.1.0` header assertion moves
into a by-version block), any other first-party document the cold read finds
carrying the stale claim, `.horos/boundary.json` and `.horos/census.json`. Create
`plugins/anamnesis/tests/test_s14_ledger.py`.

**Tests.** Add `plugins/anamnesis/tests/test_s14_ledger.py`: the ledger's header
version is `anamnesis-v5.1.0` and matches its newest row, which is an `evolution`
row; that row's frontier digest recomputes over the exact four-field line
including its final newline; the `v4.1.0` row keeps revision `declared-scope` and
digest `13c730d9f26091188d16c8c640632c21943fe3f85b2c9363c70b8e0ed499965e`; the
`SKILL.md` frontmatter matches the header; the front-door status block names
`anamnesis-v5.1.0`; the `declared-inputs` block holds exactly one row of four
non-empty fields with kind `corpus`, a note within 200 bytes, and no claim that a
corpus in a format the Warden mapper does not read is absent; no live document
under `plugins/anamnesis/` outside `docs/` and the ledger history says the
resolver always runs the Warden mapper or that an assertion records the declared
name; and the two committed documents equal the receipted artefacts byte for
byte. The audit runner contract is
`python3 plugins/anamnesis/tests/elenchus.py --step 14 {report}`, its format is
`elenchus.unittest.v1`, and Warden writes
`.hexaemeron/elenchus/anamnesis-step-14.json`. Also run the study's three demo
commands, the anamnesis suite from the repository root, the root suite from a
clean snapshot, `python3 scripts/promise_machine.py sync --check`, and
`git diff --check`. Expected new focused tests: 8.

**Disciplines.** phylax: none, the step edits documents and reads three
specimens, and it opens no boundary and adds no input class. ephoros: none, the
refusal stream this run extended is unchanged here. metron: none, no budget is
declared and the demo prints its existing baselines. elenchus: the prose
reconciliation is driven by a cold grep rather than by memory of what was
written, so a document the run missed is a test failure rather than an oversight.
hypomnema: the ledger row and the corrected declared input are the durable
records of what this run settled, their home is fixed by the versioning contract,
and the row cites the step 3 decision record rather than restating it.
