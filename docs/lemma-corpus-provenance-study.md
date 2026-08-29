# Study: make chunk corpora the first consumer of Ariadne's dataset predicate

Topic: skills#409, `lemma-1`. Base ref `7e449ba35e1519d28b33f06225c4c4137b548a23`
on branch `fiat/409-chunk-corpora-carry-dataset-provenance`.

Assuming, unless corrected:

1. The exact interpreter in [`.python-version`](../.python-version), which reads
   `3.13.15`, with the standard library only. `tests/test_python_contract.py`
   refuses any other minor, and the ambient `python3` on this machine is 3.12.13.
2. The owning skill is `lemma`, whose ledger is
   `plugins/lemma/skills/lemma/EVOLUTION.md` at `lemma-v0.1.1`. The filing's
   `chunk-v0.1.0` and its `skills/chunk` path are historical; ADR-013 renamed the
   canonical skill.
3. This is generation work. It owes one generation row on Lemma's ledger and
   must not touch the held frontier. The held job stays `abi-return-and-mutability`.
4. Ariadne is read, not changed. No row is owed on `ariadne-v2.2.0`. Section 4
   states what would change that.
5. No Solidity ships. The security suite is waived for this run and the receipt
   records why. Phylax, Ephoros and Hypomnema still run.
6. A container runtime is not available in this environment (`docker info` fails,
   no `podman`), so `plugins/lemma/solc-container` cannot run here. A local
   `solc` is present at `/Users/kethcode/.local/bin/solc`, reporting
   `0.8.35+commit.47b9dedd.Darwin.appleclang`. Every Solidity figure below was
   produced with that binary and says so.
7. `--source-ref` is a string the operator asserts. Nothing in this delivery
   resolves it, fetches it, or checks that it names a real object.

I will proceed on these unless corrected.

## 1. Problem statement

**What is being built.** A delivered Lemma corpus carries no checkable record of
what produced it. This run makes each chunker write one provenance record beside
its `chunks.jsonl`, inside the directory Ariadne's `capture-dataset` walks, so
that the source ref, the compiler identity, the chunker version and the input
digests are bound by digest into a `https://ariadne.wildcat.finance/dataset/v1`
statement that `ariadne verify` accepts.

**For whom.** Two readers. The person who receives a `chunks.jsonl` and has to
decide whether a citation out of it can be trusted, and the person rebuilding a
corpus two years later who has to know which compiler produced the AST the chunk
boundaries came from.

**What a working prototype means here.** Not a new predicate, not a new
statement writer inside Lemma. It means: run a chunker, run `capture-dataset`
over the directory it wrote, run `verify`, and read the four values back out of
the statement's subjects.

**The demo path that proves it.** From the repository root, with the pinned
interpreter:

```bash
python3 plugins/lemma/baseline/standard_input.py \
  --src plugins/lemma/baseline/solidity/src --out "$W/standard-input.json"
python3 plugins/lemma/chunkers/solidity.py \
  --input "$W/standard-input.json" --solc solc --expect-solc 0.8.35 \
  --include 'src/**' --source-ref 'wildcat-finance/skills@<sha>:plugins/lemma/baseline/solidity/src' \
  --out "$W/corpus/chunks.jsonl"
python3 plugins/ariadne/scripts/ariadne.py capture-dataset \
  --release "$W/corpus" --name lemma-baseline-corpus-v0 \
  --coverage-dimension 'source unit' --coverage-start 1 --coverage-end 4 \
  --producer-tool lemma --producer-version 0.2.1 \
  --producer-command python3 --producer-command plugins/lemma/chunkers/solidity.py \
  --input 'name=solc standard JSON,locator=<ref>,file='"$W/standard-input.json" \
  --first-release-reason 'the first corpus built from this input' \
  --out "$W/statement.json"
python3 plugins/ariadne/scripts/ariadne.py verify "$W/statement.json"
```

Success is: both chunker commands exit 0, `verify` exits 0 and prints seven gate
passes plus three check passes, and the statement's `dataset_subjects` lists
`provenance.jsonl` with a digest and `record_count` of 1. The same run with
`--out` and no `--source-ref` exits non-zero and writes nothing.

## 2. Prior art

### In this repository

**The chunkers and the shared schema.** `plugins/lemma/schema.py:72-80` already
declares a provenance tier on `Chunk`: `corpus_build_id`, `source_ref`,
`protocol_version`, `deployment_status`, `effective_date`, `doc_version`,
`supersedes`, all defaulting to `None`. `schema.py:204-215` defines `stamp()`,
whose docstring says the pipeline owns these values because "letting each one
guess is how two chunks from one build end up claiming different origins".
`plugins/lemma/INVARIANTS.md:42-46` states the same thing as invariant I6.

Nothing calls `stamp()` in production. A repository-wide search for `stamp(`
returns two hits outside the definition, both in
`plugins/lemma/tests/test_solidity.py:369` and `:374`. Neither chunker's
`main()` stamps anything; `plugins/lemma/chunkers/solidity.py:1098-1101` and
`plugins/lemma/chunkers/markdown.py:1163-1166` both write
`json.dumps(c.to_dict())` straight from the chunker's output.

Reproduced at this base with the pinned interpreter:

```text
python3 chunkers/markdown.py --root baseline/docs --summary SUMMARY.md \
  --exclude SUMMARY.md --out $W/corpus/chunks.jsonl
  -> 39 records, 39 with both source_ref and corpus_build_id null
```

The Solidity side is the same. Every record carries the twenty keys
`schema.py` declares, and the seven provenance keys are `null` on all of them.

**The compiler is read and then thrown away.**
`plugins/lemma/chunkers/solidity.py:969` calls
`require_solc_version(solc, expect_solc)` and binds the result to a local named
`version`. Line 970 prints it. Nothing else in the function uses it. The printed
line for an ungated run reads:

```text
  compiler      : 0.8.35+commit.47b9dedd.Darwin.appleclang  (unpinned — pass --expect-solc to gate on it)
```

That string reaches a terminal and no file.

**Ariadne's dataset predicate.** Registered, gated and schema-bound.
`plugins/ariadne/scripts/ariadne_lib/predicates/dataset.py:36` sets
`TYPE = "https://ariadne.wildcat.finance/dataset/v1"`; its gates are gate 2
(`:133`), gate 5 (`:290`), a fields check (`:565`), a coverage check (`:384`) and
an inputs check (`:486`). The published shape is
`plugins/ariadne/schemas/dataset-v1.json`, held to the module by
`plugins/ariadne/tests/test_schema_drift.py`. The capture path is
`plugins/ariadne/scripts/ariadne_lib/capture/dataset.py`, documented in
`plugins/ariadne/docs/capturing-a-dataset.md` and `docs/dataset.md`.

**The predicate already accepts a Lemma corpus, and that is the problem.** Run
at this base, over the directory the Solidity chunker wrote:

```text
gate 2 environment: pass -- lemma 0.1.1, 0 input(s), 2 released file(s)
check coverage: pass -- source unit 1 to 4, 0 gap(s) recorded
check inputs: pass -- 0 input(s), 0 digested, 0 recorded absent
verify exit 0
```

Every gate passed. The `0.1.1` in gate 2's line is a string I typed into
`--producer-version`; nothing read it from Lemma. No compiler appears anywhere in
the statement. No source ref appears anywhere in the statement. The predicate is
doing its job; what is absent is the corpus-side capture.

**Wave peer skills#407, `alexandria-1`, has landed.** Merged and closed
2026-08-26. It emits
`https://ariadne.wildcat.finance/alexandria-release/v1`
(`plugins/alexandria/scripts/alexandria_lib/statement.py:18`), a predicate type
Ariadne does not register.
`plugins/alexandria/docs/release-statements.md` states the consequence plainly:
"The Alexandria predicate is not registered there, so predicate-owned gates 2
and 5 remain visibly unchecked." Its audit record,
`audit/rounds/fiat-407-emit-an-ariadne-ready-release-statement.md`, repeats it in
all three rounds: "Ariadne reported five core-gate passes, the predicate
unregistered, the statement unsigned, and gates 2 and 5 unchecked."

That is the shape skills#409 forbids by name, and the landed peer is the reason
to say so out loud rather than treat it as hypothetical. It did not establish a
corpus vocabulary this run can consume; it established that minting a type gets
you a statement nobody's verifier checks. Carried forward as a rejected option in
section 4.

Two further items carried forward from that record:

- Its round 2 finding S1-R2-01 bound the emitter's output size to Ariadne's
  `DEFAULT_MAX_BYTES`, because a successful write above that cap is not readable
  by the tool it was written for. Not applicable here: this run writes no
  statement. Recorded as answered rather than open.
- Its round 2 note that "the accepted study's statement that `EVOLUTION.md`
  would not be edited is historical planning text superseded by the source-bound
  runbook's explicit generation advance". Answered here by section 3, which
  settles the ledger row in the study rather than leaving it to the runbook.

**Other wave peers, checked at this base.** `tabularium-2` (skills#408, "emit
release evidence through Ariadne's dataset predicate") is open. `probitas-1`
(skills#410) is open. `janus-3` (skills#334) is open. `berean-next` (skills#411)
is open. `lemma-next` (skills#388, the held frontier job) is open. No peer has
landed a dataset-predicate corpus vocabulary, so there is nothing to consume and
nothing this run would duplicate. If skills#408 lands first, its producer and
coverage conventions become the ones to match; that is a reason to keep this
run's contribution on the Lemma side of the seam rather than in Ariadne.

**The last two merged pull requests that changed the subject.** The subject here
is the chunker code and the shared schema. `git log --no-merges -- plugins/lemma/schema.py plugins/lemma/chunkers/` returns exactly one commit at this base:
`f0665874 Add Lemma plugin (#32)`, merged 2026-08-16. There is no second
code-changing pull request to read. The two most recent merged pull requests
touching `plugins/lemma` at all are #96 (`docs(lemma): compress chunking prose`,
merged 2026-08-18) and #32. Neither carries unfinished work into this topic.
`docs/decisions/ADR-013-make-lemma-the-canonical-skill-name.md` carried the
rename forward and is answered by assumption 2. Said plainly: there was no
second code pull request to read.

### Audit sources

`python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .` was
run from the target root and exited 0. Every one of the 25 pairs reported
`committed=match`, so the whole-set currency check holds and a verified synopsis
is a valid reading view.

In-scope sources and what was actually read:

| Source | Read | Evidence for the choice |
| --- | --- | --- |
| `plugins/ariadne/audit/AUDIT.md` | `plugins/ariadne/audit/AUDIT_SYNOPSIS.md` | Whole-set check exited 0 and this pair reported `committed=match`. Ariadne is read but not changed. |
| `audit/rounds/fiat-407-emit-an-ariadne-ready-release-statement.md` | the source directly | It is the landed peer's own record and the design turns on what it says about gates 2 and 5. |
| `plugins/lemma/audit/` | nothing to read | The directory does not exist. Lemma has never been through a Fiat audit loop. |
| `audit/AUDIT.md` | not in scope | The root record covers the root source. This run changes no root skill. |

From the Ariadne synopsis, the findings this design must respect, each kept with
its id and status:

- **S4-R1-02, medium, fixed.** `--repository` was recorded verbatim, so a URL
  carrying `user:token@` put the token into the statement. Fixed by
  `scrub.credentials()` at
  `plugins/ariadne/scripts/ariadne_lib/scrub.py:100`, called from
  `capture/foundry.py:395`. **Carried forward as content.** Lemma's
  `--source-ref` is the same shape of operator-supplied string written to disk,
  so the provenance record strips userinfo from a ref that parses as a URL and
  keeps the rest. Lemma implements the rule rather than importing it; a
  cross-plugin import would break both the marketplace boundary and the portable
  runtime packaging.
- **S4-R1-03, low, fixed.** A heading claimed capture does not carry your
  secrets, which was broader than what it did. **Carried forward.** Lemma's
  prose says what is stripped and says that prose fields are not.
- **S5-R2-02, medium, fixed.** The examples recorded that tests and a fuzz
  campaign passed when nobody ran either; capture took those dispositions from
  its caller. **Carried forward.** Every value in the provenance record says
  whether it was read from a tool or asserted by the caller.
- **S1-R1-03 and S2-R2-02, low and medium, both fixed.** A fifo passed where a
  regular file was expected blocks the reader. **Not applicable** to this
  delivery, which writes files rather than reading caller-named ones, but named
  so the audit loop does not have to rediscover why.
- **Leads not pursued, still open in Ariadne.** Homoglyph keys in gate 4; one
  subject standing in for another in a multi-subject statement; short key
  formats below the 32-character redaction threshold; replay sandboxing. All
  four are Ariadne's and out of scope here. The third one bounds what Lemma's
  own userinfo strip can promise, and section 5 records it.
- `[missing legacy field: audit-schema]`, `[missing legacy field: covered]`,
  `[missing legacy field: not-checked]` and
  `[missing legacy field: elenchus-verdict]` appear on every Ariadne round in the
  synopsis. Those remain unknown; the rounds predate the `fiat-audit-round/v2`
  schema.

### A defect found while establishing the baseline

`plugins/lemma/INVARIANTS.md:194-211` records the reproducible baseline. Its
Markdown block no longer matches what the command produces at this base:

| Figure | Recorded | Produced at `7e449ba3` |
| --- | --- | --- |
| chunks | 38 | 39 |
| chunks placed in the SUMMARY hierarchy | 34 | 35 |
| median characters | 141 | 184 |
| p99 characters | 568 | 1010 |
| maximum characters | 568 | 1010 |

The cause is visible: `plugins/lemma/baseline/docs/` carries a
`marketplace-context` block in nine of its files, and the corpus text
`grep -c "Marketplace context"` finds in `chunks.jsonl` is 9. The block was
propagated into the synthetic corpus after the figures were recorded, and
nothing in either test suite compares the two. The Solidity block still matches
exactly, including `model p99 761 characters; maximum 761`, confirmed against
solc 0.8.35 rather than the 0.8.25 the figures were recorded with; the Solidity
sources carry no marketplace block.

This is the same class of failure the topic is about: a corpus changed and no
record said so. Section 3 puts the Markdown re-record in scope and the Solidity
re-record out of it.

### Outside this repository

in-toto Statement v1 (`https://in-toto.io/Statement/v1`) and its
ResourceDescriptor subject shape, which Ariadne implements. SLSA provenance is
the neighbouring standard and is deliberately not used: Ariadne's dataset
predicate already covers a corpus, and a second vocabulary would have to be
reconciled with it. solc standard JSON is the Solidity compiler's own input
format and is what the chunker consumes.

## 3. Constraints and non-goals

**Starting ref.** `7e449ba35e1519d28b33f06225c4c4137b548a23`, branch
`fiat/409-chunk-corpora-carry-dataset-provenance`, cut from `main`.

**Toolchain and pins.**

- Interpreter: the exact value in `.python-version`, `3.13.15`. `pyproject.toml`
  declares the supported minor. Standard library only; no dependency is added.
- Plugin suite: `hexaemeron` 1.6.5, all four wildcat-labs plugins pinned
  `current` at this base.
- `plugins/lemma/solc-container` pins
  `ethereum/solc@sha256:231d46593eae6105dbb9a1225d318c9605a4e353e10371fe28ccce291be8ea35`,
  which resolves to 0.8.25. `plugins/lemma/baseline/regenerate` gates on
  `--expect-solc 0.8.25` and its own comment says the two move together.
- No container runtime is available here, so any figure this run records for the
  Solidity side names the compiler that produced it.

**Measured baseline at this base.**

| Suite | Command | Result |
| --- | --- | --- |
| root | `python3 -m unittest discover -s tests` | 460 tests, OK |
| lemma markdown | `python3 tests/test_markdown.py` | 126 checks, 0 failures |
| lemma solidity, no compiler | `python3 tests/test_solidity.py` | 33 checks, 0 failures |
| lemma solidity, local solc | `python3 tests/test_solidity.py --solc solc` | 142 checks, 0 failures |
| ariadne | `python3 -m unittest discover -s plugins/ariadne/tests -t plugins/ariadne` | 689 tests, 7 skipped, OK |

Repository checks at this base, each exit 0: `scripts/promise_machine.py check`
(15 plugins, 15 copies), `scripts/promise_machine.py coverage --check`
(`promises=73 coverage_rows=73 coverage_selected=73`),
`scripts/portable_promise_machine.py check`,
`plugins/horos/skills/horos/scripts/horos.py check .` ("boundary matches the
tree"), `audit_synopsis.py --check .`, and phylax, ephoros and hypomnema over
`plugins/lemma`.

**The ledger obligation, stated exactly.** Lemma owns this change, so the row
goes on `plugins/lemma/skills/lemma/EVOLUTION.md` and nowhere else.

- The row is a `generation` row. `tests/test_evolution_contract.py:204-238`
  requires a generation row's version to be `(evolution, generation + 1, epoch)`
  of its predecessor. `lemma-v0.1.1` parses as `(0, 1, 1)`, so the new row is
  **`lemma-v0.2.1`**.
- The same test requires a generation row's `Frontier revision` and
  `Frontier SHA-256` to equal its predecessor's. Both stay
  `abi-return-and-mutability` and
  `2d4f0d7948208fefdca52f4380b3f4c83261917a282256571a2ee611c5d9d36c`.
- `tests/test_evolution_contract.py:183-203` recomputes that digest from the
  header block as `sha256("{status}|{frontier revision}|{current frontier}|{next Fiat job}\n")`.
  I recomputed it at this base and it matches, so **all four header values must
  stay byte for byte identical**:

  ```text
  - Frontier status: `open`
  - Frontier revision: `abi-return-and-mutability`
  - Current frontier: Callable-surface ABI validation does not independently check return types or state mutability.
  - Next Fiat job: Make callable-surface ABI validation cover return types and state mutability as well as names and input types, with any divergence rejecting the output. Before the run finishes, cold-read and reconcile all mutable first-party marketplace prose.
  ```

  Only `- Current version:` changes, to `lemma-v0.2.1`.
- `tests/test_evolution_contract.py:172-182` requires
  `plugins/lemma/skills/lemma/SKILL.md`'s frontmatter `version: "0.1.1"` to
  become `version: "0.2.1"`.
- `plugins/hexaemeron/skills/VERSIONING.md` says a generation "may clarify
  surrounding explanation to reflect earlier changes, but it must not change the
  target or its acceptance condition", and that only a completed frontier job may
  replace the target. The `Current frontier` sentence is inside the digested
  line, so it may not be clarified either.

**No row is owed on Ariadne.** This run reads Ariadne and calls its published
command. It changes no file under `plugins/ariadne/`. Two things would change
that, and section 4 rejects both: adding a field to the dataset predicate, and
teaching `capture-dataset` to read a producer block from a file. If either is
adopted mid-run, Ariadne owes a generation row of its own,
`ariadne-v2.2.0` to `ariadne-v2.3.0`, retaining `grounded-agent-predicate` and
`4ac9d0c0523...`, and that becomes an amendment to this study rather than a
runbook decision.

**Repository contracts this run must respect.** `AGENTS.md`'s
`## Checks for changes to this repository` is the authoritative list. The ones
this change reaches:

- `python3 scripts/portable_promise_machine.py check`, and `sync` when a
  mirrored file changes. Established from the checker rather than from memory:
  `scripts/portable_promise_machine.py:108-113` omits only
  `plugins/*/.claude-plugin/`, `plugins/*/.codex-plugin/`, `plugins/*/audit/`,
  `plugins/*/tests/` and three named Alexandria example directories. Every other
  tracked file under `plugins/lemma/` is mirrored, confirmed by listing
  `.agents/skills/promise-machine/runtime/plugins/lemma/`, which holds
  `chunkers/solidity.py`, `chunkers/markdown.py`, `schema.py`, `SKILL.md`,
  `EVOLUTION.md`, `README.md`, `INVARIANTS.md`, `AGENTS.md`, `solc-container`
  and all of `baseline/`. **So a change to any of those must carry its mirror
  copy in the same commit; a change under `plugins/lemma/tests/` must not.**
- `python3 plugins/horos/skills/horos/scripts/horos.py check .`, and
  `scan . --write` when it drifts. `horos.py:899-913` compares entries by path
  and by whole entry value. `.horos/boundary.json` holds one entry for
  `.agents/skills/promise-machine/runtime/` recording `bytes: 20299658` and
  `files: 904`, so any mirror resync moves that entry and the boundary must be
  regenerated in the same commit. `scan . --write` also writes
  `.horos/candidates.json` beside `.horos/boundary.json`, and
  `tests/test_boundary_currency.py` reads both.
- `python3 scripts/promise_machine.py check` and `coverage --check`. Section 12
  records that this run earns one new promise, which takes both counts from 73
  to 74.
- The shipped-prose lint (`tests/test_shipped_prose_lints.py`) over every tracked
  Markdown file outside `audit/`, `docs/**` and the vendored trees, and the
  shipped-tree lints (`tests/test_shipped_tree_lints.py`) running phylax,
  ephoros and hypomnema over `plugins/` and `docs/`.
- `tests/test_unique_identifiers.py` and `tests/test_promise_machine_contract.py`.
- `tests/test_marketplace_prose.py`. Lemma's marketplace-context block appears in
  15 tracked files, nine of them inside `baseline/docs/`. Changing that sentence
  changes the synthetic corpus, so it is a non-goal below.

**Non-goals.**

- No new predicate type, and no change to `dataset-v1.json` or to any Ariadne
  gate.
- Lemma does not write an in-toto statement, does not sign, and does not shell
  out to Ariadne. `AGENTS.md` says Lemma "stops after producing source-linked
  chunks" and its SKILL.md says it "does not embed, index, retrieve, answer,
  evaluate, or attest".
- No embedding, indexing or retrieval.
- The Lemma marketplace-context sentence is not edited. It sits in nine baseline
  corpus files, and editing it would move the very figures this run is
  re-recording.
- The Solidity baseline figures in `INVARIANTS.md` are not re-recorded, because
  no container runtime is available here to run the pinned 0.8.25 and a figure
  recorded against 0.8.35 would silently replace one recorded against the pin.
  The Markdown figures are re-recorded, because that side runs no compiler and
  anyone can repeat it.
- The held frontier job is untouched. Return types and state mutability stay
  where they are.
- No change to which fields `Chunk` declares.

**Always.** Both Lemma suites and the root suite before a commit. The imprimatur
lint on every shipped document, then brevitas. `portable_promise_machine.py sync`
and `horos scan . --write` in the same commit as any mirrored plugin change.
The exact pinned interpreter for every `python3`.

**Ask first.** Making `--source-ref` required alongside `--out`, which breaks
every existing invocation including `baseline/regenerate`. Adding a field to
`Chunk`. Bumping the Lemma plugin package version, which touches
`.claude-plugin/plugin.json`, `.codex-plugin/plugin.json`,
`.claude-plugin/marketplace.json` and `tests/test_version_propagation.py`'s
`DELIVERY_PACKAGE_VERSIONS`. Changing anything under `plugins/ariadne/`.
Re-recording a baseline figure produced by a compiler that is not the pinned one.

**Never.** Edit the four digested ledger header values. Write a compiler pin the
run did not make. Write `unknown` into a provenance field. Commit a corpus, a
statement or a `chunks.jsonl` into this repository. Import Ariadne from Lemma.
Delete a failing check to make a suite pass. Claim a command ran when it did not.

## 4. Design options

All four options answer the same question: how do the four values reach a
verified dataset statement? What the seam has to bridge is fixed and worth
stating first, because it decides the options.

**What Ariadne already reads, and what it cannot.** `capture-dataset` derives
exactly two things from a release directory: a `sha256` per file
(`capture/dataset.py:130`) and a `record_count`, which it derives only for
`.jsonl` and `.ndjson` and otherwise refuses rather than guesses
(`capture/dataset.py:103-112`). Everything else is caller-supplied. Its
`--input` flag accepts `file=<path>` to digest or `disposition=<state>` with a
reason, and there is no way to hand it a digest computed elsewhere
(`plugins/ariadne/scripts/ariadne.py:200-226`). `commands` is written as an empty
list unconditionally (`capture/dataset.py:355`). `producer.parameters_digest` is
a digest over the parameters and does not carry their values
(`capture/dataset.py:152-160`), so a `--parameter solc=0.8.25` is unreadable
afterwards.

So of the four values: **the digest is automatic**; the **chunker version**,
**source ref** and **compiler identity** are all caller-typed today, and Ariadne
has no mechanism to read any of them from the release. `gate_fields`
(`predicates/dataset.py:565-584`) refuses any top-level predicate key outside the
seven the type defines, and `dataset-v1.json` sets `additionalProperties: false`,
so none of them can be added as a new field without changing Ariadne.

That leaves one place a corpus can put a value where Ariadne binds it without
being changed: a file inside the release directory. Its digest becomes a
`dataset_subjects` entry, and gate 2 requires every such digest to be a subject
of the statement (`predicates/dataset.py:226-229`).

**Option A: a provenance record inside the corpus directory. Chosen.**

Each chunker writes one line of JSON to `provenance.jsonl` beside its `--out`
file, and stamps `source_ref` and `corpus_build_id` onto every chunk through the
existing `schema.stamp()`. The record carries the schema id, the chunker and its
version, the source ref as given with any URL userinfo stripped, the
`corpus_build_id` recomputed from the written chunks, the digested inputs, the
selection (include patterns, source units present, source units selected, and
the excluded ones), the compiler block, and the chunk count. The chunker also
prints the `capture-dataset` flags that match what it just wrote, so the operator
copies rather than composes them.

For Solidity the compiler block records the `--solc` argument verbatim, the
version the compiler reported, and the pin. For Markdown there is no compiler,
and the block records that as an absence with a reason rather than as a null.

The trade: two files instead of one, and a consumer that reads only
`chunks.jsonl` sees the ref and the build id on every chunk but not the compiler.
That is deliberate. Repeating a compiler string on every one of several thousand
records to serve a fact that is one per corpus is what `schema.py:13-24`'s own
tier argument already rejects.

What it buys: no Ariadne change, no new predicate type, the record's bytes bound
by a digest gate 2 insists is a statement subject, and a `record_count` of 1
derived automatically because the file is line-delimited.

Verified at this base, with a hand-written `provenance.jsonl` placed beside a
real corpus:

```text
dataset_subjects:
  chunks.jsonl      sha256 47ff2593e912b8d9054c1bca313fe239d6aab32f24e8ec8e39029baaae33e7dc  25 records
  provenance.jsonl  sha256 12185cfa35d4f6430b12e44a5ebcb420dbd33dec96d16d0deeef7379741a90e0   1 record
inputs: 1 digested, locator carries the ref
verify: seven gates and three checks, all pass, exit 0
```

**Option B: fill only the per-chunk provenance fields. Rejected.**

Call `stamp()` from the CLI with `source_ref` and `corpus_build_id` and stop
there. Cheapest by far, and it closes half of the open end `plugins/lemma/INVARIANTS.md`
leaves at I6. Rejected
because the compiler identity and the chunker version have no `Chunk` field, and
adding two top-level fields to the type every consumer reads, for two facts
identical on every record, is the schema-mostly-nulls failure `schema.py`
already argues against. It also cannot carry the include patterns or the input
digests, so a reader still cannot tell which source units the corpus describes.
Its per-chunk half is kept inside option A.

**Option C: Lemma writes the statement. Rejected.**

Lemma emits `chunks.jsonl` and a dataset-predicate statement beside it. The
values would come from the build rather than from a typed flag, which is the
strongest version of the promise. Rejected on two grounds. First, the marketplace
boundary: `AGENTS.md` says Lemma stops at chunks, and `SKILL.md` says Lemma does
not attest; `plugins/ariadne/docs/capturing-a-dataset.md` owns the capture path.
Second, the landed peer. skills#407 took exactly this shape and its own
documentation records the result: an unregistered predicate whose gates 2 and 5
go unchecked. Reusing the registered dataset type would avoid that specific
outcome, but it would put a second implementation of Ariadne's capture rules
inside Lemma, where nothing holds the two in agreement.

**Option D: give the dataset predicate a corpus block. Rejected.**

Add a field to `dataset-v1.json` and to `PREDICATE_FIELDS`, gate it, add
conformance fixtures, update the drift test, and extend `capture-dataset` to fill
it. This is the only option under which Ariadne *checks* the compiler and the ref
rather than binding bytes that assert them, and that difference is real. Rejected
as the most expensive option that meets the same criterion: it is an Ariadne
evolution with its own ledger row, its own audit surface and its own conformance
fixtures, and the filing points away from it. Named here with its one genuine
advantage so a later run can reopen it on evidence rather than on preference.

**The chosen design's coverage reading.** `capture-dataset` requires
`--coverage-dimension`, `--coverage-start` and `--coverage-end`, all integers,
and the coverage check refuses an absent `gaps` key so that "an interval printed
with no gaps reads as complete" cannot happen by accident. A chunk corpus has no
block height. The reading chosen here is the **source unit**: bounds are the
1-based index range over the sorted set of source units the input declared, and
each maximal run of units present in the input but not selected by the include
patterns is a gap with the reason that names the pattern. Both chunkers already
compute exactly that set: `chunkers/solidity.py:556-566` builds `selected` from
`out["sources"]`, and `chunkers/markdown.py:1032-1050` counts and prints
`skipped` excluded files.

The alternative reading, `start=1, end=<selected count>, gaps=[]`, was rejected:
it makes the excluded units vanish from an interval that then reads as complete,
which is the exact failure the coverage check exists to catch. The provenance
record carries the selection so the operator can write the gaps without counting
by hand.

**Where the compiler identity ends up in the statement.** In `dataset_subjects`,
by digest, through `provenance.jsonl`. It also appears in `producer.command` when
the operator passes the printed argv, because `--expect-solc 0.8.25` and
`--solc ./solc-container` are literal words in it. It does not appear as a
first-class predicate field, and section 5 records that a reader must open the
provenance file to see it.

## 5. Risk register seed

The concerns below are what the audit loop should look hardest at. Two of them
deserve a sentence a line cannot carry.

`require_solc_version` at `chunkers/solidity.py:511-522` compares with
`found.startswith(expected)`. So `--expect-solc 0.8.25` accepts
`0.8.25+commit.b61c2a91` and equally accepts `0.8.25+commit.deadbeef`. The pin is
a prefix pin, not an exact one. A provenance record that says "pinned" without
saying "prefix" would overstate what the gate did, and the reported version has
to sit beside the pin so a reader can see the difference.

The userinfo strip carried forward from Ariadne's S4-R1-02 is a defence against
an accident, not against a determined caller. Ariadne's own record leaves "short
key formats" open: a twenty-character key passes its 32-character threshold.
Lemma's strip covers the `user:token@host` shape and nothing else, and the prose
has to say so rather than repeat the heading Ariadne's S4-R1-03 had to correct.

```risk-register
unpinned-recorded-as-pinned | the compiler block the Solidity chunker writes | an ungated run records the reported version with no pin and a stated reason, and never a pin the run did not make
prefix-pin-read-as-exact | require_solc_version's startswith comparison at chunkers/solidity.py:517 | the record names the pin as a prefix and carries the exact reported version beside it
unknown-written-as-a-value | every field of the provenance record | no field is ever written as the string unknown; an absent value is an absence with a reason, as Markdown's compiler block is
operator-asserted-ref | the --source-ref string, which nothing resolves | the record and the shipped prose both say the ref is asserted by the caller and that nothing fetched or checked it
credential-in-a-ref | the ref string on its way to disk | a ref that parses as a URL loses its userinfo and keeps the rest, and the prose says that is all that is stripped
partial-corpus-write | the two files a chunker writes under one --out | a run that fails after writing one file leaves no directory a capture would read as a whole corpus
provenance-drift | the relation between chunks.jsonl and provenance.jsonl | the recorded corpus_build_id is recomputed from the chunks actually written, and a disagreement fails the build
stamp-inside-the-chunker | the boundary between chunk() and the pipeline above it | chunk() still leaves source_ref and corpus_build_id unset, as INVARIANTS I6 states and test_solidity.py:366 asserts
sidecar-outside-the-release | the directory capture-dataset walks | the provenance file lands beside chunks.jsonl so its digest becomes a dataset_subjects entry gate 2 requires to be a subject
record-count-not-derivable | the provenance file's extension | the file is line-delimited JSON with one record, so capture-dataset derives its count without --record-count
coverage-with-no-gaps | the coverage block the operator hands capture-dataset | excluded source units are recorded as gaps with reasons rather than dropped from an interval that then reads as complete
held-frontier-replaced | plugins/lemma/skills/lemma/EVOLUTION.md | the generation row keeps the revision, digest, status and held job byte for byte and the root suite recomputes the digest from the header
mirror-out-of-step | .agents/skills/promise-machine/runtime/plugins/lemma | the portable sync and the horos rescan land in the same commit as the plugin change, and both checkers exit zero
baseline-figures-stale | the recorded baseline in plugins/lemma/INVARIANTS.md | the Markdown figures are re-recorded from a command anyone can repeat and the Solidity figures keep the compiler that produced them named
required-flag-breaks-a-caller | every existing --out invocation, including baseline/regenerate | the refusal names the missing flag and the run that must add it, and regenerate is updated in the same commit
```

## 6. Glossary seeds

- **Corpus.** One `chunks.jsonl` and the provenance record beside it, in one
  directory, produced by one chunker invocation.
- **Provenance record.** The single-line JSON document a chunker writes to
  `provenance.jsonl`, carrying what produced the corpus.
- **Source ref.** The string the operator asserts as the origin of the chunked
  source. Recorded verbatim apart from URL userinfo. Nothing resolves it.
- **Compiler identity.** The `--solc` argument as given, the version string the
  compiler reported for itself, and the pin, if any, that was gated on.
- **Prefix pin.** What `--expect-solc` performs: the reported version must start
  with the given string. Not an exact match.
- **Chunker version.** The `lemma` skill's governed version from
  `EVOLUTION.md`, which is also `SKILL.md`'s frontmatter version.
- **Corpus build id.** A digest recomputed from the chunks actually written,
  over their ordered ids and content hashes.
- **Source unit.** One entry in a solc standard JSON `sources` map, or one
  Markdown file under `--root`. The dimension the coverage block counts.
- **Selection.** The include patterns, the source units present, the ones
  selected, and the ones excluded.
- **Dataset subject.** One released file in an Ariadne dataset statement, with
  its name, release-relative path, digest and record count.
- **Generation row.** A ledger row that records behaviour change while retaining
  the held frontier revision, digest, status and next job.

## 7. Sources

- skills#409, `lemma-1`, labels `origin:ai` and `wish`, milestone
  `Wave 10 — portable releases and accessible state`. Its 26 August 2026 review
  is binding.
- skills#407 `alexandria-1` (closed 2026-08-26), #408 `tabularium-2`, #410
  `probitas-1`, #334 `janus-3`, #411 `berean-next`, #388 `lemma-next`.
- `plugins/lemma/schema.py`, `chunkers/solidity.py`, `chunkers/markdown.py`,
  `INVARIANTS.md`, `README.md`, `AGENTS.md`, `solc-container`,
  `baseline/regenerate`, `baseline/README.md`, `skills/lemma/SKILL.md`,
  `skills/lemma/EVOLUTION.md`, `tests/test_solidity.py`, `tests/test_markdown.py`.
- `plugins/ariadne/skills/ariadne/SKILL.md`, `EVOLUTION.md`,
  `docs/dataset.md`, `docs/capturing-a-dataset.md`, `schemas/dataset-v1.json`,
  `scripts/ariadne.py`, `scripts/ariadne_lib/predicates/dataset.py`,
  `scripts/ariadne_lib/capture/dataset.py`, `scripts/ariadne_lib/capture/tree.py`,
  `scripts/ariadne_lib/digests.py`, `scripts/ariadne_lib/scrub.py`,
  `audit/AUDIT_SYNOPSIS.md`.
- `plugins/alexandria/docs/release-statements.md`,
  `scripts/alexandria_lib/statement.py`, `skills/alexandria/SKILL.md`,
  `skills/alexandria/EVOLUTION.md`.
- `audit/rounds/fiat-407-emit-an-ariadne-ready-release-statement.md`.
- `AGENTS.md`, `PROMISE_MACHINE.md`,
  `plugins/hexaemeron/skills/VERSIONING.md`,
  `plugins/hexaemeron/skills/protasis/SKILL.md`.
- `tests/test_evolution_contract.py`, `tests/test_version_propagation.py`,
  `tests/test_boundary_currency.py`, `tests/test_marketplace_prose.py`,
  `tests/test_shipped_prose_lints.py`, `tests/test_shipped_tree_lints.py`,
  `tests/test_unique_identifiers.py`, `tests/promise_machine_coverage.json`,
  `scripts/portable_promise_machine.py`, `repo_contract.py`,
  `plugins/horos/skills/horos/scripts/horos.py`.
- `docs/decisions/ADR-013-make-lemma-the-canonical-skill-name.md`. The next free
  number in `docs/decisions/` is ADR-042.
- in-toto Statement v1, `https://in-toto.io/Statement/v1`.

## 8. Signals, and the questions behind them

These commands run from a terminal, so there is no page and no alert. There is
still a person reading the output at the moment the corpus is produced, and
these are the four questions they ask. Ephoros owns what a signal must carry.

1. *Which compiler produced this AST?* The Solidity chunker already prints one
   `compiler` line. It gains the `--solc` argument as given, so a container run
   and a PATH-binary run are told apart on sight, and it says prefix rather than
   pinned when `--expect-solc` was used.
2. *Did this corpus actually get a provenance record, or did I get chunks
   only?* The chunker prints the provenance path and the corpus build id beside
   the existing `written:` line, or prints the refusal and writes nothing.
3. *What exactly do I type into `capture-dataset`?* The chunker prints the
   producer, coverage and input flags that match what it just wrote, so the
   operator copies rather than composes. This is the signal that removes the
   transcription failure, and it is the reason the seam holds without an Ariadne
   change.
4. *Which source units does this corpus not describe?* The chunker prints the
   selected and excluded counts and names the excluded units, which is what the
   gaps block needs.

Steps 2 and 3 emit all four.

## 9. Boundaries, per capability

Phylax owns the boundary list and the controls. This delivery opens two
boundaries and widens neither.

**Operator-supplied string written to disk.** `--source-ref` arrives from a
command line and is written into a file that is later digested and named in a
statement. Worth taking at it: a credential embedded in a URL, and a ref that
claims an origin nothing checked. Controls: strip URL userinfo the way
`plugins/ariadne/scripts/ariadne_lib/scrub.py:100` does, record the value
verbatim otherwise, and say in the record and in the prose that the ref is
asserted rather than resolved. This is the `credential-in-a-ref` and
`operator-asserted-ref` pair in section 5.

**A second file written under `--out`.** The chunkers already write one file.
Writing a second creates a window in which the directory holds a corpus with no
provenance, or a provenance record describing chunks that were never written.
Worth taking at it: a capture that reads a half-written directory as whole.
Controls: compute everything first, refuse before writing anything if the run
cannot produce a complete record, and write the provenance record only after the
chunks are on disk with the build id recomputed from them. This is
`partial-corpus-write` and `provenance-drift`.

**Not opened.** No network. No subprocess beyond the `solc --version` and
`solc --standard-json` calls that already exist at
`chunkers/solidity.py:502` and `:532`. No credential is read. No dependency is
added. No untrusted document is parsed that was not already parsed. Phylax,
ephoros and hypomnema all report clean over `plugins/lemma` at this base, and
that is the state to keep.

## 10. The budget, or its absence

There is a budget, and it is a size budget rather than a time one. Metron owns
what a budget carries and how it is checked.

The provenance record must stay one line of line-delimited JSON, because
`capture/dataset.py:103-112` derives a record count only for `.jsonl` and
`.ndjson` and a multi-record file would report a count that means nothing.
Measured by reading the emitted file:

```bash
test "$(wc -l < "$W/corpus/provenance.jsonl")" -eq 1
python3 plugins/ariadne/scripts/ariadne.py capture-dataset --release "$W/corpus" ... \
  | python3 -c 'import json,sys; print([e["record_count"] for e in json.load(sys.stdin)["predicate"]["dataset_subjects"] if e["path"]=="provenance.jsonl"])'
```

Expected: `1` and `[1]`.

There is no time budget. The record is composed from values the chunkers already
hold in memory and written once. The one added cost is digesting the input files
for the `inputs` block; those are the same standard JSON files the chunker
already reads whole, and on the baseline corpus the chunker run is under a second
either way. No performance claim is made and none is measured, because there is
no prior figure to compare against and inventing one would be worse than saying
there is none.

## 11. The fail-closed posture

Elenchus owns the triage order and the guard rule. What stops a run:

- `--out` with no `--source-ref` refuses and writes nothing. A corpus delivered
  with a null origin is the defect this run exists to close, so producing one is
  not a degraded success.
- A `--source-ref` that is empty or only whitespace refuses. `stated()` in
  Ariadne's predicate at `predicates/dataset.py:114-121` refuses the same shape
  for the same reason, and a field holding `"   "` satisfies a presence check
  while naming nothing.
- A compiler version that cannot be parsed already raises `ChunkError` at
  `chunkers/solidity.py:507`, and a mismatch against `--expect-solc` already
  raises at `:515`. Both keep that behaviour.
- A recomputed `corpus_build_id` that disagrees with the chunks on disk refuses
  and leaves no directory a capture would read as whole.
- Both chunkers already refuse to write on a schema problem
  (`solidity.py:1102-1104`, `markdown.py:1167-1168`). The provenance record is
  written after that refusal point, never before it.

The guard convention: every fix lands with a check in
`plugins/lemma/tests/test_solidity.py` or `test_markdown.py` that fails without
it, using the existing `check(name, ok, detail)` harness at
`test_solidity.py:39`, and the suite's printed failure count is the report. Those
two files are the runner contract for any step whose audit claims a fix. They are
not mirrored into the portable runtime, so a test-only change carries no sync.

## 12. Decisions and their homes

Hypomnema owns which decisions earn a record and where each one lives.

**Expensive to reverse, and earning a decision record.** Putting corpus
provenance in a sidecar file rather than in the `Chunk` schema. Once a consumer
reads `provenance.jsonl`, moving those fields into `Chunk` means changing the
type every consumer reads. The alternatives, their trades and the marketplace
boundary that rules out Lemma writing a statement all belong in one place:
`docs/decisions/ADR-042-record-corpus-provenance-beside-the-chunks.md`, the next
free number.

**Expensive to reverse, and living in the shipped contract rather than a record.**
Making `--source-ref` required alongside `--out`. It changes every caller.
Its home is `plugins/lemma/skills/lemma/SKILL.md`, `plugins/lemma/README.md` and
the refusal message itself, which names the missing flag.

**The record shape.** A published shape is what a consumer builds against.
`plugins/lemma/INVARIANTS.md` is where Lemma states its guarantees, so the record
shape and its fields go there as an extension of invariant I6, which already says
provenance is pipeline-owned and applied through `schema.stamp()`. This run makes
the CLI the pipeline that I6 has been describing since the plugin landed.

**A new Promise Machine contract, and it is earned.** The provenance record
authorises a transition the existing three promises do not: an Ariadne dataset
capture over the corpus. `lemma-solidity-chunks` and `lemma-markdown-chunks`
promise schema-valid, source-linked JSONL; neither says anything about a record
binding an origin. The precedent is exact: skills#407 added
`alexandria-release-statement` to `plugins/alexandria/skills/alexandria/SKILL.md`
for the same class of work. So `lemma-corpus-provenance` goes in
`plugins/lemma/skills/lemma/SKILL.md`, with evidence classes `checked` and
`recorded`, and a boundary saying what the record does not establish.

Its home in the coverage file is one new row in `tests/promise_machine_coverage.json`
under `rows`, with its five MOPRS case ids and their `evidence` entries pointing
at named selectors in the two Lemma test files. That takes
`scripts/promise_machine.py coverage --check` from
`promises=73 coverage_rows=73` to 74 and 74.

**What the record establishes, and what it does not.** This belongs in the
boundary line of that contract and in `INVARIANTS.md`, and it is the sentence the
whole delivery turns on. A corpus carrying this record, captured and verified,
establishes that:

- the bytes of `chunks.jsonl` and of `provenance.jsonl` are the ones digested,
  and neither has changed since (`checked`);
- the compiler reported that version of itself to that invocation, and the
  operator asserted that ref (`recorded`);
- the corpus build id was recomputed from the chunks actually written
  (`recomputed`).

It does not establish that the source ref names a real object, that the ref was
clean, that the compiler was honest about its own version, that the compiler was
the one the corpus was meant to be built with when no pin was gated, that the
chunker read the source correctly, or that a citation out of the corpus is
faithful. A digest binds bytes. It does not bind the truth of what they say.
Ariadne's own conformance document is the model for this paragraph and the
wording follows it.

**Decisions that earn no record.** The field names inside the record, the choice
of `provenance.jsonl` as the filename, and the print format of the added lines.
Each is reversible in one commit and none is a boundary.

## Proposed step shape

Three steps. The topic is one capability and does not decompose into modules: the
record, the emitters and the seam cannot ship or be verified separately, because
a record nothing writes proves nothing and an emitter with no published shape
has nothing to write.

**Step 1: publish the record shape and commit the spec.** Commit this study and
the runbook under `plugins/lemma/docs/`, following the peer's convention at
`plugins/alexandria/docs/release-statement-study.md`. Add the builder and the
validator for `lemma-corpus-provenance/v1` to `plugins/lemma/schema.py`, with
the userinfo strip and the refusal of a blank ref, and extend `INVARIANTS.md`'s
I6. Exit: both Lemma suites exit 0 with their new checks printed, the root suite
stays at 460, the portable sync and the horos rescan both exit 0.

**Step 2: both chunkers write it and stamp the corpus.** Add `--source-ref` and
`--provenance` to `chunkers/solidity.py` and `chunkers/markdown.py`; refuse
`--out` without a ref; record the compiler block with its pin state on the
Solidity side and the compiler absence with its reason on the Markdown side;
call `schema.stamp()` from the pipeline and not from `chunk()`; update
`baseline/regenerate`; re-record the Markdown baseline figures. Exit: both
suites exit 0, a corpus built by each chunker carries a one-line
`provenance.jsonl`, and `--out` without `--source-ref` exits non-zero having
written nothing.

**Step 3: close the seam and demonstrate it.** Print the matching
`capture-dataset` flags; document the handoff in `SKILL.md`, `README.md` and
`AGENTS.md`; write ADR-042; add the `lemma-corpus-provenance` contract with its
coverage row and evidence entries; append the `lemma-v0.2.1` generation row and
set the SKILL.md frontmatter to `0.2.1`. Exit: the demo path in section 1 runs
end to end, `ariadne verify` exits 0, the four values are read back out of the
statement, and every check in section 3's list exits 0.
### Amendment -- 2026-08-28

**What changed.** The committed copies of this study and of the runbook land as
flat files directly under `docs/`, at `docs/lemma-corpus-provenance-study.md`
and `docs/lemma-corpus-provenance-runbook.md`, rather than under
`plugins/lemma/docs/`.

**Why.** Item 1 of the assumptions block above carries the one relative link in
this study, to the file that records the interpreter pin. A relative link
resolves from the directory holding the file, so a byte-identical copy carries
a resolving pointer only from one directory below the repository root. Under
`plugins/lemma/docs/` the same bytes point at a path that does not exist, and
Hypomnema refuses it through the shipped-tree lint, which walks every plugin.
The receipted bytes cannot change, so the location moves instead: the copy
stays byte for byte the artefact this run received, and its pointer resolves.
The repository already keeps flat study files at that depth, so the move
follows a convention rather than inventing one.

**Steps touched.** Step 1.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit
holds. Step 3: entry holds; exit holds.
