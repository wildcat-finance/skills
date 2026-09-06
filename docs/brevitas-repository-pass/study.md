# Repository-wide Brevitas pass

## Problem statement

The repository has 202 tracked Markdown files. The agreed exclusions leave 159
files at the starting ref. The committed study and runbook will raise the final
in-scope corpus to 161. Baseline Brevitas lint leaves 40 files clean and rejects
119 files with 375 diagnostics. `README.md` is 847 lines and `audit/AUDIT.md` is
902 lines.

The work rewrites engineering and repository prose for maintainers, skill users,
auditors and reviewers. It changes volume, structure and connective text after
Imprimatur and Vulgate have dealt with vocabulary and register. It must preserve
every claim, command, link, anchor, normative requirement and evidence token that
the shorter document still needs to carry.

A working delivery has 13 sequential pull requests merged into `main`, with each
task branch deleted and receipted by Fiat. The final proof checks 161 files, leaves
all exclusions and protected passages byte-identical, reports every allowed
evidence refusal, keeps `README.md` at 300 lines or fewer, and leaves `hexctl
status` and `hexctl verify` at `done`.

The visible demo path is the final `main` checkout. A reviewer can run every root
`AGENTS.md` command, all repository link checks, Agent Skills validation for every
changed canonical skill, `git diff --check`, the exclusion and protected-passage
SHA-256 checks, Imprimatur, and Brevitas with each file's saved entry-ref source.
The proof fails when any protected byte, evidence token, generated document,
frontier digest, local link or test has drifted.

## Existing work

Repository mechanisms already cover most of the delivery:

- `plugins/brevitas/skills/brevitas/scripts/brevitas.py` enforces finding, fence,
  heading and table budgets. Its `--source` mode checks addresses, transaction
  hashes, `file:line` references and numeric tokens.
- `plugins/brevitas/skills/brevitas/scripts/run_evals.py` protects three real audit
  fixtures with recorded SHA-256 values and includes an irreducible-evidence case.
- `plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py` supplies the first
  prose pass. `plugins/hexaemeron/skills/vulgate/SKILL.md` supplies the register
  pass. Brevitas runs after both.
- `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` owns the study, runbook,
  implementation, audit, prose, push and receipt sequence.
- `audit/AUDIT.md` records prior Fiat audit rounds. Its finding tables conflict
  with Brevitas's minimum 3-row by 3-column table rule when a round has only one
  or two findings.
- `tests/test_evolution_contract.py` and
  `plugins/hexaemeron/tests/test_evolution.py` parse the table-shaped History
  sections in 14 governed `EVOLUTION.md` ledgers. The parser must accept the
  compact list form without changing version labels, axes, revisions, frontier
  digests, evidence or change text.
- `plugins/probitas/scripts/probitas_lib/render.py` owns
  `plugins/probitas/docs/example-dossier.md`.
- `plugins/pandects/scripts/pandects_lib/render.py` owns
  `plugins/pandects/docs/catalogue.md`. Their renderers and byte-for-byte tests
  must change with the documents.
- `.agents/skills/` exposes portable entries that point at the canonical plugin
  skills. Root and plugin `AGENTS.md` files define the validation and test
  boundary.

Organisation-level precedents are the marketplace-context blocks, the shared
`plugins/hexaemeron/skills/VERSIONING.md` contract, Fiat's per-step audit loop and
the installed Brevitas and Sapheneia skills. The same repository already treats
the Pashov `fizz`, `x-ray` and `solidity-auditor` roots as vendored material and
keeps their attribution in `LICENSE` or `NOTICE.md` files.

Outside precedents stop short of the required contract:

- CommonMark 0.31.2 defines headings, lists, links and fenced code blocks, but
  does not impose engineering-prose budgets.
- `markdownlint` checks Markdown syntax and style through named rules, but does
  not preserve audit evidence against a source draft.
- Vale applies configurable prose rules to files, but it does not carry the
  repository's five-line finding form or evidence precedence.
- The Agent Skills specification defines portable `SKILL.md` metadata and
  layout; the repository's validator applies that contract to changed skills.

## Constraints and readings

The exact starting ref is clean `main` at
`a7d001009e7e2a7e63343e206ef10ecabc2cab42`. Each step fetches current
`origin/main`, branches from that ref because `git.step_base=base`, and stops on a
rejected push, failed external gate, required independent approval or controller
verification failure.

Corpus rules:

- Enumerate tracked `*.md` paths with Git. Exclude every Markdown path below
  `plugins/hexaemeron/skills/fizz/`,
  `plugins/hexaemeron/skills/x-ray/` and
  `plugins/hexaemeron/skills/solidity-auditor/`, plus every basename matching
  `LICENSE*` or `NOTICE*`.
- The three roots contain 42 Markdown paths and the licence/notice name rule
  overlaps three of them. Four notice files exist, so the unique exclusion set is
  43 files and the entry corpus is 159.
- “Every piece of Markdown” means the 159 entry-ref files plus the committed
  `docs/brevitas-repository-pass/study.md` and `runbook.md`. No extra Markdown is
  needed for this delivery.
- “Legal text” means the bytes of an operative licence, copyright, attribution,
  legal-terms, warranty or liability passage. A technical sentence that merely
  uses a word such as “attribution” is not frozen. This reading protects legal
  language without exempting unrelated engineering prose.
- Record complete excluded-file digests and exact protected-passage byte ranges
  under ignored `.hexaemeron/` state before step 1. Verify their SHA-256 values
  after every step and in the final proof.

Evidence rules:

- Save each batch's entry-ref source under ignored `.hexaemeron/` state before
  editing it. Run Brevitas with `--source` against that saved file.
- Addresses, transaction hashes, `file:line` references, numbers, concrete
  counterexamples, reproduction steps and explicit establishment limits outrank
  every structural budget. Cut prose before evidence.
- Keep the three Brevitas `evals/cases/*/original.md` files byte-identical because
  their `case.json` files pin SHA-256 values. Keep
  `plugins/lazarus/examples/aave-v4-spoke-v0/README.md` byte-identical because
  `manifest.json` records `b8a0441746fdd8feb6657bcc78f13ff199c94b081a6462981e8e8a233ae0c09b`.
- Record those four refusals. Any other refusal needs a checked byte digest or a
  provenance fixture that would break under a rewrite.
- The linter mechanically protects token classes. Manual audit owns
  counterexamples, reproduction steps, establishment limits, link intent,
  commands and normative meaning.

Document rules:

- Apply Imprimatur, then Vulgate, then Brevitas to each in-scope file and every PR
  description. PR description source drafts also remain in ignored state for the
  `--source` comparison.
- Use no table with fewer than 3 real-data rows and 3 real-data columns. Remove
  section headings when fewer than 3 real sections remain. Keep each code fence
  to 15 content lines and one fence per point.
- Preserve marketplace frontiers, held Next Fiat jobs, versioning digests, local
  links, rendered anchors, commands and normative requirements.
- Reduce root `README.md` from 847 lines to at most 300 by routing plugin detail to
  plugin READMEs, merging install/use duplication and removing the 125-line
  repository tree.
- Do not add a permanent Brevitas command, formatter or CI gate. The delivery uses
  the checked-in Brevitas script and ignored run state.

Versioning and generated-document rules:

- Probitas moves from generation `0.1.0` to `0.2.0`; Pandects moves from
  generation `1.1.0` to `1.2.0`. Neither frontier, frontier revision nor Next Fiat
  job changes.
- Every other skill version and all frontier text remain fixed.
- Change the Probitas and Pandects renderers before regenerating their Markdown;
  their suites must prove the checked-in files are exact renderer output.
- Ariadne and Tabularium link tests may permit only the canonical shared
  `VERSIONING.md` link. They must continue rejecting other paths outside their
  plugin roots.

Delivery rules:

- The Solidity security suite is waived because no Solidity change is planned.
  One real manual audit round still runs for every step.
- Root tests and the affected plugin suite run on every pull request. Lazarus runs
  in a fresh environment installed from `requirements.lock`. Both Lemma suites
  run in its step. Pandects runs its Python suite, `forge build` and `forge test`.
  The Hexaemeron step runs the controller and Imprimatur suites.
- Each pull request appends one concise round to `audit/AUDIT.md`. Findings use
  claim, location, mechanism, impact and fix lines. A zero-finding round is prose,
  not a small table.
- Use `step-<n>-<slug>` branches, scoped commits, the required Shoggoth trailers,
  `origin:ai`, the origin marker and the repository's permitted merge method.
  Record exact head and merge SHAs, then delete the branch.
- No task issue is attached. Marketplace reassessment may select only the already
  installed Brevitas and Sapheneia skills.

Non-goals:

- Do not alter code comments, commit-message prose, Solidity behaviour, data
  schemas, fixture meaning or completeness-oriented specification content.
- Do not change word choice on Brevitas's behalf; Imprimatur owns banned language
  and Vulgate owns register.
- Do not reshape prose for AuDHD legibility on Brevitas's behalf; Sapheneia owns
  agent interaction shape.
- Do not rewrite vendored Pashov text or any protected legal byte.
- Do not advance a plugin frontier. This is repository maintenance, not a Fiat,
  Brevitas or Sapheneia frontier job.

## Design options

### One repository-wide pull request

Rewrite all 161 final files at once and prove the tree only at the end. This has
the fewest Git operations, but a reviewer cannot isolate a lost claim from an
unrelated plugin rewrite. Generated documents, version ledgers and the root README
would share one large failure surface.

### Thirteen sequential pull requests

Use the existing Fiat controller and divide the corpus by plugin and shared
contracts. Save entry sources and protected digests outside Git, run one audit and
the relevant tests per step, then merge before starting the next branch. This costs
more CI and merge time, but each review has one document family, one evidence
comparison and a small set of affected parsers or renderers.

The sequence is:

1. Shared study, runbook, audit-log format and evolution parser.
2. Brevitas and its portable entry.
3. Sapheneia and its portable entry.
4. Hermes and its portable entry.
5. Lemma, its baseline documentation and portable entry.
6. Ariadne and its portable entry.
7. Lazarus and its portable entry.
8. Alexandria and its portable entry.
9. Probitas, its portable entry, renderer and regenerated dossier.
10. Pandects, its portable entry, renderer and regenerated catalogue.
11. Tabularium and its portable entry.
12. First-party Hexaemeron Markdown.
13. Root and global Markdown, including the root README.

This is the selected option. It is the cheapest to comprehend because each PR maps
to a stable ownership boundary and proves its own source-preservation contract.
The serial base also prevents concurrent edits to `audit/AUDIT.md` and shared
portable-skill tests.

### Generated formatter and CI gate

Build a repository formatter that rewrites every Markdown file and install it as a
required check. This would make later enforcement cheap, but a formatter cannot
decide which counterexample or establishment limit carries the evidence. It also
violates the explicit ban on a permanent Brevitas command or CI gate.

### Parallel per-plugin branches

Rewrite plugin families concurrently and reconcile the shared files at the end.
This shortens elapsed drafting time, but every branch appends the same audit log,
and late merges would compare sources from different bases. The reconciliation
cost is higher than the time saved.

## Risk register seed

- Protected text boundary: an over-broad rewrite changes vendored or legal bytes.
  Mitigation: entry-ref path inventory, protected byte ranges, SHA-256 checks after
  every step and a final full-tree comparison.
- Evidence boundary: `--source` covers token classes but not semantic
  counterexamples, reproduction order or establishment limits. Mitigation: source
  diff plus a manual audit round that names any claim it could not establish.
- Digest boundary: rewriting a Brevitas original fixture or the Lazarus README
  invalidates recorded provenance. Mitigation: the four named refusal digests are
  checked before commit and after merge.
- Generator boundary: hand-editing a rendered dossier or catalogue creates a
  second source of truth. Mitigation: edit the renderer, regenerate, and require
  the byte-for-byte renderer tests.
- Version boundary: changing ledger layout can lose a history field or make a
  generation move appear to advance a frontier. Mitigation: adapt both evolution
  parsers, preserve all six history fields, recompute no frontier digest, and test
  generation-axis rules.
- Link boundary: shortening prose can remove anchors or move a relative link out
  of scope. Mitigation: run all link checks and keep Ariadne and Tabularium's only
  external exception equal to the resolved shared `VERSIONING.md` path.
- Command boundary: collapsing install and usage material can erase required flags
  or working-directory assumptions. Mitigation: compare every backticked command
  with its source and exercise documented proof paths where the plugin suite does
  not already do so.
- Arithmetic boundary: the pass depends on counts of 159, 161, 43, 300, 15, 13 and
  the 3-by-3 table threshold. Mitigation: derive corpus and line counts from Git and
  the filesystem; do not maintain them by hand in a separate tracked manifest.
- GitHub boundary: fetch, push, checks, labels and merges are external calls. A
  stale base or rejected gate can make later receipts false. Mitigation: fetch
  before every step, read each PR back, wait for required checks and halt on any
  rejected external transition.
- Credential boundary: the existing GitHub session can publish and merge. No
  document or receipt needs identity or credential material. Mitigation: never
  print or persist tokens; record only repository, branch and SHA evidence.
- Review boundary: the root README reduction can remove the only copy of an
  instruction. Mitigation: route detail to canonical plugin READMEs, preserve the
  selection boundary, and prove every local link after the line cap is met.
- Scope boundary: terms such as “attribution” occur in non-legal technical prose.
  Mitigation: protect exact operative passages rather than freezing every lexical
  match, and audit the protected-range manifest before step 1.

No contract arithmetic, custody flow, upgrade proxy or on-chain external call is
changed. Those security-suite surfaces remain outside this Markdown-only delivery.

## Glossary

- Batch entry ref: the fetched `origin/main` commit from which one step branches.
- Canonical skill: the plugin `SKILL.md` named by a portable `.agents/skills/`
  entry.
- Corpus: tracked Markdown included by the path and filename rules.
- Evidence refusal: a logged decision to keep a digest- or provenance-bound file
  byte-identical instead of forcing structural compliance.
- Evidence token: an address, transaction hash, `file:line` reference or numeric
  token mechanically compared by Brevitas.
- Establishment limit: an explicit statement that a fact, property or conclusion
  could not be established.
- Frontier digest: SHA-256 over a skill's status, revision, current frontier and
  Next Fiat job under `VERSIONING.md`.
- Generation change: a document, renderer or packaging improvement that changes
  the middle version counter without advancing the frontier.
- Protected passage: an exact byte range containing operative licence, copyright,
  attribution, legal terms, warranty or liability text.
- Source snapshot: the ignored entry-ref copy passed to Brevitas `--source` after
  a rewrite.
- Zero-finding round: an audit round that states what was checked and that no
  finding survived, without an undersized finding table.

## Sources

Repository sources:

- `AGENTS.md`: repository boundaries, test commands and Agent Skills validation.
- `README.md`: 847-line entry document, plugin selection text and repeated usage
  material.
- `audit/AUDIT.md`: 902-line shared audit history and current table format.
- `plugins/brevitas/skills/brevitas/SKILL.md`: evidence precedence, budgets,
  exclusions and pass order.
- `plugins/brevitas/skills/brevitas/scripts/brevitas.py`: fail-closed rules and
  `--source` token extraction.
- `plugins/brevitas/skills/brevitas/evals/cases/*/case.json`: three pinned source
  fixture digests.
- `plugins/lazarus/examples/aave-v4-spoke-v0/manifest.json`: the README component
  length and SHA-256 binding.
- `tests/test_evolution_contract.py` and
  `plugins/hexaemeron/tests/test_evolution.py`: ledger fields and axis rules.
- `plugins/hexaemeron/skills/VERSIONING.md`: marketplace version and frontier
  contract.
- `plugins/probitas/scripts/probitas_lib/render.py` and
  `plugins/pandects/scripts/pandects_lib/render.py`: generated Markdown sources.
- `.hexaemeron/state.json`: topic, base, waiver, controller configuration and
  deferred marketplace reassessment for this run.

External sources:

- [CommonMark 0.31.2](https://spec.commonmark.org/0.31.2/): Markdown block and
  inline syntax used by the corpus.
- [markdownlint](https://github.com/DavidAnson/markdownlint): named Markdown style
  rules and configuration precedent.
- [Vale documentation](https://vale.sh/docs/): configurable prose-lint precedent.
- [Agent Skills specification](https://agentskills.io/specification): portable
  skill directory and metadata contract.
