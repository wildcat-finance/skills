# study: schema, timestamp, and synopsis for fiat audit records

assuming, unless corrected:

| id | assumption | evidence and consequence |
| --- | --- | --- |
| A1 | the starting point is `main` at `ced4e6f439021b7509833ed5da66348c86d22f01`, and issue 429 is the complete authority for this generation run | `main`, `origin/main`, and the run branch resolved to that commit; the issue is open and names `#327 -> #429 -> #369 -> #453 -> #363` |
| A2 | this is one audit-record-format capability, not three independently shippable modules | the issue requires schema, timestamp, then synopsis in that order; cutting the schema or timestamp makes the synopsis a disposable prose scraper |
| A3 | every byte present in the six audit logs at the starting commit is immutable evidence | the root log may gain issue-429 rounds after its recorded prefix; no existing heading or entry is rewritten to satisfy the new schema |
| A4 | `fiat-audit-round/v1` governs only entries receipted after this change | legacy entries remain readable and are reported as legacy; missing legacy fields are not inferred from prose |
| A5 | Fiat state stays version 1 | new audit-round leaves are additive; legacy state and ledger rounds may still omit them, matching issue 327's compatibility rule |
| A6 | the heading timestamp is when the round is recorded, not when review began or how long it ran | the canonical form is UTC `YYYY-MM-DDTHH:MM:SSZ`, with no fractional seconds; duration is outside this record |
| A7 | "under 15%" means physical synopsis lines are strictly fewer than 15% of physical source lines | the check uses integer arithmetic, `synopsis_lines * 100 < audit_lines * 15`, so no float or rounding choice can change the verdict |
| A8 | a `Leads not pursued` line means every physical source line containing that exact phrase, occurrence for occurrence | the generator also carries the remaining lead section so a wrapped reason is not cut off |
| A9 | the six current `**/audit/AUDIT.md` paths are the release set | discovery is deterministic and currently returns exactly six; adding a seventh audit log makes the currency test name its missing sibling synopsis |
| A10 | no dependency, CI, Solidity, Protasis, Sapheneia, Horos, or downstream issue change is authorised | the implementation is Python 3.12 standard library, existing unittest discovery, Fiat-owned contracts, and derived Markdown only |
| A11 | the active v5.12.1 controller cannot prove a v5.13.1 self-change while it governs this run | the checked-in new controller must prove the new receipt in a disposable run; this run must not claim its older controller enforced a rule it cannot contain |
| A12 | `/Users/kethcode/.local/bin/python3` is the repository Python for this run | it is Python 3.12.13; the run-worktree shell otherwise resolves `/usr/bin/python3` 3.9.6 |

these assumptions are grounded in the issue, current tree, prior delivery, and
live repository state. proceed on them unless corrected.

## 1. problem statement

Fiat's audit receipt records a finding count, lint exits, an optional fixes
commit, and issue 327's exact Elenchus declaration. It does not check the
Markdown entry that later readers trust. The audit-loop reference requires a
date heading, a findings table, and a leads line by convention, while coverage
and negative space remain optional prose. The six logs are also expensive to
read as one body.

build one versioned audit-record format for Wardens and make the receipt check
the final appended entry before state or ledger mutation. A new record states
all study risk ids as `reviewed` or `not-applicable`, says what was not checked,
carries the canonical findings table and leads field, records issue 327's exact
verdict or `null`, and uses a second-precision UTC heading. Derive a deterministic
`AUDIT_SYNOPSIS.md` beside every log without changing a source byte.

a working prototype has two proof paths:

1. a disposable v5.13.1 controller run refuses each missing or inconsistent
   field without state or ledger drift, then receipts a complete round and
   preserves `guarded`, `unguarded`, `passed`, and `inconclusive` exactly;
2. the repository synopsis check regenerates all six views in memory, matches
   the committed bytes, proves the strict line budget, and proves every leads
   occurrence survived.

the release is done when these commands exit 0 from the repository root:

```bash
/Users/kethcode/.local/bin/python3 \
  plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .
/Users/kethcode/.local/bin/python3 -m unittest \
  plugins.hexaemeron.tests.test_hexctl tests.test_audit_synopsis_currency
/Users/kethcode/.local/bin/python3 -m unittest discover -s tests
npx --yes --package=node@26.6.0 --call \
  '/Users/kethcode/.local/bin/python3 plugins/hexaemeron/tests/run_tests.py'
/Users/kethcode/.local/bin/python3 scripts/promise_machine.py check
```

the final proof also runs both Protasis modes over the committed study and
runbook, the three active-plugin lints over their declared scopes, the prose
gates, `git diff --check`, and the prefix-preservation test described below.

## 2. prior art and current state

### current controller and contract

`plugins/hexaemeron/skills/fiat/scripts/hexctl.py` v5.12.1 owns
`cmd_audit_round`. It requires the `security_suite` receipt, finding count,
three lint exits for non-Solidity rounds, and a paired fixes commit plus one of
`guarded`, `unguarded`, `passed`, or `inconclusive`. It records
`elenchus_verdict: null` for a new no-fix round and lets legacy rounds omit the
key. It stores `log` but never reads the path or its bytes. `now()` already
returns an ISO-8601 UTC value for state and ledger receipts.

`plugins/hexaemeron/skills/fiat/references/audit-loop.md` tells Warden to append
a dated heading, one canonical five-column findings table, and a
`Leads not pursued` line. `plugins/hexaemeron/agents/warden.md` owns the append
and signed audit-fix commit; the orchestrator owns the controller receipt.
Keeping that division avoids a controller write landing after Warden's signed
commit.

`tests/test_boundary_currency.py` is the closest currency precedent: render a
fresh deterministic artefact, compare committed meaning, and mutation-prove
the guard in both directions. The synopsis needs byte comparison, not Horos's
entry-set comparison. Python's `hashlib`, `datetime`, `pathlib`, `tempfile`,
and `os.replace` cover the implementation without a dependency. The timestamp
shape is the RFC 3339 UTC form with a literal `Z`.

### current audit-record census

all six logs were decoded as UTF-8 and exhaustively inventoried before the
options below were drawn. The inventory walked every H2 record, every canonical
`id/severity/file/finding/status` table, and every physical line containing
`Leads not pursued`. Its canonical JSON census hashes to
`c710c1d924497f3fb6aad9d1ba4e8b9eb6238555845fc580e6b695dfa0ab109d`:
420 H2 records, 297 canonical findings tables, and 373 leads occurrences.

| log | bytes | lines | H2 records | findings tables | leads occurrences | SHA-256 | projected synopsis lines |
| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| `audit/AUDIT.md` | 580,893 | 9,392 | 343 | 232 | 298 | `96583f59dea6da5363bf83feadc6686d8c4897adc282f4d33de7b4aa0a5d52e9` | 344, 3.66% |
| `plugins/ariadne/audit/AUDIT.md` | 32,253 | 466 | 21 | 16 | 21 | `d8d13eb238b6e270fb9f89ec11fea797b4a3aa27025b5a62a7f36ac2642617af` | 22, 4.72% |
| `plugins/hexaemeron/audit/AUDIT.md` | 5,621 | 71 | 2 | 2 | 2 | `8acff29ed567c97902941a85d72e41171c10850de6aa898b5d50564248eac28f` | 3, 4.23% |
| `plugins/pandects/audit/AUDIT.md` | 45,906 | 696 | 17 | 11 | 16 | `66908cb68630f3c3cbea432aec6cf6efc305bcab85ccf5fadb278c535635edf9` | 18, 2.59% |
| `plugins/probitas/audit/AUDIT.md` | 52,540 | 842 | 24 | 23 | 23 | `ba532815ae3abe13be3494b96044bf5d874cfb23842249d8e1cd867186e486c9` | 25, 2.97% |
| `plugins/tabularium/audit/AUDIT.md` | 14,400 | 262 | 13 | 13 | 13 | `1de310b5df5784d7e623ea9dbda83ae77e02cb1798b3aeedffc5d0c715f8e3a7` | 14, 5.34% |

the issue-time 5,978-line and 299-entry root measurements are stale. The six
logs now total 731,613 bytes and 11,729 lines. Of 420 H2 records, 417 have a
date-only ISO heading, two use prose dates, and one is a later disposition
section. None has the new timestamp shape. Legacy syntax also includes zero
findings as prose, H3 leads headings, inline leads labels, wrapped lead reasons,
risk tables with several header spellings, and Probitas sections that are audit
evidence but are not named `round`. A legacy parser must report that variety,
not retrofit one story onto it.

the latest issue-327 rounds are decisive prior evidence. They keep all four
Elenchus values distinct, record explicit null and a missing legacy key in the
proof, and repeatedly carry issues 429, 369, 453, and 363 forward. Their risk
coverage tables contain values that a synopsis limited to findings and leads
would lose, so risk tables are part of legacy extraction.

every unrelated accepted lead in all six logs remains exactly where its round
left it. This run neither closes nor reopens Ariadne, Pandects, Probitas,
Tabularium, Horos, Phylax, or old Hexaemeron findings; their format diversity is
input evidence only. The two known H003 alerts over historical root-log text
also remain unedited, as the worktree delivery recorded.

### merged pull requests read before choosing

| surface | last two applicable merged pull requests | carried-forward treatment here |
| --- | --- | --- |
| controller, Fiat skill, ledger, and tests | [#493](https://github.com/wildcat-finance/skills/pull/493), [#477](https://github.com/wildcat-finance/skills/pull/477) | preserve all four verdicts and legacy null/missing behavior; leave #453 evidence binding and #363 identity work open; do not disturb the dedicated-worktree contract |
| audit-loop format | [#493](https://github.com/wildcat-finance/skills/pull/493), [#206](https://github.com/wildcat-finance/skills/pull/206) | extend the checked-and-recorded field mechanism without claiming report-byte attestation; keep lint exits and clean-round composition unchanged |
| Warden packet and append owner | [#493](https://github.com/wildcat-finance/skills/pull/493), [#365](https://github.com/wildcat-finance/skills/pull/365) | keep the source-bound runbook/risk packet and role identity; #363 remains the owner of visible delegated-task identity |
| root audit record | [#493](https://github.com/wildcat-finance/skills/pull/493), [#486](https://github.com/wildcat-finance/skills/pull/486) | issue-327 dependencies carry forward; Phylax P008 exclusions are unrelated and stay open as recorded |
| currency-test pattern | [#267](https://github.com/wildcat-finance/skills/pull/267) | this file has only one merged introduction; reuse deterministic regeneration and mutation proof, but compare complete synopsis bytes rather than hard-boundary entry sets |
| release and marketplace surfaces | [#493](https://github.com/wildcat-finance/skills/pull/493), [#469](https://github.com/wildcat-finance/skills/pull/469), and marketplace-specific [#445](https://github.com/wildcat-finance/skills/pull/445) | keep Apache licensing and three package-version surfaces aligned; leave #363's held frontier revision and digest unchanged |

closed issues [#368](https://github.com/wildcat-finance/skills/issues/368) and
[#428](https://github.com/wildcat-finance/skills/issues/428) are folded here.
[#369](https://github.com/wildcat-finance/skills/issues/369) stays open and owns
changing Protasis's read source. [#453](https://github.com/wildcat-finance/skills/issues/453)
stays open and owns report-byte binding plus the production `guarded` gate.
[#363](https://github.com/wildcat-finance/skills/issues/363) stays open and owns
delegation identity. None is silently broadened into this packet.

## 3. constraints and non-goals

the entry ref is `ced4e6f439021b7509833ed5da66348c86d22f01` on
`main`. Fiat is `v5.12.1`; this ordinary generation should become
`fiat-v5.13.1` while retaining frontier revision `state-shape-validation`,
digest `e413d6041edb34b3807a54019489605814a591f60547755f8f66f01830f643aa`,
and the held issue-363 target byte for byte. Hexaemeron's package patch moves
from `1.5.5` to the next aligned release surface. The state-container version
does not move.

included:

- strict future-entry schema and receipt validation on the configured log;
- UTC record timestamps and additive receipt evidence;
- a bounded standard-library synopsis parser, renderer, write/check CLI, six
  committed synopses, currency/prefix/legacy tests, governed prose, and release
  surfaces;
- a disposable checked-in-controller demonstration that proves the new rule
  without attributing it to this run's older controller.

excluded:

- changing what a Warden audits, security severity policy, maximum rounds,
  Elenchus classification, or whether a non-`guarded` verdict blocks;
- rewriting, reordering, trimming, or normalising any existing audit entry;
- making Protasis read a synopsis (#369), injecting known guards (#453), or
  changing delegated identity (#363);
- adding JSONL as a second source of truth, classifying `AUDIT.md` or a synopsis
  behind Horos, adding `.gitattributes`, changing Horos categories, touching CI,
  or adding a dependency;
- a latency claim, audit-log retention policy, log rotation, or migration of a
  third-party repository with no synopsis.

always: run both repository suites before a Fiat-created commit; run the
synopsis check and prefix proof after any audit-log change; run Imprimatur over
every shipped document; record a measurement before any performance claim.

ask first: a dependency, CI edit, public schema rename, state-version change,
`.gitattributes` rule, log-path widening, or a write outside a log's sibling
synopsis.

never: edit a receipted legacy byte, infer a missing legacy field, commit a
credential, use a shell for parsing or generation, follow a supplied symlink,
delete a failing test, or call the old controller's acceptance proof for the
new one.

## 4. design options

### option A -- validate the Warden-appended Markdown and derive one canonical view

chosen. Warden appends and signs the log as it does now, runs the synopsis
writer, then the controller reads the configured log, validates the last H2
entry as `fiat-audit-round/v1`, checks the sibling synopsis bytes, and only then
records state and ledger evidence. No new content-bearing CLI flags are needed.

the strict entry is:

```markdown
## <state topic>, step <n>, round <r> -- 2026-08-23T02:17:46Z

Audit schema: fiat-audit-round/v1

Covered: schema-bypass=reviewed; frontier-drift=not-applicable

Not checked: none

Elenchus verdict: null

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

Leads not pursued: none
```

`Covered` contains every study risk id exactly once and accepts only
`reviewed` or `not-applicable`; no unknown id is accepted. `Not checked` and
`Leads not pursued` each require a non-empty same-line value, where `none` is
an explicit value. The findings table shape stays unchanged and its data-row
count must equal `--findings`; zero uses the exact placeholder above.
`Elenchus verdict` must equal the CLI declaration or `null`. The heading must
match the state topic, step and next round and carry a calendar-valid UTC
second. The receipt stores the schema, heading timestamp, entry SHA-256, log
end offset, synopsis SHA-256, and existing verdict beside its current fields.
Legacy stored rounds may omit all new leaves.

the synopsis has one metadata line and one physical line per H2 source record.
The metadata carries `fiat-audit-synopsis/v1`, repository-relative source path,
source SHA-256, and H2 count; it carries no generation clock. Each record line
keeps, in source order, the exact H2 heading, strict field labels, canonical
findings table, any legacy risk-id table, every physical leads occurrence, and
the remaining leads section. Source lines join with a fixed `<br>` token, so
each retained physical line's exact text survives without spending another
synopsis line. Legacy omissions are labelled as omissions, never filled from
nearby prose.

this gives `synopsis_lines = H2_records + 1`, the projected figures in item 2,
and exact regeneration. It trades away pleasant source-like line wrapping:
some synopsis records are long. That is preferable to dropping finding or
lead evidence, and Horos treats long-line geometry as advisory rather than a
hard read exclusion. The synopsis header deliberately contains none of
Horos's generated markers; the current six must remain absent from the hard
boundary so #369 can read them.

### option B -- let `audit-round` append and timestamp a body file

the controller would accept `--entry <path>`, validate a heading-free body,
stamp it with its own `now()`, append the log, rewrite the synopsis, then write
state and ledger. This gives the controller sole formatting authority and one
clock. It loses because the controller would dirty tracked files after
Warden's signed fixes commit and would need a recoverable transaction across
log, synopsis, state, and ledger. That is a larger state-machine change than
the format needs.

### option C -- carry each field as CLI or JSON sidecar data

explicit flags mirror the existing lint exits, while a JSON sidecar avoids
multiline argv. Both are easy to parse. Flags put audit prose in the process
table and shell history; a sidecar becomes a second durable representation
whose agreement with Markdown needs another gate. Both trade one checked
record for two sources of truth.

### option D -- normalise all legacy logs first

rewriting old headings and missing fields would make generation trivial. It
destroys the append-only evidence the feature is supposed to make readable,
and any filled negative space would be fiction. It is forbidden.

## 5. risk register seed

```risk-register
legacy-prefix-integrity | the six append-only AUDIT.md byte prefixes at ced4e6f | the permanent prefix test proves every starting byte and order remain unchanged while later rounds only append
schema-bypass | the final H2 entry read by audit-round before its state transition | every required field is unique and well formed, findings agree with the receipt, and refusal leaves state and ledger bytes unchanged
risk-id-drift | the receipted study risk register and the Covered field | every source id appears exactly once as reviewed or not-applicable and no unknown or duplicate id passes
timestamp-ambiguity | the new audit heading and its stored receipt leaf | only calendar-valid YYYY-MM-DDTHH:MM:SSZ UTC values pass and existing date-only headings remain legacy
verdict-loss | issue 327 state, log field, and synopsis extraction | guarded, unguarded, passed, inconclusive, null, and legacy absence stay distinct without inventing a fifth verdict
legacy-parser-confusion | heterogeneous H2 sections, tables, headings, and wrapped leads across six logs | extraction is fence-agnostic but source-ordered, bounded, occurrence-preserving, and labels missing legacy fields instead of inferring them
synopsis-drift | each AUDIT.md and sibling AUDIT_SYNOPSIS.md | byte comparison fails after any source mutation without regeneration and passes only on exact fresh bytes
lead-omission | every physical source line containing Leads not pursued | multiset equality proves every occurrence and its lead-section continuation survives the synopsis
partial-write | replacement of a committed synopsis during regeneration | a same-directory temporary file is flushed and atomically replaced so interruption leaves the old or complete new view and currency check names staleness
path-boundary | repository root, discovered logs, and sibling output paths | regular UTF-8 files stay inside the real repository, symlinks and oversized inputs are refused, and no shell or network is used
horos-self-defeat | the derived synopsis as the future Protasis read surface | no hard generated marker or attribute is added and the Horos hard boundary remains free of all six synopsis paths
self-hosting-overclaim | this run's v5.12.1 controller versus the changed v5.13.1 source | a disposable run proves the checked-in controller while the active ledger records only evidence its actual controller can receipt
frontier-drift | Fiat and Hexaemeron evolution and package surfaces | one generation row and aligned package patch retain the state-shape revision digest and issue-363 held target byte for byte
```

the permanent prefix fixture records the six byte lengths and SHA-256 values
from item 2. For each source, it hashes exactly the first recorded byte length;
shortening, inserting, editing, or reordering old content fails, while a later
append remains possible. The generator is read-only over `AUDIT.md` and writes
only the sibling synopsis through atomic replacement.

## 6. glossary seeds

| term | meaning |
| --- | --- |
| strict entry | a new H2 audit record carrying `Audit schema: fiat-audit-round/v1` and every checked field |
| legacy entry | an H2 section written before the schema; it is extracted but never repaired or inferred |
| covered set | the exact receipted risk-register ids, each mapped once to `reviewed` or `not-applicable` |
| negative space | the explicit `Not checked` value for work the round did not establish |
| record timestamp | the UTC second at which Warden records the round, not its start or duration |
| source prefix | the exact audit-log bytes present at `ced4e6f`, protected from later edits |
| synopsis | a deterministic derived Markdown view with one physical line per H2 audit record |
| currency | byte identity between a committed synopsis and fresh rendering of its source log |
| leads occurrence | one physical source line containing the exact text `Leads not pursued`, counted with duplicates |

## 7. sources and evidence inventory

| source | version or digest | use |
| --- | --- | --- |
| [issue 429](https://github.com/wildcat-finance/skills/issues/429) | live open body read 2026-08-23 UTC | scope, acceptance, folded issues, dependency chain |
| [issue 327](https://github.com/wildcat-finance/skills/issues/327) and [PR 493](https://github.com/wildcat-finance/skills/pull/493) | merged at `ced4e6f` | exact four-value verdict, null/missing compatibility, downstream boundaries |
| [issues 368](https://github.com/wildcat-finance/skills/issues/368) and [428](https://github.com/wildcat-finance/skills/issues/428) | closed into 429 | synopsis and timestamp rationale |
| [issues 369](https://github.com/wildcat-finance/skills/issues/369), [453](https://github.com/wildcat-finance/skills/issues/453), and [363](https://github.com/wildcat-finance/skills/issues/363) | open | explicit exclusions and consumers |
| `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` | `01efd29fcc0b1198aa62989291c1dbe4713d7c26cccbba40a1fbe4b210884870` | current receipt, clock, bounded paths, state and ledger behavior |
| `plugins/hexaemeron/tests/test_hexctl.py` | `fb7873bc4c899736e10c7da1cd6456285239757175c7de14284542e16bbaa886` | refusal, drift, verdict and legacy fixtures |
| `plugins/hexaemeron/tests/test_fiat_skill.py` | `ed8f3b00ddb2c50c87862cb02743f9a0f3b2c7ccd945dadaa04139d697eec131` | prose/runtime contract agreement |
| `plugins/hexaemeron/skills/fiat/references/audit-loop.md` | `499841279b902a0f5336644a1e25bca3575198911edbc5e152889a42dd41e7fe` | current log shape and Warden sequence |
| `plugins/hexaemeron/agents/warden.md` | `65d6b0ae1538f3454c40bc792d3d2d13f06fdd5664a2f8cd39eb4e317920c4cd` | log writer and handoff boundary |
| `plugins/hexaemeron/skills/fiat/SKILL.md` | `30516188cf3970cb5c9851dacc745ca413d1d5105e14c7ac15962224cc4bdc13` | receipt table and Promise Machine contract |
| `plugins/hexaemeron/skills/fiat/EVOLUTION.md` | `0806cdf018296e8c899be65381924d383e1e993e7b4beda070ad41f441fc2cff` | v5.12.1 version, held frontier and generation policy |
| `tests/test_boundary_currency.py` | `4932d590dcd2b65cf44eb8c46bf323d4343ca79cf0b767be1b4eb64cb78804b6` | deterministic currency and mutation-proof precedent |
| `.horos/boundary.json` | `4462dd0f4a10f918d3956a4a2c67682fc824093ff7f7eb70d9b4526006d1f594` | reading boundary consulted before broad read; no target audit path is hard-classified |
| six audit logs | per-file digests and census in item 2 | all legacy records, findings, dispositions and leads |
| `plugins/hexaemeron/docs/elenchus-audit-round-verdict/{study,runbook}.md` | `425152f8...` and `a98c67bd...` | issue-327 design, command/report owner and compatibility proof |
| RFC 3339 | `date-time`, UTC `Z`, whole seconds | canonical new heading timestamp identifier |

source reads were local repository bytes and GitHub issue/PR API responses. No
external package, generated build tree, binary boundary entry, or unpinned web
summary informed the design.

## 8. signals and the questions behind them

[Ephoros](../../skills/ephoros/SKILL.md) owns signal shape. This is a bounded
CLI and test path, not an unattended service, so it adds no metric, trace, alert,
or pager surface. It must answer four operator questions through deterministic
receipts and diagnostics:

| question | signal and owning step |
| --- | --- |
| which exact audit entry did the controller accept? | the audit-round state and ledger event carry schema, record timestamp, entry SHA-256, log end offset, source path, synopsis SHA-256, and existing verdict; the schema step emits them |
| why did a receipt refuse? | a stable field-specific diagnostic names the missing, duplicate, malformed, mismatched, stale, escaping, or oversized input before mutation; the schema step tests each class |
| which synopsis is stale and by how much? | `audit_synopsis.py --check .` names the source and synopsis, expected and actual digest, and line-budget result; the synopsis step owns it |
| did legacy extraction drop a lead or issue-327 value? | focused tests report per-log occurrence counts and the exact missing line or verdict; the final demonstration owns the six-log result |

## 9. boundaries per capability

[Phylax](../../skills/phylax/SKILL.md) owns the boundary controls. The new
capabilities open these concrete lines:

| capability | boundary and thing worth protecting | closing control |
| --- | --- | --- |
| strict receipt | Warden-authored Markdown crosses into controller state and ledger; receipt integrity and old evidence are at stake | configured contained path only, bounded regular UTF-8 read, exact last-H2 parser, risk-id parity, count/verdict/timestamp checks, synopsis currency, mutation only after every check |
| legacy extraction | heterogeneous authored Markdown crosses into a derived read view; omissions can erase accepted risk | no semantic inference, exact source order, canonical table/risk-table recognition, occurrence-preserving leads scan, explicit legacy omissions, fixture coverage over all observed shapes |
| synopsis write | derived bytes replace a tracked sibling; interruption can leave a stale or partial view | deterministic in-memory render, same-directory mode-preserving temporary, flush, `os.replace`, cleanup, exact post-write read, no source write |
| repository discovery | a caller-supplied root determines what is read and written | real repository containment, fixed basename pair, sorted tracked audit paths, no symlink following, file/entry/line caps, no network or shell |
| append-only proof | future commits could edit history while keeping a current synopsis | permanent baseline length/digest assertions over all six prefixes plus source-digest header and currency guard |
| Horos interaction | a derived file could classify itself out of the future read path | no hard marker or attribute, root boundary check, explicit test that none of six synopsis paths enters hard entries |

the parser must cap each log before reading, cap H2 records and physical line
size, and report only path, rule, counts, and digests on failure. It never prints
source content, which may contain a credential someone already mishandled in an
old record. The implementation should choose caps above the current 580,893-byte
largest log and record them beside tests; 16 MiB, 10,000 H2 entries, and 1 MiB
per physical line are the proposed bounds.

## 10. budget or its absence

[Metron](../../skills/metron/SKILL.md) owns performance measurements. There is
no latency or memory-improvement claim, so no runtime baseline is warranted.
There is one product budget: each committed synopsis has strictly fewer than
15 physical lines per 100 source lines. Currency also requires byte identity,
not merely equal fields.

the exact budget command is:

```bash
/Users/kethcode/.local/bin/python3 \
  plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .
```

it prints, for each of six paths, source lines, synopsis lines, integer ratio
verdict, source SHA-256, fresh synopsis SHA-256, and committed-byte verdict.
The study's one-line-per-H2 construction projects 2.59% to 5.34% across the six
current logs. Input caps are safety bounds, not a performance assertion.

## 11. fail-closed posture and recovery

[Elenchus](../../skills/elenchus/SKILL.md) owns failure triage and guard proof.
The controller stops before state and ledger mutation on an absent log or
synopsis, non-regular or escaping path, invalid UTF-8, unsupported size,
missing or duplicate field, risk-id mismatch, malformed/non-UTC timestamp,
finding-count disagreement, verdict disagreement, stale synopsis, or changed
protected prefix in the repository test.

recovery is bounded:

| failure | state after refusal | recovery |
| --- | --- | --- |
| unreceipted strict tail is malformed | no new controller receipt; candidate log commit remains reviewable | correct only the unreceipted tail, rerun schema validation and synopsis generation, then reattempt the same round |
| log is valid but synopsis is stale or absent | no new controller receipt; source log is untouched | run the writer for that log, inspect the bounded diff, then rerun `--check` and the receipt |
| synopsis replacement is interrupted | old complete synopsis or complete new synopsis remains; currency may be stale | remove only a named temporary owned by the failed invocation if present, rerun writer and check |
| legacy parser meets an unsupported shape | generator refuses with path, H2 index, and rule; no output is replaced | add a minimal fixture reproducing that shape, fail it on the old parser, extend the parser without reinterpreting earlier shapes, then regenerate |
| protected prefix differs | acceptance is blocked; generation cannot repair evidence | restore exact bytes from `ced4e6f`, append any explanation as a new entry, and rerun the prefix proof |
| checked-in-controller demo differs from active controller | active run remains governed by v5.12.1 and no new-rule claim is made | run the tracked v5.13.1 controller in a disposable repository and bind its exact source digest and output in the proof |

each observed defect starts with a focused test that fails against the unfixed
parent and passes after the cause is fixed. A stale-synopsis mutation, each
missing schema field, duplicate/unknown risk ids, each verdict value, timestamp
variants, legacy omission, leads duplication, atomic-write interruption, and
prefix mutation all need red-before-fix guards. Full suites close the step.

## 12. decisions and their homes

[Hypomnema](../../skills/hypomnema/SKILL.md) owns record placement. The durable
format, timestamp, compatibility, and one-line synopsis choices are expensive
to reverse but belong to one governed skill. Their standing record is one Fiat
generation row in `plugins/hexaemeron/skills/fiat/EVOLUTION.md`, linked to the
committed study and proof. A second repository ADR would duplicate that home.

the executable and reader-facing homes are:

| decision or contract | canonical home |
| --- | --- |
| strict round schema, heading, receipt sequence, and recovery | `plugins/hexaemeron/skills/fiat/references/audit-loop.md` with one complete example |
| Warden's append/generate/handoff duty | `plugins/hexaemeron/agents/warden.md` |
| controller validation and stored receipt evidence | `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` and Fiat's existing Promise in `SKILL.md` |
| synopsis schema and CLI | `plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py`, documented by Fiat's runtime contract and plugin README |
| legacy and append-only evidence | committed study, prefix/currency tests, six source logs, and six sibling synopses |
| version and rejected alternatives | Fiat `EVOLUTION.md` generation row; package manifests and marketplace entries only propagate the Hexaemeron patch |

no Sapheneia, Horos, Protasis, Elenchus, or downstream ledger row moves. The
field list adopts Sapheneia's separation of observed state and negative space;
it does not activate or widen that session-shaping skill.

## open uncertainty and falsifiers

no unresolved question changes the chosen construction or build order. Three
facts remain for implementation to establish rather than assume:

| claim | what would falsify it | required response |
| --- | --- | --- |
| one line per H2 stays below 15% for every current log | any release log reports `entries + 1` at or above its integer cap | stop before committing, reduce metadata without dropping evidence, or report the acceptance conflict |
| exact legacy extraction preserves all issue-327 values | a focused fixture or live synopsis lacks any of the four strings present in the source risk/finding/lead material | add the missing structural source class; do not infer the value |
| synopses stay outside Horos's hard boundary | a fresh Horos scan returns any `AUDIT_SYNOPSIS.md` as a hard entry | remove the self-classifying marker or format cause without weakening currency; do not change Horos in this run |

## exact pre-receipt checklist result

study-phase result: **10 of 15 passed, 0 failed, 5 pending the runbook phase**.
The pending checks concern a document that does not exist yet; they do not
authorise implementation.

| # | Protasis check | result | evidence |
| ---: | --- | --- | --- |
| 1 | the study answers all twelve items | pass | headings 1 through 12 are present and non-empty |
| 2 | items 8 through 12 each carry an answer or a stated none with its reason | pass | each names the concrete result and cites its owner |
| 3 | the last two merged pull requests touching the target were read and carried work treated | pass | item 2 maps each mutable surface; the currency precedent has only one merged introduction and says so |
| 4 | every in-scope audit record was read before options | pass | all six logs, 420 records, 297 canonical tables, 373 leads occurrences, census digest recorded before item 4 |
| 5 | no discipline core is restated where a citation belongs | pass | items 8 through 12 cite Ephoros, Phylax, Metron, Elenchus, and Hypomnema and state only this topic's effects |
| 6 | assumptions are on the page and confirmed or corrected | pass | A1-A12 were checked against issue, repository, controller, toolchain, and merged evidence; the study says it proceeds unless corrected |
| 7 | every success criterion names a command, test, or demo | pass | item 1 gives the exact release commands and two demo paths |
| 8 | the chosen design says what it traded away | pass | option A trades source-like wrapping for evidence-preserving one-line records; B-D name their losses |
| 9 | always, ask-first, and never carry concrete entries | pass | item 3 names all three sets |
| 10 | each step carries goal, entry, exit, files, tests, disciplines | pending | runbook not yet derived |
| 11 | every discipline a step names carries a reason | pending | runbook not yet derived |
| 12 | no exit rests on anything but a command | pending | runbook not yet derived |
| 13 | step 1 scaffolds and the last step demonstrates | pending | runbook not yet derived |
| 14 | steps are in dependency order | pending | runbook not yet derived |
| 15 | decomposed modules trace to steps | pass, not applicable | item 2 establishes one capability; schema, timestamp, and synopsis are ordered concerns inside it, not independent modules |

the study is ready to derive a runbook. it establishes the current evidence,
chosen format, compatibility boundary, failure model, and proof commands. it
assumes A1-A12. it does not establish that the parser exists, the current logs
pass a future generator, or the new controller enforces the receipt. the next
action is to derive and mechanically check the discrete runbook without adding
a design decision.

recommended study receipt skill CSV:
`hexaemeron:protasis,hexaemeron:phylax,hexaemeron:elenchus,hexaemeron:hypomnema`.

### Amendment -- 2026-08-23

**What changed.** option A's receipt validator is narrowed from a whole-log
CommonMark/GFM visibility model to one raw appended-record delta. the controller
still reads the configured log once through the existing bounded,
descriptor-relative, no-follow path. it does not decide which old source lines a
Markdown renderer would expose.

the delta start comes from durable evidence already available to the controller,
in this order:

1. if the latest audit round for the same canonical log carries a non-boolean
   integer `log_end_offset` inside the byte cap, that offset is authoritative.
   the current log must be longer than the offset. a findingful round with no
   `fixes_commit` and a clean signed log-only round therefore have the same
   next-boundary semantics as any other receipted round; the validator does not
   require a later verified commit to represent the offset.
2. if no prior round carries that leaf, the controller takes the audit-log blob
   at `last_local_commit(step)`, the locally verified implementation or audit-fix
   commit, as the first-round baseline. the live log must preserve that blob
   byte-for-byte. a Git-proved absent path means a zero-byte baseline; an
   unavailable commit, ambiguous Git result, unsafe path, oversized blob, or
   mismatch refuses before mutation.
3. if a prior same-log receipt carries a malformed or out-of-range offset, or
   names another log, the controller refuses instead of falling back and
   guessing. legacy rounds with missing leaves remain readable by `status`,
   `next`, and `verify`; the verified-blob rule supplies their first strict
   append boundary.

after that boundary, the controller accepts exactly one LF-canonical record.
a non-empty baseline ending in LF takes one leading LF before the record; a
non-empty baseline without LF takes two; an empty baseline takes none. the
record starts with the exact raw ATX line
`## <topic>, step <n>, round <r> -- <timestamp>` and ends at EOF. between
those points it contains, in order, one `Audit schema`, one `Covered`, one
`Not checked`, one `Elenchus verdict`, the exact five-column findings
header and separator, the declared number of physical data rows, and one
`Leads not pursued`, each separated by the documented blank line. there are
no extra headings, prelude, continuation rows, or trailing records. field
values remain opaque non-empty same-line UTF-8. a small linear row scanner
handles five physical cells; no renderer, HTML recogniser, inline parser, or
fence state participates.

the existing checks remain: `fiat-audit-round/v1`; calendar-valid
`YYYY-MM-DDTHH:MM:SSZ`; every study risk id exactly once as `reviewed` or
`not-applicable`; finding count parity and the exact clean placeholder; and
`guarded`, `unguarded`, `passed`, `inconclusive`, or `null` matching
the receipt flags. only the delta is decoded and line-checked. all checks,
including fixes-range verification and lint consistency, finish before state
or ledger mutation. an accepted round keeps the existing schema, log,
timestamp, entry digest, and end-offset leaves.

the six permanent prefix fixtures still prove that every byte present at
`ced4e6f439021b7509833ed5da66348c86d22f01` survives in the repository.
a prior `log_end_offset` identifies where the new bytes begin; it does not
prove that every earlier byte still belongs to a particular signed commit.
the controller likewise checks and records the live entry digest without
attesting that a clean log-only commit contains it. issue 453 still owns that
report-byte and commit binding. issues 369 and 363 remain unchanged.

step 2 must not reuse the removed visibility recogniser. its synopsis is a
derived view, not receipt authority: split the six fixed sources on their raw
ATX record markers, recognise strict fields by the raw line grammar, preserve
legacy material without inference, and retain every physical
`Leads not pursued` occurrence. rounds 1 through 10 stay immutable input and
are never revalidated against the narrower append grammar.

the focused proof matrix adds new-run first strict rounds, a prior strict
same-log offset, a findingful no-fix predecessor, a clean no-fix log-only
round, legacy state with missing leaves, a Git-proved absent baseline log, all
four Elenchus values plus `null`, and this run's round-10 boundary. refusal
cases cover a malformed, mismatched, or past-EOF offset; no safe first-round
blob; a changed first-round prefix; bad separator; extra prelude, field,
heading, row, or trailer; every existing field mismatch; unsafe paths, invalid
UTF-8, caps, and state or ledger drift. the active evidence is concrete:
round 10 records offset 601787, and
`1f82d9f4a879dc46a70ee8cbc1fd00cc755629dc` holds a 601787-byte root log.

**Why.** ten findingful rounds produced 34 findings. the acceptance bugs moved
through raw HTML block types, fences, ASCII versus Unicode whitespace and case,
ATX and Setext headings, GFM row continuation and escaped pipes, inline markup,
and lossy visibility masking. another local patch would claim an unpinned
Markdown implementation one exception at a time. issue 429 requires a checked
record and timestamp; it does not require Fiat to reproduce CommonMark or
GitHub rendering.

the new boundary is falsifiable. if the delta parser consults any byte before
the stored boundary to decide Markdown visibility, accepts more than the one
raw grammar, or mutates state after a failed check, the redesign failed. if a
later requirement says arbitrary CommonMark/GFM source must render every field
as visible nodes, the current step-1 exit is broken and needs a runbook repair
plus either a pinned parser dependency or a different artefact format. this
amendment makes no such rendering claim. no shell, network call, or new runtime
package is needed; the first-round fallback uses Fiat's existing bounded Git
subprocess.

**Steps touched.** Step 1 replaces the nonconvergent visibility code and its
renderer-shaped tests with the raw delta, offset/baseline, compatibility, and
failure-before-mutation guards above; its docs state the narrower evidence
claim. Step 2 keeps its stated outputs and checks, but its extractor stays a
raw, lossy derivation over immutable source rather than becoming another
Markdown authority. Step 3 exercises first-round, prior-offset, legacy,
no-fix, active self-hosting, and refusal paths, then runs the same release
commands and preserves the three downstream exclusions.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit
holds. Step 3: entry holds; exit holds.

### Amendment -- 2026-08-23

**What changed.** the prior amendment's terminal blank line is retained as the
separator before this append-only correction. no product or design requirement
changes. the receipted candidate now ends immediately after the holding
verdicts so its exact tracked copy satisfies `git diff --check`.

**Why.** the first amendment passed Protasis and Imprimatur, but its terminal
blank line made the required raw diff gate exit 2. rewriting receipted bytes is
forbidden. a second amendment is Fiat's supported recovery: it turns that byte
into an internal separator and leaves a diff-clean EOF. the correction fails if
the first amendment digest changes or the final candidate still reports a
whitespace defect.

**Steps touched.** Step 1 copies the newly receipted study into governed docs
and reruns the exact diff gate. Steps 2 and 3 have no semantic change.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit
holds. Step 3: entry holds; exit holds.
