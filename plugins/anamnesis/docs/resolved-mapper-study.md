# Make the declared mapper select the implementation that reads a source

Assuming, unless corrected:

1. The starting ref is `main` at `f0ef92663484c548c5fee26f2964628349a03892`; the
   run branch `fiat/1464-make-the-declared-mapper-select-the-impleme` was cut
   from it.
2. Python `3.14.6` per `.python-version`, standard library only, `unittest`. No
   new dependency.
3. Anamnesis's held job at `anamnesis-v4.1.0` is the acceptance authority, and
   its two halves are separate: an unknown mapper refuses at curation, and a
   source in a second producer's format is admitted under a mapper the policy
   selects, with the release naming the mapper that actually read it.
4. **The ledger's `declared-inputs` row is out of date.** It records
   `foreign-format-corpus | corpus | absent`. Section 2 records the search that
   found the input present in this checkout. This study proceeds on the found
   input and treats correcting that row as work this run owes. If the maintainer
   rejects the found corpus, candidate `registry-only` in section 4 is the
   fallback and the second half is not shown.
5. The second-format corpus preserves the same 41 findings the pilot already
   preserves, in a second producer's format. It adds a format and a mapper, not
   coverage. Section 1 states what that does and does not demonstrate.
6. The synopsis view is current:
   `python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .`
   exited 0 from the run root on 8 September 2026, with every row
   `committed=match`.
7. The runbook's step 3 is the step that builds the second corpus. The design
   record's one conformance criterion names `step:3` as its stop point.

## 1. Problem statement

The curation policy declares a mapper, and nothing reads the declaration as a
choice. `anamnesis.py:567` defines
`MAPPER = {"name": "warden-audit-round-markdown", "version": "1"}` and the token
`MAPPER` occurs exactly once in the file: nothing references it. `parse_source`
(`:610`) is the only parser, and it is called unconditionally, from `curate`
(`:737`) and from `cmd_ingest` (`:1539`). `curate` reads `mapper =
policy["mapper"]` (`:727`) and `_assertion` (`:703`) copies that declared object
into every assertion at `:710`. `load_curation_policy` (`:1232`) checks the
declared object's shape and never its meaning.

Rerun on 8 September 2026 at `f0ef9266`, sharper than the filing recorded it: a
release built from the estate specimen under a curation policy declaring
`{"name": "a-mapper-that-does-not-exist", "version": "9"}` exits 0, produces 17
findings, and writes that name into **all 55 assertions** and into the
manifest's recorded policy. Because `release_id` (`:920`) hashes the canonical
curation policy, the false name is hashed into the corpus identity: the probe
released `8bae874752c55b9f`, not the estate's shipped `50923976`. A reader of
that release is told, by the release id and by every record in it, which mapper
made the record. Nothing checked it.

The gap has a second face the ledger does not name, and this study found it by
running the current mapper over foreign bytes. `parse_source` over the three
committed `AUDIT_SYNOPSIS.md` files returns **31 rounds and 0 findings**. It
does not refuse. It matches the round headings, fails to match any finding row,
and produces 31 structurally valid empty rounds. The current mapper fails open
on a format it does not read.

**Who this is for.** Whoever reads an Anamnesis release and wants to know which
implementation produced its records, and whoever later adds a producer whose
records are not Warden Markdown.

**What a working prototype means here.** The curation policy's `mapper` is
resolved through a registry; an unresolved name refuses before any record is
written; every assertion records the resolved implementation rather than the
declared string; and a third corpus of `fiat-audit-synopsis/v1` records is
admitted, curated and released under a mapper the policy selects, rebuilding to
its own release id.

**Demo path.** Three commands from the worktree root:

```bash
python3 plugins/anamnesis/skills/anamnesis/scripts/anamnesis.py curate \
  --policy plugins/anamnesis/specimens/synopsis/policy.json \
  --curation-policy plugins/anamnesis/tests/fixtures/unknown-mapper-policy.json
# exits non-zero, refusing the unresolved mapper by rule, writing nothing

python3 plugins/anamnesis/skills/anamnesis/scripts/anamnesis.py demo \
  --specimen plugins/anamnesis/specimens/synopsis
# two fresh builds agree; 41 findings across 31 rounds, 12 with no findings

python3 plugins/anamnesis/skills/anamnesis/scripts/anamnesis.py verify-rebuild \
  --specimen plugins/anamnesis/specimens/pilot
# the pilot still rebuilds to 41d640fb, unchanged
```

**What this does not demonstrate.** It does not demonstrate that the corpus now
reaches an independent auditor's findings. The synopsis corpus renders the same
three audit records the pilot preserves, so the two corpora hold the same 41
findings in two formats. What it demonstrates is that the declared mapper
selects the implementation, and that two implementations reading the same
underlying record produce the same 41 findings while the wrong implementation
produces 0. It does not demonstrate that any third-party format is admissible,
that a second mapper is the right shape for every producer, or that the shipped
corpora were ever wrong: every release built so far declared the mapper that in
fact ran.

## 2. Prior art

**In this repository.** `plugins/anamnesis/skills/anamnesis/scripts/anamnesis.py`
holds admission (`admit_source`, `:300`), curation (`curate`, `:715`), the
release (`build_release`, `:965`) and the declared scope (`check_scope`, `:409`).
`CURATION_POLICY_KEYS` (`:79`) makes `mapper` a required closed key of the
curation policy. Two corpora ship: `specimens/pilot` (41 findings, 31 rounds,
release `41d640fb`) and `specimens/estate` (17 findings, release `50923976`).
Decision records live in `plugins/anamnesis/docs/decisions/`; ADR-006 records
the declared corpus scope. The Elenchus step runner is
`plugins/anamnesis/tests/elenchus.py`, whose `STEPS` tuple currently admits 1 to
10 and whose suites are `test_s1_*.py` through `test_s10_ledger.py`; this run's
step numbers must be admitted there before its guards can run.

**The second format, and its producer.** `plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py`
writes `fiat-audit-synopsis/v1`: a header line declaring the schema, the source
path, the source SHA-256 and an H2 count, then one physical line per round with
`<br>` between the producer's own cells. Twelve such files are committed, six
plugin-level and the rest under `audit/rounds/`. They are a second producer's
format by every test the ledger states, and the current mapper reads 0 findings
from them.

**Outside.** No standard applies. The two candidate formats are both local:
`fiat-audit-synopsis/v1`, above, and the `FINDING` ... `END` key-value block at
`plugins/brevitas/skills/brevitas/evals/cases/fund-safety-evidence-exception/original.md`,
an excerpt of an external red-team agent's record over the `inferrex` project,
digest-bound at `08e534ff9fd8005778e2224f374bd1e42a4bb129c2504e8aa54549f8621f0494`.

**The declared input the ledger records as absent.** The ledger's
`declared-inputs` block says a preserved audit record whose producer writes a
format the Warden mapper does not read is `absent`, and the issue says that
without one the second half cannot be shown. That claim was tested rather than
accepted. The search covered `plugins/anamnesis/specimens/`, every
`plugins/*/audit/` directory, all 142 files under `audit/rounds/`, the bundled
Pashov suite, `plugins/janus/examples/`, `plugins/synkrisis/examples/` and
`references/`, `plugins/dokimasia/docs/evidence/`, `plugins/brevitas/.../evals/`,
`tests/fixtures/` and every Markdown, JSON and CSV path whose name carries
audit, review, finding, report or security. It found no CSV, no vendored
third-party audit report, no Slither, Mythril, Semgrep or SARIF output. It found
six real preserved records in formats the Warden mapper does not read; two are
viable corpus sources and become candidates in section 4. The declaration was
true when written and is false at `f0ef9266`. Correcting that row is work this
run owes.

**The last two merged pull requests touching the target.**

[#1471](https://github.com/wildcat-finance/skills/pull/1471), merged at
`f0ef9266`, gave `verify_release` an optional event sink so the `A077`
declared-scope refusal emits the durable event the study claimed for it. Its
"Not established" section records that the other seven refusals in
`verify_release` still emit nothing, deliberately. **Carried forward as a stated
non-goal**: this run adds refusals in `curate`, which already sits inside the
`refusals_recorded` boundary, so it inherits the event and widens nothing in
`verify_release`.

[#1468](https://github.com/wildcat-finance/skills/pull/1468) delivered the
declared corpus scope. Its `carryover` block carries eight rows; each is
answered here by name:

- `declared-mapper-selects-nothing | filed | #1464`: **this run's topic.**
- `a077-emits-no-refusal-event | filed | #1465`: closed by #1471 above.
- `plugin-package-version-not-bumped | duplicate | #1341`: **stays open**, a
  repository-wide convention, and a non-goal here.
- `resolver-reproduces-at-the-study-tree`: two of the corpus-scope record's
  eight criteria read code that run changed. **Carried forward as a constraint**:
  section 3 records that this run moves the program digest and must leave
  `pilot-artefacts-rebuilt` rerunning to its recorded values.
- `pilot-source-dead-link | none`: **stays open by contract**; the corpus keeps
  the producer's bytes unchanged and the declared lint scope exits 0.
- `estate-refused-event-example | none`: **answered**. This run ships a refusal
  specimen for the unresolved mapper, which is a refusal event example the
  estate corpus lacked.
- `packaged-payload-byte-cap | filed | #1467`: **stays open**; section 3 records
  the added bytes so the run does not worsen it silently.
- `runbook-named-an-unpassable-check | duplicate | #1437`: **stays open**;
  section 3 names the exact exit commands to avoid repeating it.
- `demo-lane-second-producer | none`: the DEMONSTRATION.md held job asks for a
  second corpus from more than one producer. **Stays open and is named in
  section 12**: the synopsis corpus is a second format, not a second producer of
  findings, so it does not close that demo frontier.

**Audit records read, and how.** Anamnesis has no `plugins/anamnesis/audit/`
directory; its records are three files under `audit/rounds/`, plus the root
`audit/AUDIT.md`, which covers only the root source.
`python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .` ran
from the run root and exited 0, with `committed=match` on every row, so the
verified synopsis is the normal reading view. In-scope sources and what was
actually read:

| In-scope source | Read | Evidence for the choice |
| --- | --- | --- |
| `audit/rounds/fiat-1351-anamnesis-2-declared-corpus-scope.md` | source | grep over the source bytes for mapper, parser, format and producer, because the synopsis elides the `Leads not pursued` prose these findings live in |
| `audit/rounds/fiat-anamnesis-source-bound-curation-and-release-of-a.md` | source | same |
| `audit/rounds/fiat-admit-the-anamnesis-corpus-projection-into-a-syn.md` | source | same |
| `audit/rounds/fiat-shoggoth-front-door-derived.md` | not read beyond the mapper grep | it names Anamnesis only in the front-door card, which section 3 covers as a re-pin |
| `audit/AUDIT.md` | not read | the root pair covers the root source, which this run does not change |

No finding id or status was dropped: the grep returned whole `Not checked` and
`Leads not pursued` fields, not extracts. Three carried items bear on this run
and each is answered:

1. *"whether the mapper reads every Warden format that has ever existed"* is
   still **not checked**, and still a non-goal. This run adds a second mapper; it
   does not widen the first.
2. *"The mapper's finding-row pattern combines two lazy quantifiers with
   surrounding whitespace classes, which is a backtracking shape; on the pilot
   and the fixtures it is linear, and the source byte cap bounds any input it
   sees, so no bound was measured and none is claimed."* This is **carried forward and
   widened by this run**: the second mapper reuses `FINDING_ROW` over
   `<br>`-split cells, so the same shape now runs over a second corpus. Risk
   register id `mapper-backtracking` holds it.
3. *"The new held job's claim was verified rather than assumed and is sharper
   than the ledger states it"* was reverified independently here, in section 1.

The corpus-scope run also recorded that the security suite waiver is on the
ledger and that x-ray, solidity-auditor and fizz have no Solidity target in this
plugin. That holds unchanged for this run.

## 3. Constraints and non-goals

**Starting ref.** `main` at `f0ef92663484c548c5fee26f2964628349a03892`.

**Toolchain.** Python `3.14.6` from `.python-version`, standard library only,
`unittest`. No new dependency, no network.

**The exact exit commands.** The root check runner is
`python3 scripts/run_checks.py --base origin/main`; three lints are not CI, and
a step exit must name the root suite. Per-step guards run through
`plugins/anamnesis/tests/elenchus.py --step N REPORT`, whose `STEPS` tuple this
run must extend before it can name a new step, and whose suites must be
`plugins/anamnesis/tests/test_sN_*.py` for that N. Anamnesis suites also run
directly as `python3 -m unittest plugins.anamnesis.tests.test_sN_...` from the
worktree root.

**Re-pins this run incurs.** Changing `anamnesis.py` bytes moves the program
digest, so `plugins/anamnesis/skills/anamnesis/DEMONSTRATION.md` re-pins its
`program` source digest and the root `README.md` re-pins the front-door demo
card digest. `.horos/census.json` tracks every tracked file's byte count and is
rescanned with
`python3 plugins/horos/skills/horos/scripts/horos.py scan . --census --write`.
The program digest is carried by exactly one tracked file today,
`DEMONSTRATION.md`, so the re-pin must land there and nowhere else or the
corpus-scope record's `pilot-artefacts-rebuilt` count moves.

**A receipted criterion that must still rerun.** `plugins/anamnesis/docs/corpus-scope/reports/resolve.py`'s
`pilot-artefacts-rebuilt` counts files carrying the pilot's tokens, one of which
is the program digest, and
`plugins/anamnesis/tests/test_s8_scope.py::TheRebuiltCountSeesArtefactsAndNotGuards`
reruns all four candidates against their recorded values, with
`release-policy-scope` pinned at 7. That test must stay green.

**Release identity is fixed for both shipped corpora.** The pilot must still
rebuild to `41d640fb` and the estate to `50923976`. Because assertions record the
mapper, the resolved object must be byte-identical to the declared one for a
policy whose mapper resolves, or both release ids move. That is a hard gate in
the design record, not a preference.

**Frontier obligations.** This is a frontier run. `done integrate` refuses
unless `EVOLUTION.md` gains exactly one valid row: evolution increments,
generation and epoch retained, the digest recomputed over the new four-field
frontier line, header and row naming the same version, and either one evidenced
next job or `mature`. The run also owes the cold read of every mutable
first-party marketplace prose surface, and the `declared-inputs` correction from
assumption 4.

**Non-goals.**

- Widening the Warden Markdown mapper to read any format it does not read today.
- Detecting a source's format from its bytes. Detecting is not declaring, and
  a sniffing resolver makes the declaration decorative again.
- Admitting a third-party auditor's findings into the corpus. Section 4's
  `registry-and-red-team-mapper` covers that option and is not selected.
- Moving the plugin package version, which is `#1341`.
- Closing the DEMONSTRATION.md `second-preserved-audit-corpus` frontier.
- Emitting refusal events from the seven `verify_release` checks #1471 left
  silent.

## 4. Design options

Four candidate constructions. The prose explains them; `.hexaemeron/design-evidence.json`
selects one from measured cells, and every number below is a report in
`.hexaemeron/reports/`.

**`registry-and-synopsis-mapper` (selected).** A module-level registry maps
`(name, version)` to an implementation. `curate` and `ingest` resolve
`policy["mapper"]` through it, refuse by rule when it does not resolve, and
record the resolved registry entry on every assertion. A second implementation,
`fiat-audit-synopsis` version 1, reads `fiat-audit-synopsis/v1`: it checks the
header's declared schema and refuses bytes that are not its format, then splits
each round line on `<br>` and applies the round-field and finding-row grammar
the first mapper already owns. A third specimen,
`plugins/anamnesis/specimens/synopsis`, admits the three committed
`AUDIT_SYNOPSIS.md` files under Apache-2.0 with its own declared scope.
*Measured*: 41 findings across 31 rounds from those bytes, against 0 from the
current mapper; 36,455 source bytes; 0 shipped release policies changed.
*The trade*: the second corpus renders the same three audit records the pilot
preserves, so it adds a format and not a producer of findings. The run buys a
checkable second format and an exact control, the same 41 findings through two
implementations, and pays by not reaching any new audit history. The synopsis
header carries `source_sha256`, and for all three sources it equals the digest
the pilot's admission policy already records, so that "same findings" claim is
mechanical rather than asserted.

**`registry-and-red-team-mapper`.** The same registry, with the second
implementation reading the `FINDING` ... `END` key-value block and the third
corpus admitting the one preserved external red-team record.
*The trade*: the producer is genuinely independent and external, which is more
than the selected candidate offers, but the corpus is one record, the format
declares no schema or version anywhere in its bytes, and the producer wrote no
finding identifiers, so the mapper would have to assign them. A mapper that
cannot check the bytes are its format fails open exactly the way the current one
does. **Fails** `second-format-declares-its-own-schema`.

**`registry-only`.** The registry and the refusal, with no second implementation
and no third corpus. The ledger's first half only; the second recorded as still
unshown, with a successor job.
*The trade*: cheapest, adds 0 source bytes, and is fully honest about what it
did not show, but it leaves the frontier open on the same input and hands the
next run the identical question. **Fails** `second-format-declares-its-own-schema`,
because there is no second format at all. This is the fallback if assumption 4
is corrected.

**`per-source-mapper`.** The mapper declaration moves from the curation policy
to each admitted source in the admission policy, resolved through the same
registry, so one corpus can preserve two producers' formats at once.
*The trade*: it is the more general mechanism and it is what a mixed corpus will
eventually need, but `mapper` leaves `CURATION_POLICY_KEYS`, so both shipped
curation policies change their canonical bytes, and `release_id` hashes that
policy. **Fails** `shipped-release-policies-changed`, measured at 2: it moves
both shipped release ids, which ADR-006, two DEMONSTRATION.md observation lines
and the front-door card all depend on.

**Selection.** Three candidates each fail one selection hard gate.
`registry-and-synopsis-mapper` fails none and is the sole survivor, so
`unique-frontier` holds with one candidate on the frontier.
`design_evidence.py --transition design-lock` exits 0.

## 5. Risk register seed

The concerns the audit loop must enumerate. Two are inherited by name from the
corpus-scope run's leads: `mapper-backtracking` widens that run's unmeasured
backtracking shape to a second corpus, and `release-identity-drift` holds the
constraint that receipted release ids and a receipted grep count must not move.
`fail-open-mapper` is the defect section 1 found and is the reason the selected
second mapper checks its own format before reading.

```risk-register
unresolved-mapper-writes-records | curate, between reading policy["mapper"] and the first assertion | an unresolvable name refuses before any assertion, quarantine entry or release directory exists
fail-open-mapper | the second mapper's entry, on bytes that are not its format | the mapper refuses by rule rather than returning empty or partial rounds, and a guard feeds it Warden Markdown and the pilot's bytes
declared-not-resolved-in-assertion | the mapper object written into every assertion | the recorded object comes from the registry entry that ran, not from the policy string, and a guard proves the two differ when the policy lies
release-identity-drift | the pilot and estate release ids, and the corpus-scope pilot-artefacts-rebuilt count | the pilot rebuilds to 41d640fb, the estate to 50923976, and test_s8_scope reruns all four recorded counts unchanged
mapper-backtracking | FINDING_ROW and the second mapper's own patterns, over the widest cell any admitted source produces | the corpus-scope lead is carried forward by name; either a bound is measured over the synopsis corpus or the absence of a bound is restated with the byte cap that stands in for one
synopsis-cell-splitting | the <br> split inside one physical synopsis line | a producer cell containing the separator, an unterminated row and a header-less file each refuse or are preserved verbatim, never silently truncated
third-corpus-rights-basis | the synopsis specimen's declared rights basis and disclosure | the basis is licence, Apache-2.0, holder Wildcat Labs, and the statement names the repository LICENSE the way the pilot's three sources already do
scope-bounds-for-the-third-corpus | the synopsis curation policy's declared record bounds against 41 records | the bounds are declared, the corpus holds 41, and a corpus outside them refuses A073
program-digest-repin | DEMONSTRATION.md and the root README front-door card | both re-pin to the new digests and the front-door check and demonstrations suite exit 0
registry-mutability | the module-level registry object at import time | the registry is not writable by policy, source bytes or environment, and a source cannot register an implementation
```

## 6. Glossary seeds

- **Declared mapper.** The `{name, version}` object the curation policy carries.
- **Resolved mapper.** The registry entry the declared object selects, and the
  implementation that actually reads a source.
- **Registry.** The module-level map from `(name, version)` to implementation;
  the only place an implementation becomes selectable.
- **Second format.** `fiat-audit-synopsis/v1`, written by
  `plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py`.
- **Fails open.** Returns a structurally valid result from bytes it did not
  understand. The current mapper reads 31 empty rounds from a synopsis.
- **Synopsis corpus.** `plugins/anamnesis/specimens/synopsis`, this run's third
  specimen.

## 7. Sources

- `plugins/anamnesis/skills/anamnesis/scripts/anamnesis.py` at `f0ef9266`, lines
  cited individually in sections 1 and 2.
- `plugins/anamnesis/skills/anamnesis/EVOLUTION.md`, `anamnesis-v4.1.0`,
  frontier revision `declared-scope`, and its `declared-inputs` block.
- `plugins/hexaemeron/skills/VERSIONING.md`, the frontier discipline, the
  declared-inputs contract and "What every frontier run owes".
- `plugins/hexaemeron/skills/protasis/SKILL.md` version 5.10.0, and
  `scripts/design_evidence.py`.
- `plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py`, the producer of
  the second format.
- Issue [#1464](https://github.com/wildcat-finance/skills/issues/1464); pull
  requests [#1468](https://github.com/wildcat-finance/skills/pull/1468) and
  [#1471](https://github.com/wildcat-finance/skills/pull/1471).
- `audit/rounds/fiat-1351-anamnesis-2-declared-corpus-scope.md`,
  `audit/rounds/fiat-anamnesis-source-bound-curation-and-release-of-a.md`,
  `audit/rounds/fiat-admit-the-anamnesis-corpus-projection-into-a-syn.md`.
- `plugins/anamnesis/docs/decisions/ADR-006-declared-corpus-scope.md`.
- `plugins/hexaemeron/audit/AUDIT_SYNOPSIS.md`,
  `plugins/pandects/audit/AUDIT_SYNOPSIS.md`,
  `plugins/tabularium/audit/AUDIT_SYNOPSIS.md`, SHA-256
  `2e919d92...`, `ecde800e...` and `2432d6fd...`, the second corpus's sources.
- `plugins/brevitas/skills/brevitas/evals/corpus.json` and
  `evals/cases/fund-safety-evidence-exception/`, the rejected candidate's source
  and its recorded redistribution review.
- `.hexaemeron/design-evidence.json` and the 32 reports under
  `.hexaemeron/reports/`, produced by `.hexaemeron/reports/resolve.py`.

## 8. Signals, and the questions behind them

[ephoros](https://github.com/wildcat-finance/skills/blob/f0ef92663484c548c5fee26f2964628349a03892/plugins/hexaemeron/skills/ephoros/SKILL.md) owns what a signal must
carry. Anamnesis runs from a terminal and adds no remote telemetry, so the
questions are about a refusal an operator reads afterwards, not about an
unattended service.

1. *Why did this build refuse, and which mapper did the policy ask for?* The
   step that adds the registry emits the existing `anamnesis.source.refused`
   JSONL event for the new unresolved-mapper rule, carrying the rule, the record,
   the policy version and the correlation id. `curate` already runs inside the
   `refusals_recorded` boundary, so the event comes with the refusal rather than
   being added beside it.
2. *Which implementation read the source this record came from?* Every assertion
   carries the resolved mapper's name and version, and the manifest carries the
   policy that named it. This is the signal the run exists to make true.
3. *Did the second mapper refuse these bytes, or read them as empty?* The step
   that adds the synopsis mapper makes a refusal the only outcome for bytes
   without the declared header, so "0 findings" and "not my format" stop being
   the same observation.

No new event kind, no new sink, no counter. Adding one would be an unused
surface: the existing stream already answers all three.

## 9. Boundaries, per capability

[phylax](https://github.com/wildcat-finance/skills/blob/f0ef92663484c548c5fee26f2964628349a03892/plugins/hexaemeron/skills/phylax/SKILL.md) owns the boundary list
and the controls. This run opens two boundaries and widens none.

1. **A second parser over untrusted preserved bytes.** Worth taking: a source
   crafted to make the parser loop, allocate without bound, or emit a record it
   did not contain. Controls: the existing `MAX_SOURCE_BYTES_CEILING` read cap
   and digest re-check at curation apply unchanged; the second mapper refuses on
   a missing or wrong schema header before reading any row; the `<br>` split is
   bounded by the same line the cap already bounds; and `mapper-backtracking`
   and `synopsis-cell-splitting` in section 5 are the audit loop's obligations.
2. **A registry that decides which code runs from a value in a policy file.**
   Worth taking: a policy that reaches an implementation the operator did not
   intend, or that mutates the registry. Controls: the registry is a
   module-level constant map, lookup is exact on `(name, version)` with no
   fallback and no default, an unresolved name refuses rather than selecting
   anything, and nothing in a policy or a source can add an entry.

No network, no subprocess, no credential, no new dependency, and no new
filesystem path outside the specimen directory the run creates. The existing
no-symlink, no-escape resolution in `resolve_within` covers the third specimen's
sources unchanged.

## 10. The budget, or its absence

No performance budget is declared, and that is the deliberate position the
corpus-scope and consumer-projection runs already took: `demo` prints duration
and peak resident memory as baselines with no budget.
[metron](https://github.com/wildcat-finance/skills/blob/f0ef92663484c548c5fee26f2964628349a03892/plugins/hexaemeron/skills/metron/SKILL.md) owns what a budget carries.

Two measurements are recorded rather than budgeted. The design record's
`acceptance-check-ms` measures the parse work each candidate's acceptance needs,
at 1 millisecond for all four, which is why time did not separate them. The
selected candidate adds 36,455 source bytes and one specimen directory to a
packaged payload already at 95.2 per cent of a 25 MiB cap under
[#1467](https://github.com/wildcat-finance/skills/issues/1467); the run records
the added bytes in its integration report so that cap is not approached
silently.

If a budget is wanted later, the command is
`python3 plugins/anamnesis/skills/anamnesis/scripts/anamnesis.py demo --specimen plugins/anamnesis/specimens/synopsis`,
whose printed duration and peak resident memory are the numbers a budget would
bind.

## 11. The fail-closed posture

[elenchus](https://github.com/wildcat-finance/skills/blob/f0ef92663484c548c5fee26f2964628349a03892/plugins/hexaemeron/skills/elenchus/SKILL.md) owns the triage order
and the guard rule. Anamnesis's default is deny, and this run keeps it: a
non-zero exit means the requested operation did not happen, and no partial
release is promoted, because `build_release` stages beside its destination and
promotes only when complete.

What stops the run:

- A declared mapper that does not resolve. Refusal by rule, before any
  assertion, quarantine entry or release directory exists.
- Bytes handed to the synopsis mapper without its declared schema header.
  Refusal by rule, never an empty round.
- A shipped release id that moves, or `test_s8_scope`'s recorded counts that
  fail to rerun. Either one stops the step it appears in.
- A step whose root suite is red. Three lints are not the exit.

The guard convention: each fix carries the exact specimen that reproduced it, in
the suite this run's step runner executes, and the guard is run against the
parent commit to show it fails there. That is the convention the corpus-scope
and curation runs followed, and it is why their fixes are still checkable.

## 12. Decisions and their homes

[hypomnema](https://github.com/wildcat-finance/skills/blob/f0ef92663484c548c5fee26f2964628349a03892/plugins/hexaemeron/skills/hypomnema/SKILL.md) owns which
decisions earn a record and where each one lives. Three are expensive to
reverse.

1. **The mapper is resolved through a registry keyed by name and version, and
   the resolved entry is what an assertion records.** This changes what every
   future assertion means and cannot be reversed without invalidating the claim
   the corpus makes about its own records. Home: a new ADR under
   `plugins/anamnesis/docs/decisions/`, numbered against the default branch
   immediately before pushing, because ADR numbers collide before merge.
2. **The mapper stays in the curation policy rather than moving per source.**
   Rejecting `per-source-mapper` keeps two shipped release ids stable and defers
   the mixed-format corpus. Recorded in the same ADR, with the measured
   `shipped-release-policies-changed` value of 2 as its reason.
3. **The second corpus preserves the same findings the pilot preserves.** This
   governs what the release may be cited for, and it is the decision most likely
   to be misread later. Home: the same ADR, and the synopsis curation policy's
   own `scope.preserves` sentence, which is inside the release and hashed into
   its id.

Two prose homes are obligations rather than decisions. `EVOLUTION.md` takes the
one new frontier row and the corrected `declared-inputs` block.
`plugins/anamnesis/docs/` takes the committed copies of this study and its
runbook, and `SKILL.md` and both READMEs take the cold read every frontier run
owes.

**The successor frontier job, if this one closes.** The corpus can then select
an implementation but still holds one producer's findings in two formats. The
evidenced next job is to admit a corpus whose findings a party other than this
repository produced, under a per-source mapper declaration so one corpus can
hold both. The input it needs is the `foreign-format-corpus` row rewritten as
what is actually missing: not a second format, which this run shows exists, but
a second producer's findings with a rights basis to redistribute them. The
external red-team record rejected in section 4 is one candidate for it, and the
DEMONSTRATION.md `second-preserved-audit-corpus` frontier is the same question
asked in the demonstration lane.

## Boundaries this run works inside

**Always.** The root suite before a commit, as
`python3 scripts/run_checks.py --base origin/main`. The Imprimatur lint on every
shipped document. `.horos/census.json` rescanned after any tracked-file edit.
Both shipped release ids reverified after any change to `anamnesis.py`.

**Ask first.** Adding a dependency. Changing `CURATION_POLICY_KEYS` or any other
release-hashed shape. Touching CI. Admitting a source whose producer is outside
this repository. Rewriting a released digest.

**Never.** Commit key material or an RPC credential. Edit a vendored directory.
Delete a failing test to make a suite pass. Claim a command ran when it did not.
Report the second half of the acceptance condition as shown by a corpus whose
findings the pilot already holds, without saying so.

### Amendment -- 2026-09-08

**What changed.** Assumption 7 said the runbook's step 3 is the step that builds
the second corpus, reading the design record's `blocks` value of `step:3` as
naming the producing step. It names a deadline instead. The second corpus and
its `second-corpus-rebuilds-deterministically` report are built in step 2, and
step 2's exit proves the `step:3` boundary.

**Why.** `hexctl.py` at `done push` computes its next design transition from the
first step still marked `pending`; the step being pushed is `open`. At step N's
push the transition checked is therefore `step:N+1`, so `step:3` is checked at
the end of step 2. Measured against the receipted record at `f0ef9266`:
`--transition design-lock`, `step:1` and `step:2` each print `clean` and exit 0,
while `step:3`, `step:4` and `integration` each exit 1 with
`D008 registry-and-synopsis-mapper/second-corpus-rebuilds-deterministically
report is unavailable or outside the record directory`. A step-3 build produces
the report one transition after it is owed, and step 2's push refuses. No step
count moves the deadline, because the `blocks` value is fixed in the receipted
record.

**Steps touched.** Steps 2 and 3.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit
holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds.

### Amendment -- 2026-09-08

**What changed.** The third demo command in section 1 is
`python3 plugins/anamnesis/skills/anamnesis/scripts/anamnesis.py verify-rebuild --specimen plugins/anamnesis/specimens/pilot --report tmp/demo/pilot-rebuild.json`.
It was written without `--report`, and the comment beneath it stands unchanged:
the pilot still rebuilds to 41d640fb.

**Why.** `verify-rebuild` has required `--report` since `d4ebacc4`, which
predates this run's base, so the command as first written exits 2 on an
argparse usage error and demonstrates nothing. Step 4's exit requires each of
the three demo commands to behave as this study states, and that clause could
not be met while one of them could not run. The report path is inside the
worktree because the runner binds it there, and `tmp/` is ignored, so running
the demonstration leaves the tree clean.

**Steps touched.** Step 4

**Still holding.** Step 4: entry holds; exit holds.
