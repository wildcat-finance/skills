# Unified live and archive collection

One Probitas `collect` run should be able to gather live or fixture-backed
adapter evidence and archive-backed Alexandria evidence into a single evidence
file, with every coverage row naming which of the two produced it.

Task issue: [skills#391](https://github.com/wildcat-finance/skills/issues/391).
Run branch `fiat/391-unified-live-and-archive-collection`, cut from `main` at
`2b1c5cccca6d688c5d0223d311dd8df177ca5614`.

Assuming, unless corrected:

1. The exact interpreter in `.python-version`, currently `3.14.6`, with the
   standard library and `unittest`. Probitas takes no third-party dependency
   and this run adds none.
2. Issue #391 is generation work on the `probitas` skill. It leaves the held
   frontier job, `morpho-midnight-coverage`, untouched, and the ledger gains
   exactly one generation row.
3. The Wave Atlas review on #391 says to keep it behind the current frontier
   for sequencing reasons. #390 has not run. The user asked for #391 by name,
   so it runs first; nothing in the work below depends on a Morpho Midnight
   adapter existing.
4. `alexandria` is the only archive source Probitas reads. No second archive
   backend is designed for.
5. The two routes are disjoint today and the design must not assume they stay
   that way.

## 1. Problem statement

`cmd_collect` in `plugins/probitas/scripts/probitas.py` returns as soon as
`--alexandria-index` is given:

```python
if args.alexandria_index:
    _collect_alexandria(args.alexandria_index, evidence)
    return _write_evidence(args, evidence)
```

`--fixtures` and `--alexandria-index` also sit in a mutually exclusive argparse
group. So archive-backed Goldfinch and Clearpool history can never share an
evidence file with live or fixture-backed Wildcat, Morpho Blue, Euler v1 and
Euler v2 findings. A counterparty who borrowed on a wound-down venue and on a
live one has two dossiers and no single one, which is not the record a lender
is trying to read.

Built for whoever runs `collect` against a counterparty: an underwriter, a
business-development lead, or the reviewer checking their document afterwards.

A working prototype means all of this holds:

- `collect` accepts an Alexandria index together with an adapter route and
  writes one evidence file carrying both sets of records.
- Every coverage row states its source class, and an archive row names the
  Alexandria releases behind it.
- Gate 2 counts every coverage row rather than collapsing rows that share a
  venue, and every registry venue still has at least one row.
- `--alexandria-index` on its own reaches no network, exactly as today.
- The demo path proves it offline. `plugins/alexandria/examples/credit-history-v0/demo.py`
  builds the index, runs the union, and its pinned evidence and dossier
  digests rebuild byte for byte.

Checked by: `python3 -m unittest discover -s plugins/probitas/tests -t .`,
`python3 -m unittest discover -s plugins/alexandria/tests -t .`,
`python3 -m unittest discover -s tests`, and
`python3 plugins/alexandria/examples/credit-history-v0/demo.py build` followed
by `verify` on the same output.

## 2. Prior art

Read in this repository, at `2b1c5cc`:

- `plugins/probitas/scripts/probitas.py`, `cmd_collect` and
  `_collect_alexandria`. The early return and the mutually exclusive group are
  the whole defect.
- `plugins/probitas/scripts/probitas_lib/evidence.py`. `Coverage` carries
  `venue`, `status`, `endpoint`, `block_range`, `note`, `records` and nothing
  naming a source class. `Evidence.add_coverage` appends without checking for
  a venue it already holds.
- `plugins/probitas/scripts/probitas_lib/gates.py`. `gate_2_coverage` builds
  `rows = {row["venue"]: row for row in payload["coverage"]}`, so two rows for
  one venue silently become one and the surviving row is whichever came last.
  `known_tokens` reads coverage fields from the fixed tuple
  `("venue", "status", "endpoint", "block_range", "note", "records")`, so any
  field added to a coverage row is outside gate 3's permitted-figure set.
- `plugins/probitas/scripts/probitas_lib/render.py`. `_coverage` prints
  `| Venue | Status | Range | Records | Note |`; `load` requires
  `schema == 1`.
- `plugins/probitas/scripts/probitas_lib/adapters/__init__.py`.
  `unchecked_coverage` already separates `unconfigured` from `unimplemented`,
  which is the distinction the merged "nobody checked" row has to keep.
- `plugins/alexandria/scripts/alexandria_lib/probitas.py`. `translate` emits
  records and coverage only for `SUPPORTED_VENUES = {"clearpool", "goldfinch"}`
  and already puts release, capture and row identities in each record's values
  and the release ids in the coverage note's prose.
- `plugins/alexandria/examples/credit-history-v0/`. `demo.py` runs Probitas
  over the built index and `expected-probitas.json` pins the evidence and
  dossier SHA-256 and the coverage status counts, so a schema change to
  Probitas lands as a receipt regeneration here.
- `plugins/alexandria/tests/test_index.py` invokes `probitas.py collect
  --alexandria-index` directly.
- Root invariants: `tests/test_evolution_contract.py` fixes the generation
  arithmetic and the frontier digest, `tests/test_version_propagation.py`
  pins `probitas` at package `0.1.1` in a hard-coded map,
  `tests/promise_machine_coverage.json` holds one row per promise id, and
  `.agents/skills/promise-machine/runtime/` is generated by
  `scripts/portable_promise_machine.py sync` and must never be hand-edited.
- `plugins/probitas/tests/test_docs.py` turns the README's counts into
  assertions and requires every `collect` flag to appear in the README as
  `` `--flag` ``.

Merged pull requests that last changed this surface:

- [#62](https://github.com/wildcat-finance/skills/pull/62), *Publish
  Alexandria lending-data archive*, merged 2026-08-16. Introduced
  `--alexandria-index`, the bridge, and the offline demonstration. Its own
  cold read fixed an operator-chosen SQLite filename reaching a
  Markdown-bound coverage field, which is why the endpoint label is the fixed
  string `Alexandria index`. No carried-forward section; the union was not
  recorded as deferred anywhere except issue #391.
- [#65](https://github.com/wildcat-finance/skills/pull/65), *Add Euler
  coverage to Probitas*, merged 2026-08-17. Added the Euler v1 and v2
  adapters and last touched `probitas.py`. Reports 276 Probitas tests, which
  is the count the suite still runs. No carried-forward section.

Audit records. The whole-set currency check passes, so a synopsis is the
normal reading view:

```text
python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .   exit 0
```

- `plugins/probitas/audit/AUDIT.md` maps to `plugins/probitas/audit/AUDIT_SYNOPSIS.md`,
  `committed=match`, 24 rounds. Read the synopsis, not the source. Findings
  carried forward into this run's risk register: S2-R1-01, a URL source
  escaping a Markdown link, which is why anything operator-supplied reaching a
  table cell is a boundary here; S2-R1-02, an address silently keeping the
  last of two provenance tiers, which is the same silent-overwrite shape as
  gate 2's venue-keyed row map; PP-01 and RM-02, README counts that went stale
  and were fixed by turning them into assertions. Every listed finding is
  `fixed` or `accepted`. The only open lead is S1-R1-03, digest-pinning CI
  actions, `accepted` and unrelated. Legacy rounds predate the current record
  schema, so `Covered`, `Not checked` and `Elenchus verdict` read as
  `[missing legacy field: ...]` and stay unknown rather than being assumed
  clean.
- `plugins/alexandria` has no `audit/` directory and no audit record of any
  kind. Nothing was read for it because nothing exists to read. This run
  changes alexandria's demo receipts and its bridge documentation, so that
  absence is an evidence gap and is recorded as one rather than reported as a
  clean history.

Outside this repository: nothing. The change is internal to two first-party
plugins and standardises no external format.

## 3. Constraints and non-goals

Constraints:

- Starting ref `main` at `2b1c5cccca6d688c5d0223d311dd8df177ca5614`.
- Interpreter pinned by `.python-version` to `3.14.6`; standard library only.
- `--alexandria-index` on its own must keep reaching no network. Alexandria's
  reproducibility demonstration and every existing archive invocation depend
  on it.
- The generation row must retain frontier revision `morpho-midnight-coverage`
  and digest `5f66077a0c39a9ee647bd34233504b3891493f864fe4a16a9eb0c0337b3ee688`
  byte for byte, so no word of the frontier block changes.
- `.agents/skills/promise-machine/runtime/` is regenerated, never edited.
- Neither the Probitas nor the Alexandria suite runs in any CI workflow, so
  every step runs both locally and says so. `repo.yml` runs the root
  invariants only.

Non-goals, each with its reason:

- **No source class on `Record`.** The issue asks for it on the coverage row,
  and adding a required field to `Record` changes every construction site in
  four adapter modules and their tests for a field that does any work only
  where both routes observe one venue, which cannot happen today. Archive
  records already carry `alexandria_release_id` in their values and adapter
  records carry none, so the two remain distinguishable. Recorded in the risk
  register as `overlap-attribution`.
- **No `--source`-style flag rewrite.** Replacing `--fixtures`,
  `--live` and `--alexandria-index` with one repeatable selector would read
  better and would break every documented invocation, the Alexandria demo, its
  tests and four documents, for a naming improvement nobody asked for.
- **No CI workflow for Probitas or Alexandria.** Both suites are absent from
  `.github/workflows/`, which is a real gap and a wider change than this
  issue: it needs a workflow file plus entries in `PYTHON_WORKFLOWS` and
  `PLUGIN_WORKFLOW_PATHS` in `tests/test_python_contract.py`. Carried forward
  in the run's pull request.
- **No shared Elenchus runner.** Step 1 adds a fifth near-copy of the same
  per-plugin `run_tests.py`, because each one locates its own suite from its
  own path. Consolidating the five is worth doing and is not this issue.
  Carried forward.
- **No new venue coverage.** Morpho Midnight is the held frontier job and
  belongs to #390.
- **No change to what `translate` supports.** Goldfinch and Clearpool stay the
  archive venues.

## 4. Design options

**A. Additive archive route, explicit live opt-in, one coverage row per
venue and source class.** Drop the mutually exclusive group. `--fixtures` and
`--alexandria-index` combine. A new `--live` flag names the network adapter
route explicitly, so an index alone still runs no adapter. `Coverage` gains
`source` from a closed vocabulary and `releases`. Gate 2 keys rows on the pair
rather than the venue, requires at least one row per registry venue, and fails
a repeated pair by name. Trade: `--live` is a flag whose necessity a reader
has to be told about, because on its own it names the existing default.

**B. Make `--alexandria-index` implicitly additive.** No new flag: passing an
index simply stops suppressing the adapter route. Reads the most naturally of
the four. Trade: `--alexandria-index` alone would start making outbound
requests, which breaks Alexandria's offline demonstration and silently changes
what every existing archive invocation touches. A provenance tool that
quietly widens what it reaches is the wrong failure to accept for a shorter
command line.

**C. Leave `collect` alone and add a `merge` subcommand over two evidence
files.** Trade: two runs mean two `run_id` values and two collection times in
one document, and the merge has to reconcile subject addresses, coverage and
gap sets after the fact, which is a second schema-level contract for
something one `collect` already has the inputs to do. The issue asks for one
run.

**D. Replace the three source flags with one repeatable `--source`.** The
cleanest end state. Trade: it breaks every documented invocation and every
caller for a naming improvement outside this issue's scope.

**Chosen: A.** It is the cheapest of the four to comprehend that still meets
the problem statement. B is cheaper to write and pays for it with a silent
change to what an existing command reaches. C and D both cost more than the
capability is worth. A's one real cost, explaining `--live`, is one line in
each of four documents.

The route table A commits to:

| Flags | Adapter route | Archive route |
| --- | --- | --- |
| none | live network | not run |
| `--fixtures D` | fixture directory | not run |
| `--alexandria-index X` | not run | archive |
| `--fixtures D --alexandria-index X` | fixture directory | archive |
| `--live --alexandria-index X` | live network | archive |
| `--live` | live network | not run |
| `--live --fixtures D` | refused, exit 2 | refused, exit 2 |

Coverage `source` vocabulary: `live`, `fixtures`, `archive`, `none`. A `none`
row is emitted only for a venue no requested route observed, and its note
names why each requested route did not cover it. A venue observed by any
route is not also reported as an unchecked gap; an `error` row still produces
one, because a route that failed is a hole even when another route answered.

The evidence schema becomes `2`. `render.load` refuses a schema-1 file by
name and says to re-collect, rather than letting it reach gate 2 and fail for
a missing source in language that reads like a defect in the document.

## 5. Risk register seed

The audit loop should look hardest at silent collapse and at anything that
widens what a run reaches. Gate 2's venue-keyed row map is the same shape as
audit finding S2-R1-02, where an address kept the last of two provenance
tiers: a dictionary comprehension over a non-unique key, losing evidence
without saying so. Release ids are operator-adjacent strings that end up in a
Markdown table cell, which is finding S2-R1-01's shape.

```risk-register
coverage-row-collapse | gate 2's map from coverage rows to venues | two rows for one venue are both counted, and a repeated venue-and-source pair fails the gate by name rather than overwriting
unrequested-network | the adapter route when an archive index is named | an index alone reaches no network, and outbound requests happen only under --live or the existing no-flag default
schema-refusal | render.load against an evidence file from an earlier version | a schema-1 file is refused by name with a re-collect instruction, not failed at a gate
release-id-figures | gate 3's known-token set and the rendered coverage table | every coverage field that reaches the document is inside the permitted-figure set, so a release id is not read as an invented number
overlap-attribution | records for a venue that both routes observed | both coverage rows are printed and archive records remain identifiable by their alexandria_release_id value
gap-double-count | the gap list when one route observed a venue and another did not | a venue any route observed is not also listed as an unchecked gap, and an error row still produces one
demo-receipt-drift | alexandria's pinned evidence and dossier digests | the offline demonstration rebuilds byte for byte and its receipts are regenerated in the same step that changes the schema
markdown-injection | release ids and source labels reaching a Markdown table cell | the source vocabulary is closed and release ids pass the existing source and value sanitisers before they are rendered
```

## 6. Glossary seeds

- **Adapter route.** The venue adapters in `ADAPTERS`, backed either by the
  network or by a fixture directory.
- **Archive route.** `alexandria_lib.probitas.translate` over a disposable
  Alexandria SQLite index.
- **Source class.** Which route produced a coverage row: `live`, `fixtures`,
  `archive`, or `none` for a venue nobody checked.
- **Observing row.** A coverage row whose status is `checked` or `empty`.
- **Union run.** One `collect` invocation in which both routes ran.
- **Overlap.** A venue that both routes observed. Impossible today; the design
  represents it rather than assuming it away.

## 7. Sources

- Issue [skills#391](https://github.com/wildcat-finance/skills/issues/391),
  including its dated Wave Atlas review block.
- `plugins/probitas/` at `2b1c5cc`: `scripts/probitas.py`,
  `scripts/probitas_lib/{evidence,gates,render,registry}.py`,
  `scripts/probitas_lib/adapters/__init__.py`, `tests/`, `README.md`,
  `AGENTS.md`, `skills/probitas/SKILL.md`,
  `skills/probitas/references/{gates,venues}.md`, `docs/adding-a-venue.md`,
  `audit/AUDIT_SYNOPSIS.md`, `skills/probitas/EVOLUTION.md`.
- `plugins/alexandria/` at `2b1c5cc`: `scripts/alexandria_lib/probitas.py`,
  `examples/credit-history-v0/{demo.py,expected-probitas.json}`,
  `tests/test_index.py`, `tests/test_demo.py`, `docs/address-index.md`,
  `README.md`.
- `plugins/hexaemeron/skills/VERSIONING.md` for the generation rules.
- Root invariants: `tests/test_evolution_contract.py`,
  `tests/test_version_propagation.py`, `tests/test_python_contract.py`,
  `tests/promise_machine_coverage.json`, `.github/workflows/repo.yml`.
- Merged pull requests [#62](https://github.com/wildcat-finance/skills/pull/62)
  and [#65](https://github.com/wildcat-finance/skills/pull/65).

## 8. Signals, and the questions behind them

Probitas is a command an operator runs and watches, not a service that runs
unattended, so the questions are asked at the terminal rather than at three in
the morning. Three are worth answering in what the run emits;
[ephoros](../plugins/hexaemeron/skills/ephoros/SKILL.md) owns what each signal has to carry.

1. *Which routes actually ran, and did anything reach the network?* The
   `collect` summary on stderr names each requested route and its backing, and
   the coverage rows carry the same answer in the file. Step 3 emits it.
2. *I passed an index, so why does this venue say nobody checked it?* The
   `none` row's note names why each requested route did not cover that venue,
   rather than reporting a missing credential when the truth is that the venue
   was not harvested. Step 3.
3. *Which Alexandria release is this row standing on?* The `releases` field on
   an archive coverage row, lifted out of the note's prose so a gate and a
   reader see the same value. Step 2.

## 9. Boundaries, per capability

[phylax](../plugins/hexaemeron/skills/phylax/SKILL.md) owns the boundary list and its controls. This
change opens no new process boundary; it changes which existing ones can be
open at once.

- **The archive index path.** Already read through Alexandria's confined
  reader and its own schema and digest checks. This run passes the operator's
  path through unchanged and adds no new file handling. Control: unchanged,
  and the fixed `Alexandria index` endpoint label stays fixed, because #62's
  cold read put it there to keep an operator-chosen filename out of a
  Markdown cell.
- **The network adapter route.** Now reachable in the same run as the archive
  route. Control: only `--live` or the existing no-flag default opens it, so
  no existing invocation starts making requests it did not make before, and
  `--live` with `--fixtures` is refused.
- **The fixture directory.** Unchanged; adapters already read it.
- **Release ids reaching the document.** New, because `releases` becomes a
  rendered field. Control: values pass the existing source and value
  sanitisers, the `source` vocabulary is closed, and gate 3 holds every
  rendered figure against the permitted set.

## 10. The budget, or its absence

None, and no performance claim is made. A union run does the work of the two
routes that already run separately, and no step changes an algorithm in the
name of speed. Because nothing is claimed, [metron](../plugins/hexaemeron/skills/metron/SKILL.md)
refuses nothing here; if a later step wants to make a speed claim it needs a
recorded before and after first.

## 11. The fail-closed posture

[elenchus](../plugins/hexaemeron/skills/elenchus/SKILL.md) owns the triage order and the guard rule.
Four things stop a run, and each gets a test that fails without its guard:

- `--live` together with `--fixtures` exits 2 and names the contradiction.
- A schema-1 evidence file is refused by `render.load` with a re-collect
  instruction.
- A repeated venue-and-source pair fails gate 2 by name.
- A coverage row with no source class, or one outside the vocabulary, fails
  gate 2 by name.

A gate is fixed by fixing the document or the collection, never by editing the
gate. Each step names its exact Elenchus runner command, report format and
report file; a missing, stale or malformed report is `inconclusive` and not
evidence that a repair is guarded.

## 12. Decisions and their homes

[hypomnema](../plugins/hexaemeron/skills/hypomnema/SKILL.md) owns which decisions earn a record and
where each one lives. Two are expensive to reverse:

- **The route table and the `--live` opt-in.** It fixes what an existing
  command reaches.
- **One coverage row per venue and source class, and evidence schema 2.** It
  changes a published file format and the gate contract that reads it.

Both belong to one governed skill rather than cutting across the repository,
so the standing record is the `probitas` generation row in
`plugins/probitas/skills/probitas/EVOLUTION.md`, pointing at the committed
copy of this study for the options that lost. No new file under
`docs/decisions/` is written: hypomnema puts a single-skill decision in that
skill's ledger, and an ADR number here is a repository-global identifier
picked early and guarded after the fact, which is a collision this run does
not need to risk. The gate contract change is written where the gate contract
already lives, in `plugins/probitas/skills/probitas/references/gates.md`, and
the route table in the README, `SKILL.md` and `AGENTS.md`.

## Boundaries this run holds

**Always.** Both plugin suites and the root suite in `tests/` before a commit.
The imprimatur lint on every shipped document. `portable_promise_machine.py
sync` then `check` whenever a plugin file changes. `horos.py check .` before
the final push.

**Ask first.** Adding a dependency. Changing the evidence schema beyond the
two coverage fields and the version number. Touching CI. Changing what
`translate` supports. Renumbering or writing an ADR.

**Never.** Hand-edit `.agents/skills/promise-machine/runtime/`. Change the
frontier block in `EVOLUTION.md`. Delete a coverage row or a failing test to
make a suite pass. Claim a lint, a suite or a demo ran when it did not.

### Amendment -- 2026-08-28

**What changed.** The union demonstration moves out of
`plugins/alexandria/examples/credit-history-v0/demo.py` and into Probitas's own
suite, as `plugins/probitas/tests/test_union.py`. That demonstration builds a
disposable Alexandria index offline through `alexandria_lib`, runs the union
against `plugins/probitas/tests/fixtures/demo`, and checks the five gates.
The Alexandria demonstration keeps its existing job: proving that the
archive-only path still rebuilds byte for byte after the schema change, with
its two pinned digests regenerated. Item 1's other conditions and its command
list are unchanged, and `demo.py build` followed by `verify` remains a required
check in every step from step 2 onward.

**Why.** `plugins/alexandria/examples/` is inside the tree that
`scripts/portable_promise_machine.py` mirrors into
`.agents/skills/promise-machine/runtime/`, and that mirror excludes every
`tests` directory. A union run inside the Alexandria demonstration would have
to read `plugins/probitas/tests/fixtures/demo`, which the portable copy does
not contain, so the mirrored demonstration would break. Materialising
synthetic venue fixtures inside Alexandria instead would duplicate Probitas's
own fixtures and drift from its adapter response shapes, and adding a second
Probitas run to `summary.json` would require a new version of
`plugins/alexandria/schemas/demo-summary-v1.schema.json`. Probitas's suite has
neither problem: it already owns those fixtures and Probitas already imports
`alexandria_lib` at runtime.

**Steps touched.** Step 4's goal, exit, files and tests, which is where the
demonstration is built. No earlier step referenced the demonstration's
location.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit
holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds.
