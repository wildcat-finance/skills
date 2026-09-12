# Study: Ephoros reads E001 to E003 on the TypeScript surface it already opens

Assuming, unless corrected:

1. The run starts from `main` at `e7d0fdea1a636e06725fc55a55d02c24f74a64ee`, on
   branch `fiat/1420-ephoros-next-extend-e001-to-e003-to-the-typ`.
2. The pinned application clone is `wildcat-app-v2` at commit `564a189b`. That
   is the commit the ephoros evidence already names, not a commit chosen here:
   `docs/ephoros-wallet-address-telemetry-study.md` pins `564a189` in its first
   assumption and again in item 3, and the closing audit round of that run
   records that the pinned clone reads exactly 882 tracked TypeScript files. An
   extraction of `564a189b` holds exactly 882 `.ts`/`.tsx` files, so the
   identification is confirmed rather than assumed. This run reads it by
   detached extraction, `git -C "$APP_CLONE" archive 564a189b | tar -x -C
   .hexaemeron/validation/wildcat-app-v2`, from a local read-only clone of the
   application repository whose own head has moved since. The extraction is
   untracked and is never edited, formatted, installed or built.
3. Python 3.11 and the standard library are the implementation boundary. The
   attributed lexer vendored at `plugins/hexaemeron/lib/typescript_lexer.py` is
   the only permitted TypeScript reader. No Node invocation, no tree-sitter, no
   new dependency.
4. E000 to E005 keep their numbers. The Python and block-YAML behaviour of
   every rule is unchanged; only the TypeScript surface gains E001, E002 and
   E003. E005 keeps the address-shaped label subset it claimed from E002, so
   the TypeScript E002 recogniser inherits that split rather than reopening it.
5. A template literal carrying no `${}` interpolation is a constant string and
   does not fire E001. This diverges from the Python side, where an f-string
   with no placeholder is still a `JoinedStr` and fires. The divergence is
   deliberate and is stated in item 3 as a limit rather than left implicit.
6. This is frontier work on the `typescript-rule-parity` revision. Closing it
   moves the ephoros evolution counter; the label is whatever
   `tests.test_evolution_contract` accepts for a completed frontier from
   `ephoros-v1.2.0`, and the runbook declares that relation rather than writing
   a concrete token, because the previous run wrote `ephoros-v0.3.0` in its own
   study and the contract's arithmetic corrected it at step 4. The run owes the
   cold read of mutable first-party marketplace prose that
   `plugins/hexaemeron/skills/VERSIONING.md` requires of every frontier run.
   The source-coverage refresh clause in the same section does not apply, since
   it names Alexandria, Tabularium, Lazarus and Probitas.
7. The security suite is waived for this run, so an audit round runs the
   phylax, ephoros and hypomnema lints plus the repository root suite.

I will proceed on these assumptions unless corrected.

## 1. Problem statement

`plugins/hexaemeron/skills/ephoros/scripts/ephoros.py` reads `.ts` and `.tsx`
files today, through the shared masked lexer, for one rule. E005 finds an
address used as a metric label, a dashboard key or a log index in TypeScript.
E001, E002 and E003 read Python only, so a log message assembled by
interpolation, an unbounded metric label and a mean-summarised duration are
caught in the language the marketplace's tooling is written in and missed in
the language the application ships in. Build that parity, for Wildcat
contributors and for the Fiat gates that run the tree lints on every step.

A working prototype is established by these commands, in this order, on the
finished tree:

- `python3 -m unittest plugins.hexaemeron.tests.test_ephoros_checker` reports
  one E001 for an interpolated logger message, one E002 for an unbounded
  metric label and one E003 for a mean-summarised duration, each held by a
  TypeScript fixture observed red before its recogniser lands, and each with a
  close safe neighbour that stays clean.
- `python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
  scripts docs` exits 0 over this marketplace, which is the exact argument
  vector `lint-ephoros` carries in `tests/check-map-v1.json`.
- `python3 .hexaemeron/design-probes/clone_verdict.py` reports the E001 count
  over the pinned application clone and that count is 14, matching the verdict
  stated in item 2 rather than a clean run assumed in advance.
- `python3 plugins/hexaemeron/tests/run_tests.py` passes.
- `python3 -m unittest discover -s tests` passes, 1,623 tests at this base.

The demo path is that block, run in order.

## 2. Prior art

**In this repository.** The checker is one 1,055-line script. Its TypeScript
pass, `check_typescript`, lexes the file, blanks comment and string spans into
a mask that preserves offsets, maps every opening bracket to its closer in one
stack pass, and then walks the opening brackets. For each one it parses the
dotted chain backwards with `_ts_chain_before`, drops anything rooted at
`console`, and applies three cheap sink-name gates: a metric word anywhere in
the chain, a `.labels` call, or a log word in the penultimate segment. Only a
bracket that passes a gate pays for span work, which `_TsSpanIndex` serves from
per-file tables built once and read by bisection. E001 to E003 sit in the
Python `ast.NodeVisitor` above it and never see a TypeScript file.

The three recognisers this run needs sit differently against that machinery.
E001 and E002 land on brackets the existing gates already identify: a
`logger.debug(` bracket is already classified as a log call, and the
`labels:`, `labelNames:`, `tags:` and `attributes:` containers are already
found and split into keys by `_label_container`. E003 does not, because a mean
over a duration is an assignment rather than a call on a named sink, so it is
the one recogniser that needs a shape the current pass does not already
produce. That asymmetry is what the design options below turn on.

**The last two merged pull requests that changed the ephoros skill directory,
both read.**

- [skills#1238](https://github.com/wildcat-finance/skills/pull/1238), "Govern
  one demonstration ledger per skill" (merged 2026-09-06), which added
  `plugins/hexaemeron/skills/ephoros/DEMONSTRATION.md` among 43 files and later
  swapped its numbered decision-record citation for the stable slug
  `adr/govern-real-data-demonstrations-separately`. Carried forward in its
  body: finding `S2-R1-03`, an accepted ADR number collision against the
  default branch, resolved by merge-time decision assignment rather than in
  that run. It stays out of scope here by name, and this study takes the
  operational lesson instead: a new decision record picks its number
  immediately before it is pushed, not when it is drafted.
- [skills#1107](https://github.com/wildcat-finance/skills/pull/1107), "data:
  swap VENUES.json for the generated SOURCES.md and wire its refresh" (merged
  2026-09-01), which replaced the coverage manifest and added the
  `- Sources:` line to the ephoros ledger. Carried forward in its body: the
  refresh obligation in `VERSIONING.md`, which fires on a completed frontier
  job on Alexandria, Tabularium, Lazarus or Probitas. Ephoros is none of those,
  so the obligation does not attach to this run, and `SOURCES.md` is generated
  output that stays untouched.

Neither pull request left ephoros lint work unfinished.

**Audit records.** `python3
plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .` was run
from the target root and the whole-set currency check exits 0, with every
in-scope pair reported `committed=match`. The verified synopsis is therefore
the admitted reading view. Two in-scope sources carry ephoros content, and for
both the authoritative source was read directly rather than its synopsis,
because the synopses compress 14,172 lines to 426 and 71 lines to 3 and the
per-round finding ids and lead text this study has to carry forward do not
survive that compression:

- `audit/AUDIT.md`, source read directly at lines 5,951 to 6,268 (the eight
  `E319` alert-annotation rounds and two post-cap closures, sixteen findings)
  and 7,343 to 7,660 (the seven `Ephoros wallet-address telemetry` rounds that
  built the TypeScript pass this run extends). Sixteen findings resolved in the
  first group, thirteen in the second across `S3-R1-01` to `S3-R1-09`,
  `S3-R2-01` to `S3-R2-04`, `S3-R3-01`, `S3-R3-02` and `S3-R4-01`; the step 1,
  step 2, step 3 round 5 and step 4 rounds each recorded `No findings.` and
  status `clean`. No finding in either group is open. No entry carries a
  `[missing legacy field: ...]` marker.
- `plugins/hexaemeron/audit/AUDIT.md`, source read directly, 71 lines. Its
  `F-01` to `F-10` concern `hexctl.py`, `hook_gate.py` and the vendored prose
  lint, and none touches ephoros.

Leads not pursued in those rounds, each carried forward here by name:

- **The shared lexer's recursion defect** in
  `plugins/hexaemeron/lib/typescript_lexer.py`, which reproduces identically
  under phylax and predates both runs. It stays open and outside this run: the
  fix belongs to the owning surface, and this checker contains it at its own
  boundary through the unsuppressible E000 path, re-confirmed by 178
  fail-closed fuzz cases in step 3 round 5. This run adds no new reader, so it
  neither widens nor narrows that containment.
- **The `s?` suffix family shared by `ADDRESS_KEY` and `UNBOUNDED`**, which
  misses `-es` plurals such as `addresses` and `hashes`. It is live here,
  because the TypeScript E002 recogniser has to choose a vocabulary. This study
  resolves it by construction rather than by reopening the Python rule: the
  TypeScript side matches on the same word set E005 already splits out of
  `walletAddress` and `wallet_address` alike, where `addresses` and `hashes`
  are ordinary words, so the
  plural gap does not exist on the new surface. The Python gap stays open, and
  item 3 records the resulting asymmetry as a stated limit.
- **Nested mappings under a YAML `labels:` key pass silently**, and **the E005
  message says wallet address for any address fragment such as `ip_address`**.
  Both are stated limits of E005 in `SKILL.md`, neither is TypeScript, and
  neither is reopened.
- **A Python `#` pragma matches inside a Python string.** Open, on the Python
  surface, outside this run's diff. The TypeScript pragma already reads from
  genuine line-comment spans only, which is the behaviour the new findings
  inherit.
- **Computed object keys, method-call dashboard access, a generic-call type
  argument that hides a chain, and read-versus-write subscripts.** Each is a
  lexical depth declared a non-goal with parity across both language sides.
  The three new recognisers hold the same line; item 3 restates it.
- **Two pre-existing hypomnema pointer hits inside historical Hermes entries of
  `audit/AUDIT.md`.** Outside the acceptance lint scope, unchanged here.

The performance findings in that history are design evidence rather than
background. `S3-R2-02` measured a forward-scanning chain grammar at 62.8
seconds on a 100 KB file and hours at the 1 MiB cap; `S3-R3-01` extrapolated a
per-bracket forward scan to roughly 1.9 hours at the cap; `S3-R4-01` measured
sink-named overlapping spans at 107 seconds on 160 KB. All three were fixed by
anchoring work to bracket positions and indexing each file once. A new
recogniser that reintroduces a forward scan reintroduces that class, inside the
untrusted-read boundary. The design record below measures exactly that.

**The surfaces, surveyed rather than assumed.**

- This marketplace holds 22 tracked `.ts` and `.tsx` files. Nineteen sit under
  a `fixtures` directory the walk already skips. The three the walk reaches are
  `plugins/horos/examples/fixture-ts/market.ts`, which contains one
  `console.log` and no logger, label set or mean, and the two Alexandria
  upstream files, which contain none of the three shapes. The current lint over
  the gate's own argument vector, `plugins tests scripts docs`, exits 0.
- The pinned application clone at `564a189b` holds 882 tracked TypeScript
  files. It has 21 logger call sites and no metric label container at all: a
  search for `labels:`, `labelNames:`, `tags:` or `attributes:` followed by an
  array or object literal returns nothing, `.labels(` returns nothing, and
  `mean(`, `average(`, `avg(` and `fmean(` return nothing. Its telemetry is the
  SDK logger imported from `@wildcatfi/wildcat-sdk/dist/utils/logger`, the
  consent-gated Hotjar init, and `console.*` output, which the lint excludes
  the way it excludes `print`.
- Of the 21 logger call sites, 14 pass an interpolated template literal as the
  first argument and 7 pass a constant one. The known interpolated logger
  message the held job names is
  `src/app/[locale]/borrower/market/[address]/hooks/useGetLenders.ts`, the call
  opening at line 29 and its template argument at line 30, reading
  ``logger.debug(`Got authorised lenders : ${res.data.market?.controller?.authorizedLenders}`)``.
  It interpolates the authorised lender list into the message. The other 13 sit
  in `useGetWithdrawals.ts` (7), `useGetLenderWithdrawals.ts` (5) and
  `updateMarkets.ts` (1).

**The verdict this run will record.** The clone does not run clean. Under the
rule this study picks, E001 fires 14 times over the pinned clone, truly, at the
14 sites above, and the named message is one of them. It is not excluded by a
narrowing rule, and no suppression pragma is added to a tree this run may not
edit. The acceptance permits exactly this: it asks for a verdict decided on its
own evidence, with the known message either firing truly or excluded by a
stated rule. The clean-run criterion in item 1 therefore covers this
marketplace only, which is where the previous run's criterion also had force.

Outside this repository, the closest prior art is a linter rule family rather
than a paper: `eslint-plugin-no-template-curly-in-string` and the structured
logging rules in `pino` and `winston` documentation each state the same shape,
that a message with values welded into it cannot be queried by field. None of
them reads the Wildcat rule set, and none is a dependency this study proposes.

## 3. Constraints and non-goals

- Starting ref `main` at `e7d0fdea1a636e06725fc55a55d02c24f74a64ee`. The
  application clone is read at `564a189b` by detached extraction, read-only.
- Python 3.11, standard library only, plus the vendored lexer in
  `plugins/hexaemeron/lib/`.
- Finding codes are stable interfaces. E000 to E005 keep their numbers and
  their Python and block-YAML behaviour. The only committed expectation that
  moves is the TypeScript fixture `logger-message.ts`, whose test currently
  asserts an empty finding list; it becomes one E001 and no E005, under a guard
  test observed red first, exactly as the E002-to-E005 move was pinned.
- `lint-ephoros` in `scripts/run_checks.py` runs
  `plugins/hexaemeron/skills/ephoros/scripts/ephoros.py`, which is the very
  script this run changes. Every audit round therefore executes the tree's
  current checker over the tree, and a defect in a new recogniser can present
  as a lint failure somewhere unrelated. Read a non-zero `lint-ephoros` as a
  finding against this run's own diff before reading it as a finding against
  the file it names.
- Every tracked-file edit changes byte counts that `HorosCensusCurrencyTests`
  reads, so `python3 plugins/horos/skills/horos/scripts/horos.py scan . --write`
  then `python3 plugins/horos/skills/horos/scripts/horos.py scan . --census
  --write` run before every commit.
- The commit gate in `.githooks` runs the repository root suite, 1,623 tests at
  this base. The root suite command is `python3 -m unittest discover -s tests`,
  taken from the `root-suite` scope in `tests/check-map-v1.json` and confirmed
  against `python3 scripts/run_checks.py --plan`.
- `SOURCES.md` is generated by a maintainer-held tool and is never hand-edited.
- `plugins/hexaemeron/skills/ephoros/DEMONSTRATION.md` pins source digests, so
  a change to the fixture it names re-pins that digest in the same commit. The
  demo frontier is a separate lane and does not move here.
- Non-goals, each deliberate. A TypeScript analogue of E004, which is a YAML
  alert rule and has no TypeScript form. Any `console.*` discipline. Dataflow
  or rename tracking: the rules are lexical, so a duration reaching a mean
  through an innocently named variable passes. Computed object keys, method-call
  dashboard access and chains hidden behind a generic type argument, each a
  parity-preserving lexical depth nobody has asked to widen. The Python `s?`
  plural gap and the Python string-pragma behaviour, both open on their own
  surface. The shared lexer's recursion defect. Widening the walk beyond
  `.py`, `.yaml`, `.yml`, `.ts` and `.tsx`. CI changes.
- The task issue's own boundary, carried here as written: this job does not
  establish that the three recognisers are correct on TypeScript beyond their
  fixtures, and a stated verdict over the pinned clone does not establish that
  the application emits no unbounded telemetry. The lint covers the rules the
  parser implements and nothing else.
- **Always.** Both suites, `python3 -m unittest discover -s tests` and
  `python3 plugins/hexaemeron/tests/run_tests.py`, before a commit. The Horos
  scan and census write before a commit. The phylax, ephoros and hypomnema
  lints before a step closes. The imprimatur lint on every shipped document.
  A recorded measurement before any performance claim.
- **Ask first.** Adding a dependency. Touching CI. Changing a finding code's
  meaning or number. Widening the walk to a new suffix. Editing the extracted
  application clone. Adding a suppression pragma to any tree this run does not
  own.
- **Never.** Edit a vendored directory or the extracted clone. Hand-edit
  `SOURCES.md`. Weaken an existing rule to make a tree pass. Delete a failing
  test. Commit a credential. Claim a command ran when it did not. Write an
  absolute path outside this repository into a shipped document.

## 4. Design options

The recognisers themselves are settled by the acceptance: E001 fires when a log
call's first argument is a message built by formatting, meaning an interpolated
template literal or a concatenation involving a string literal; E002 fires when
a key in a label, tag or attribute container matches an unbounded word that
E005 has not already claimed; E003 fires when a declaration or assignment whose
name or expression carries a duration word takes a mean, meaning a call to
`mean`, `average`, `avg` or `fmean`, or the reduce-over-length idiom. What is
open is how the checker reads TypeScript to find them, and that choice is what
the audit history above makes expensive to get wrong. Three constructions were
drawn and all three were measured.

**A. `span-index`.** Extend the existing bracket-anchored pass and
`_TsSpanIndex` inside `check_typescript`. E001 and E002 attach to brackets the
current sink gates already classify and read their argument or key spans from
the tables the file already built. E003 adds one indexed pass for the
assignment shape, keyed to the same bracket tables. The trade: the span index
is the largest structure in the file and every new recogniser has to be written
against its bisection discipline rather than against the text, which is a real
comprehension cost paid by whoever reads the checker next.

**B. `unmasked-regex`.** Recognise the three shapes with regular expressions
over the raw file text, with no lexer and no mask. Cheapest to write. The trade
it makes is the one the E319 rounds already priced: scanning unmasked text
means a commented-out or quoted occurrence is indistinguishable from a real
one.

**C. `forward-scan`.** Share the lexer and the mask, but add a second
independent pass that walks every identifier chain forward to its bracket and
reads each argument span on its own, rather than reusing the span index. It
keeps the mask's correctness and avoids coupling new recognisers to the index.
The trade is that a forward scan reads each candidate span from its own start,
which is the shape `S3-R2-02` and `S3-R3-01` measured.

The design record at `.hexaemeron/design-evidence.json` selects among them from
five checked criteria rather than from this prose, and the reports beneath
`.hexaemeron/reports/` carry each measured value. The measurement corpus for
recall is the 882 clone files plus one stated decoy file holding two
occurrences that appear only inside a block comment and inside a string
literal, so a reader that respects the mask reports 14 and a reader that does
not reports 16. The timing specimen is 64 KiB of nested log-call brackets, the
shape the audit history names, measured as the median of three runs.

The results, at `design-lock`:

| Criterion | `span-index` | `unmasked-regex` | `forward-scan` |
| --- | --- | --- | --- |
| `interpolated-message-recall`, equals 14 | 14, pass | 16, fail | 14, pass |
| `cap-scale-runtime`, at most 2,000 ms | 27, pass | 2,813, fail | 2,720, fail |
| `reader-peak-space`, minimise bytes | 831,792 | 132,667 | 198,562 |
| `stdlib-only`, at most 0 | 0, pass | 0, pass | 0, pass |
| `fail-closed-bypass`, equals 0 | 0, pass | 1, fail | 0, pass |

`unmasked-regex` fails three gates: it counts the two decoy occurrences, it
scans each candidate span forward from its own start, and it still reports a
site in a file the shared lexer refuses, so it walks straight through the E000
boundary that the untrusted-read control depends on. `forward-scan` respects
the mask and the boundary but is 100 times slower on the stated specimen, which
extrapolates past the cap into the class the audit already closed twice. Both
are removed by hard gates, `span-index` is the sole survivor, and the record's
`unique-frontier` rule selects it. `python3 design_evidence.py
.hexaemeron/design-evidence.json --transition design-lock` exits 0.

The comparative metric records the price honestly: `span-index` is the most
expensive of the three in space, 831,792 bytes of peak traced allocation
against 132,667 for the cheapest, because the tables it builds are the reason
it is fast. It buys a hundredfold in time with roughly sixfold in transient
memory on a file bounded at 1 MiB, and no candidate that beat it on space
survived a correctness or recovery gate.

One conformance cell stays pending on every candidate: `clone-verdict-e001`
blocks `integration`, resolves through `python3
.hexaemeron/design-probes/clone_verdict.py`, and requires the count to equal
14. It cannot resolve before the recognisers exist, and a guessed value there
would be exactly the fabrication the record refuses.

Two sub-decisions ride the pick.

- **A constant template literal is not formatting.** ``logger.debug(`Getting
  all markets...`)`` is a stable message with no values welded in, and firing on
  it would report 21 sites over the clone instead of 14 while catching nothing
  the rule exists to catch. Python's E001 does fire on a placeholder-free
  f-string, because `ast` gives it a `JoinedStr` either way. The two surfaces
  therefore differ, deliberately, and item 3 records it.
- **The committed `logger-message.ts` expectation moves.** That fixture holds
  ``logger.debug(`Retrieved market updates for lender ${walletAddress}`)`` and
  its test asserts an empty finding list, pinning that an address inside a
  message is not an E005 key. Under E001 it becomes one finding. The test is
  re-pinned to assert one E001 and no E005, which keeps the original claim
  intact and states the new one, under a guard observed red before the
  recogniser lands.

## 5. Risk register seed

The audit loop should look hardest at three things: the untrusted-read boundary
this run adds work behind, the clone verdict, and the fixture whose expectation
moves. The first is where every serious finding of the previous run lived, and
the second is the one criterion an implementer could satisfy by narrowing a
rule until the number came out clean.

```risk-register
recogniser-scan-shape | new per-bracket work inside the TypeScript pass | every new recogniser reads from the per-file index rather than scanning a span forward, and a cap-scale specimen is measured before and after
e000-containment | a TypeScript file the shared lexer cannot terminate | the three new codes stay unreportable when lexing fails, and a pragma still cannot suppress E000
clone-verdict-honesty | the stated count of 14 E001 findings over the pinned clone | the count is produced by the shipped checker over the extracted clone, and a recogniser narrowed to move that number is a finding rather than a fix
constant-template-boundary | a template literal with no interpolation | it stays clean on the TypeScript side and the Python placeholder-free f-string keeps firing, each pinned by a test
e002-e005-overlap | a label key that is both address-shaped and unbounded | the address subset keeps reporting E005 alone on the TypeScript side, as it already does on the Python side
e003-duration-shape | a mean taken over something that is not a duration | sentence lengths, layout positions and prices stay clean, and the reduce-over-length idiom fires only under a duration-named target or expression
fixture-repin-scope | the committed logger-message.ts expectation | the re-pin asserts one E001 and no E005, so the original E005 claim is preserved rather than deleted
marketplace-clean-honesty | the three walked TypeScript files in this repository | the tree lint exits 0 without a pragma, and a fixture-directory specimen is proved unreachable by the walk
pragma-surface-parity | suppression of the three new TypeScript codes | a reasoned line comment suppresses on the line and the line above, a bare pragma suppresses nothing, and pragma text in a string, template or block comment suppresses nothing
self-lint-recursion | lint-ephoros running the script this run edits | a non-zero lint is triaged against this run's diff first, and the checker is never edited to make its own lint pass
```

What the block cannot carry: `clone-verdict-honesty` is the risk that decides
whether this run is worth anything. The held job asks for a verdict on the
clone's own evidence, and the tempting failure is to add an exclusion until the
count reaches zero and call that clean. Fourteen is the answer this study
measured before any recogniser existed. If the finished checker reports a
different number, the fix is to explain the difference, not to move the rule
until the number returns.

## 6. Glossary seeds

- Message built by formatting: a log call's first argument assembled from
  values, meaning an interpolated template literal or a concatenation involving
  a string literal, as opposed to a stable name with fields beside it.
- Constant template literal: a backtick string carrying no `${}`, semantically
  a quoted string and outside E001 on the TypeScript side.
- Label container: the array or object literal following a `labels`,
  `labelNames`, `label_names`, `tags` or `attributes` property, or the argument
  of a `.labels(...)` call.
- Unbounded label: a label name drawn from a source with no small fixed set,
  such as a hash, a transaction id, a request or run id, a raw URL or the text
  of an error.
- Mean-summarised duration: a duration reduced to an arithmetic average, by a
  named mean function or the reduce-over-length idiom, instead of recorded as a
  histogram.
- Masked source: TypeScript text whose comment and string spans are blanked to
  spaces with offsets preserved, so a recogniser cannot match inside either.
- Span index: the per-file tables built once from the mask that answer bracket,
  comma, colon and property questions by bisection.
- Sink gate: the cheap chain-name test that decides whether a bracket is a
  telemetry sink before any span work is paid for.
- Reasoned pragma: `// ephoros: allow <why>` as a genuine line comment, on the
  finding line or the one above; a bare pragma suppresses nothing.
- Pinned application clone: `wildcat-app-v2` at `564a189b`, read by detached
  extraction into an untracked directory and never edited.

## 7. Sources

- `plugins/hexaemeron/skills/ephoros/scripts/ephoros.py`, read in full: the
  checker, its Python visitor, its block-YAML pass, `check_typescript`,
  `_ts_chain_before` and `_TsSpanIndex`.
- `plugins/hexaemeron/skills/ephoros/SKILL.md`, `EVOLUTION.md`,
  `DEMONSTRATION.md` and `agents/openai.yaml`: the rule prose, the held job and
  its acceptance, the pinned demonstration source digest.
- `plugins/hexaemeron/tests/test_ephoros_checker.py`, 720 lines, 115 tests, and
  the 25 fixtures under `plugins/hexaemeron/tests/fixtures/ephoros/`: the
  conventions the new fixtures extend, and the `logger-message.ts` expectation
  that moves.
- `plugins/hexaemeron/lib/typescript_lexer.py` and
  `plugins/hexaemeron/skills/phylax/scripts/phylax.py`: the shared reader and
  the boundary precedent.
- `plugins/hexaemeron/skills/VERSIONING.md`, section "What every frontier run
  owes": the cold-read obligation and the source-refresh clause that does not
  apply here.
- `docs/ephoros-wallet-address-telemetry-study.md` and its runbook: the
  previous frontier run, and where the clone commit `564a189` is pinned.
- `docs/decisions/ADR-010-split-address-telemetry-from-boundary-control.md`:
  the ephoros and phylax line over shared TypeScript files.
- `audit/AUDIT.md`, source read directly at lines 5,951 to 6,268 and 7,343 to
  7,660; `plugins/hexaemeron/audit/AUDIT.md`, source read directly.
  `audit_synopsis.py --check .` exits 0 over the whole set.
- [skills#1420](https://github.com/wildcat-finance/skills/issues/1420): the
  task issue and its stated boundary.
- [skills#1238](https://github.com/wildcat-finance/skills/pull/1238) and
  [skills#1107](https://github.com/wildcat-finance/skills/pull/1107): the last
  two merged pull requests that changed the ephoros skill directory.
- `tests/check-map-v1.json` and `scripts/run_checks.py --plan`: the
  `root-suite` and `lint-ephoros` argument vectors.
- The pinned application clone at `564a189b`:
  `src/app/[locale]/borrower/market/[address]/hooks/useGetLenders.ts`,
  `.../borrower/market/[address]/hooks/useGetWithdrawals.ts`,
  `.../lender/market/[address]/hooks/useGetLenderWithdrawals.ts`,
  `.../borrower/hooks/getMaketsHooks/updateMarkets.ts`, `package.json`,
  `src/config/query-keys.ts`, `src/utils/timestamp.ts`.

## 8. Signals, and the questions behind them

None, and here is why. The deliverable is a lint invoked from a terminal and
from the Fiat gates, so it has no unattended path and nobody is woken by it.
Its whole visibility contract is its exit code and its finding lines, and the
audit rounds already record both. [ephoros](../plugins/hexaemeron/skills/ephoros/SKILL.md)
owns what a signal must carry; this run changes what that skill enforces on
other people's code, not what the run itself emits.

One thing is worth saying rather than leaving implicit. The finding line is the
only output a reader gets, so the three new messages have to name the shape and
the remedy in one sentence each, the way the existing five do. That is a
content obligation on the implementation, not a signal to add.

## 9. Boundaries, per capability

This run opens no new boundary. It adds recognisers behind a boundary the
previous run already opened and the previous run's rounds already audited: the
checker reads untrusted TypeScript from an outside repository. What is worth
taking there is the checker's own runtime, and the controls are unchanged, a
1 MiB read cap applied before lexing, E000 fail-closed on any construct the
lexer cannot terminate, no execution or import of inspected source, and no
pragma able to suppress E000. The two register lines `recogniser-scan-shape`
and `e000-containment` are how the audit loop checks that adding work behind
that boundary did not weaken it, since a quadratic recogniser inside a bounded
read is a denial of the gate rather than a slow lint.

The line between the two lints is unchanged and is recorded once, in
[ADR-010](../docs/decisions/ADR-010-split-address-telemetry-from-boundary-control.md).
[phylax](../plugins/hexaemeron/skills/phylax/SKILL.md) owns secrets, raw HTML,
persisted session credentials, fetch hosts and address linkage; ephoros owns
the shape of the telemetry a step leaves behind. E001, E002 and E003 are
telemetry shape on both surfaces, so no pattern moves and no new record is
needed for the boundary itself.

## 10. The budget, or its absence

There is a budget, because the untrusted-read boundary makes runtime a control
rather than a preference, and because three separate audit findings in this
checker's own history were quadratic scans behind that boundary. The budget:
the full lint over the pinned application clone, 882 TypeScript files, stays
under two seconds, and the stated 64 KiB adversarial nested-bracket specimen
stays under 2,000 milliseconds. The measuring commands are `python3
.hexaemeron/design-probes/runtime.py span-index` for the specimen and `time
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py
.hexaemeron/validation/wildcat-app-v2` for the clone, each recorded as the
median of three runs with its spread. The current baseline is the previous
run's recorded 0.86 seconds over the same clone, and 27 milliseconds on the
specimen through the existing pass.
[metron](../plugins/hexaemeron/skills/metron/SKILL.md) owns what a budget
carries and how it is checked; this study names the numbers and the commands
and leaves the method there.

## 11. The fail-closed posture

The lint stops rather than guesses. An unreadable file, a file over 1 MiB, an
unparseable Python module and a TypeScript construct the lexer cannot terminate
each report E000 and fail the run; findings exit 1; a bad invocation exits 2; a
bare pragma suppresses nothing and no pragma suppresses E000. The three new
codes inherit all of that unchanged, which is what `e000-containment` is there
to confirm rather than assume.

During the audit loop every fix follows the guard-test convention this
checker's own history already practises across twenty-nine resolved findings:
the failing case lands as a test observed red before the fix and kept green
after, with the red observation recorded in the round.
[elenchus](../plugins/hexaemeron/skills/elenchus/SKILL.md) owns the triage
order and the guard rule; this study names where they apply. One triage
ordering is specific to this run and is stated in item 3: because
`lint-ephoros` executes the script under change, a non-zero lint is read
against this run's diff before it is read against the file it names.

## 12. Decisions and their homes

Three decisions here are expensive to reverse, and
[hypomnema](../plugins/hexaemeron/skills/hypomnema/SKILL.md) owns which
decisions earn a record and where each one lives.

- **The three rules' TypeScript scope, including the constant-template
  boundary and the camel-case word vocabulary.** Once published, other tools
  cite the codes and read the counts, so narrowing or widening later changes
  recorded findings. Home: the mechanical-subset section of
  `plugins/hexaemeron/skills/ephoros/SKILL.md` and the new evolution row in its
  `EVOLUTION.md`, which is where E004's and E005's equivalent decisions live.
- **The stated verdict of 14 E001 findings over the pinned application clone at
  `564a189b`.** It is the first time this checker records a non-clean verdict
  over a real tree, and a later reader will otherwise assume the omission of a
  clean-run claim was an oversight. Home: the same evolution row, stating the
  count, the commit and that the finding is true rather than suppressed.
- **The divergence between the Python and TypeScript readings of E001.** It
  binds two surfaces of one code, it will be read as a bug by whoever meets it
  first, and the reason is a property of the two parsers rather than of the
  rule. Home: an architecture decision record under `docs/decisions/`, pointed
  at from the `SKILL.md` sentence rather than restated in it. Its number is
  picked immediately before the branch is pushed, because numbers are checked
  against the default branch and collide when drafted early, which is what
  finding `S2-R1-03` in skills#1238 cost.
