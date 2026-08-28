# Runbook: make chunk corpora the first consumer of Ariadne's dataset predicate

Derived from the study receipted at sha256
`4ad10330c89188922fc8f4b0fad650ce2bc098229b254844abe38182dbc4b7fc`. Three steps,
in dependency order. Step 1 scaffolds and publishes the shape; the last step runs
the demo path from the study's problem statement.

Every `python3` below means `/Users/kethcode/.local/bin/python3.13`, the exact
interpreter in `.python-version`. `tests/test_python_contract.py` refuses any
other minor and the ambient interpreter on this machine is 3.12.13.

No step owes the Hexaemeron plugin suite. That suite covers
`plugins/hexaemeron/`, and no step changes a file under it. Its runner is named
in each step's Tests field only to say why it does not apply.

## Step 1: Publish the provenance record shape

**Goal.** Publish the `lemma-corpus-provenance/v1` record shape and its refusals
in Lemma's shared schema, record the decision behind it, and commit the
receipted study and runbook.

**Entry.** Run branch `fiat/409-chunk-corpora-carry-dataset-provenance` at
`7e449ba35e1519d28b33f06225c4c4137b548a23`, with the study receipted at sha256
`4ad10330c89188922fc8f4b0fad650ce2bc098229b254844abe38182dbc4b7fc`. Measured
baselines the step may assume: the root suite runs 460 tests and reports OK;
`plugins/lemma/tests/test_markdown.py` prints 126 checks and 0 failures;
`plugins/lemma/tests/test_solidity.py` prints 33 checks and 0 failures with no
compiler and 142 checks and 0 failures under `--solc solc` reporting
`0.8.35+commit.47b9dedd.Darwin.appleclang`; the Ariadne suite runs 689 tests
with 7 skipped and reports OK; `scripts/promise_machine.py coverage --check`
prints `promises=73 coverage_rows=73 coverage_selected=73`;
`scripts/promise_machine.py check` prints `clean: 15 plugin(s), 15 copy/copies`;
`scripts/portable_promise_machine.py check` and
`plugins/horos/skills/horos/scripts/horos.py check .` both exit 0, the latter
printing `boundary matches the tree`; and
`plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .` exits 0
with all 25 pairs reporting `committed=match`. Lemma's ledger reads
`lemma-v0.1.1`, frontier status `open`, frontier revision
`abi-return-and-mutability`, frontier digest
`2d4f0d7948208fefdca52f4380b3f4c83261917a282256571a2ee611c5d9d36c`. Ariadne's
ledger reads `ariadne-v2.2.0` and is not touched by this run. No container
runtime is available: `docker info` fails and there is no `podman`, so
`plugins/lemma/solc-container` cannot run and every Solidity figure this run
records names the compiler that produced it.

**Exit.** `plugins/lemma/schema.py` exports `PROVENANCE_SCHEMA` holding
`lemma-corpus-provenance/v1`, a `provenance_record(...)` builder and a
`validate_provenance(record)` returning a list of problems in the same shape as
the existing `validate()`. The builder refuses a source ref that is empty or
only whitespace, naming the flag. It strips userinfo from a ref that parses as a
URL and keeps the rest of the URL, following the rule Ariadne's audit finding
S4-R1-02 established at
`plugins/ariadne/scripts/ariadne_lib/scrub.py:100`, implemented locally because
a cross-plugin import would break both the marketplace boundary and the portable
runtime packaging. No field is ever written as the string `unknown`: a compiler
that does not apply is recorded as an object carrying `applicable` false and a
reason, and a compiler that applies but was not gated records the reported
version with a null pin beside a stated reason. A gated compiler records the pin
as a prefix pin with the exact reported version beside it, because
`plugins/lemma/chunkers/solidity.py:517` compares with `startswith`. `stamp()` is
unchanged and `chunk()` is untouched, so the assertion at
`plugins/lemma/tests/test_solidity.py:366` that the chunker leaves provenance
unset still holds. `plugins/lemma/INVARIANTS.md` extends I6 to name the record,
the two files a delivered corpus holds and the four values the record carries.
`docs/decisions/ADR-042-record-corpus-provenance-beside-the-chunks.md` records
the sidecar decision with the three rejected options and the marketplace
boundary that rules out Lemma writing a statement. The receipted study and this
runbook are committed under `plugins/lemma/docs/`. No chunker behaviour changes
in this step and no corpus is written differently, so the plugin's public
commands still behave exactly as they did at entry. Prove the exit with
`python3 plugins/lemma/tests/test_solidity.py`;
`python3 plugins/lemma/tests/test_solidity.py --solc solc`;
`python3 plugins/lemma/tests/test_markdown.py`;
`python3 -m unittest discover -s tests`;
`python3 scripts/promise_machine.py check`;
`python3 scripts/promise_machine.py coverage --check`;
`python3 scripts/portable_promise_machine.py sync`;
`python3 scripts/portable_promise_machine.py check`;
`python3 plugins/horos/skills/horos/scripts/horos.py scan . --write`;
`python3 plugins/horos/skills/horos/scripts/horos.py check .`;
`python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests`;
`python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests`;
`python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents/skills/promise-machine/SKILL.md .agents/skills/promise-machine/PORTABLE.md plugins docs`;
`python3 "$PLUGIN_ROOT/skills/protasis/scripts/protasis.py" --study plugins/lemma/docs/corpus-provenance-study.md`;
`python3 "$PLUGIN_ROOT/skills/protasis/scripts/protasis.py" plugins/lemma/docs/corpus-provenance-runbook.md`;
`python3 "$PLUGIN_ROOT/skills/imprimatur/scripts/imprimatur.py" plugins/lemma/INVARIANTS.md` and one further invocation per changed prose file;
`python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py plugins/lemma/INVARIANTS.md` and one further invocation per changed prose file, since Brevitas takes a single positional path;
`git diff --check`; `rm -rf .elenchus uv.lock`; and `git status --short` printing
nothing.

**Files.** Create `plugins/lemma/docs/corpus-provenance-study.md`, the receipted
study committed as this run's change-control boundary. Create
`plugins/lemma/docs/corpus-provenance-runbook.md`, this runbook, for the same
reason. Create
`docs/decisions/ADR-042-record-corpus-provenance-beside-the-chunks.md`, because
putting provenance in a sidecar rather than in the `Chunk` type is expensive to
reverse once a consumer reads it. Change `plugins/lemma/schema.py`, which gains
the record shape, its builder, its validator and its refusals. Change
`plugins/lemma/INVARIANTS.md`, whose I6 is the published statement of what
provenance a Lemma corpus carries. Change
`plugins/lemma/tests/test_solidity.py`, which gains the compiler-free shape
guards. The remaining paths are written by sanctioned commands rather than by
hand: `python3 scripts/portable_promise_machine.py sync` rewrites the mirror
under `.agents/skills/promise-machine/runtime/`, because
`scripts/portable_promise_machine.py:108-113` omits only a plugin's
`.claude-plugin`, `.codex-plugin`, `audit` and `tests` directories, so
`schema.py`, `INVARIANTS.md` and everything under `plugins/lemma/docs/` are
mirrored while `plugins/lemma/tests/` is not; and
`python3 plugins/horos/skills/horos/scripts/horos.py scan . --write` rewrites
both `.horos/boundary.json` and `.horos/candidates.json`, because the boundary
carries one entry for that runtime directory recording its byte and file counts
and the sync moves them. No other path is in scope for this step without a
receipted amendment to the study.

**Tests.** Red first, in this order. One: a record built from a source ref that
is empty or only whitespace is refused, which fails against `schema.py` at entry
because no builder exists there, and turns green when the builder raises naming
the flag. Two: a ref spelled as a URL carrying `user:token@` loses its userinfo
and keeps the rest, which fails against a builder that stores the ref verbatim
and turns green when the strip lands. Three: no field of a built record equals
the string `unknown`, which fails against a builder that defaults an absent
compiler to that word and turns green when the absence becomes an object
carrying `applicable` false and a reason. Four: an ungated compiler records the
reported version with a null pin and a stated reason, which fails against a
builder that fills the pin from the reported version. Five: a gated compiler
records the pin as a prefix pin with the reported version beside it, which fails
against a builder writing a bare `pinned` flag. Six: the validator returns every
problem rather than the first, which fails against a validator that returns
early and turns green when it accumulates the way `validate()` does. Seven: the
existing assertion at `plugins/lemma/tests/test_solidity.py:366` that the
chunker leaves `source_ref` and `corpus_build_id` unset is kept unchanged and
must still pass, because the shape lands above `chunk()` and not inside it. All
seven are compiler-free and are called from `main()` before the `if args.solc`
blocks, so they run in the no-compiler set. Counts: `test_solidity.py` moves
from 33 checks to 33 plus the number of new cases with no compiler, and from 142
to 142 plus the same number under `--solc solc`; no case is removed, so both
printed check counts must be strictly greater than their entry values and both
printed failure counts must be 0. `test_markdown.py` stays at 126 checks and 0
failures, because this step adds no Markdown case. The root suite stays at 460
tests and OK, because this step adds no test method: the new decision record is
read by the five existing cases in `tests/test_decision_records.py` rather than
by a generated one. The Ariadne suite stays at 689 tests with 7 skipped, because
no file under `plugins/ariadne/` changes. Elenchus runner contract: none is
available for this step's guards, and this is the case the contract's fallback
covers. `plugins/lemma/tests/test_solidity.py` and `test_markdown.py` are
bespoke printers built on the `check(name, ok, detail)` harness at
`test_solidity.py:39`; they emit no `unittest-json-v1` report, and no
repository-owned emitter wraps them or the root suite at this base. The three
runners that accept `--elenchus-report` are
`plugins/lazarus/tests/run_tests.py`, `plugins/alexandria/tests/run_tests.py`
and `plugins/hexaemeron/tests/run_tests.py`, and none of them covers Lemma or
`tests/`; the Hexaemeron runner is named here only to record that it reports on
`plugins/hexaemeron/`, which this step does not touch. The exact command whose
output a fix records beside the verdict is
`python3 plugins/lemma/tests/test_solidity.py --solc solc`, and its captured
output is written to `.elenchus/lemma-step-1.txt`.

**Disciplines.** phylax: this step writes the first code that handles
`--source-ref`, so the credential strip carried from Ariadne's S4-R1-02 and the
refusal of a blank ref are built and guarded here, before any caller supplies
one. ephoros: the record is what an operator reads after the run, so this step
settles what it may say when a value is absent, which is the
`unknown-written-as-a-value` entry in the study's register. metron: none, and
the reason is that this step adds a builder and a validator over values already
held in memory and makes no performance claim; the study's only budget is the
one-line size of the emitted file, which step 2 measures. elenchus: the red-first
order above, and the step stops rather than proceeding if either Lemma suite or
the root suite reports a failure. hypomnema: the sidecar decision earns
ADR-042, because moving those fields into `Chunk` later would change the type
every consumer reads.

## Step 2: Emit provenance from both chunkers

**Goal.** Make both chunkers write the provenance record beside their chunks,
stamp the corpus, refuse an output with no source ref, and re-record the stale
Markdown baseline.

**Entry.** Step 1's exit state: the run branch with
`plugins/lemma/schema.py` exporting the record shape, its builder and its
validator; `plugins/lemma/INVARIANTS.md` extended at I6; ADR-042 committed; the
study and runbook committed under `plugins/lemma/docs/`; the mirror and the
boundary regenerated; every command in step 1's exit list green.

**Exit.** `plugins/lemma/chunkers/solidity.py` and
`plugins/lemma/chunkers/markdown.py` each accept `--source-ref REF` and an
optional `--provenance PATH`, defaulting to `provenance.jsonl` beside the file
`--out` names. Either chunker invoked with `--out` and no `--source-ref` exits
non-zero, names the missing flag and writes nothing, because a corpus delivered
with a null origin is the defect this run exists to close. Neither chunker
writes the record before the chunks are on disk and past the existing schema
refusal at `plugins/lemma/chunkers/solidity.py:1102-1104` and
`plugins/lemma/chunkers/markdown.py:1167-1168`, and a run that cannot produce a
complete record refuses before writing anything, so no directory is left that a
capture would read as a whole corpus. The record is one line of JSON, so
Ariadne's capture derives its count without `--record-count`; the study's budget
is met when `wc -l` over the emitted file prints 1. The recorded
`corpus_build_id` is recomputed from the chunks actually written and a
disagreement fails the build. Both chunkers call `schema.stamp()` from the
pipeline above `chunk()`, so every emitted chunk carries `source_ref` and
`corpus_build_id` while `chunk()` still leaves both unset. The Solidity record
carries the `--solc` argument as given, the version the compiler reported for
itself, and the pin with its prefix nature named; the Markdown record carries
the compiler absence with its reason and no compiler version at all.
`plugins/lemma/baseline/regenerate` passes a literal source ref naming the
synthetic corpus, so the script keeps working without reaching for git and a
dirty tree cannot turn the ref into a false claim. The Markdown block of the
recorded baseline in `plugins/lemma/INVARIANTS.md` is re-recorded from a run
anyone can repeat, replacing 38 chunks, 34 placed in the hierarchy, median 141,
p99 568 and maximum 568 with the figures the command prints; the Solidity block
is left as recorded and keeps naming solc 0.8.25, because no container runtime
is available here and a figure taken from another compiler would silently
replace one taken from the pin. `plugins/lemma/README.md` states the two flags
and what the record carries. Prove the exit with
`python3 plugins/lemma/chunkers/markdown.py --root plugins/lemma/baseline/docs --summary SUMMARY.md --exclude SUMMARY.md --out "$W/corpus/chunks.jsonl"` refusing before the flag is supplied and succeeding after it;
`test "$(wc -l < "$W/corpus/provenance.jsonl")" -eq 1`;
`python3 plugins/lemma/tests/test_solidity.py`;
`python3 plugins/lemma/tests/test_solidity.py --solc solc`;
`python3 plugins/lemma/tests/test_markdown.py`;
`python3 -m unittest discover -s tests`;
`python3 scripts/promise_machine.py check`;
`python3 scripts/promise_machine.py coverage --check`;
`python3 scripts/portable_promise_machine.py sync`;
`python3 scripts/portable_promise_machine.py check`;
`python3 plugins/horos/skills/horos/scripts/horos.py scan . --write`;
`python3 plugins/horos/skills/horos/scripts/horos.py check .`;
`python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests`;
`python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests`;
`python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents/skills/promise-machine/SKILL.md .agents/skills/promise-machine/PORTABLE.md plugins docs`;
`python3 "$PLUGIN_ROOT/skills/imprimatur/scripts/imprimatur.py" plugins/lemma/INVARIANTS.md` and one further invocation per changed prose file;
`python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py plugins/lemma/INVARIANTS.md` and one further invocation per changed prose file;
`git diff --check`; `rm -rf .elenchus uv.lock`; and `git status --short` printing
nothing.

**Files.** Change `plugins/lemma/chunkers/solidity.py`, which gains the two
flags, the refusal, the compiler block and the stamp above `chunk()`. Change
`plugins/lemma/chunkers/markdown.py`, which gains the same flags, the same
refusal, the compiler absence with its reason and the same stamp. Change
`plugins/lemma/baseline/regenerate`, the only in-repository caller passing
`--out`, which must supply a literal ref. Change
`plugins/lemma/INVARIANTS.md`, whose Markdown baseline block no longer matches
the command. Change `plugins/lemma/README.md`, which states the flags a user
types. Change `plugins/lemma/tests/test_solidity.py` and
`plugins/lemma/tests/test_markdown.py`, which gain the emitter guards. The
remaining paths are written by sanctioned commands:
`python3 scripts/portable_promise_machine.py sync` rewrites
`.agents/skills/promise-machine/runtime/`, because both chunkers, the baseline
script, `INVARIANTS.md` and `README.md` are mirrored; and
`python3 plugins/horos/skills/horos/scripts/horos.py scan . --write` rewrites
both `.horos/boundary.json` and `.horos/candidates.json`. No other path is in
scope for this step without a receipted amendment to the study.

**Tests.** Red first, in this order. One: a chunker given `--out` and no
`--source-ref` exits non-zero and leaves the output path absent, which fails
against both chunkers at entry because they write on success and turns green
when the refusal lands before any write. Two: a successful run leaves exactly
two files in the output directory, which fails against a chunker that writes one
and turns green when the record is written after the chunks. Three: the recorded
`corpus_build_id` equals a digest recomputed from the written `chunks.jsonl`,
which fails against an identifier taken before deduplication and turns green
when it is recomputed from the file. Four: every emitted chunk carries the
stamped ref and build identifier, which fails against the current pipeline that
never calls `stamp()`. Five: `chunk()` still leaves both fields unset, the
existing assertion at `test_solidity.py:366`, which must keep passing and is the
guard that the stamp did not migrate into the chunker. Six: a Markdown run
records the compiler absence with its reason and carries no compiler version,
which fails against a record that writes a null. Seven, compiler-dependent: an
ungated Solidity run records the reported version with no pin, and a run gated
with `--expect-solc` records a prefix pin with the reported version beside it;
both fail against a record that reports a bare pinned flag. Cases one to six are
compiler-free; case seven runs only under `--solc solc`. Counts: both Lemma
suites gain cases, so `test_markdown.py` must print more than 126 checks and
`test_solidity.py` more than its step 1 entry count in both the no-compiler and
the `--solc solc` runs, with 0 failures in every run and no case removed. The
root suite stays at 460 tests and OK, and the Ariadne suite stays at 689 tests
with 7 skipped, because neither `tests/` nor `plugins/ariadne/` changes. The
re-recorded Markdown baseline is prose rather than a guard, so it is proved by
running
`python3 plugins/lemma/chunkers/markdown.py --root plugins/lemma/baseline/docs --summary SUMMARY.md --exclude SUMMARY.md --source-ref '<literal>' --out "$W/corpus/chunks.jsonl"`
and comparing its printed chunk count, placement count, median, p99 and maximum
with the block, which at entry disagree at 39 against 38, 35 against 34, 184
against 141, 1010 against 568 and 1010 against 568. Elenchus runner contract:
none is available, for the reason step 1 records; the exact command whose output
a fix records beside the verdict is
`python3 plugins/lemma/tests/test_solidity.py --solc solc` followed by
`python3 plugins/lemma/tests/test_markdown.py`, and their captured output is
written to `.elenchus/lemma-step-2.txt`. The Hexaemeron runner does not apply,
because no file under `plugins/hexaemeron/` changes.

**Disciplines.** phylax: this is the step where `--source-ref` reaches disk, so
the strip and the refusal built in step 1 are exercised through both command
lines here, and the second file written under one `--out` is the new filesystem
boundary the study names as `partial-corpus-write`. ephoros: the four operator
questions the study lists are answered by this step's printed lines, and the
compiler line has to distinguish a container invocation from a binary on the
path, since a record that cannot tell them apart is the same silence as writing
`unknown`. metron: the study's one budget applies here, and it is met when
`wc -l` over the emitted record prints 1, because Ariadne derives a record count
only for line-delimited files. elenchus: the red-first order above; the step
stops on any Lemma or root failure, and the recomputed build identifier is the
guard that fails closed rather than shipping a record describing chunks nobody
wrote. hypomnema: none earns a new record, because ADR-042 in step 1 already
holds the decision this step implements and the flag contract lives in
`README.md` and in the refusal message itself.

## Step 3: Close the seam and record the run

**Goal.** Print the matching capture flags, document the handoff, add the
provenance promise, append the generation row, and demonstrate the whole path
through Ariadne.

**Entry.** Step 2's exit state: both chunkers writing the record and stamping the
corpus, `--out` refusing without a ref, `baseline/regenerate` updated, the
Markdown baseline re-recorded, `README.md` stating the flags, the mirror and the
boundary regenerated, and every command in step 2's exit list green.

**Exit.** Both chunkers print, beside the existing `written` line, the
`capture-dataset` producer, coverage and input flags matching the corpus just
written, so the operator copies rather than composes them; the printed coverage
reads the source unit dimension with bounds over the sorted source units the
input declared, and names the excluded units as gaps with the pattern that
excluded them, because an interval printed with no gaps reads as complete.
`plugins/lemma/skills/lemma/SKILL.md` states the handoff to
`python3 plugins/ariadne/scripts/ariadne.py capture-dataset`, states that Lemma
writes no statement and signs nothing, and carries a new
`lemma-corpus-provenance` Promise Machine contract whose evidence classes are
`checked`, `recorded` and `recomputed` and whose boundary says what the record
does not establish: that the ref names a real object, that the ref was clean,
that the compiler was honest about its own version, that an ungated compiler was
the intended one, or that a citation out of the corpus is faithful.
`plugins/lemma/AGENTS.md` names the handoff in the runtime contract, and
`plugins/lemma/README.md` shows the two commands end to end.
`plugins/lemma/skills/lemma/EVOLUTION.md` gains one generation row reading
`lemma-v0.2.1` on the `generation` axis with frontier revision
`abi-return-and-mutability` and frontier digest
`2d4f0d7948208fefdca52f4380b3f4c83261917a282256571a2ee611c5d9d36c`, and its
`- Current version:` line becomes `lemma-v0.2.1`; the `- Frontier status:`,
`- Frontier revision:`, `- Current frontier:` and `- Next Fiat job:` lines are
unchanged byte for byte, because
`tests/test_evolution_contract.py:183-203` recomputes the digest from those four
values joined with a pipe and a trailing newline.
`plugins/lemma/skills/lemma/SKILL.md`'s frontmatter version becomes `0.2.1`. No
row is added to any Ariadne ledger and no file under `plugins/ariadne/` changes.
The Lemma plugin package version stays `0.1.2` across both manifests, the
marketplace listing and `tests/test_version_propagation.py`, because the study
lists a package bump as ask-first and no answer was given; a bump arrives as a
receipted amendment rather than as a runbook decision. The demo path from the
study's problem statement runs end to end and `ariadne verify` exits 0 printing
seven gate passes and three check passes, with `provenance.jsonl` listed among
`dataset_subjects` carrying a digest and a record count of 1. Prove the exit with
the study's demo path, ending in
`python3 plugins/ariadne/scripts/ariadne.py verify "$W/statement.json"`;
`python3 plugins/lemma/tests/test_solidity.py`;
`python3 plugins/lemma/tests/test_solidity.py --solc solc`;
`python3 plugins/lemma/tests/test_markdown.py`;
`python3 -m unittest discover -s tests`;
`python3 -m unittest discover -s plugins/ariadne/tests -t plugins/ariadne`;
`python3 scripts/promise_machine.py check`;
`python3 scripts/promise_machine.py coverage --check` printing
`promises=74 coverage_rows=74 coverage_selected=74`;
`python3 scripts/portable_promise_machine.py sync`;
`python3 scripts/portable_promise_machine.py check`;
`python3 plugins/horos/skills/horos/scripts/horos.py scan . --write`;
`python3 plugins/horos/skills/horos/scripts/horos.py check .`;
`python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests`;
`python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests`;
`python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents/skills/promise-machine/SKILL.md .agents/skills/promise-machine/PORTABLE.md plugins docs`;
`python3 "$PLUGIN_ROOT/skills/imprimatur/scripts/imprimatur.py" plugins/lemma/skills/lemma/SKILL.md` and one further invocation per changed prose file;
`python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py plugins/lemma/skills/lemma/SKILL.md` and one further invocation per changed prose file;
`git diff --check`; `rm -rf .elenchus uv.lock`; and `git status --short` printing
nothing.

**Files.** Change `plugins/lemma/chunkers/solidity.py` and
`plugins/lemma/chunkers/markdown.py`, which gain the printed capture flags.
Change `plugins/lemma/skills/lemma/SKILL.md`, which gains the handoff, the new
promise and the frontmatter version. Change
`plugins/lemma/skills/lemma/EVOLUTION.md`, which gains the generation row and
its current-version line. Change `plugins/lemma/AGENTS.md`, the runtime contract
an agent reads before running the skill, which must name the new required flag
and the handoff. Change `plugins/lemma/README.md`, which shows the two commands
end to end. Change `tests/promise_machine_coverage.json`, which gains one row
and its five case entries under `evidence`. Change
`tests/test_promise_machine_contract.py`, whose frozen Lemma promise set at
lines 555 to 559 must name the new promise. Change
`plugins/lemma/tests/test_solidity.py` and
`plugins/lemma/tests/test_markdown.py`, which gain the printed-flag guards and
the selectors the coverage entries name. The remaining paths are written by
sanctioned commands: `python3 scripts/portable_promise_machine.py sync` rewrites
`.agents/skills/promise-machine/runtime/`, because the chunkers, `SKILL.md`,
`EVOLUTION.md`, `AGENTS.md` and `README.md` are all mirrored; and
`python3 plugins/horos/skills/horos/scripts/horos.py scan . --write` rewrites
both `.horos/boundary.json` and `.horos/candidates.json`.
`python3 scripts/promise_machine.py sync` is not run and no
`plugins/*/PROMISE_MACHINE.md` copy changes, because the root law is untouched
and those copies mirror the law rather than a skill's promises. No other path is
in scope for this step without a receipted amendment to the study.

**Tests.** Red first, in this order. One: the printed capture flags name the
file the chunker actually wrote and the include pattern it actually used, which
fails against both chunkers at entry because they print nothing of the kind.
Two: `python3 scripts/promise_machine.py coverage --check` fails once
`lemma-corpus-provenance` is declared in `SKILL.md` and no row names it,
reporting 74 promises against 73 rows, and turns green when the row and its five
case entries land. Three:
`python3 -m unittest tests.test_promise_machine_contract` fails until the frozen
Lemma set at lines 555 to 559 names the new promise. Four:
`python3 -m unittest tests.test_evolution_contract` fails until the generation
row and the frontmatter agree, and fails again if any of the four digested
header lines is edited, because the digest is recomputed from them rather than
read. Five: the demo path is the last guard and is a command rather than a test
case, ending in `ariadne verify` exiting 0. Counts: both Lemma suites gain cases
and must print more checks than their step 2 entry counts with 0 failures. The
root suite stays at 460 tests and OK, because the coverage row and the frozen
set are data read by existing cases rather than new test methods. The Ariadne
suite stays at 689 tests with 7 skipped and is run here because the demo path
exercises the seam, so a regression in the tool this step depends on has to be
visible before the demonstration is believed. Elenchus runner contract: none is
available, for the reason step 1 records; the exact command whose output a fix
records beside the verdict is
`python3 plugins/lemma/tests/test_solidity.py --solc solc` followed by
`python3 plugins/lemma/tests/test_markdown.py` and
`python3 -m unittest discover -s tests`, and their captured output is written to
`.elenchus/lemma-step-3.txt`. The Hexaemeron runner does not apply, because no
file under `plugins/hexaemeron/` changes.

**Disciplines.** phylax: none new is opened, and the reason is that this step
prints and documents rather than reading anything fresh; the printed flags echo
values already stripped and refused in steps 1 and 2, and the guard is that the
print carries no value the record does not. ephoros: this step owns the third
operator question the study lists, which is what to type into `capture-dataset`,
and answering it in the chunker's own output is what removes the transcription
failure the seam would otherwise carry. metron: none, and the reason is that
this step adds printed lines and prose and makes no performance claim; the only
budget the study states was measured in step 2. elenchus: the red-first order
above, and the step stops if `coverage --check`, the contract test or the
evolution test reports a failure, because each of those is the mechanical guard
on a claim this step makes about itself. hypomnema: the new
`lemma-corpus-provenance` promise and the `lemma-v0.2.1` generation row are the
two records this step owes, the first because it authorises a transition the
existing three promises do not, and the second because the evolution contract
requires one row for behaviour that changed without advancing the frontier.
### Amendment -- 2026-08-28

**What changed.** Complete replacement Exit: `plugins/lemma/schema.py` exports `PROVENANCE_SCHEMA` holding
`lemma-corpus-provenance/v1`, a `provenance_record(...)` builder and a
`validate_provenance(record)` returning a list of problems in the same shape as
the existing `validate()`. The builder refuses a source ref that is empty or
only whitespace, naming the flag. It strips userinfo from a ref that parses as a
URL and keeps the rest of the URL, following the rule Ariadne's audit finding
S4-R1-02 established at
`plugins/ariadne/scripts/ariadne_lib/scrub.py:100`, implemented locally because
a cross-plugin import would break both the marketplace boundary and the portable
runtime packaging. No field is ever written as the string `unknown`: a compiler
that does not apply is recorded as an object carrying `applicable` false and a
reason, and a compiler that applies but was not gated records the reported
version with a null pin beside a stated reason. A gated compiler records the pin
as a prefix pin with the exact reported version beside it, because
`plugins/lemma/chunkers/solidity.py:517` compares with `startswith`. `stamp()` is
unchanged and `chunk()` is untouched, so the assertion at
`plugins/lemma/tests/test_solidity.py:366` that the chunker leaves provenance
unset still holds. `plugins/lemma/INVARIANTS.md` extends I6 to name the record,
the two files a delivered corpus holds and the four values the record carries.
`docs/decisions/ADR-042-record-corpus-provenance-beside-the-chunks.md` records
the sidecar decision with the three rejected options and the marketplace
boundary that rules out Lemma writing a statement. The receipted study and this
runbook are committed as flat files under `docs/`, where the study's one
relative link resolves from the copy as it does from the receipt. No chunker behaviour changes
in this step and no corpus is written differently, so the plugin's public
commands still behave exactly as they did at entry. Prove the exit with
`python3 plugins/lemma/tests/test_solidity.py`;
`python3 plugins/lemma/tests/test_solidity.py --solc solc`;
`python3 plugins/lemma/tests/test_markdown.py`;
`python3 -m unittest discover -s tests`;
`python3 scripts/promise_machine.py check`;
`python3 scripts/promise_machine.py coverage --check`;
`python3 scripts/portable_promise_machine.py sync`;
`python3 scripts/portable_promise_machine.py check`;
`python3 plugins/horos/skills/horos/scripts/horos.py scan . --write`;
`python3 plugins/horos/skills/horos/scripts/horos.py check .`;
`python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests`;
`python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests`;
`python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents/skills/promise-machine/SKILL.md .agents/skills/promise-machine/PORTABLE.md plugins docs`;
`python3 "$PLUGIN_ROOT/skills/protasis/scripts/protasis.py" --study docs/lemma-corpus-provenance-study.md`;
`python3 "$PLUGIN_ROOT/skills/protasis/scripts/protasis.py" docs/lemma-corpus-provenance-runbook.md`;
`python3 "$PLUGIN_ROOT/skills/imprimatur/scripts/imprimatur.py" plugins/lemma/INVARIANTS.md` and one further invocation per changed prose file;
`python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py plugins/lemma/INVARIANTS.md` and one further invocation per changed prose file, since Brevitas takes a single positional path;
`git diff --check`; `rm -rf .elenchus uv.lock`; and `git status --short` printing
nothing.

Complete replacement Files: Create `docs/lemma-corpus-provenance-study.md`, the receipted
study committed as this run's change-control boundary. Create
`docs/lemma-corpus-provenance-runbook.md`, this runbook, for the same
reason. Create
`docs/decisions/ADR-042-record-corpus-provenance-beside-the-chunks.md`, because
putting provenance in a sidecar rather than in the `Chunk` type is expensive to
reverse once a consumer reads it. Change `plugins/lemma/schema.py`, which gains
the record shape, its builder, its validator and its refusals. Change
`plugins/lemma/INVARIANTS.md`, whose I6 is the published statement of what
provenance a Lemma corpus carries. Change
`plugins/lemma/tests/test_solidity.py`, which gains the compiler-free shape
guards. The remaining paths are written by sanctioned commands rather than by
hand: `python3 scripts/portable_promise_machine.py sync` rewrites the mirror
under `.agents/skills/promise-machine/runtime/`, because
`scripts/portable_promise_machine.py:108-113` omits only a plugin's
`.claude-plugin`, `.codex-plugin`, `audit` and `tests` directories, so
`schema.py`, `INVARIANTS.md` and everything under `plugins/lemma/docs/` are
mirrored while `plugins/lemma/tests/` is not; and
`python3 plugins/horos/skills/horos/scripts/horos.py scan . --write` rewrites
both `.horos/boundary.json` and `.horos/candidates.json`, because the boundary
carries one entry for that runtime directory recording its byte and file counts
and the sync moves them. No other path is in scope for this step without a
receipted amendment to the study.

**Why.** The receipted study carries one relative link, to the file recording
the interpreter pin, and a relative link resolves from the directory holding
it. A byte-identical copy under `plugins/lemma/docs/` therefore points at a
path that does not exist, and the shipped-tree lint walks every plugin and
refuses it, which turns the root suite red on a copy this step is required to
make byte for byte. The receipted bytes cannot change, so the copies move to
the depth where the same bytes carry a resolving pointer. The study records the
same correction in its own amendment of this date. Nothing else in the step
moves: the same two artefacts are committed, checked by the same two Protasis
invocations, for the same reason.

**Steps touched.** Step 1.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit
holds. Step 3: entry holds; exit holds.
### Amendment -- 2026-08-28

**What changed.** Complete replacement Entry: Step 1's exit state: the run branch with
`plugins/lemma/schema.py` exporting the record shape, its builder and its
validator; `plugins/lemma/INVARIANTS.md` extended at I6; ADR-042 committed; the
study and runbook committed as flat files under `docs/`, where the study's one
relative link resolves; the mirror and the
boundary regenerated; every command in step 1's exit list green.

**Why.** This step's entry described the state step 1 leaves behind, and the
first amendment of this date moved that state: the committed study and runbook
are flat files under `docs/`, because a relative link resolves from the
directory holding the file and the receipted bytes could not change. The entry
now names where the copies actually are, so a check against it reads the tree
rather than a superseded location. Nothing else about the entry moves, and no
exit, file, test or discipline changes.

**Steps touched.** Step 2.

**Still holding.** Step 2: entry holds; exit holds. Step 3: entry holds; exit
holds.
### Amendment -- 2026-08-28

**What changed.** Complete replacement Files: Change `plugins/lemma/chunkers/solidity.py` and
`plugins/lemma/chunkers/markdown.py`, which gain the printed capture flags.
Change `plugins/lemma/skills/lemma/SKILL.md`, which gains the handoff, the new
promise and the frontmatter version. Change
`plugins/lemma/skills/lemma/EVOLUTION.md`, which gains the generation row and
its current-version line. Change `plugins/lemma/AGENTS.md`, the runtime contract
an agent reads before running the skill, which must name the new required flag
and the handoff. Change `plugins/lemma/README.md`, which shows the two commands
end to end. Change `tests/promise_machine_coverage.json`, which gains one row
and its five case entries under `evidence`. Change
`tests/test_promise_machine_contract.py`, whose frozen Lemma promise set at
lines 555 to 559 must name the new promise. Change
`plugins/lemma/tests/test_solidity.py` and
`plugins/lemma/tests/test_markdown.py`, which gain the printed-flag guards and
the selectors the coverage entries name. The remaining paths are written by
sanctioned commands: `python3 scripts/portable_promise_machine.py sync` rewrites
`.agents/skills/promise-machine/runtime/`, because the chunkers, `SKILL.md`,
`EVOLUTION.md`, `AGENTS.md` and `README.md` are all mirrored; and
`python3 plugins/horos/skills/horos/scripts/horos.py scan . --write` rewrites
both `.horos/boundary.json` and `.horos/candidates.json`.
`python3 scripts/promise_machine.py sync` is not run and no
`plugins/*/PROMISE_MACHINE.md` copy changes, because the root law is untouched
and those copies mirror the law rather than a skill's promises. Change `docs/lemma-corpus-provenance-runbook.md`, the committed copy of this
runbook, which has been one amendment behind the receipt since step 1 committed
it: every amendment lands after the step that would have carried it, and this is
the last step, so it is the only place the copy can be returned to the receipted
bytes. No other path is in scope for this step without a receipted amendment to
the study.

**Why.** The committed copy of the runbook is a strict prefix of the receipted
bytes, 36,354 against 37,429, and has been since step 1 committed it: each
amendment lands after the step that would have carried it, so no step could
have kept the copy current at the moment it was made. This is the last step and
the only one that can close the gap, and a committed copy that does not match
the artefact it claims to be is the same defect this delivery argues against one
level up. The study copy is unchanged and already byte-identical.

**Steps touched.** Step 3.

**Still holding.** Step 3: entry holds; exit holds.
