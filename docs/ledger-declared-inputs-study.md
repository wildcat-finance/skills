# Study: declare a held job's required inputs in the ledger

Source: [skills#1276](https://github.com/wildcat-finance/skills/issues/1276),
`versioning-wish`, labels `origin:ai` and `wish`, `Fiat-Required: 1`.

## Assumptions

Stated before the content that rests on them. Work proceeds on these unless
corrected.

1. Python 3.14.6, the exact interpreter in `.python-version`, with stdlib
   `unittest`. `pyproject.toml` pins `requires-python = "==3.14.*"`.
2. No Solidity and no Foundry or Hardhat project, so the bundled Pashov suite
   is waived for this run by the controller.
3. `VERSIONING.md` is the ledger format authority for every governed skill in
   the checkout, not only for the skills Kronos ranks.
4. Kronos stays mature and terminal. This run advances its generation counter
   and retains its frontier line byte for byte.
5. The 27 governed ledgers in this checkout carry no declaration today, so an
   optional block leaves all 27 unchanged. Measured, not assumed: see item 4.
6. The declaration is a claim its ledger's owner makes. Nothing in this run
   checks that a declared input exists.

## 1. Problem statement

**What is being built.** One optional declared block on a governed evolution
ledger naming the inputs its held `Next Fiat job` needs before the job can
start, and, for each, whether the ledger's owner says it is presently
available. A Kronos ranking reads that block where it is present, and the
recorded pass says which candidates supplied one.

**For whom.** The Kronos ranking pass, and the person reading its table
afterwards. Today a ledger states what to build and what accepts it. It never
states what the job needs in order to start, so the third scoring axis,
readiness of inputs and acceptance conditions at 20 of 100, has half its
subject stated and half inferred from the job's prose. The inference is
unrecorded, so nobody can tell later whether a score was read or guessed.

**What a working prototype means here.** Three things hold together:

1. A ledger may carry the block, and a ledger without one behaves exactly as
   it does today, including its frontier digest.
2. `kronos.py` reads the block from the ledger on disk, refuses a malformed
   one, and records what it found on the scoreboard line.
3. `kronos/SKILL.md` tells the ranking to read the block where present and to
   say in the basis that it inferred where absent.

**The demo path.** From the target root:

```bash
python3 plugins/hexaemeron/skills/kronos/scripts/kronos.py record \
  --scoreboard <tmp>/.kronos/scoreboard.jsonl --root <fixture root> < pass.json
python3 plugins/hexaemeron/skills/kronos/scripts/kronos.py show \
  --scoreboard <tmp>/.kronos/scoreboard.jsonl
```

over a fixture root holding one ledger that declares inputs and one that does
not. `show` prints the declaration for the first and `declared: none` for the
second. The same two commands over the real checkout print `declared: none`
for all 21 rankable skills, which is the true state of `main` and is now
recorded rather than absent.

**Success criteria.**

- `python3 scripts/run_checks.py` exits 0.
- `python3 tests/test_evolution_contract.py` accepts all 27 governed ledgers
  unchanged, and refuses each malformed specimen the new shape check names.
- Every governed ledger's frontier SHA-256 is byte-identical to the value
  recorded on `main` at `5bc2494c`. Kronos's stays
  `ac28d95d80724aa001a92740f76416164e65d7b7b9cb5da43674d1ea73a214d1`.
- `plugins/hexaemeron/tests/run_tests.py` exits 0, including new cases for a
  present block, an absent block, and each refusal.
- The demo path above prints one declaration and one `declared: none`.

## 2. Prior art

### In this repository

- `plugins/hexaemeron/skills/VERSIONING.md` defines the label form, the three
  counters, the five header fields, and the frontier digest over the exact
  UTF-8 line `{status}|{frontier revision}|{current frontier}|{next Fiat job}`
  including its final newline. It also carries the frontier-discipline rules a
  generation entry must obey.
- `plugins/hexaemeron/skills/kronos/SKILL.md` holds the four scoring axes at
  40, 25, 20 and 15, the tie-break, rank-only mode, the parked lane, and the
  `kronos-frontier-ranking` promise whose Boundary already says the checker
  "does not make subjective scores objective".
- `plugins/hexaemeron/skills/kronos/scripts/kronos.py` is the writer. Two of
  its existing decisions are the template for this one. `held_job_hash` is
  computed from the ledger on disk rather than taken from the caller, because
  taking a hash from the caller would be a second way of naming one thing.
  `drift` marks an axis that moved for a candidate whose held job did not.
- `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` reads the same ledgers
  through two different readers. `ledger_field` and `ledger_frontier_digest`
  take the first regular-expression match anywhere in the file.
  `_ledger_field_bytes` requires exactly one match outside a fenced block, via
  `_unfenced_markdown_lines`. `ledger_rows` scans every line; the
  version-relation reader `_ledger_history_records` scans unfenced lines only.
  That asymmetry is the hazard item 5 records.
- `tests/test_evolution_contract.py` is the repo-wide gate. It recomputes each
  ledger's four-field digest and compares it with the final history row, over
  every governed skill.
- `tests/check-map-v1.json` declares the ownership graph
  `scripts/run_checks.py` selects from. `plugins/hexaemeron` maps to scope
  `hexaemeron`, `tests` and `tests/check-map-v1.json` to `root`, `docs` to
  `docs`. Every path this run touches already has a declared owner, so the map
  needs no new entry.

### The recorded evidence the filing cites

The filing names a rank-only pass on `refs/heads/kronos/state` at `b8bbaa62`.
That ref resolves to `b8bbaa62c28e636ba8608fa7794335c339c2729b` and its
`scoreboard.jsonl` carries one pass: mode `full`, `rank_only` true, 21
candidates, selection `fiat`, `ungoverned` naming `fizz`,
`solidity-auditor` and `x-ray`. The three readiness scores the filing quotes
are the recorded ones: `probitas` 11, `alexandria` 10, `imprimatur` 8. The
filing's premise is confirmed against the record rather than restated.

### The last two merged pull requests touching the subject

- [#1246](https://github.com/wildcat-finance/skills/pull/1246), merged
  2026-09-05, "Stop Kronos after a currency report refusal". The last change to
  `kronos/`. It advanced `kronos-v0.8.0` by generation with the mature frontier
  and digest unchanged, and moved the Hexaemeron package from 1.6.22 to 1.6.23
  so an installed host receives the changed instruction. Its stated boundary is
  that no `hexctl.py` behaviour changed and that the work is a fail-closed
  workflow instruction with contract tests rather than runtime automation in
  `kronos.py`. It carried nothing forward: it closes #1170 "by taking its first
  named remedy", and the remaining named remedies belong to that issue rather
  than to this one. Carried forward here as the shape this run copies: a
  generation advance, a retained frontier, and a package bump.
- [#1203](https://github.com/wildcat-finance/skills/pull/1203), merged
  2026-09-04, "Point the controller at the narrow reads it already has". The
  last change to `VERSIONING.md`. It corrected the frontier clause added in
  #1138 and left three items open by name: #1066's first acceptance check,
  which it states is unprovable by any test because no test can observe an
  agent's reads; #1126, the surviving question from its item 2; and #1122, the
  surviving half of its item 3. It also filed
  [#1205](https://github.com/wildcat-finance/skills/issues/1205) for a
  `tests/promise_machine_coverage.json` walk that reaches neither of the two
  generic gates in `tests/test_unique_identifiers.py`. **Refused by name.** All
  four are about controller reads and coverage walks. None of them concerns the
  ledger format, and none blocks this run. They stay open where they were
  filed.

### In-scope audit records

```bash
python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .
```

exits 0 over 20 pairs, each reporting `committed=match`, so each synopsis is a
verified reading view of its record. Named in scope, with what was read:

| Source | Read | Evidence for the choice |
| --- | --- | --- |
| `plugins/hexaemeron/audit/AUDIT.md` | `AUDIT_SYNOPSIS.md` | Sibling pair, `committed=match`, `budget=pass` |
| `audit/AUDIT.md` | `AUDIT_SYNOPSIS.md` | Root pair, `committed=match`, 425 sections |
| `audit/rounds/fiat-447-distinguish-wave-frontier-and-maintenance-vo.md` | `.synopsis.md` | Direct-child pair, `committed=match` |
| `audit/rounds/fiat-621-isolate-disposable-fixture-signing.md` | `.synopsis.md` | Direct-child pair, `committed=match` |

No source was read directly, and no source is claimed as read where only its
synopsis was.

Findings and statuses carried forward:

- `plugins/hexaemeron/audit/AUDIT.md` step 0 round 1 records F-01 through F-10.
  F-01 through F-09 are `fixed`; F-10 is `accepted` as a documented escape
  hatch. Its four legacy fields are `[missing legacy field: ...]` and remain
  unknown. Round 2 records the exact zero-finding row and one lead not pursued,
  the vendored Pashov skills never exercised against this plugin, which stays
  true here because this run ships no Solidity.
- `audit/rounds/fiat-447` round 1 records S1-R1-01, medium, `open`, against
  ADR-035's sealed handoff. Round 2 records the zero-finding row, `Elenchus
  verdict: unguarded`, and repeats that live Kronos behaviour was `Not checked`.
  **Still open**, and out of scope: it concerns volunteer selection, not the
  ledger format.
- The root synopsis records one Kronos lead not pursued, from the parked-lane
  run's step 3 round 2: phase-only mode narrows step 8 to the six phase ledgers
  and says nothing about the scoreboard read-back step 8 also carries, accepted
  because the section says steps 3 to 7 are unchanged. **Still open by the same
  reason.** This run does not touch phase-only mode or step 8's read-back.
- Every round listed above records live Kronos behaviour under `Not checked`.
  That holds here too: this run adds contract tests and a parser, and it does
  not exercise a live ranking loop.

### Outside both

No external standard governs this. The nearest neighbours are ordinary package
manifests that separate a declared requirement from a resolved one; none is
adopted, because the block is a prose claim inside a Markdown ledger and not a
resolvable dependency.

## 3. Constraints and non-goals

**Starting ref.** Branch `fiat/1276-declare-a-held-job-s-required-inputs-in-the`,
cut from `main` at exactly `5bc2494c4f5802efcd8a92e58554809ac4b9f147`. The
worktree was clean at study time.

**Toolchain.** Python 3.14.6 from `.python-version`, `requires-python =
"==3.14.*"` from `pyproject.toml`, stdlib `unittest`. The checked runner is
`python3 scripts/run_checks.py`, which reads `tests/check-map-v1.json`.

**Frontier constraint.** This run is registered against
`plugins/hexaemeron/skills/kronos/EVOLUTION.md` at `kronos-v0.8.0` with 9
history rows. `hexctl done integrate` refuses until the ledger carries exactly
one new valid row. The row is a generation entry: evolution stays 0, the
version becomes `kronos-v0.9.0`, and `Frontier revision`, `Current frontier`,
`Next Fiat job` and the `Frontier SHA-256`
`ac28d95d80724aa001a92740f76416164e65d7b7b9cb5da43674d1ea73a214d1` are retained
byte for byte. `frontier_close_fault` in `hexctl.py` enforces both retentions.

**Package constraint.** `kronos/SKILL.md` changes, so the Hexaemeron package
advances from 1.6.24 to 1.6.25 in both plugin manifests and both marketplace
manifests, and `kronos/SKILL.md` frontmatter `version` becomes `0.9.0` to match
the ledger. `tests/test_version_propagation.py` and
`tests/test_evolution_contract.py` both check that agreement.

**Prose constraint.** `kronos/SKILL.md` is inside the shipped-prose scope of
`tests/test_shipped_prose_lints.py`, which requires zero Imprimatur defects.
`VERSIONING.md` and the committed study and runbook copies go through the
`AGENTS.md` written-record sequence.

**What the user ruled out.** The filing's Boundary is explicit and binds every
promise this run writes: the work makes an input requirement stated rather than
inferred. It does not make a readiness score objective, does not verify that a
declared input exists, and does not stop a ledger declaring an input wrongly.

**Non-goals.**

- No reopening of the Kronos frontier. Kronos stays `mature` and the evolution
  counter stays at 0.
- No declaration written into another skill's ledger. This run cannot know
  whether Alexandria's two live providers are available, and writing that claim
  would be this run forging another owner's statement. The three ledgers the
  filing names keep no declaration.
- No change to the four axes, their caps, the tie-break, the parked lane, or
  Fiat ownership of delivery.
- No change to the digested frontier line, and therefore no change to
  `hexctl.py`.
- No verification, expiry, or refresh of a declared input. Deferred past the
  prototype and not scheduled.
- No scoring formula that converts a declaration into a number. The block
  supplies the basis; the score stays the ranking agent's own work.

## 4. Design options

Four candidate constructions were measured against this checkout. The prose
below explains them; `.hexaemeron/design-evidence.json` selects one from
checked gates and comparative measurements, and is the selection interface.

**`versioning-fenced-block`, selected.** `VERSIONING.md` defines one optional
fenced block, info string `declared-inputs`, placed after the last frontier
header bullet and before the `## History` heading. One row per input:

```text
archive-rpc | endpoint | absent | An archive JSON-RPC endpoint for the capture window.
```

Four pipe-separated fields: a kebab-case id unique within the block, a `kind`
from the closed set `credential`, `endpoint`, `person`, `corpus`, `tool`, an
`availability` from `available`, `absent`, `unknown`, and a bounded note.
Kronos owns the reader and nothing else. **The trade:** the declaration sits
outside the frontier digest, so the ledger's own history cannot detect a
declaration that changed. The scoreboard's per-pass declaration digest is what
makes such a change visible, in the same way the existing `drift` check makes a
moved axis visible.

**`kronos-sidecar-file`.** Kronos owns both the format and the reader, and each
declaration lives in an `EVOLUTION.inputs.json` beside the ledger. **The
trade:** trivially digest-safe and machine-shaped, but the declaration leaves
the ledger. It is then outside the append-only surface a reviewer reads, and a
consumer that is not Kronos has to learn a second file to read one skill's
frontier. It fails the locality gate.

**`digested-fifth-field`.** A `- Declared inputs:` header bullet whose value
joins the canonical line as a fifth digested field. **The trade:** a
declaration change would then move the ledger's own digest, which is the
strongest possible detection. It costs every existing ledger: measured, all 27
stop matching their recorded history row. That is the hard failure the brief
names, and the record shows it as a number rather than as an argument.

**`undigested-header-bullet`.** The same header bullet, left outside the
four-field digest. **The trade:** the cheapest bytes and the fastest read, and
it keeps the declaration beside the fields a reader already scans. It puts
every input in one value, so an id, a kind, an availability and a note can only
be recovered by splitting a value another field already holds, and a reader
sees five header bullets of which four are digested and one is not.

### Why `VERSIONING.md` owns the field

The filing's carryover leaves this open: `which skill owns the field is
VERSIONING.md's decision`. It is settled here as ledger policy, with Kronos
holding only the reader. Three reasons, in order of weight:

1. **A reader Kronos does not own already parses these ledgers.**
   `hexctl.py`'s version-relation path reads any governed ledger, including the
   mature ones Kronos never ranks. The measurement in item 5 shows a badly
   placed block splitting that reader from `ledger_frontier_digest`. A format
   that can split `_ledger_field_bytes` from `ledger_frontier_digest` cannot be
   defined inside the consumer that calls neither.
2. **The format applies to ledgers Kronos never sees.** 27 ledgers are
   governed; the recorded pass ranked 21. Six carry a format defined for all of
   them.
3. **Kronos is mature and terminal.** Its ledger blocks work intended to
   improve Kronos. Reading a field is a generation change to the consumer;
   defining a field for 27 ledgers is not a change to Kronos at all.

The consequence is deliberate: `VERSIONING.md` states the shape, and
`tests/test_evolution_contract.py` checks it repo-wide, so a malformed block on
a mature ledger is caught by the marketplace gate rather than only by a Kronos
pass that never reads it.

### Whether the digest rule changes

It does not. The block adds no `- Name: value` line, so the four digested
fields are byte-identical and `hexctl.py` needs no change. Measured on a
specimen built from the real Kronos ledger:

| Reader | Before | After |
| --- | --- | --- |
| `ledger_frontier_digest` | `ac28d95d8072...` | `ac28d95d8072...` |
| `_ledger_field_bytes`, all four fields | one unfenced match | one unfenced match |
| `ledger_rows` | 9 rows | 9 rows, identical |
| `_ledger_history_records` | 9 rows | 9 rows, identical bytes |
| `kronos.py` `held_job_hash` | `ac28d95d8072...` | `ac28d95d8072...` |
| `_unfenced_markdown_lines` | 24 lines | 25 lines, the one added being blank |

Across all 27 governed ledgers, the count of ledgers whose recorded frontier
digest stops matching is 0 for this design and 27 for `digested-fifth-field`.

## 5. Risk register seed

The audit loop enumerates these by id. The two placement rules decide whether
the digest holds: measured on a specimen, a block placed above the header
bullets and carrying a `- Frontier status: open` row makes `ledger_field`,
`ledger_frontier_digest` and `kronos.py` read `open` from the fenced row while
`_ledger_field_bytes` skips fenced lines and reads the real `mature`. The
ledger's computed digest then disagrees with its own recorded history row. The
same specimen placed below the header bullets leaves every reader agreeing.
Separately, a block whose closing fence is missing swallows the `## History`
heading from `_unfenced_markdown_lines`, and hexctl's version-relation reader
refuses with `has no History section` while `ledger_rows` still reports 9 rows.
Both failures are reachable through an ordinary editing mistake, and neither is
detected by anything on `main` today.

```risk-register
header-shadowing | a declared-inputs row that begins with `- ` | a row opening with a hyphen, a pipe or a backtick is refused by shape, and a specimen carrying `- Frontier status:` is proved not to move any reader's value
block-placement | the block's position relative to the header bullets and `## History` | a block above the first header bullet or below the History heading is refused, with a specimen for each
unclosed-fence | the closing fence of the block | an unclosed block is refused before it can hide the History section from `_unfenced_markdown_lines`
digest-drift | the four-field canonical frontier line | all 27 governed ledgers recompute to the digest recorded on `main` at 5bc2494c, checked as a count that must equal zero
row-shape | each row's four pipe-separated fields | an id that is not kebab-case, a duplicate id, an unknown kind, an unknown availability, an empty field or a fifth field is refused with a named code
unbounded-block | the caller-controlled bytes kronos.py reads from a ledger | the row count, per-field byte caps and whole-block byte cap are enforced before any row is stored
truth-claim | the promise text kronos.py and the two skills publish | no promise, boundary or basis says a declared input exists, was verified, or makes a score objective
absent-declaration | a ledger carrying no block | a pass over the 27 real ledgers records `declared_inputs` as null and every other recorded field is byte-identical to a pass taken before the change
declaration-drift | a declaration that changes while the held job does not | `show` marks a moved declaration digest for a candidate whose held-job hash did not move
caller-supplied-declaration | the pass document kronos.py reads on stdin | a pass that tries to state `declared_inputs` itself is refused as an unknown field, exactly as an unknown field is refused today
```

## 6. Glossary seeds

- **Declared inputs block.** The optional fenced `declared-inputs` block in a
  governed ledger's frontier section, naming what the held job needs.
- **Declaration.** One row of that block: an id, a kind, an availability and a
  note.
- **Availability.** The ledger owner's claim about one input, one of
  `available`, `absent`, `unknown`. It is a claim, never a check.
- **Kind.** What sort of input a row names, from the closed set `credential`,
  `endpoint`, `person`, `corpus`, `tool`.
- **Declaration digest.** SHA-256 over the block's canonical rows, recorded per
  candidate per pass so a changed declaration is visible.
- **Held-job hash.** The existing SHA-256 over the four-field canonical
  frontier line. Unchanged by this work.
- **Frontier section.** The header bullets of a ledger, from `- Current
  version:` down to the line before `## History`.
- **Shape, not truth.** The block is checked for its form and never for whether
  its statements are correct.

## 7. Sources

- Issue: `https://github.com/wildcat-finance/skills/issues/1276`.
- Ledger policy: `plugins/hexaemeron/skills/VERSIONING.md` at `5bc2494c`.
- Kronos instruction and ledger:
  `plugins/hexaemeron/skills/kronos/SKILL.md`,
  `plugins/hexaemeron/skills/kronos/EVOLUTION.md`.
- Kronos writer: `plugins/hexaemeron/skills/kronos/scripts/kronos.py`.
- Frontier validation: `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`,
  functions `ledger_field`, `ledger_frontier_digest`, `ledger_rows`,
  `_ledger_field_bytes`, `_unfenced_markdown_lines`,
  `_ledger_history_records`, `frontier_close_fault`.
- Repo-wide ledger gate: `tests/test_evolution_contract.py`.
- Kronos writer tests: `plugins/hexaemeron/tests/test_kronos_scoreboard.py`.
- Ownership graph: `tests/check-map-v1.json`.
- Repository contract: `AGENTS.md`, sections "Checks for changes to this
  repository", "Written-record publication" and "Reading boundary".
- ADR conventions and numbering: `docs/decisions/`, and
  `docs/decisions/ADR-077-assign-adr-numbers-at-merge-not-at-authoring.md`.
- Recorded ranking pass: `refs/heads/kronos/state` at
  `b8bbaa62c28e636ba8608fa7794335c339c2729b`, file `scoreboard.jsonl`.
- Merged pull requests: `skills#1246` and `skills#1203`.
- Design record and reports: `.hexaemeron/design-evidence.json` and
  `.hexaemeron/reports/`, produced by `.hexaemeron/design/measure.py`.

## 8. Signals, and the questions behind them

The Kronos writer runs from a terminal, and a ranking pass is driven by a
person or an agent watching it. There is no unattended service here, so there
is no alerting and no metric series. What there is, and what
[ephoros](../plugins/hexaemeron/skills/ephoros/SKILL.md) owns the shape
of, is the recorded pass, which is the only thing anyone reads afterwards.

Three questions someone asks later, and where the answer comes from:

1. *Was this readiness score read from a declaration or guessed from prose?*
   Answered by the pass line's `declared_inputs`: an object when the ledger
   declared, `null` when it did not. Emitted by step 3.
2. *Did a declaration change while the held job stayed put?* Answered by `show`
   marking a moved declaration digest under an unchanged held-job hash,
   alongside the existing axis drift. Emitted by step 3.
3. *Why was this pass refused?* Answered by the named refusal code and its
   message on stderr, which the existing K-code convention already carries.
   `K022` names a malformed declaration. Emitted by step 3.

No signal claims an input exists. `declared_inputs` records what a ledger said.

## 9. Boundaries, per capability

[phylax](../plugins/hexaemeron/skills/phylax/SKILL.md) owns the boundary
list and the controls. This run opens one new boundary and widens none.

**New: a ledger's declared-inputs block, read by `kronos.py`.** The bytes are
caller-chosen in the sense that matters here: a candidate names a ledger path
in the pass document, and the file at that path is read. What is worth taking
at that boundary is the same thing worth taking at the existing ledger read: a
document large enough or malformed enough to cost more than it should.

The controls are the ones already in the module, extended to the new rows: the
ledger is resolved and required to be a regular file under the scoreboard's
root, and read under `MAX_LEDGER_BYTES`. On top of that, at most 16 rows are
accepted, the whole block is capped at 4096 bytes, each id is capped at 64
bytes and each note at 200, and `kind` and `availability` are closed sets. A
row failing any of these refuses the pass with `K022` and appends nothing,
which is the module's existing whole-or-nothing rule.

**Unchanged.** `record`, `park`, `unpark`, `show` and `parked` still start no
subprocess and open no socket. The declaration is read from the same file
handle discipline as the held-job hash. No credential, network call or
dependency is added.

**Not a boundary this run may cross.** A declaration is not evidence. Nothing
here reaches out to check whether a declared endpoint answers or a declared
person is available, and no promise says otherwise.

## 10. The budget, or its absence

There is a budget, and
[metron](../plugins/hexaemeron/skills/metron/SKILL.md) owns what it
carries. Kronos reads every governed ledger on every pass and reranks from
scratch, so a per-ledger parse is paid 27 times per pass and again on every
rescan.

**The budget.** Reading declarations for all 27 governed ledgers stays within
the cost of the design that keeps the declaration in the ledger, measured as
88 ms over 200 passes on this host and recorded in
`.hexaemeron/reports/versioning-fenced-block-declaration-read-cost.json`. The
rejected sidecar design measured 139 ms for the same work because it opens a
second file per skill.

**The command that measures it.**

```bash
python3 .hexaemeron/design/measure.py \
  --candidate versioning-fenced-block --criterion declaration-read-cost
```

The baseline is recorded before the change, in the design record, which is what
makes the comparison a measurement rather than a claim. The number is host-
local and is not a promise about any other machine.

## 11. The fail-closed posture

[elenchus](../plugins/hexaemeron/skills/elenchus/SKILL.md) owns the
triage order and the guard rule.

**What stops the run.** Any of these, at the step that incurs it:

- A governed ledger whose recomputed frontier digest stops matching its
  recorded history row. This is the hard gate; a run that moves any of the 27
  stops rather than proceeds.
- `python3 scripts/run_checks.py` exiting non-zero.
- `hexctl done integrate` refusing because the ledger did not gain exactly one
  valid generation row retaining the frontier revision and digest.
- A malformed declaration reaching `record`: the pass is refused with `K022`
  and nothing is appended, matching the module's rule that a pass is recorded
  whole or not at all.
- An Imprimatur defect on `kronos/SKILL.md` or any other shipped document.

**The guard-test convention.** Every fix earns a test that fails without it.
For this work each guard is a specimen ledger plus the exact refusal code, held
in `plugins/hexaemeron/tests/test_kronos_scoreboard.py` beside the existing
K-code cases, and each shape rule in `tests/test_evolution_contract.py` gets a
specimen that the check must refuse. A guard that passes against the unfixed
tree is not a guard, so each is observed red before the fix lands.

Two guards are already written as failing specimens by this study's own
measurement: the header-shadowing case and the unclosed-fence case in item 5.
Both were driven against the real Kronos ledger and both reproduce.

**Runner contract.** Steps that claim a fix name
`python3 plugins/hexaemeron/tests/run_tests.py`; the runbook carries the exact
Elenchus command, report format and report file per step.

## 12. Decisions and their homes

[hypomnema](../plugins/hexaemeron/skills/hypomnema/SKILL.md) owns which
decisions earn a record and where each one lives.

Three decisions here are expensive to reverse, and they belong in one decision
record rather than three, because they are one choice seen from three sides:

1. The declaration is ledger policy owned by `VERSIONING.md`, with Kronos
   holding only the reader.
2. The declaration sits outside the four-field frontier digest, so an existing
   ledger's digest never moves, and the cost is that the ledger's own history
   cannot detect a changed declaration.
3. The scoreboard's per-pass declaration digest is what carries that detection
   instead, which is why the block is legible to a reviewer and durable to a
   later pass at the same time.

**Home.** One new decision record under `docs/decisions/`, authored as
`docs/decisions/drafts/<slug>.md` with a numberless heading and the stable
identity `adr/<slug>`, per
`docs/decisions/ADR-077-assign-adr-numbers-at-merge-not-at-authoring.md`. A
number is assigned at the integration merge, not while the branch is authored,
because a concurrent merge takes a branch-local maximum. If the run assigns a
number rather than a draft slug, it re-picks it immediately before pushing.

Two decisions do not earn a record. The closed `kind` and `availability`
vocabularies are cheap to extend by an ordinary `VERSIONING.md` change, and the
16-row cap is a bound, not a boundary. Both live in `VERSIONING.md` prose with
their reasons.

The `kronos-frontier-ranking` promise in `kronos/SKILL.md` gains the
declaration to its Evidence and the shape-not-truth statement to its Boundary,
which is a contract change rather than a decision record;
`tests/promise_machine_coverage.json` and
`plugins/hexaemeron/tests/fixtures/promise-machine/evaluation-cases.json` are
its homes.

## Boundaries this run works inside

**Always.**

- Both the root suite and the Hexaemeron suite before a commit, through
  `python3 scripts/run_checks.py`.
- The Imprimatur lint on every shipped document, then Brevitas, then the
  `AGENTS.md` written-record sequence in full.
- The recorded measurement in the design record before any performance claim.
- `python3 plugins/horos/skills/horos/scripts/horos.py scan . --write` when a
  change adds or alters a classified file.

**Ask first.**

- Adding a dependency. This run plans none; `kronos.py` stays stdlib-only.
- Changing the canonical frontier line, the four header fields, or any recorded
  digest.
- Touching `hexctl.py` or CI.
- Adding a value to the closed `kind` or `availability` sets after this run.
- Writing a declaration into a ledger this run does not own.

**Never.**

- Commit key material or an RPC credential.
- Edit a vendored directory, including the bundled Pashov suite.
- Delete or weaken a failing test to make a suite pass.
- Claim a command ran when it did not.
- Change Kronos's held `Next Fiat job`, its frontier revision, or its frontier
  digest.
- State or imply that a declared input exists, was verified, or makes a
  readiness score objective.
