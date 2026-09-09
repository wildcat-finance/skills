# Study: packaged payload byte-cap margin

Issue [#1467](https://github.com/wildcat-finance/skills/issues/1467),
`framework-109`. Run branch `fiat/1467-packaged-payload-byte-cap-margin`, cut
from `main` at `12cbe2e6ed95decd6d9d355740f2dbd052956abe`.

## Assumptions

Proceeding on these unless corrected:

1. The `wildcat-finance/skills` tree at the base SHA above is the subject. The
   published package lives in `wildcat-finance/skills-runtime` and is rebuilt
   from this tree, so a change here reaches installs through that job.
2. `python3` is the interpreter in `.python-version` (`3.13.7`), with stdlib
   `unittest`. No new dependency.
3. The skills CLI is `vercel-labs/skills`, the package `npx skills` resolves.
   ADR-054 names its `download-source.ts`, and the file read here carries the
   constants ADR-054 describes.
4. The character portraits are decorative. Nothing in the packaged runtime
   executes, parses or quotes their bytes. Section 2 gives the evidence. A
   reader who renders a packaged document does see them, and section 3 records
   the operator decision that settles what happens to those references.
5. The two capped install routes are not in use. Nobody has said they are; the
   repository documents one `github` install. Section 3 records that this is
   unknown rather than established.
6. A transform applied inside the generator's byte pipeline is the only place a
   packaged copy may differ from its source. Section 4 establishes what that
   costs against the two byte-equality assertions the repository already ships.

## 1. Problem statement

The generated skills.sh payload measures 24,956,643 bytes against the
26,214,400-byte extract cap the skills CLI applies to two of its six install
routes. That is 95.2020 per cent, leaving 1,257,757 bytes. Three consecutive
deliveries recorded the figure rising and none could act on it, because each
measured it while integrating something else.

**Reproduced here.** `python3 scripts/portable_promise_machine.py package --out
<dir>` at the base SHA writes a manifest reporting `file_count` 1,323 and
`total_bytes` 24,956,643. The issue's headline figures are exact. Its remaining
margin is not: it states 1,258,757 bytes where 26,214,400 − 24,956,643 is
1,257,757, an overstatement of 1,000 bytes.

**Who this is for.** Whoever installs the Promise Machine runtime through a
route that extracts an archive, and the next delivery whose integration would
otherwise meet a red package test with no remedy inside its own scope.

**What a working prototype means here.** The generated package carries a stated
margin under the extract cap, the margin is held by a check that fails before
the cap rather than at it, the class of content kept out of the package is
declared in the manifest with its reason, as the eight existing omission classes
already are, and no reference in a packaged document points at something the
package no longer carries.

**Demo path.** `python3 scripts/portable_promise_machine.py package --out <dir>`
followed by `python3 .hexaemeron/measure_built_margin.py --candidate
omission-class-with-reference-repair`, which must report at least 5,242,880
bytes of headroom; `python3 .hexaemeron/resolve_design.py --candidate
omission-class-with-reference-repair --criterion dangling-image-references`,
which must report 0; and `python3 -m unittest tests.test_skills_sh_package -v`,
which must pass with the byte assertion held against a threshold below the cap.

## 2. Prior art

### The constraint's own record

`tests/test_skills_sh_package.py` holds two constants at lines 116 and 117:

```python
MAX_FILES = 1_400
MAX_BYTES = 25 * 1024 * 1024
```

The comment above them opens (line 70):

> The skills CLI's `SKILLS_EXTRACT_MAX_FILES` and `SKILLS_EXTRACT_MAX_BYTES`
> defaults. They gate its `well-known` and `download` source types, which are
> direct SKILL.md and archive URLs; the `github` type this repository installs
> through never consults them. Held anyway so the package stays installable by
> every route the CLI offers. See ADR-054.

Its final paragraph is the filing this run answers:

> The byte cap is now the live constraint rather than the predicted one. The
> payload measures 24,956,643 bytes, 95.2% of the 25 MiB the CLI allows, against
> 91.5% one paragraph above and 88.3% the paragraph before that. It cannot be
> raised here. Filed as framework-109.

The reasoning the comment repeats at each file-cap raise is:

> the pressure is repository-wide, no per-plugin trim closes it, and shipped
> package content is not trimmed to hold a file count.

**The file cap moved four times, not three.** The issue says three, at 1,000,
1,100 and 1,300. Measured from the history of that file, `MAX_FILES` went
1,000 → 1,100 in [#1038](https://github.com/wildcat-finance/skills/pull/1038)
(merged 2026-08-31), → 1,200 in
[#1094](https://github.com/wildcat-finance/skills/pull/1094) (2026-09-01), →
1,300 in [#1330](https://github.com/wildcat-finance/skills/pull/1330)
(2026-09-06), → 1,400 in
[#1468](https://github.com/wildcat-finance/skills/pull/1468) (2026-09-07). The
issue's table labels are one raise out of step; its byte figures are the
comment's own and are correct.

### The last two merged pull requests that changed the subject

Both were read.

- **#1468**, merged 2026-09-07T22:44:30Z, made the fourth raise. Its carryover
  block names `packaged-payload-byte-cap | filed |` this issue. That is this
  study's mandate and it is carried forward as the whole of this work. Its other
  nine carryover rows concern Anamnesis and are out of scope.
- **#1330**, merged 2026-09-06T08:25:05Z, made the third raise. Its carryover
  block has twelve rows and none of them mentions the payload, the caps or the
  package test. Nothing from it is carried forward here, and nothing from it is
  refused: the delivery recorded the raise in the test comment and filed no
  companion observation.

### Audit records

`python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check
<target-root>` ran from the target root and exited 0, every source reporting
`committed=match`, so a verified synopsis is the admitted reading view. In-scope
sources were selected by grepping every audit record for `MAX_BYTES`,
`MAX_FILES`, `test_skills_sh_package`, `portable_promise_machine`,
`SKILLS_EXTRACT` and `25 MiB`. Four are on the subject; each source was read
directly rather than through its synopsis, because the finding text carries the
measurements this study needs and a synopsis compresses them:

| Source read | What it holds |
| --- | --- |
| `audit/rounds/fiat-395-resumable-ethereum-usdc-interval-collector.md` | S1-R1-07, high, **open**. Carried forward below. |
| `audit/rounds/fiat-940-site-the-generated-skills-sh-payload.md` | S1-R1-01, low, fixed in `e1f13e6a`. A constant naming collision in the same test file; nothing about the caps. |
| `audit/rounds/fiat-949-move-the-skills-sh-payload-to-its-own-reposi.md` | No finding touching either cap. |
| `audit/AUDIT.md` | Two `MAX_BYTES` hits, both a different 4 MiB per-file cap in an unrelated reader. Not this constraint. |

**S1-R1-07 is carried forward by name.** It says the run "cannot produce a tree
that passes this suite without a repository-level decision about the portable
payload or its ceiling", and it has stayed `open and accepted` through eleven
subsequent rounds of that run. Its `Leads not pursued` measured three routes and
rejected each as outside that run's authority: raising `MAX_FILES` "would
misreport installability through a route the CLI actually gates"; omitting
`plugins/*/docs/**` "would drop two documents the canonical SKILL.md links"; and
merging schemas plus omitting one example subtree recovered four files against a
shortfall of about seven. This study is the repository-level decision that
finding asked for. The second of its three routes is the one this study takes
further: an omission class is right, but `plugins/*/docs/**` was the wrong class
to pick, because those documents are linked and the portraits are not.

**Negative evidence.** None of the three raise deliveries' audit rounds
adjudicated the raise. `fiat-dokimasia-frontend-coverage-skill.md`,
`fiat-shoggoth-front-door-derived.md` and
`fiat-1351-anamnesis-2-declared-corpus-scope.md` were each grepped for the cap
constants and the figures 1,100 to 1,400: the Dokimasia hits are a different
`paths.MAX_FILES` inside that plugin, and the other two have none. Every raise
happened during integration, after the audit loop closed. That is what the issue
means by "each measured the payload while integrating something else", and it is
confirmed rather than assumed.

### The decision records

- **ADR-040** made `.agents/skills/promise-machine/` the supported package and
  required it to be **dependency-closed**. That contract is what candidate
  `second-package` breaks.
- **ADR-054**, superseded, records the caps and states plainly that they "do not
  gate the command above", living "in the CLI's `download-source.ts`" and
  applying "only to its `well-known` and `download` source types".
- **ADR-066**, accepted 2026-08-30, moved the generated runtime to
  `wildcat-finance/skills-runtime`, rebuilt hourly by a job in the destination.
  Its rejected alternatives include **"Publish release tarballs"**, refused
  because "the skills CLI's archive path applies 25 MiB and 1,000-file extract
  caps, which the package sits close to". Candidate `other-distribution` in the
  brief's enumeration is that alternative, and it already carries a recorded
  refusal.

### Outside this repository

The skills CLI's `src/download-source.ts` was fetched from `vercel-labs/skills`
and read. Blob `198022f31cda8c547d668c8b01b0c0fc669eddb0`, 9,171 bytes, SHA-256
`ed34a01906ddf5f73526249f351612a520e8cfeeae03f0ff4609e2b82214c09e`, last changed
by `38aebbafaf68e96dd2e8cbc72ffc1e446b514fdb` on 2026-07-29. Section 3 states
what it establishes.

### What the payload is made of

Measured from the manifest this run generated, 1,323 files and 24,956,643 bytes:

| Class | Bytes | Share | Files |
| --- | ---: | ---: | ---: |
| Character portraits | 8,788,268 | 35.21% | 32 |
| Worked examples and their data | 4,676,196 | 18.74% | 192 |
| Python programs | 4,253,935 | 17.05% | 213 |
| Other shipped documents | 3,746,321 | 15.01% | 361 |
| Schemas and configuration | 1,436,181 | 5.75% | 296 |
| Skill instructions (SKILL.md, AGENTS.md) | 755,374 | 3.03% | 52 |
| Solidity | 518,970 | 2.08% | 87 |
| Other | 432,777 | 1.73% | 48 |
| Corpora (`.jsonl`) | 230,278 | 0.92% | 6 |
| Portable test fixtures | 118,343 | 0.47% | 36 |

By plugin, `plugins/hexaemeron` is 8,694,451 bytes across 281 files (34.84%) and
`plugins/lazarus` 3,041,976 across 106 (12.19%); no other plugin exceeds 9 per
cent. The single largest file is
`plugins/tabularium/examples/aave-v4-v0/events.jsonl` at 1,232,064 bytes, and the
second is `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` at 706,434.

**The largest class is 32 decorative images.** They are the character portraits
each SKILL.md opens with, 31 PNG and one WebP, from 58,214 bytes
(`anamnesis.webp`) to 426,737 (`hexaemeron-overseer.png`). Three independent
facts establish that no packaged program reads them:

1. `.horos/boundary.json`, the repository's own reading boundary, carries every
   one with `"category": "binary"`, `"grade": "hard"`, `"evidence": "file
   signature png"`. Horos exists to tell an agent what not to read, and it
   already says these.
2. Grepping the tree for `assets/characters` outside Markdown returns four
   non-boundary hits, all naming `shoggoth.png` or `promise-machine.png` in the
   public front-door checker and its tests, none of which ships in the package,
   plus the `ROOT_FILES` entry that puts `assets/characters/promise-machine.png`
   into the package.
3. The package's own closure test,
   `test_authoritative_runtime_links_close_inside_the_package`, matches
   `\[[^]]*\]\(([^)]+)\)`. The portraits are referenced by `<img src=...>` HTML,
   which that pattern does not read.

The third fact establishes that no packaged program resolves a portrait. It does
not license leaving those references pointing at nothing, and the operator
decision in section 3 says so directly. The first study pass treated the gap in
the closure test as permission; that reading is withdrawn.

**The portraits are not what is growing.** The published package at
`skills-runtime` head carries the same 32 images at the same 8,788,268 bytes as
this tree does. Every byte of the growth below is text.

### The growth rate

From the three figures the test comment records, with the merge times of the
pull requests that wrote them:

| Measured at | Merged | Bytes | Files | Share of 25 MiB |
| --- | --- | ---: | ---: | ---: |
| PR #1094 | 2026-09-01T12:56:47Z | 23,160,342 | 1,124 | 88.35% |
| PR #1330 | 2026-09-06T08:25:05Z | 23,991,363 | 1,206 | 91.52% |
| PR #1468 | 2026-09-07T22:44:30Z | 24,956,643 | 1,323 | 95.20% |

172,722 bytes per day over the first interval, 604,503 over the second, 280,316
overall; a mean of 898,150 bytes per merged delivery. The remaining 1,257,757
bytes is 4.49 days at the overall rate, or **1.40 average deliveries**. Two
points do not establish a trend and the second interval is 1.60 days long, so
treat the day rates as weak and the per-delivery figure as the usable one: the
next delivery of average size fits, and the one after it does not.

## 3. Constraints and non-goals

**Starting ref.** `12cbe2e6ed95decd6d9d355740f2dbd052956abe` on `main`. Run
branch `fiat/1467-packaged-payload-byte-cap-margin`. Base `main`.

**Toolchain.** Python 3.13.7 per `.python-version`, stdlib `unittest`, no new
dependency. The generator is `scripts/portable_promise_machine.py`; the test is
`tests/test_skills_sh_package.py`.

### Where 25 MiB comes from, and what it actually gates

Read at `vercel-labs/skills` `src/download-source.ts`, blob
`198022f31cda8c547d668c8b01b0c0fc669eddb0`:

```typescript
const DEFAULT_DOWNLOAD_MAX_BYTES = 10 * 1024 * 1024;
const DEFAULT_EXTRACT_MAX_BYTES = 25 * 1024 * 1024;
const DEFAULT_EXTRACT_MAX_FILES = 1000;
```

Four things follow, and three of them correct the issue.

1. **Verified: `github` never consults the caps.** `src/types.ts:105` declares
   six source types, `'github' | 'gitlab' | 'git' | 'local' | 'well-known' |
   'download'`. `src/add.ts` calls `downloadSource` at line 1173 inside a branch
   guarded at line 1171 by `parsed.type === 'well-known' || parsed.type ===
   'download'`; `github` takes a separate branch at line 1182. The extract caps
   exist only inside `downloadSource`. The repository's claim holds as written.
2. **The cap can be raised, by the installer.** All three limits read through
   `getPositiveIntegerEnv`, and the refusal message is `Archive extracts to more
   than ${limits.extractMaxBytes} bytes. Set SKILLS_EXTRACT_MAX_BYTES to
   override.` The issue says the byte cap "has none" of the file cap's escape and
   "cannot be raised". This repository cannot raise the *default*, which is what
   the test comment says and is true. But the cap is not unraisable: the CLI
   tells the person who hits it, in the failure text, which variable lifts it.
   The consequence the issue predicts, "a package that those two install routes
   refuse, discovered by whoever used them", is a refusal that names its own
   workaround.
3. **A tighter cap binds first, and it is already crossed.**
   `DEFAULT_DOWNLOAD_MAX_BYTES` is 10 MiB and applies to the compressed transfer,
   checked both against `content-length` and streaming. The payload built here
   compresses to 12,872,124 bytes as `tar.gz`, 122.8 per cent of that cap, and
   13,612,476 as `zip`. The real published archive of
   `wildcat-finance/skills-runtime` at its head is 11,915,647 bytes, 113.6 per
   cent. **The `download` route already refuses this package, today, at a cap the
   issue does not mention.** The 25 MiB extract cap is the only one of the three
   that the payload currently satisfies.
4. **The file cap is crossed too, at the CLI's default.** The CLI default is
   1,000; the payload is 1,323. The repository's `MAX_FILES = 1_400` is its own
   ceiling, not the CLI's, and the test comment says so in terms: raising it
   "does not claim that the `well-known` and `download` routes fit while the
   payload exceeds 1,000 files."

So the honest statement of the constraint is narrower than the issue's. Crossing
25 MiB would add a third refusal to two the package already incurs, on routes
this repository does not document, where every refusal names an environment
variable that lifts it. What it would also do is remove the last true sentence in
the test comment's chain of reasoning, and leave a delivery meeting a red assert
with no remedy in its own scope. That is the cost worth paying to avoid, and it
is a repository-maintenance cost rather than an installation failure.

### What the user ruled out

Two refusals, one from the filing and one taken during this study phase. Both
are stated constraints rather than measurement preferences, and each becomes a
hard gate.

**Deleting tracked files to buy margin.** Issue #1467 refuses "one pull request
that deletes files to buy margin", naming it "the outcome the file cap's own
comment refuses". Criterion `tracked-files-deleted` is `at-most 0` and the
refused option would score 32 against it. An omission class is a different act,
and the distinction is the repository's own: all eight classes already declared
in `scripts/portable_promise_machine.py` keep their files tracked and say so,
three of them in the words "remain in the full source checkout".

**Dangling image references in packaged documents.** Operator decision taken on
2026-09-08 during this study phase, in answer to a direct question from this
study's first pass, which had excluded those references from scoring and
recorded that scoring them would change the outcome:

> Dangling image references in packaged documents are not acceptable. Omit the
> portraits *and* remove or rewrite the `<img>` references in the packaged
> copies, so nothing dangles.

Criterion `dangling-image-references` is `at-most 0`. It is measured, not
reasoned, for every candidate; section 4 gives the cell for each. The decision
changes the selection: it eliminates the candidate the first pass chose.

### Which skill or skills this upgrades: none

The issue asks Protasis to decide. The answer is that this is repository
framework work and no skill's frontier advances.

Evidence. The change lands in `scripts/portable_promise_machine.py`,
`tests/test_skills_sh_package.py` and a new `docs/decisions/ADR-NNN`. No plugin
`SKILL.md`, no plugin `EVOLUTION.md`, no plugin `scripts/` file changes. Horos
appears throughout section 2 as the source of the classification evidence, but
its boundary is read, not modified, and the classification it already publishes
is what makes the omission defensible rather than something Horos must learn.

**This confirms the run's no-`--frontier` initialisation rather than
contradicting it.** Had the evidence pointed the other way, this section would
say so.

### Non-goals

- Deciding whether the `well-known` and `download` routes are used. Unknown,
  recorded in section 7 as unresolved.
- Deciding whether 25 MiB is the right number. It is another project's default.
- Trimming any other content class. The portraits are selected on evidence that
  no packaged program reads them; no other class has that evidence.
- Repairing the publication lag found in passing: `skills-runtime` last rebuilt
  at 2026-08-31T18:37:55Z from `wildcat-finance/skills@51fb586e`, 8 days before
  this study, against the hourly job ADR-066 describes. Its published payload is
  1,046 files and 22,362,655 bytes, 85.31 per cent of the cap, so the figure
  installs actually receive is lower than this tree's. That belongs in its own
  observation and is not repaired here.

## 4. Design options

Five candidates. The prose explains them; `.hexaemeron/design-evidence.json`
selects one, and the ranking below is that record's output rather than its
input.

**`omission-class`.** Declare `assets/characters/**` and
`plugins/*/assets/characters/**` as a ninth omission class in `OMISSIONS`, extend
`_omitted`, and drop `assets/characters/promise-machine.png` from `ROOT_FILES`.
The files stay tracked. Trade: 27 `<img src=...>` references in packaged
documents stop resolving, which the operator decision in section 3 refuses.

**`omission-class-with-reference-repair`.** The same omission, and the generator
additionally rewrites, in the packaged copy alone, each `<img>` tag whose target
left the package, replacing that tag with an HTML comment naming the omitted
path. Trade: it is the only candidate that changes a packaged document's bytes,
and it costs the two byte-equality assertions the next subsection names.

**`second-package`.** Split the runtime into two published packages. Trade:
breaks ADR-040's dependency closure, measured at 14 escaping links.

**`route-restriction`.** Document `github` as the only supported route. Trade:
recovers no margin, and leaves the next delivery the same red assert.

**`warning-gate`.** Move the byte assertion off the cap onto a stated threshold.
Trade: buys warning, not margin; the cap arrives on schedule with more notice.

### What the repair mechanism costs, established before it was scored

A content transform on packaged copies is a different mechanism from an
omission, so the question was asked first: does this repository bind packaged
bytes to repository bytes? It does, in two named places, and both are in the
suite this delivery already edits.

1. `tests/test_skills_sh_package.py:150`,
   `test_manifest_binds_every_runtime_file_to_source_bytes`. At line 188, for
   every manifest row whose `source` is not null:

   ```python
   source = ROOT / row["source"]
   self.assertTrue(source.is_file())
   self.assertEqual(data, source.read_bytes())
   ```

   The one escape is closed to a single path: a row with `source: None` is
   asserted at lines 179 to 184 to be `.horos/boundary.json` and nothing else.
2. The same test, lines 205 to 210, asserts the packaged router equals its
   repository copy byte for byte:

   ```python
   self.assertEqual(
       (RUNTIME / ".agents/skills/promise-machine/SKILL.md").read_bytes(),
       (PACKAGE / "SKILL.md").read_bytes(),
   )
   ```

   That document is one of the 27 the repair would rewrite.

So the candidate is admissible only by amending both assertions, and only by
implementing the transform inside `expected_files()` in
`scripts/portable_promise_machine.py`, which is the single place packaged bytes
are produced and digested. Two consequences follow and neither is optional. The
manifest's per-row `sha256` becomes the digest of the transformed bytes, which
keeps `verify_runtime.py` lines 58 to 63 and the generator's own `check()` at
line 378 self-consistent. And the row's `source` field would then name a
repository path whose bytes differ, so the binding must be re-expressed rather
than dropped: the row carries a declared transform id, and the amended test
asserts that applying that transform to the source bytes yields the packaged
bytes. Deleting the assertion instead would trade a dangling reference for a
lost guarantee, which is not what the operator asked for.

**Four places that could have collided and do not.** Each was checked; each is
negative evidence.

- **`SOURCES.md` and `MANIFEST.json` outside the package.** `SOURCES.md` holds
  no digests at all: `grep -cE "[0-9a-f]{40,}" SOURCES.md` returns 0. It is the
  generated lending-data coverage manifest and names no repository file.
- **`audit/`.** No audit document is packaged, so none can be rewritten.
  `plugins/*/audit/**` is the third existing omission class, applied by
  `_omitted` at `scripts/portable_promise_machine.py:173`; top-level `audit/` is
  absent from `ROOT_FILES` and is never enumerated by `source_files`. The two
  audit files that do carry an `<img>`,
  `audit/rounds/fiat-shoggoth-front-door-derived.md` and its `.synopsis.md`, are
  outside the package on both counts.
- **Horos census.** A packaged-only transform cannot reach it. `horos.py:585`
  builds its universe from `git ls-files`, widened at most to
  untracked-but-not-ignored by `--include-untracked` (line 1219);
  `.gitignore:77` ignores `.agents/skills/promise-machine/runtime/`, and `git
  ls-files .agents/skills/promise-machine/runtime` returns 0 paths. Entries in
  `.horos/boundary.json` carry `bytes`, `category`, `evidence`, `grade` and
  `path`, and no digest field. Confirmed by reading, not assumed.
- **Quotation bindings on repository prose.**
  `tests/test_router_selection.py:54` closes its quotable set to
  `frozenset({"AGENTS.md", ROUTER_PATH})` and holds each quoted sentence against
  the repository copy, not the mirror; top-level `AGENTS.md` carries no `<img>`.
  `repo_contract.py` lines 113 to 119 match Markdown link targets and a
  backticked path, not `<img>`.
- **The installation law.** `verify_runtime.py` lines 78 to 81 require every
  `plugins/*/PROMISE_MACHINE.md` to equal the root copy byte for byte. The
  transform never touches them: their image is
  `<img src="https://raw.githubusercontent.com/wildcat-finance/skills/main/assets/characters/promise-machine-binding.png" width="1200">`,
  a remote URL that cannot dangle, and the repair leaves all 19 such tags alone.

**What the packaged reference surface actually is.** Measured from the package
built at the base SHA: 458 packaged Markdown documents hold 46 `<img src=...>`
references. 19 are the remote URL above. The other 27 are relative, all 27
resolve to a character portrait, and 26 of them are in a `SKILL.md` with the
last in `plugins/hexaemeron/AGENTS.md`. Today 0 of the 46 dangle, because the
portraits are still packaged.

**The repair, and what was checked about it.** Each `<img>` tag whose resolved
target is absent from the published set is replaced by
`<!-- image omitted from the portable package: <path> -->`. Three properties
were measured rather than argued, by loading `.hexaemeron/resolve_design.py`
and comparing bytes: two runs produce identical output for all 27 documents;
re-applying the transform to its own output changes nothing, because the
replacement contains no `<img`; and reconstructing each document from the
original with only the matched tag spans substituted reproduces the transformed
bytes exactly, for all 27, so no byte outside a replaced tag moves. The cost is
970 bytes across the 27 documents.

### The matrix

Seven selection criteria and one conformance criterion, all five concerns
covered. Every selection cell resolved by `python3
.hexaemeron/resolve_design.py --candidate <id> --criterion <id>`, whose 35
reports are under `.hexaemeron/reports/`. No cell is assigned by reasoning that
a candidate changes nothing.

| Criterion | Concern | Form | `omission-class` | `omission-class-with-reference-repair` | `second-package` | `route-restriction` | `warning-gate` |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| `tracked-files-deleted` | correctness | gate, at-most 0 | 0 pass | 0 pass | 0 pass | 0 pass | 0 pass |
| `authoritative-link-closure` | correctness | gate, at-most 0 | 0 pass | 0 pass | **14 fail** | 0 pass | 0 pass |
| `dangling-image-references` | correctness | gate, at-most 0 | **27 fail** | 0 pass | 0 pass | 0 pass | 0 pass |
| `extract-margin` | space | metric, maximise | 10,046,025 | **10,045,055** | 13,697,547 | 1,257,757 | 1,257,757 |
| `install-commands` | compatibility | metric, minimise | 1 | **1** | 2 | 1 | 1 |
| `publication-files-written` | time | metric, minimise | 1,292 | **1,292** | 1,325 | 1,324 | 1,324 |
| `foreign-repositories-touched` | recovery | gate, at-most 0 | 0 pass | 0 pass | **1 fail** | 0 pass | 0 pass |
| `built-payload-margin` | space | gate at `step:3`, at-least 5,242,880 | pending | pending | pending | pending | pending |

`omission-class` fails the new gate at 27 and `second-package` fails two older
ones. Of the three survivors,
`omission-class-with-reference-repair` is at least as good on every metric and
strictly better on two, so it dominates both and the non-dominated frontier is
one candidate. `design_evidence.py --transition design-lock` exits 0 with
`unique-frontier` and selects it.

**The record carries four of these five, and the study carries all five.**
`design_evidence.py` sets `MAX_CANDIDATES = 4` at line 44 and refuses a fifth
with `D002`; Protasis states the same bound in prose, "two to four candidates".
The candidate left out of the machine record is `route-restriction`, chosen
because it and `warning-gate` score identically on all seven selection criteria,
so removing it removes no discriminating evidence and leaves the domination
argument unchanged. Its seven reports stay on disk and its row stays above. Any
other omission would have hidden a distinct profile: `omission-class` is the
candidate the operator decision eliminates, and `second-package` recovers the
most margin of any candidate while failing two gates.

Five notes on how the numbers were obtained. Each is a place the comparison
could have been rigged.

- `dangling-image-references` counts every packaged Markdown document, 458 of
  them, rather than the 52 authoritative documents the shipped link-closure test
  reads. The wider set is the honest one for a constraint about what a reader
  sees. A remote, protocol-relative or `data:` source is not counted, because it
  cannot dangle inside the package.
- `authoritative-link-closure` reproduces the rule the shipped test already
  applies, including its acceptance of a link naming a directory, so the baseline
  scores 0 exactly as CI does. The 14 escapes under `second-package` are real
  cross-package links: `plugins/*/skills/*/SKILL.md` files reaching
  `docs/decisions/ADR-*.md` and `.python-version` in the other half. The repair
  does not touch `[](...)` links, and its cell is 0 by measurement.
- `extract-margin` is computed from each candidate's own packaged bytes, so the
  repair pays for itself: 10,045,055 against `omission-class`'s 10,046,025, a
  difference of exactly the 970 bytes the 27 replacements add.
- `publication-files-written` replaced a wall-clock build time. Measured as a
  median of five runs, `route-restriction` came out at 855 ms and `warning-gate`
  at 769 ms, an 86 ms spread between two candidates whose build is
  byte-identical. A clock that separates identical things is not evidence, so the
  criterion became the deterministic count of files the hourly job writes.
- `tracked-files-deleted` and `foreign-repositories-touched` are read from the
  candidate definitions and from ADR-066, not from executing the candidates.
  Their reports say so in their command. They record that the issue's refusal was
  applied and that only `second-package` needs a change outside this repository.

**One modelling limit, stated.** The selection resolver computes each
candidate's payload from the baseline manifest rather than by regenerating the
package under the candidate. The portable `.horos/boundary.json` is generated
from the payload, so its bytes would move slightly under any candidate that
changes the payload, and the resolver carries the baseline figure for it. This
affects `omission-class`, the repair candidate and `second-package` alike, and
it is why `built-payload-margin` exists: that criterion builds the real package
and blocks `step:3` until it passes.

### What the selected candidate recovers

The payload falls to 1,291 files and 16,169,345 bytes, 61.68 per cent of the
extract cap, margin 10,045,055, which is 11.2 average deliveries at the rate in
section 2, against 1.40 today. The compressed transfer falls from 12,872,124
bytes to approximately 4,027,666, from 122.8 per cent of the 10 MiB download cap
to about 38.4, so the transfer stage of the `download` route stops refusing;
that compressed figure was measured for `omission-class` and the repair's 970
extra uncompressed bytes are not separately measured under compression. The
file count stays above the CLI's 1,000 default, so that route is not fully
restored by this change and this study does not claim it is. No reference in a
packaged document dangles.

## 5. Risk register seed

The boundaries the audit loop should look hardest at. `_omitted` is a path
predicate over `git ls-files` output, the manifest is the only statement of what
a consumer receives, and the selected candidate adds the first transform this
generator has ever applied to a packaged copy. So the risks are pattern breadth,
silent omission, a guard that can be satisfied without measuring, and every way
a byte-changing transform can reach further than it was asked to.

```risk-register
omission-pattern-breadth | the _omitted path predicate in scripts/portable_promise_machine.py | the pattern matches only assets/characters directories and cannot reach a sibling named characters elsewhere in a plugin
root-files-desync | the ROOT_FILES tuple and the OMISSIONS declaration | the promise-machine.png entry leaves ROOT_FILES in the same change that declares the class, and no path is both selected and omitted
manifest-omission-honesty | the omissions array in the generated MANIFEST.json | the new class appears with its reason, and EXPECTED_OMISSIONS in the test equals the manifest set exactly rather than containing it
silent-payload-shrink | the generated package against git ls-files | exactly 32 files leave the package and every one is a character portrait; no other path is dropped by the wider pattern
threshold-without-measurement | the byte assertion in tests/test_skills_sh_package.py | the guard compares the manifest total against a stated threshold below MAX_BYTES and fails when the margin closes, not when the cap is met
dangling-image-references | every img src reference in the 458 packaged Markdown documents | no reference resolves to a path the package does not carry, measured after the change, and the shipped link-closure test still exits 0
transform-idempotence | the packaged-copy img rewrite in expected_files | applying the transform to its own output changes no byte, so a second pass over an already-built payload is a no-op
transform-determinism | the packaged-copy img rewrite across runs | two builds of the same tree produce identical bytes for every rewritten document, and the manifest digests match run to run
transform-reaches-only-departed-targets | the set of img tags the transform rewrites | only a tag whose resolved target is absent from the published set is replaced; the 19 remote-URL tags and every tag whose target still ships are copied through unchanged
transform-changes-nothing-else | the bytes of each rewritten document | reconstructing the document from its source with only the matched tag spans substituted reproduces the packaged bytes exactly, so no prose, link, code block or frontmatter moves
manifest-source-binding-restated | the manifest row for a rewritten document and its test | the row declares the transform it carries, and the amended assertion checks that the transform applied to the source bytes yields the packaged bytes, rather than dropping the source binding
source-tree-untouched | the working tree after the change | git ls-files reports the same 32 portrait paths tracked before and after and the same bytes in every document, so nothing was deleted or edited here to buy margin
publication-lag-masking | the rebuilt package at wildcat-finance/skills-runtime | the margin is asserted against a package built from this tree, never against the published copy, which section 3 records as 8 days stale
```

## 6. Glossary seeds

- **Payload / package.** The generated portable runtime under
  `.agents/skills/promise-machine/runtime`, built by
  `scripts/portable_promise_machine.py package`.
- **Omission class.** A declared pattern in `OMISSIONS` naming content the
  package leaves out, with the reason, while the files stay tracked here.
- **Extract cap.** `SKILLS_EXTRACT_MAX_BYTES`, default 26,214,400 bytes, applied
  to an archive's uncompressed contents by the skills CLI.
- **Download cap.** `SKILLS_DOWNLOAD_MAX_BYTES`, default 10,485,760 bytes,
  applied to the compressed transfer before extraction.
- **Capped routes.** The CLI's `well-known` and `download` source types, the only
  two whose install path reaches `downloadSource`.
- **Character portrait.** One of the 32 decorative images under an
  `assets/characters/` directory, classified `binary`/`hard` by Horos.
- **Margin.** Extract cap minus the manifest's `total_bytes`.
- **Reference repair.** The generator step that replaces, in a packaged copy
  only, an `<img>` tag whose target the package no longer carries, with an HTML
  comment naming the omitted path.
- **Dangling reference.** An `<img src=...>` in a packaged document whose
  resolved, package-relative target is absent from the built package. A remote
  or `data:` source is not one.

## 7. Sources

- Issue [#1467](https://github.com/wildcat-finance/skills/issues/1467),
  `framework-109`.
- `tests/test_skills_sh_package.py`, comment at lines 70 to 115, constants at
  116 and 117.
- `scripts/portable_promise_machine.py`: `ROOT_FILES` line 37, `OMISSIONS` line
  92, `_omitted` line 171.
- `.horos/boundary.json`, 134 entries, `counts.bytes_binary` 43,942,262.
- `docs/decisions/ADR-040`, `ADR-054` (superseded), `ADR-066` (accepted).
- `audit/rounds/fiat-395-resumable-ethereum-usdc-interval-collector.md`,
  finding S1-R1-07, open.
- Pull requests [#1038](https://github.com/wildcat-finance/skills/pull/1038),
  [#1094](https://github.com/wildcat-finance/skills/pull/1094),
  [#1330](https://github.com/wildcat-finance/skills/pull/1330),
  [#1468](https://github.com/wildcat-finance/skills/pull/1468).
- `vercel-labs/skills`, `src/download-source.ts` blob
  `198022f31cda8c547d668c8b01b0c0fc669eddb0`, SHA-256
  `ed34a01906ddf5f73526249f351612a520e8cfeeae03f0ff4609e2b82214c09e`; `src/types.ts`
  line 105; `src/add.ts` lines 1171 to 1182.
- `wildcat-finance/skills-runtime` at `c08b88cb`, archive 11,915,647 bytes.
- `tests/test_skills_sh_package.py`: the source-bytes binding at line 150 with
  its assertion at 188, the `source: None` escape at 179 to 184, and the router
  byte-equality at 205 to 210.
- `.agents/skills/promise-machine/scripts/verify_runtime.py`, digest check at
  lines 58 to 63 and installation-law copy equality at 78 to 81;
  `scripts/portable_promise_machine.py`, `expected_files` at 235, `check` drift
  comparison at 378.
- `tests/test_router_selection.py` line 54, `PROSE_SOURCES`;
  `repo_contract.py` lines 113 to 119.
- `plugins/horos/skills/horos/scripts/horos.py` line 585 and the
  `--include-untracked` option at 1219; `.gitignore` line 77.
- The operator decision of 2026-09-08 recorded in section 3, taken in the study
  phase of this run.
- `design_evidence.py` line 44, `MAX_CANDIDATES = 4`.
- This run's `.hexaemeron/design-evidence.json` and the 35 reports under
  `.hexaemeron/reports/`.

**Unresolved, and not resolvable here.** Whether anyone installs through
`well-known` or `download` could not be established: no telemetry exists and no
request has been recorded. The whole margin question rests on a population
nobody has counted, and the study proceeds on the recorded reading that the
routes should keep working rather than on evidence that they are used.

**Unresolved, and deferred to the build.** Three things.

1. The exact packaged byte total under the repair. The selection resolver
   carries the baseline `.horos/boundary.json` size, which the omission and the
   rewrite both move. The figures in section 4 are the model's; the
   `built-payload-margin` criterion measures the real one and blocks `step:3`.
2. The compressed transfer size under the repair. 4,027,666 bytes was measured
   for `omission-class`; the repair's 970 extra uncompressed bytes were not
   separately compressed, so the 38.4 per cent figure is approximate for the
   selected candidate.
3. Whether any consumer outside this repository reads the manifest's `source`
   field and re-derives a digest from the named repository path. Nothing inside
   the repository does; nothing outside it could be checked from here.

## 8. Signals, and the questions behind them

Three questions, all asked by whoever is integrating a delivery rather than by
an on-call engineer, because nothing here runs unattended in this repository.

1. *How much margin is left, and did my change move it?* Answered by the failure
   text of the byte guard in `tests/test_skills_sh_package.py`. It must print the
   measured `total_bytes`, the threshold, and the remaining margin, not a bare
   assertion, so the number appears in CI output whether the guard passes or
   fails. Emitted by the step that installs the guard.
2. *Did the omission drop something it should not have?* Answered by the
   manifest's own `omissions` array and by the test asserting the omitted set is
   exactly 32 portrait paths. Emitted by the step that declares the class.
3. *Which packaged documents did the build rewrite, and why each one?* Answered
   by the transform id on each manifest row plus a build line naming the count
   and the omitted target for each replacement. What goes wrong is a build that
   rewrites a document nobody expected and ships it, so the count must appear in
   normal build output rather than only on failure, and a run that rewrites a
   number of documents other than the expected one must fail rather than log.
   Emitted by the step that installs the repair.

The hourly publication job in `wildcat-finance/skills-runtime` does run
unattended, and its 8-day silence went unnoticed until this study measured it.
That is a real Ephoros gap and it is out of scope here; it is recorded in section
3 as a separate observation rather than answered.
[ephoros](../../plugins/hexaemeron/skills/ephoros/SKILL.md) owns what those signals must carry.

## 9. Boundaries, per capability

Two boundaries are opened and one is narrowed.

**Opened: the generator may now alter a packaged document's bytes.** Until this
change every packaged file was a verbatim copy, and
`test_manifest_binds_every_runtime_file_to_source_bytes` was the control that
said so. What goes wrong is a transform that reaches a document, or a span
inside one, that nobody asked it to touch, and that ships because the assertion
which would have caught it was weakened in the same change. Four controls, all
in the register: the transform is confined to `expected_files()`, the single
place packaged bytes are produced; it replaces only a matched `<img>` tag whose
resolved target is absent from the published set; the amended manifest binding
asserts that the declared transform applied to the source bytes yields the
packaged bytes, so the source binding is restated rather than dropped; and the
rewritten-document count is asserted, not logged. The regex is the sharp edge:
it parses HTML with a pattern, so a tag it fails to match ships a dangling
reference and a tag it over-matches eats neighbouring markup. Both directions
are covered by `transform-reaches-only-departed-targets` and
`transform-changes-nothing-else`.

**Opened: the omission predicate as a filter on published content.** `_omitted`
decides what a consumer receives. A pattern wider than intended silently removes
content, and what goes wrong is a package that builds, verifies and installs
while missing something. The control is the `silent-payload-shrink` register
line: the change is admitted only against a measured diff of exactly 32 paths,
every one a portrait, and `EXPECTED_OMISSIONS` in the test is compared for
equality rather than containment, which the existing test already does.

**Narrowed: nothing new is executed.** The change adds no subprocess, no URL
fetch, no credential, no dependency and no parsing of untrusted input. The
generator's existing `git ls-files` subprocess is unchanged and keeps its
`# phylax: allow subprocess` marker.

The two resolvers this study ships, `.hexaemeron/resolve_design.py` and
`.hexaemeron/measure_built_margin.py`, each spawn the generator with a fixed
local argv and no shell, write only to a `--out` path, and touch no controller
state. [phylax](../../plugins/hexaemeron/skills/phylax/SKILL.md) owns the boundary list and the controls.

## 10. The budget, or its absence

One budget, and it is the point of the work rather than a performance concern.

**Budget.** The generated payload holds at least 5,242,880 bytes of headroom
under the 26,214,400-byte extract cap: at most 20,971,520 bytes total. At the
898,150 bytes per delivery measured in section 2, that is 5.84 average deliveries
of warning, against 1.40 today. The repair spends 970 of those bytes: 0.0185 per
cent of the budget, 0.11 per cent of one average delivery.

**Command.** `python3 .hexaemeron/measure_built_margin.py --candidate
omission-class-with-reference-repair`, which builds the package and reports the
margin. Run at the current tree it reports 1,257,757 and the gate fails, which
is correct: it can only pass once the omission and the repair land. It is the
`built-payload-margin` conformance criterion, blocking `step:3`.

No wall-clock budget. Section 4 records why: a median of five builds separated
two byte-identical candidates by 86 ms, so this repository's build time cannot be
measured to a useful precision on the hardware available, and no claim about it
is made. [metron](../../plugins/hexaemeron/skills/metron/SKILL.md) owns what a budget carries and how it is
checked.

## 11. The fail-closed posture

**What stops the run.** Six things, each an existing or added assertion in
`tests/test_skills_sh_package.py`, all of which fail the suite rather than warn:
the manifest's `omissions` set not equalling `EXPECTED_OMISSIONS`; the omitted
path set not being exactly the 32 portraits; `total_bytes` at or above the
stated threshold; any `<img src=...>` in any packaged Markdown document
resolving to a path the package does not carry; a manifest row without a
declared transform whose bytes differ from its source; and a build that rewrites
a number of documents other than the expected one. The generator itself already
fails closed on a missing or symlinked source path via `PackageError`, and that
path is unchanged.

**The guard convention.** A fix admitted during the audit loop carries a test
that fails without it. For a byte-threshold change that means a test asserting
the threshold's relationship to `MAX_BYTES`, not just the current measurement,
so a later raise of the threshold to meet a grown payload trips the same guard
the file cap's comment describes. For an omission-pattern fix it means a case
constructed against a path the wrong pattern would catch. For a transform fix it
means a constructed document, not a real one: a tag the pattern mishandles, put
through the transform, with the whole document compared byte for byte, because a
guard that only counts replacements cannot see a transform that ate the markup
around one.
[elenchus](../../plugins/hexaemeron/skills/elenchus/SKILL.md) owns the triage order and the guard rule.

## 12. Decisions and their homes

Three decisions are expensive to reverse, and one is not.

1. **Declaring a content class the package omits.** Reversing it means
   republishing a larger payload to installs that have already taken the smaller
   one. It is also the decision that answers S1-R1-07 and supersedes ADR-066's
   reasoning on payload size. Home: a new
   `docs/decisions/ADR-NNN-omit-decorative-assets-and-repair-their-packaged-references.md`,
   extending ADR-040 and ADR-066, recording the 35.21 per cent measurement, the
   Horos classification that justifies it, and the three cap facts section 3
   establishes. The number is allocated immediately before pushing, because this
   repository assigns them against the default branch at merge.
2. **Allowing the generator to alter a packaged document's bytes.** This is the
   expensive one, and it is expensive because of what it gives up rather than
   what it costs to undo. Until now every packaged file was a verbatim copy and
   a shipped assertion said so; afterwards the guarantee is the weaker "verbatim,
   or the declared transform of verbatim". Every later question about what an
   install received is answered under the weaker rule, and a second transform
   will be cheaper to add than this one was. Home: the same ADR, as its own
   decision section, recording the operator decision that required it, the two
   assertions amended, and the four bindings section 4 checked and found not to
   collide.
3. **Moving the byte guard off the CLI's default onto a repository threshold.**
   It changes what the test claims to hold: today the constant says "the CLI's
   default", and afterwards it says "this repository's margin". Home: the same
   ADR, as a third decision section, plus the comment in
   `tests/test_skills_sh_package.py`, which is where four raises of the sibling
   constant have already been reasoned in place.

Not expensive: the exact threshold value. It is one integer with a stated
derivation and can be moved by a commit.

The selected candidate binds to one home. The draft carries the numberless form
Hypomnema names for use before integration assigns a number, and Step 1 commits
it beside the study:

```design-bridge
schema | hypomnema-design-bridge/v1
decision | omission-class-with-reference-repair
record | docs/decisions/drafts/omit-decorative-assets-and-repair-their-packaged-references.md
```

[hypomnema](../../plugins/hexaemeron/skills/hypomnema/SKILL.md) owns which decisions earn a record and where
each one lives.
