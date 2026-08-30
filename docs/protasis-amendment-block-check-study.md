# Study: make Protasis the study-amendment shape authority

Assuming, unless corrected:

1. Issue [#497](https://github.com/wildcat-finance/skills/issues/497) is the
   current `protasis-next` frontier delivery. Its acceptance is the exact
   `Next Fiat job` at the run start; the older issue prose is prior art, not a
   version pin.
2. The start is `main` at
   `9e25b995bf4be01919559596d2af2ff65ba896a4`, with Python `3.14.6` from
   `.python-version` and the standard library only.
3. P000 through P006 and S000 through S007 remain stable. The study-amendment
   shape joins the S-series as S008; the runbook amendment keeps P005.
4. Protasis owns the dated heading, calendar date, final placement, ordered
   four-field shape, cardinality, and non-empty-value verdict. Fiat retains
   receipt-prefix continuity, step topology, touched-step rules, per-unbuilt-
   step verdict coverage, transaction recovery, and receipts.
5. The implementation may extract values from a suffix already accepted by
   Protasis, but it must not make a second shape verdict in `hexctl.py`.
6. Completion advances Protasis from `protasis-v4.9.0` to
   `protasis-v5.9.0`. The current evidence supports a mature frontier after
   this job; a new open target is recorded only if implementation or audit
   supplies a concrete unmet acceptance condition.

These assumptions are confirmed by the current issue review, exact source
tree, evolution ledger, and versioning contract. If integration evidence
invalidates assumption 6, the run must amend this study before writing a
different frontier row.

## 1. Problem statement

Protasis fixes the shape of a study amendment but `protasis.py --study` does
not inspect amendments. A study with `### Amendment` but no date, or a study
amendment missing `What changed`, `Why`, `Steps touched`, or `Still holding`,
still exits clean if its twelve baseline items and risk register are valid.
That is a false clean at the content-contract boundary.

Fiat's `amend study` transition already validates that shape inside
`hexctl.py`, then invokes the bundled Protasis checker. Direct Protasis use and
controller use can therefore disagree, and the same four-field grammar can
drift in two files. Protasis also has a runbook amendment scanner that already
checks the common dated four-field base before applying runbook-only
replacement rules.

For direct Protasis users and Fiat operators, the working prototype makes one
Protasis scanner authoritative for the common amendment shape. Study mode
reports S008 for each real malformed study amendment, ignores fenced examples,
accepts every complete amendment, and leaves a study with no amendment
unchanged. Runbook mode keeps P005 and its replacement-field rules. Fiat calls
the study checker before consuming the accepted suffix and keeps only the
controller facts that Protasis cannot know.

The direct demo path is:

```bash
mise exec python@3.14.6 -- python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study plugins/hexaemeron/tests/fixtures/protasis/complete-study.md
mise exec python@3.14.6 -- python3 -m unittest plugins.hexaemeron.tests.test_protasis_checker plugins.hexaemeron.tests.test_hexctl
mise exec python@3.14.6 -- python3 -m unittest discover -s tests
mise exec python@3.14.6 -- python3 plugins/hexaemeron/tests/run_tests.py
```

The first command must remain clean for the no-amendment fixture. The focused
tests must prove a complete amendment clean, each required date or field
omission S008-red, fenced examples inert, existing P005 behavior unchanged,
and `amend study` refusing malformed shape through Protasis before any durable
mutation. The two complete suites must exit zero.

## 2. Prior art

The current source establishes four useful boundaries.

- `plugins/hexaemeron/skills/protasis/scripts/protasis.py` already supplies one
  fence-aware `_scan`, bounded reads, `AMENDMENT`, `AMENDMENT_LIKE`, and the
  four field names. `_runbook_amendment_findings` checks the common shape and
  P005's runbook-only replacement clauses. `check_study` checks items and the
  risk register but never calls an amendment check.
- `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` has a separate Markdown
  scanner and amendment grammar. `_study_amendment_boundary` validates the
  date and number of blocks, while `_study_amendment_fields` validates
  placement, cardinality, order, and values. `_study_step_verdicts` then uses
  controller state to check touched and unbuilt steps. `cmd_amend_study` builds
  the controller record before `_check_amended_study` invokes Protasis.
- `plugins/hexaemeron/tests/test_protasis_checker.py` has 89 clean baseline
  tests at the start. Its study cases end at S007 and its fixtures include no
  study amendment. `plugins/hexaemeron/tests/test_hexctl.py` covers the
  controller's date, field, fence, prefix, verdict, recovery, and drift rules.
- `docs/protasis-risk-register-block-check-study.md` chose extension of the
  existing study walk over a separate script or controller parse because one
  study command is the content authority. `docs/protasis-amendment-contract-study.md`
  fixed the append-only four-field shape. `docs/fiat-receipted-study-amendments-study.md`
  then deliberately kept correction truth and step-verdict correctness
  outside the controller's evidence claim.
- Outside the repository, CommonMark 0.31.2 sections 4.2, 4.4, and 4.5 define
  ATX headings, four-space indented code, and fenced code. In particular, a
  fence uses at least three matching backticks or tildes, may be indented by
  no more than three spaces, and closes with the same marker at no shorter
  length. The local scanner intentionally implements only the subset its
  contract names; this run preserves that declared boundary instead of adding
  a general Markdown parser.
- A GitHub code search for `"### Amendment --" org:wildcat-finance` on
  2026-08-29 returned only `wildcat-finance/skills` and its generated portable
  copies. No separate Wildcat organisation repository supplies another
  amendment scanner or a carried interface to reconcile.

The two latest merged deliveries that changed Protasis were read before the
options below were drawn. The newest is issue #556's three-PR stack, ending at
PR #708; the exact surviving heads are #603 at
`417c2a876df77ac2a3d04e6378d959bca6299fc1`, #604 at
`882776b8e1e5c33d6b93fefa997552b3fb75b1b4`, and #708 at
`7339825123cc96d29fdc2a084ca5cc04bf4c087a`. It added P006 and
`version-relations`, retained this frontier byte for byte, and carried no
amendment-shape successor. The next latest is issue #369's audit-synopsis read
view at `bdff15f39e7eab1d6a05d080674ae86b3af91687`; it retained this frontier
and requires the source/view inventory recorded below. GitHub currently
returns 404 for the removed Shoggoth-authored PR records, so their exact local
PR heads, main commits, committed studies, runbooks, and verified audit
synopses were the available reading view. Their unavailable body wording
remains unknown; no hidden carried-forward item is claimed.

The repository-wide synopsis check ran from the target root and exited zero:

```bash
mise exec python@3.14.6 -- python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .
```

Every in-scope audit source remains authoritative. These were the actual read
views after that successful whole-set check:

- `audit/AUDIT.md` through `audit/AUDIT_SYNOPSIS.md`, source SHA-256
  `c271237691dc76a95059651f08710411e9d095b12d92b3d5f960182e357bb9fa`.
  The Protasis discipline, study-schema, risk-register, amendment-contract,
  register-check, receipted-study-amendment, and runbook-amendment records were
  read. Their legacy `Audit schema`, `Covered`, `Not checked`, and `Elenchus
  verdict` fields remain explicitly unknown where the synopsis says
  `[missing legacy field: ...]`; findings, statuses, and `Leads not pursued`
  were retained.
- `plugins/hexaemeron/audit/AUDIT.md` through
  `plugins/hexaemeron/audit/AUDIT_SYNOPSIS.md`, source SHA-256
  `8acff29ed567c97902941a85d72e41171c10850de6aa898b5d50564248eac28f`.
  Both rounds were read; F-01 through F-09 are fixed, F-10 is accepted, and
  the recorded concurrency, filesystem, and JSON-output leads stay outside
  this change.
- `audit/rounds/fiat-556-resolve-runbook-target-versions-at-integrate.md`
  through its sibling synopsis, source SHA-256
  `189d2803df08bcc755595c2c33ed56e2ff3594311e8102d600feca655e69d878`.
  All 19 rounds were read. Every named finding is fixed; value-free P006
  diagnostics, printable-character bounds, native Git evidence, and the
  stated lack of an external trust anchor remain intact.
- `audit/rounds/fiat-369-read-audit-synopsis-resigned.md` through its sibling
  synopsis, source SHA-256
  `a5bbc01858fb95cb5334a503285c73418e2ee4a7618f66920f89c1aafa94f784`.
  Its only round is clean, all thirteen risks are `reviewed`, the waived and
  unavailable surfaces remain `Not checked`, `Elenchus verdict` is `null`,
  and there are no unpursued leads.

The relevant carry-forward is narrow. Full CommonMark handling beyond the
documented fence subset remains deliberately unsupported. S002 still checks
presence, not answer quality. Fiat retains prefix continuity, verdict
coverage, recoverable writes, and the refusal to prove amendment prose true.
P005 keeps the four-space fence and replacement-Exit command guards. General
transaction rewrites, a runbook-repair transition, external signed state,
stale historical README test counts, and plugin-cache ownership stay outside
this frontier.

## 3. Constraints and non-goals

- Start from the exact SHA and Python pin in the assumptions. Add no package,
  network call, storage format, public ABI, or CI change.
- Keep `protasis.py`'s regular-file and byte caps, deterministic finding model,
  bounded fence walk, value-free controlled-input diagnostics, text/JSON
  parity, and exit codes 0, 1, and 2.
- Preserve all P000-P006 and S000-S007 firing conditions. S008 settles only
  study-amendment shape; it does not judge whether the correction, reason,
  touched-step claim, or holding verdict is true.
- Preserve P005's complete-replacement grammar and Exit-command rule. A common
  scanner may share date, placement, and four fields, but study mode must not
  inherit runbook-only replacement clauses.
- Preserve Fiat's exact receipted prefix, one-final-suffix, touched-step,
  topology, unbuilt-step verdict, lock, pending record, recovery, state, and
  ledger rules. Protasis has no controller state and must not claim them.
- A no-amendment study remains valid without a pragma. Fenced amendment
  examples are not live amendments. Existing historical studies are not
  rewritten merely to exercise the new rule.
- Completion owes one evolution row, a current-state rewrite of Protasis
  prose, a cold read of every mutable first-party marketplace description,
  propagated portable copies, package-version reconciliation, and the
  repository's selected checks.
- Non-goals: changing the four-field contract, supporting arbitrary CommonMark,
  adding a general Markdown parser, introducing a machine-readable amendment
  receipt schema in Protasis, proving amendment content, changing runbook
  amendment semantics, repairing a runbook, or raising Fiat audit limits.

**Always.** Run both suites before a commit; run Protasis over the study and
runbook; run Imprimatur on every shipped document; keep exact source-bound
fixture evidence; sign and verify every Fiat commit.

**Ask first.** Add a dependency, change CI, widen accepted Markdown, change a
receipt or state shape incompatibly, reopen a mature frontier without external
evidence, or choose a non-patch plugin release.

**Never.** Delete or suppress a failing guard to pass; copy untrusted document
text into an unbounded diagnostic; make `hexctl.py` a second content authority;
edit vendored code; publish a version row without its digest evidence; commit
credentials or raw signing material; claim an unrun command.

## 4. Design options

1. **One parameterised amendment scanner in Protasis, with a narrow Fiat
   consumer after the check. Chosen.** Refactor the common dated-heading,
   calendar-date, final-placement, four-field order/cardinality, and non-empty
   checks into one helper in `protasis.py`. Runbook mode maps common faults to
   P005 and then applies its replacement clauses. Study mode maps them to S008
   and applies no runbook clause. Fiat runs `protasis.py --study` before it
   derives receipt data, locates the suffix by exact prior digest, and consumes
   only `Steps touched` and `Still holding` for state-bound rules. This keeps
   one shape verdict and the smallest controller change. It trades away a
   typed cross-process parse result: Fiat still extracts already-accepted
   values, but that extraction cannot authorise shape.
2. **Add study amendment checks beside the current runbook helper and leave
   Fiat unchanged.** Rejected: direct study checks improve, but the controller
   keeps a second date and field authority, so the issue's drift remains.
3. **Move the grammar to a new shared module imported by both tools.**
   Rejected: it creates another public file and import boundary for a small
   parser already owned by Protasis. It also makes `protasis.py --study` less
   visibly authoritative.
4. **Make Protasis emit a new successful amendment JSON schema for Fiat.**
   Rejected for this frontier: it removes even the narrow extractor, but adds
   a durable machine interface, output limits, schema tests, and compatibility
   work not required to catch the omissions.

## 5. Risk register seed

```risk-register
false-clean | live study amendments among fenced examples and ordinary sections | every missing date or field fixture reports S008 while complete and absent amendments remain clean
scanner-drift | Protasis shape authority beside Fiat receipt construction | malformed shape reaches the Protasis refusal before controller record construction and no second shape verdict remains in hexctl.py
field-extraction | Fiat consuming Steps touched and Still holding after Protasis accepts the suffix | extraction is confined to accepted bytes and hostile order duplicate empty and unexpected fields cannot reach controller state
prefix-continuity | the boundary between the receipted study and accepted amendment | prefix mutation duplicate final blocks and trailing sections still refuse without a durable write
fence-semantics | common scanning across study and runbook modes | backtick tilde long-fence and four-space specimens preserve the documented CommonMark subset and do not change P005
interface-stability | S008 added beside cited P000-P006 and S000-S007 codes | existing focused tests pass unchanged and text and JSON reports retain their stable fields
partial-write | checker-before-record ordering around amendment recovery | validation completes before the pending record and interruption cases recover to matching artefact state and ledger
frontier-arithmetic | protasis-v5.9.0 maturity row and package propagation | evolution version propagation Promise Machine portable-copy and frontier gates all pass on the final tree
```

The audit loop should look first for `scanner-drift` and `false-clean`. A clean
direct checker that is not the controller's authority, or a controller path
that can accept a shape the direct checker rejects, would leave issue #497
open even if every positive fixture passed.

## 6. Glossary seeds

- Common amendment shape: one real dated `### Amendment -- YYYY-MM-DD`
  section, final in the document, with `What changed`, `Why`, `Steps touched`,
  and `Still holding` exactly once, in order, with non-empty values.
- S008: the stable study finding for a malformed common amendment shape.
- Shape authority: the checker whose zero exit authorises treating the named
  amendment bytes as structurally accepted, and no stronger claim.
- Validated-value consumer: Fiat's state-aware extraction from a suffix after
  the shape authority exits zero; it does not make another shape verdict.
- Absent amendment: a study with no real amendment-like heading outside a
  fence; this remains outside S008.
- Frontier closure: the evolution row proving this held target completed and
  either naming one evidenced successor or recording `None -- mature`.

## 7. Sources

- Issue [#497](https://github.com/wildcat-finance/skills/issues/497), current
  review dated 2026-08-26, and the Wave 0 acceptance text retained there.
- Start commit `9e25b995bf4be01919559596d2af2ff65ba896a4`.
- `plugins/hexaemeron/skills/protasis/SKILL.md`, SHA-256
  `0f83579ead5fe6a7a472e076fa8bbdf4df16b170bf7ca5852833212df07702cf`;
  `EVOLUTION.md`, SHA-256
  `cb9d334817d343b2a1b3e4228fbb51979e196ee3715caec9bcf4eb5651ccdf89`;
  `scripts/protasis.py`, SHA-256
  `9e7f90f52abd2626f260665635f8653a30478f7c25a40e2b371a5c637aeaad4d`.
- `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`, SHA-256
  `c6542ed717a31ddfc187417a540c7160c08be1fb60877497c6a706393cf23f14`.
- `plugins/hexaemeron/tests/test_protasis_checker.py`, SHA-256
  `5c2d49f6e2e14dfdaa396f5b63901008d3b4fda13deb3188623aa60c992b92bf`;
  `plugins/hexaemeron/tests/test_hexctl.py`, SHA-256
  `4799ef3fa57f958a67ac74716f06ecc6250586d7f11c1d2504ab3136cecc4dbe`;
  and `plugins/hexaemeron/tests/fixtures/protasis/`.
- `plugins/hexaemeron/skills/VERSIONING.md`, `PROMISE_MACHINE.md`,
  `plugins/hexaemeron/AGENTS.md`, and `.horos/boundary.json`.
- [CommonMark 0.31.2](https://spec.commonmark.org/0.31.2/), sections 4.2,
  4.4, and 4.5, read 2026-08-29.
- GitHub code search `"### Amendment --" org:wildcat-finance`, run through
  `gh search code` on 2026-08-29; every result belonged to
  `wildcat-finance/skills`.
- `docs/protasis-amendment-contract-study.md`,
  `docs/protasis-risk-register-block-check-study.md`, and
  `docs/fiat-receipted-study-amendments-study.md`.
- The four audit sources and verified synopsis mappings listed in item 2.
- Surviving pull heads for #603, #604, and #708, issue #369 commit
  `bdff15f39e7eab1d6a05d080674ae86b3af91687`, and integration reconciliation
  commit `3d247758a38a05cee36184f3488bfac0932f2c76`.
- [ephoros](../plugins/hexaemeron/skills/ephoros/SKILL.md),
  [phylax](../plugins/hexaemeron/skills/phylax/SKILL.md),
  [metron](../plugins/hexaemeron/skills/metron/SKILL.md),
  [elenchus](../plugins/hexaemeron/skills/elenchus/SKILL.md), and
  [hypomnema](../plugins/hexaemeron/skills/hypomnema/SKILL.md).

## 8. Signals, and the questions behind them

No unattended signal is added. This is a terminal-invoked lint and an
interactive controller transition. The existing finding line, exit status,
bounded controller refusal, state, and ledger answer the useful questions:

1. Did direct study validation see a malformed amendment? S008 names the path,
   source line, and fixed structural fault.
2. Was a malformed amendment stopped before mutation? `amend study` reports
   the bounded Protasis rejection, and state, ledger, and canonical study stay
   unchanged.
3. Which controller-only condition failed after shape acceptance? Existing
   prefix, touched-step, verdict, phase, recovery, and drift diagnostics retain
   their own names.
4. Did the refactor change runbook behavior? The P005 corpus and complete
   Hexaemeron suite answer that question.

The implementation and focused-test step emits those operator-visible
answers. [Ephoros](../plugins/hexaemeron/skills/ephoros/SKILL.md) remains the
signal authority; no metric, trace, alert, or new background log is justified.

## 9. Boundaries, per capability

The direct checker accepts a caller-named path and untrusted Markdown bytes.
The existing regular-file check, 2 MiB cap, UTF-8 replacement behavior,
bounded item/step counts, shared fence state, fixed finding fields, and
value-free diagnostics close the admitted mechanical boundary. S008 adds no
filesystem traversal, subprocess, socket, dependency, or secret handling.

Fiat accepts a scoped candidate path, captures bounded bytes, writes a private
temporary for Protasis, and invokes a fixed sibling checker with
`sys.executable`, argv only, bounded output, and a timeout. After zero exit, it
may derive only the exact-prefix and state-bound receipt facts. The existing
lock, pending marker, atomic replacement, ledger chain, and recovery path close
the durable-write boundary.

[Phylax](../plugins/hexaemeron/skills/phylax/SKILL.md) owns these boundary
rules. The implementation must preserve its current clean scan and must not
turn controlled Markdown into a shell argument, import path, or echoed
unbounded diagnostic.

## 10. The budget, or its absence

There is no performance claim and therefore no Metron comparison budget. The
common scanner is a bounded linear walk over an already capped document; the
controller already pays for one Protasis subprocess. The design removes shape
work from the controller rather than adding another checker invocation.

The repeatable functional commands are the focused unit suite and complete
Hexaemeron suite in item 1. Any optimization, cache, or latency claim requires
a study amendment before implementation. [Metron](../plugins/hexaemeron/skills/metron/SKILL.md)
remains the measurement authority.

## 11. The fail-closed posture

The known gap is captured as parent-red guards before the fix: the current
`protasis.py --study` returns zero for a complete baseline study appended with
`### Amendment` lacking a date, and for each variant missing one of the four
fields. The fixed tree makes each specimen report S008. A complete appended
amendment and the same baseline with no amendment stay green.

Controller guards must show that malformed shape reaches the Protasis refusal
before any pending record, artefact replacement, state update, or ledger event.
Existing prefix, fence, verdict, interruption, recovery, and post-amendment
drift tests stay green. Removing the shared scanner call or restoring a
controller shape verdict must make a named regression fail.

Any focused, complete-suite, Promise Machine, frontier, portable-copy,
Imprimatur, Phylax, Hypomnema, or selected-check failure stops the step. Work a
failure under [Elenchus](../plugins/hexaemeron/skills/elenchus/SKILL.md), keep
the red parent evidence, fix its cause, and rerun the exact guard. Never edit a
fixture or finding expectation merely to make a false clean pass.

## 12. Decisions and their homes

S008 and the one-scanner ownership boundary become part of Protasis's public
mechanical interface. Their contract, boundary, and current-state wording live
in `plugins/hexaemeron/skills/protasis/SKILL.md`; implementation lives in its
`scripts/protasis.py`; red-to-green evidence lives in the focused tests and
fixture studies. Fiat's narrower post-check ownership is stated only where its
controller contract needs it.

The completed frontier and current maturity decision live in
`plugins/hexaemeron/skills/protasis/EVOLUTION.md` as `protasis-v5.9.0`. The
current survey found no further mechanical content shape fixed by Protasis but
left unchecked: study items, risk registers, study amendments, runbook steps,
runbook amendments, and version relations all have one bounded check after
this job. `None -- mature` is therefore the chosen closure unless a later
implementation or audit finding supplies contrary evidence. Reopening after
that point requires the external evidence and epoch entry in `VERSIONING.md`.

The accepted study and runbook are copied to
`docs/protasis-amendment-block-check-study.md` and
`docs/protasis-amendment-block-check-runbook.md`; those root-level homes keep
the source links valid in both the receipted and published copies. Hexaemeron
package manifests and marketplace listings take the smallest valid package
increment on the final integration base; tests pin the one chosen value.
Portable Promise Machine copies and the Horos boundary are regenerated only
through their repository commands. No standalone ADR is needed: this is one
governed skill's already-held ownership and interface decision, whose
established home is its ledger and canonical skill.
[Hypomnema](../plugins/hexaemeron/skills/hypomnema/SKILL.md) remains the
record-placement authority.
