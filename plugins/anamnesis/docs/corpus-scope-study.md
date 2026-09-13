# Declare the corpus scope in the release policy, and build the estate corpus under its own

Assuming, unless corrected:

1. The starting ref is `main` at `0bc39f278e24d8cdd79abed5da16bd5ce81e4c5a`; the
   run branch `fiat/1351-anamnesis-2-declared-corpus-scope` was cut from it.
2. Python `3.14.6` per `.python-version`, standard library only, `unittest`. No
   new dependency.
3. Anamnesis's held job is the acceptance authority and admits two outcomes.
   The ordered overlay of 6 September 2026 (entry An.1) and the 6 September 2026
   member answer, both held by the maintainer, chose the first: a declared
   `scope`, and a second corpus holding the estate's own findings, accepted when
   that corpus rebuilds to its own release id. This study measures that choice
   against the second outcome rather than assuming it.
4. The maintainer permits public derived text for the seventeen estate findings
   named in section 4. Confirmation is pending; section 1 states the question.
   If refused, the estate sources become `restricted`, the corpus can be
   released in the public tree only as identifiers and digests, and the `demo`
   and `verify-rebuild` acceptance cannot run there because a rebuild reads the
   source bytes on disk while `verify` reads only the release. The run then
   stops at the step that writes the estate policy and reports blocked.
5. The estate corpus declares record bounds of 10 to 40 and holds 17 records;
   the pilot declares 25 to 50 and holds 41. The estate bounds are this study's
   reading and the maintainer may change them. Only their being declared
   matters to the design.
6. The synopsis view is current:
   `python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .`
   exited 0 from the run root on 6 September 2026 with every row
   `committed=match`.

## 1. Problem statement

Anamnesis's ledger holds one job: decide what the corpus preserves beyond the
pilot. Today the curation scope is `seed_scope` at
`plugins/anamnesis/skills/anamnesis/scripts/anamnesis.py:398-405`, a constant
of 25 to 50 records called once, from `cmd_admit_seed` (`:488-501`). Nothing in
a release says what it preserves or why those records. `release_id`
(`:868-877`) hashes the canonical curation policy, the admitted
`id:sha256:bytes` triples and the five graph components, and nothing from the
admission policy, so a scope declared in the curation policy is already inside
the release id; a scope held in a constant is inside nothing.

What is built, for the maintainer who has to say what the corpus preserves and
for the counterparty-history programme whose panel will cite open findings per
venue:

1. `scope`, a required closed object in the curation policy
   (`anamnesis-curation-policy/v1`), checked both ways against the admitted
   sources and against the declared record bounds wherever the two policies
   meet, and the constant removed.
2. The pilot re-released under its own declared scope, `warden-seed-pilot`,
   with its admission policy, sources and admitted events byte-identical.
3. A second specimen, `plugins/anamnesis/specimens/estate/`, under scope
   `capture-estate-findings`: two sources authored by Wildcat Labs from the 31
   August 2026 archive verification and the 5 September 2026
   counterparty-history programme note, 17 records, its own release, both
   projections and its events.
4. The ledger row `anamnesis-v4.1.0`, and every mutable first-party document
   that describes the old state reconciled.

A working prototype means both commands exit 0:

```bash
python3 plugins/anamnesis/skills/anamnesis/scripts/anamnesis.py demo \
  --specimen plugins/anamnesis/specimens/estate
python3 plugins/anamnesis/skills/anamnesis/scripts/anamnesis.py demo \
  --specimen plugins/anamnesis/specimens/pilot
```

The first prints two fresh builds agreeing on the estate release id across 7
components, the committed estate release verifying with 17 findings across 4
rounds, the Elenchus view for one query with `verdict None`, and the Synkrisis
cohort with 17 included against 17 findings. The second prints the pilot's new
release id, 41 findings, 31 rounds, 12 with no findings, as today. Three
refusals prove the other half: the estate admission policy under the pilot's
curation policy refuses `A074` (an admitted source outside the declared scope)
and `A075` (a declared scope source not admitted); a curation policy without
`scope` refuses `A012`; a record count outside the declared bounds refuses
`A073` naming those bounds rather than the number 25.

Done is checked by: `design_evidence.py --transition integration` exits 0; the
Anamnesis suite is green (194 tests today, 1 skipped, plus this run's guards);
the root suite is green; `git diff --check` is clean; the ledger carries exactly
one new row; and both demo commands above run from a clean snapshot.

Question for the maintainer, stated here and not resolved: may the seventeen
finding texts listed in section 4 be published in
`plugins/anamnesis/specimens/estate/sources/` as public derived text, rights
basis `permission`, holder Wildcat Labs, disclosure `public`? Yes lets the
estate step proceed as specified. No makes both sources `restricted`, and the
acceptance cannot run in the public tree (assumption 4).

## 2. Prior art

**In this repository.**

- `anamnesis.py:79-85` closes the curation policy to `version`, `mapper`,
  `taxonomy`, `disclosure` and optional `duplicates`; `load_curation_policy`
  (`:1107-1126`) enforces it. `schemas/policy-v1.json` declares the same four
  required keys with `additionalProperties: false`, and `release-v1.json`
  embeds it by `$ref` as `manifest.policy`, beside `manifest.sources` (id,
  sha256, bytes, disclosure).
- `seed_scope` (`:398-405`) refuses `A073` outside 25 to 50. It is the only
  scope statement in the tree and only `cmd_admit_seed` calls it; `curate`,
  `release`, `verify-rebuild` and `demo` build a release of any size.
- `verify_release` (`:1019-1093`) recomputes the release id from `policy.json`,
  the manifest's sources and the five components, so anything the release id
  covers must be inside the release. `_rebuild_once` (`:1369-1377`) and
  `verify_rebuild` (`:1380-1410`) read the admission policy, the curation
  policy and the source bytes from the specimen directory.
- The mapper `warden-audit-round-markdown` version 1 (`:515-548`) reads
  `## <label>, round N -- <date>` headings and
  `| id | severity | file | finding | status |` rows whose native id matches
  `[A-Z]?\d*S?\d+-R\d+-\d+` and whose severity matches `[a-z-]+`. A status
  opening `open`, `carried forward` or `deferred` maps to adjudication
  `unknown` and no remediation (`read_status`, `:603-630`). The producer is a
   field of the source, not of the mapper.
- The pilot: `specimens/pilot/policy.json` (3 sources, 41 records, SHA-256
  `5de0d04c338776fd29cc6e27a902fac498a1335700dce1eae7b364ba67cf8901`),
  `curation-policy.json` (326 canonical bytes, version `curation-2026-08-31`),
  a release of 7 files and 168,532 bytes under id
  `079ed18d172d6031551cbda55d25a2c064d255186cd8e27a62e90d26da06ae56`, two
  projections, and two event streams. The three admitted events carry
  correlation ids derived from the admission policy digest; the one refused
  event's id derives from a different policy's bytes and does not move with the
  pilot policy.
- `skills/anamnesis/DEMONSTRATION.md` pins the program digest
  `6318f3ae4cd74e35354d706a1216fa76fea2b6446a2fc2f5b45ad1a61401e645` and the
  admission policy digest, and its observation lines carry the release id and
  cohort id. The root `README.md` front-door card binds that record's digest
  `e97b9dd7490b5d1c0168b9739186bc37f55857d733ad7a07c45b700beeff9ee7` (check
  `FD19` in `scripts/check_public_front_door.py`). Its demo frontier's next job
  is a second corpus from another producer; section 12 says why this run does
  not register the estate specimen there.
- Tests that pin the constant or the pilot bytes: `test_s1_admission.py`
  `PilotScope` (10 and 60 refused `A073`, 41 admitted, admission alone does
  not enforce the range) and `Report` (the exact `admit-seed` report object);
  `test_s3_consumers.py` `ExpectedProjections` (two committed projections),
  `DeterministicRebuild` (the committed release equals a fresh build) and
  `RiskRegister` (reads the first study's eleven ids and the first run's audit
  record; unchanged by this run); `test_s2_curation.py` `ByteCap` (skips when
  the worktree's design record declares no `seed-release-byte-cap`, which is
  the one skip today and stays one); `test_s6_ledger.py` pins
  `anamnesis-v3.1.0` and the `v2.1.0` row. `tests/elenchus.py` admits
  `STEPS = (1, 2, 3, 4, 5, 6)`.
- `docs/study.md` calls 25 to 50 "a curation scope, not a performance claim";
  `docs/demo.md` says the demo does not establish "that the pilot's 41 findings
  are the right 41 to have kept". `docs/synkrisis-admission-study.md` and its
  runbook are the shape this study follows. ADR-001 to ADR-005 stand; ADR-003
  names `permission` as a written grant and `restricted` as identifiers and
  digests alone. `docs/shoggoth-public-front-door-study.md` carries the pilot
  release id as a shipped record and is not edited.
- No `plugins/anamnesis/audit/` directory exists; the plugin's audit history is
  the two run records under `audit/rounds/` below.

**Held by the maintainer, outside this repository.** Cited by date, section and
SHA-256 of the copy read; never by location.

- The 5 September 2026 counterparty-history programme note, SHA-256
  `4349d5f93468acd0117b40765828a3ad974ab2295302a463239d23d85b5a8efa`. §2 lines
  55-63: the Silo halt, verbatim `refused: eth_getLogs: URLError` and
  `stopped at v2/markets/optimism.json`, runner not alive, no release, no
  handover note; and the 31 August headline, "Families proved futureproof:
  0/6", with Maple rated High. §9 lines 261-268: three open actions carried
  from prior handovers.
- The 31 August 2026 archive verification, report SHA-256
  `f8d3391b031ac6eced37a02f3757515198f71490a843bc1e5d8dedf559b6350e`, its
  README `45b4d089090cd3564bd74ca525a354406278fa6e5b27fd4dd41a4f4dba02500a`.
  Executive verdict at lines 7-20 (51 archives, 51/51 digests, 5 with
  undeclared members, 4/6 families with a demonstrated defect, 0/6 proved
  futureproof); twelve priority findings at lines 39-105, four `[High]` and
  eight `[Medium]`; family verdicts at 111-156; remediation order at 158-165.
- The 6 September 2026 member answer, SHA-256
  `19335c0cb893d5125b05776b832f12addac793ecdb14e2cc5ef7db0424b6f9ab`. Desire 1
  is this run. Its refusal: "I will not admit programme sources into the pilot
  corpus by widening a constant, because the release id would then stop being
  a function of a declared policy."
- The ordered overlay of 6 September 2026, SHA-256
  `5f2c6dda3565ef415e2801bc13c6caefebda95dd02ae93b8756e5d4d255d6ed2`, entry
  An.1 at lines 57-62: `policy.scope` as a declared field, a corpus under it
  holding the headline, the Maple High rating, the Silo halt and the §9 open
  actions, accepted when it rebuilds to its own release id.

**The last two merged pull requests that changed the subject.** Nine pull
requests touched `plugins/anamnesis` after #1070: #1080 and #1107 (the Sources
pointer line in the ledger), #1159 (unused bindings), #1238, #1237, #1279, #1278
and #1303 (the demonstration ledger and its runner), and #1330 (the public
surface). None changed the scope, the release path or the pilot, so the two
read are #1070 (`ed6a400c`, 2026-08-31) and #1024 (`b1375b80`, 2026-08-31).

#1070 carries ten rows. Disposition here:

- `boundary-rescan-at-step-end` (#1063, closed) and
  `step-exit-omitted-the-root-suite` (#1067, closed): content. Every step's
  exit names the root suite and `python3 plugins/horos/skills/horos/scripts/horos.py check .`
  before its pull request is ready.
- `resolver-not-committed`: content. The 32 reports name
  `python3 .hexaemeron/reports/resolve.py <candidate> <criterion>`, and step 1
  commits `resolve.py` beside the reports under
  `plugins/anamnesis/docs/corpus-scope/reports/`, so the values can be rerun
  from the repository.
- `study-copy-is-a-rendering`: content. The five discipline citations below are
  commit-pinned absolute URLs already, so the committed copy can be
  byte-identical to the receipted one.
- `second-corpus-specimen-missing`: content. It is the estate specimen.
- `runner-exit-codes-undeclared`, `sk008-probe-not-committed`,
  `reader-is-a-surface-not-a-consumer`, `adr-004-body-keeps-its-original-clause`:
  stay open under their stated reasons; none touches the scope or the release
  path, and Synkrisis is a non-goal.
- `v2-1-0-row-reads-oddly-beside-v3-1-0`: stays as history. The `v3.1.0` row
  will read the same way beside `v4.1.0`, and history is append-only.

#1024 carries seven bullets. Synkrisis admission closed as ADR-005 in #1070 and
is a non-goal here. The unknowns map's recomputability, the two `rename`
promotions and the out-of-release path rule stay open under their existing
wording; each is a boundary on what verification establishes and none is
touched by a scope field. The payload cap accommodation left this tree with the
payload in #1038 and is not this run's. `lazarus-suite` is not re-checked here
and is not this run's. "The pilot is three skills, not the repository. Whether
these 41 findings are the right 41" is this run's subject: the scope is
declared, and judging the 41 stays a non-goal (section 3).

**Audit records.** Two sources are in scope and both were read through their
verified synopsis, because the whole-set check exited 0 with every row
`committed=match` (assumption 6); the sources themselves were not read.

`audit/rounds/fiat-anamnesis-source-bound-curation-and-release-of-a.md`
(source SHA-256
`84203e2761025f5a9057eee11e477384dbcaace57e2e65c8e0dc6710c81c2a61`, ten
rounds). Findings, all `fixed in this round`: S1-R1-01, S1-R1-02, S1-R1-03
(medium), S1-R2-01, S1-R2-02 (low), S1-R3-01 (low), S2-R1-01, S2-R1-02 (high),
S2-R1-03 (medium), S2-R1-04 (low), S2-R2-01 (medium), S2-R2-02 (low),
S3-R1-01 (high), S3-R1-02 (low), S3-R2-01 (low). Elenchus verdicts by round:
guarded, guarded, passed, null; guarded, guarded, null; guarded, passed, null.
`Covered`: every register id reviewed or not-applicable in every round.
`Not checked`: the security suite (waived, no Solidity), hosted CI, the receipt,
push and publication, whether a declared rights basis is lawful, whether the
mapper reads every Warden format, whether the pilot's 41 findings are the right
41, whether another interpreter reproduces the release, and whether Synkrisis
would accept the producer. `Leads not pursued` that bear on this run: S1-R2-01
moved the 25-to-50 check from `admit` into `seed_scope`, and the round wrote
that "the seed_scope bound of 25 to 50 is now a resolver-side constant rather
than a policy field, which is right for the seed the runbook fixes and wrong
for a second pilot; making the scope a declared policy field is step 2's to
decide when the release policy schema lands". Step 2 landed the schema and did
not decide it. This run is that decision. The other carried leads (three
bounded races, the unknowns map, the `rename` promotions, the path rule, the
finding-row pattern's backtracking shape bounded by the byte cap) stand.

`audit/rounds/fiat-admit-the-anamnesis-corpus-projection-into-a-syn.md`
(source SHA-256
`9ebc7a0647ddf49e9f83a36963828939dc49f116c48575c4a3cdbd98db98faa6`, seven
rounds). Findings, all `fixed in this round`: S1-R1-01 (low), S1-R2-01
(medium), S2-R1-01 (medium), S2-R1-02 (low), S3-R1-01 (medium). Verdicts:
guarded, guarded, null; guarded, null; guarded, null. `Covered`: every id
reviewed or not-applicable. `Not checked`: the security suite (waived), hosted
CI, receipt, push, publication, whether the cohort-boundary argument is
correct, whether Synkrisis would decline if asked, whether the new held job is
the most valuable one. `Leads not pursued` that bear here: step 3 round 1
recorded that "the new held job's acceptance condition names a corpus built
under a different declared scope rebuilding to its own release id, and no such
second specimen exists yet, so the condition is testable in principle and
untested in fact"; the Horos boundary went stale twice and nothing rescans it
at step end; the committed reports name an uncommitted resolver; and the study
copy is a rendering. The first two are this run's content; the last two are
answered above.

## 3. Constraints and non-goals

- Starting ref `main` at `0bc39f278e24d8cdd79abed5da16bd5ce81e4c5a`; run branch
  `fiat/1351-anamnesis-2-declared-corpus-scope`.
- Python `3.14.6` per `.python-version`, standard library only, `unittest`.
- Anamnesis suite from the repository root:
  `python3 -m unittest discover -s plugins/anamnesis/tests -t plugins/anamnesis`
  (194 tests today, 1 skipped). Root suite:
  `python3 -m unittest discover -t . -s tests`. Demo:
  `python3 plugins/anamnesis/skills/anamnesis/scripts/anamnesis.py demo --specimen plugins/anamnesis/specimens/pilot`
  rebuilds to `079ed18d…` in 0.01 s wall clock in this checkout; `verify_rebuild`
  alone measures 14 to 19 ms over five runs.
- `plugins/anamnesis/tests/elenchus.py` numbers steps by plugin history. This
  run's runbook steps are admitted as 7 onward, and each step's Tests line
  names `python3 plugins/anamnesis/tests/elenchus.py --step N {report}`, format
  `elenchus.unittest.v1`, report `.hexaemeron/elenchus/anamnesis-step-N.json`.
- `audit/` files and `plugins/*/audit/AUDIT.md` are byte-pinned. The shipped
  studies, runbooks and ADR-001 to ADR-005 are records and are not edited;
  ADR-004's status annotation stays as #1070 left it.
- The mutable prose the last step reconciles: the ledger row and header, the
  `SKILL.md` frontmatter version, the marketplace-context blocks in
  `plugins/anamnesis/README.md`, `AGENTS.md` and `skills/anamnesis/SKILL.md`,
  the front-door status block in `plugins/anamnesis/README.md`,
  `DEMONSTRATION.md`'s pinned digests and observation lines, and the root
  `README.md` card's record digest. The root `.horos/boundary.json` is checked
  before every commit and rescanned when the check reports drift.
- The plugin package version `0.3.0` in `.claude-plugin/plugin.json` and
  `tests/test_version_propagation.py` is a different counter and does not move
  with the frontier; it stayed at `0.3.0` across `v2.1.0` to `v3.1.0`.
- Ledger arithmetic per `VERSIONING.md`: one row, evolution 3 to 4, generation
  1 and epoch 0 retained, the prior revision `corpus-scope` and digest
  `1da8d2f843cb3b0ff1fd6dac5d41d4cafb5746388635c3f1ba5e41adde1d1f77` preserved,
  header and row naming `anamnesis-v4.1.0`, frontmatter `4.1.0`.
- The estate specimen, the study, the runbook, ADR-006 and every report never
  name the maintainer-held documents' repository, branch, file paths or local
  disk paths; they cite date, section and SHA-256.
- Non-goals: a second mapper (the grammar is the mapper's subject and the
  `producer` field is the truth about who wrote it, so a Wildcat Labs-authored
  source in the Warden grammar reads under `warden-audit-round-markdown` and
  says so in its engagement); reopening ADR-005 or touching anything under
  `plugins/synkrisis`; changing the rights model or ADR-003; judging whether the
  pilot's 41 findings are the right 41 beyond declaring their scope; a network
  path of any kind; moving the plugin package version; registering the estate
  specimen in the demonstration ledger (section 12).

## 4. Design options

Four candidates were drawn and scored in `.hexaemeron/design-evidence.json`
(SHA-256 `b9e9d4d14113b460b6ffbd78aa463d86620bf1b46fe948becf1e49874702f32b`).
Every value is the output of
`python3 .hexaemeron/reports/resolve.py <candidate> <criterion>` run from the
run root at this commit, over the tree plus the candidate's declared
construction: which document holds the scope, which pilot tokens it moves, and
how many corpora its acceptance rebuilds. The resolver holds those declarations
as data, and step 1 commits it beside the reports.

**`release-policy-scope`.** `scope` becomes a required closed object in the
curation policy, the policy the manifest records and `release_id` already
hashes. The trade: the pilot is re-released (seven committed files change, the
admission policy and events do not), and every corpus must now say what it
preserves before it can be built.

**`admission-policy-scope`.** `scope` goes into the admission policy
(`anamnesis-pilot-policy/v1`) and `release_id` is extended to hash that
policy's canonical bytes. The trade: the scope sits beside the source list it
constrains, at the cost of a release id that depends on a document the release
does not carry, so `verify_release` could no longer recompute it from the
release alone without a further manifest change, and the pilot's admitted
events change with the policy digest.

**`permanent-seed-record`.** No code change. A decision record states the
hand-picked 41-record seed is the permanent shape and names what governs
additions. The trade: it is the cheapest and it is the outcome the maintainer's
overlay refused, because the estate corpus (17 records) then cannot be
admitted at all: `seed_scope(17)` refuses `A073` today.

**`widen-constant`.** Keep `seed_scope`, widen it or add a second constant for
the estate. The trade: the estate becomes admissible and the release id still
says nothing about scope, which is the member answer's stated refusal.

**Criteria and results.** Five concerns, eight criteria, 32 cells, no cell
pending.

| Criterion | Kind | `release-policy-scope` | `admission-policy-scope` | `permanent-seed-record` | `widen-constant` |
| --- | --- | --- | --- | --- | --- |
| `release-id-declared-function` (correctness, gate, equals true) | the scope's document is hashed by `release_id`, at this commit or by the candidate's declared extension | true | true | false | false |
| `scope-recorded-in-release` (correctness, gate, equals true) | the scope's document is a release component in the pilot manifest | true | false | false | false |
| `estate-findings-admissible-without-widening` (correctness, gate, equals true) | 17 records pass the bound the candidate reads: `seed_scope(17)` today, or the declared 10 to 40 | true | true | false | false |
| `foreign-ledgers-touched` (compatibility, gate, equals 0) | governed `EVOLUTION.md` files outside Anamnesis in the candidate's file set | 0 | 0 | 0 | 0 |
| `pilot-artefacts-rebuilt` (compatibility, metric, minimise, count) | tracked files under `plugins/anamnesis` carrying a token the candidate moves | 7 | 6 | 0 | 1 |
| `policy-bytes-added` (space, metric, minimise, bytes) | canonical bytes the pilot scope adds to the policy file that holds it | 340 | 220 | 0 | 0 |
| `acceptance-check-ms` (time, metric, minimise, milliseconds) | median of five `verify_rebuild` runs over the pilot, times corpora rebuilt (2, 2, 0, 1) | 35 | 35 | 0 | 19 |
| `scope-recovery-by-policy-edit` (recovery, gate, equals true) | a scope refusal is recovered by editing a policy file rather than `anamnesis.py`, where the literal bound sits today | true | true | false | false |

How each was measured. `release-id-declared-function` reads `release_id`'s
body for `canonical(policy)`, the curation policy; the admission policy is not
hashed at this commit and `admission-policy-scope` declares the extension, so
its value comes from that declaration. `scope-recorded-in-release` reads the
pilot manifest: `policy.json` is a component whose bytes equal
`manifest.policy`; no component's digest equals the admission policy's.
`estate-findings-admissible-without-widening` calls `seed_scope(17)` for the
two candidates that keep the constant and evaluates `10 <= 17 <= 40` for the
two that declare bounds. `pilot-artefacts-rebuilt` runs `git grep -l` under
`plugins/anamnesis` for the tokens each candidate moves: the curation policy's
version string and component digest (five files: `curation-policy.json`,
`release/policy.json`, `release/manifest.json`, `release/relations.json`,
`projections/synkrisis-cohort.json`), the release id (four: the manifest, both
projections, `DEMONSTRATION.md`), the program digest (`DEMONSTRATION.md`), and
the admission policy digest and its correlation ids (`policy.json`,
`events/admit.jsonl`, `DEMONSTRATION.md`). `policy-bytes-added` is
`len(canonical(policy with scope)) - len(canonical(policy))` over the pilot
policy the candidate names: 326 to 666 bytes for the curation policy with a
`sources` list, 220 for the admission policy without one, since that policy
already lists its sources. `acceptance-check-ms` is measured, not estimated;
the estate corpus is smaller than the pilot, so the figure is an upper bound.
`scope-recovery-by-policy-edit` confirms the literal `25 <= record_count <= 50`
sits in `anamnesis.py` at this commit and asks whether the candidate moves the
bound into a policy file.

**Selection.** `permanent-seed-record` and `widen-constant` fail three gates
each: `release-id-declared-function`,
`estate-findings-admissible-without-widening` and
`scope-recovery-by-policy-edit`, and `scope-recorded-in-release` besides.
`admission-policy-scope` passes everything except `scope-recorded-in-release`:
the admission policy is not in the release, so a release id that depended on
it could not be recomputed from the release, which `verify_release` requires
today and which the first study's `partial-release` and `source-byte-drift`
controls rest on. `release-policy-scope` passes every gate and is the sole
survivor, so the rule is `unique-frontier`. Its metrics are not the smallest
(seven files against six, 340 bytes against 220); they were never compared
because the frontier had one member. `design_evidence.py --transition
design-lock` exits 0.

The numbers rest on one point. A release must be verifiable from its own
bytes. The curation policy is a release component and the admission policy is
not, so a scope that must be inside the release id has one place to live, and
the cheaper-looking alternative moves the scope out of the release.

**The construction under `release-policy-scope`.**

The scope object, closed:

```json
"scope": {
  "id": "warden-seed-pilot",
  "preserves": "Warden audit rounds from three first-party skills as preserved at commit 1c1137898bce.",
  "sources": ["hexaemeron-audit-rounds", "pandects-audit-rounds", "tabularium-audit-rounds"],
  "records": {"minimum": 25, "maximum": 50}
}
```

`id` is kebab-case; `preserves` is one bounded sentence; `sources` is a
non-empty list of unique source ids; `records.minimum` and `maximum` are
integers with `1 <= minimum <= maximum`. `CURATION_POLICY_KEYS` gains
`scope: True` and `schemas/policy-v1.json` gains it as required. A malformed
scope refuses `A076`; a missing one refuses `A012` through `closed_object`.

`check_scope(policy, admitted, record_count)` runs wherever the curation policy
and the admission result meet: `admit-seed` (which gains `--curation-policy`),
`curate`, `release`, and `_rebuild_once` for `verify-rebuild` and `demo`. It
refuses `A074` when an admitted source is not in `scope.sources`, `A075` when a
scope source was not admitted, and `A073` when the record count is outside the
declared bounds, naming the bounds. `verify_release` gains the both-ways source
check over `manifest.sources` and `manifest.policy.scope.sources`, which are
both inside the release, and refuses `A077` on a mismatch. `seed_scope` is
removed. The `admit-seed` report keeps criterion `seed-source-rights-admitted`
and records the new command line.

The pilot's `curation-policy.json` gains the scope above and moves its
`version` to `curation-2026-09-06`, because a policy with new bytes is a new
policy. The seven files named under `pilot-artefacts-rebuilt` change and
nothing else under the pilot does: `policy.json`, the three sources,
`events/admit.jsonl`, `events/refused.jsonl`, `engagements.json`,
`assertions.json`, `quarantine.json` and `unknowns.json` are byte-identical.

The estate specimen, `plugins/anamnesis/specimens/estate/`:

- `policy.json` (`anamnesis-pilot-policy/v1`; the schema name is the admission
  policy's name and is not changed here), `policy_version`
  `estate-2026-09-06`, `max_source_bytes` 1000000, two sources, 17 records.
- Source `archive-verification-2026-08-31`, `text/markdown`, producer
  "Wildcat Labs, archive verification of 31 August 2026", provenance origin
  "the 31 August 2026 archive verification, held by the maintainer, SHA-256
  f8d3391b…", `origin_path` naming the sections and lines read (executive
  verdict 7-20; priority findings 39-105; family verdicts 111-156), no
  `origin_commit`, retrieved 2026-09-06. Rights: basis `permission`, holder
  Wildcat Labs, disclosure `public`, statement recording the maintainer's
  grant once given (assumption 4). Two rounds. "Priority findings, round 1 --
  31 August 2026" holds V1-R1-01 to V1-R1-12: four `high` (Maple omits fields
  the pinned schema and live API return, which is the Maple High rating; Euler
  Earn histories missing for 46 discoverable vaults; Aave v3 and v4 schema
  surface not established; Euler raw-source and block-scope descriptions
  contradict the archived method) and eight `medium` (365 undeclared
  AppleDouble members across five archives; Compound v3 Arbitrum out of order
  with a collector that can advance past a failed range; Compound v2's eight
  misread state gaps; stale Euler schema interpretation; a Wildcat hash check
  recorded as passed with no hash supplied; Maple provenance that cannot
  reproduce its rows; present checks stronger than the bundled release gates;
  no kit establishing its registry is current). "Family verdicts, round 2 --
  31 August 2026" holds V1-R2-01, severity `unrated`, finding "Families proved
  futureproof: 0/6". Every status is `open`.
- Source `counterparty-history-2026-09-05`, producer "Wildcat Labs,
  counterparty-history programme note of 5 September 2026", provenance origin
  naming the note by date and SHA-256 `4349d5f9…`, `origin_path` "§2 lines
  55-63; §9 lines 261-268". Two rounds. "Capture inventory, round 1 -- 5
  September 2026" holds P1-R1-01, `unrated`: Silo halted with
  `refused: eth_getLogs: URLError` and `stopped at v2/markets/optimism.json`,
  runner not alive, no release, no handover note. "Open actions carried from
  prior handovers, round 2 -- 5 September 2026" holds P1-R2-01 (rotate the
  Graph gateway key that reached an operator's shell history; the record names
  the key's existence and never its value), P1-R2-02 (Compound v3 and Euler V2
  releases carry a release id and no statement: built, never sealed) and
  P1-R2-03 (Silo V2 optimism onward unresumed and unreleased). Every status is
  `open`.
- `curation-policy.json`: version `estate-2026-09-06`, mapper
  `warden-audit-round-markdown` 1, taxonomy `estate-severity` 1 with
  severities `high`, `medium`, `unrated`, disclosure `derived_text: [public]`,
  and scope `capture-estate-findings` preserving "the capture estate's own
  verification findings and open actions of 31 August and 5 September 2026",
  sources both ids, records 10 to 40. `unrated` is declared so the headline,
  the halt and the open actions are curated rather than quarantined; no rating
  is invented for them.
- `release/` (7 components, its own id), `projections/` (severity `high`
  analogues; the cohort of 17), `events/admit.jsonl`.

The mapper is unchanged, so the estate release will hold 17 submissions, 17
findings, 4 verifications all `unknown`, 0 remediations, and occurrences for
every row with a non-empty file column. Those zeros are the truth about the
sources: nothing in either document records a fix.

## 5. Risk register seed

```risk-register
scope-in-release-id | the curation policy the manifest records | the scope object sits inside canonical(policy), and a one-byte change to any scope field changes the release id in a guard
constant-removed | anamnesis.py | no literal record bound remains in the resolver; every bound the code enforces is read from a policy file
scope-both-ways | the admitted source set against scope.sources | an admitted source outside scope refuses A074 and a scope source not admitted refuses A075, each with its own specimen, at build and at verify
estate-provenance | the estate sources' producer and provenance fields | each names its original by date and SHA-256, the producer is the estate verification and not Warden, and the engagement carries that producer
private-origin-unnamed | every byte of the estate specimen, ADR-006, the study, the runbook and the reports | no repository name, branch, file path or local disk path of the maintainer-held documents appears; a guard refuses local path prefixes and URL schemes in the estate sources
disclosure-assumption | the estate sources' rights.disclosure | public is written only once the maintainer's grant is recorded in the rights statement; until then the estate step is blocked, not guessed
pilot-rebuild-drift | the committed pilot specimen and DEMONSTRATION.md | the pilot's admission policy, sources and events are byte-identical, the new release id appears in every file that carried the old one, and the pilot demo exits 0
killed-build | the staging directory of the estate release build | a killed build leaves no directory that verifies; the existing A100 and A103 guards run over the estate specimen
ledger-arithmetic | plugins/anamnesis/skills/anamnesis/EVOLUTION.md | exactly one new row, evolution 3 to 4, generation and epoch retained, prior revision and digest preserved, header version equal to the newest row and to the SKILL.md frontmatter
stale-prose | mutable first-party marketplace prose | the three marketplace-context blocks, the front-door status block, DEMONSTRATION.md's digests and observation lines, and the root README card digest are cold-read and reconciled
demo-status | DEMONSTRATION.md | the demonstration stays real-data over the pilot and the estate specimen is not a material input of it
```

A round cites each id as reviewed or not applicable. `disclosure-assumption`
is the one that can stop the run rather than fail a test: it is reviewed at the
estate step against the recorded grant, and a step that writes `public` without
one has misread assumption 4.

## 6. Glossary seeds

- **Declared scope.** The `scope` object of a curation policy: id, what it
  preserves, the admitted source ids, and the record bounds.
- **Release policy.** The curation policy, so called because the manifest
  records it and the release id hashes it.
- **Admission policy.** `anamnesis-pilot-policy/v1`, which names the sources,
  their rights and the records a corpus admits. Not in the release; its digest
  keys the events.
- **Resolver-side constant.** A bound held in code rather than in a policy,
  such as `seed_scope`.
- **Estate corpus.** The specimen under `capture-estate-findings`: the capture
  estate's own verification findings and open actions.
- **Derived text.** Finding text, labels and dates a release may carry from a
  source; `public` admits it, `restricted` admits identifiers and digests.
- **Unrated.** A severity declared in the estate taxonomy for a record its
  source never rated. Not a rating.
- **Held job.** The `Next Fiat job` line in `EVOLUTION.md`; a target, not a
  writing prompt.

## 7. Sources

- `plugins/anamnesis/skills/anamnesis/scripts/anamnesis.py` lines 79-85,
  398-405, 488-501, 515-548, 603-630, 868-877, 1019-1093, 1107-1126,
  1369-1410.
- `plugins/anamnesis/skills/anamnesis/schemas/policy-v1.json`,
  `release-v1.json`, `source-v1.json`, `rights-v1.json`.
- `plugins/anamnesis/specimens/pilot/` (policy, curation policy, release,
  projections, events, sources).
- `plugins/anamnesis/skills/anamnesis/EVOLUTION.md`, `SKILL.md`,
  `DEMONSTRATION.md`; `plugins/anamnesis/README.md`, `AGENTS.md`.
- `plugins/anamnesis/docs/study.md`, `runbook.md`, `demo.md`,
  `synkrisis-admission-study.md`, `synkrisis-admission-runbook.md`,
  `decisions/ADR-001` to `ADR-005`.
- `plugins/anamnesis/tests/elenchus.py`, `test_s1_admission.py`,
  `test_s2_curation.py`, `test_s3_consumers.py`, `test_s6_ledger.py`.
- `audit/rounds/fiat-anamnesis-source-bound-curation-and-release-of-a.synopsis.md`
  and `audit/rounds/fiat-admit-the-anamnesis-corpus-projection-into-a-syn.synopsis.md`.
- Pull requests wildcat-finance/skills#1070 and #1024, `## Carried forward`;
  issues #1063, #1067, #1351.
- `plugins/hexaemeron/skills/VERSIONING.md` and `DEMONSTRATIONS.md`;
  `scripts/check_public_front_door.py`; root `README.md` lines 74-87.
- The maintainer-held documents in section 2, by date and SHA-256.
- `.hexaemeron/design-evidence.json` and `.hexaemeron/reports/`.

## 8. Signals, and the questions behind them

Nothing here runs unattended; every command runs from a terminal and reports
through its exit status. The one question someone will ask later is "why was
this source or record refused under the declared scope", and it is answered by
the existing durable refusal stream: `A073`, `A074`, `A075`, `A076` and `A077`
are raised inside the `refusals_recorded` boundary and so emit
`anamnesis.source.refused` with the rule, the record, the policy version and
the correlation id, the same way every refusal has since S1-R2-02. No new event
kind is added and no remote telemetry exists.
[ephoros](https://github.com/wildcat-finance/skills/blob/0bc39f278e24d8cdd79abed5da16bd5ce81e4c5a/plugins/hexaemeron/skills/ephoros/SKILL.md)
owns what a signal must carry; the new refusals carry what the old ones do.

## 9. Boundaries, per capability

Four boundaries, none new in kind.

- The estate source bytes enter through the admission path that already
  exists: an ordinary file below the policy root, no symlink followed, a byte
  cap, an exact digest. The control is unchanged and the guards run over the
  new specimen.
- The scope check reads two policy files and compares bounded strings and
  small integers. The control is the closed-object and bounded-text validation
  every policy field already passes through.
- The estate finding texts are derived text from documents held by the
  maintainer. What is worth taking at this boundary is a repository name, a
  path, or a credential value. The control is the rule in section 3, a review
  of the authored bytes, and a guard that refuses local path prefixes and URL
  schemes in the estate sources. P1-R2-01 records that a key needs rotating
  and carries no key.
- No network, no subprocess over untrusted input, no credential, no new
  dependency.
  [phylax](https://github.com/wildcat-finance/skills/blob/0bc39f278e24d8cdd79abed5da16bd5ce81e4c5a/plugins/hexaemeron/skills/phylax/SKILL.md)
  owns the boundary list and its controls.

## 10. The budget, or its absence

No performance budget is declared. The demo prints wall clock and peak resident
memory as baselines with no threshold, for both specimens. The release byte
cap of 50,000,000 already applies to any release and `measure-release` checks
the estate release against it. The `acceptance-check-ms` values in the design
record (35 ms for two corpora) are selection evidence, not a budget.
[metron](https://github.com/wildcat-finance/skills/blob/0bc39f278e24d8cdd79abed5da16bd5ce81e4c5a/plugins/hexaemeron/skills/metron/SKILL.md)
owns what a budget carries; none is declared and no change here is made in the
name of speed.

## 11. The fail-closed posture

What stops the run: a scope refusal (`A073` bounds, `A074` source outside
scope, `A075` scope source not admitted, `A076` malformed scope, `A077`
manifest sources not the declared scope at verify); `verify-rebuild` refusing
`A150` to `A152`; `demo` refusing `A153` when the committed release is not
what a fresh build produces; the design checker at a step boundary; the ledger
tests; the front-door `FD19` digest check; the Horos boundary check; and the
imprimatur and hypomnema lints on every shipped document. A fix follows the
guard convention: the guard names its exact specimen, fails against the parent
commit and passes against the fixed tree, and a refusal code has one specimen
per code.
[elenchus](https://github.com/wildcat-finance/skills/blob/0bc39f278e24d8cdd79abed5da16bd5ce81e4c5a/plugins/hexaemeron/skills/elenchus/SKILL.md)
owns the triage order and the guard rule.

## 12. Decisions and their homes

Four decisions are expensive to reverse.

- **The scope is declared in the release policy.** Not in the admission
  policy, not in a constant. Its home is the ledger row in
  `plugins/anamnesis/skills/anamnesis/EVOLUTION.md`, the governed skill's
  decision home; a plugin-level record,
  `plugins/anamnesis/docs/decisions/ADR-006-declared-corpus-scope.md`, holds
  the four alternatives and the matrix in full and is cited from the row's
  Evidence column.
- **A policy with new bytes is a new version.** The pilot's curation policy
  moves to `curation-2026-09-06` when it gains a scope. Recorded in ADR-006's
  consequences.
- **The estate sources' rights basis and disclosure.** Recorded where ADR-003
  puts every such claim: the `rights` object of each source in the estate
  `policy.json`, with the maintainer's grant as the statement. ADR-003 is not
  reopened.
- **The demonstration ledger is re-pinned and not advanced.** `DEMONSTRATION.md`
  must carry the new program digest and observation lines, which is a
  generation entry on the demo lane. The estate specimen is not added as a
  command: its sources are authored derived text, a constructed material input,
  and the record would fall from `real-data` to `mixed` and fail the front-door
  card. The demo lane's next job stays as written. Recorded in the
  `DEMONSTRATION.md` history row.

[hypomnema](https://github.com/wildcat-finance/skills/blob/0bc39f278e24d8cdd79abed5da16bd5ce81e4c5a/plugins/hexaemeron/skills/hypomnema/SKILL.md)
owns which decisions earn a record and where each one lives. The new held job
is chosen at the last step from the evidence then in hand: the member answer
records two further desires (a per-venue rights and disclosure decision before
any venue reaches a panel; a blocking-finding projection read at build time),
and `mature` is the other admissible answer.

```design-bridge
schema | hypomnema-design-bridge/v1
decision | release-policy-scope
record | plugins/anamnesis/skills/anamnesis/EVOLUTION.md
```
