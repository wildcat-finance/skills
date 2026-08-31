# Study: restore the Shoggoth public front door and demo frontier

Assuming, unless corrected:

1. The working base is the current public `origin/main`, commit
   `a2b634d8e039af988bf30c8316defccf70071d8d`. `git ls-remote origin main`,
   `git rev-parse HEAD`, and `git rev-parse origin/main` all returned that
   commit on 31 August 2026.
2. “Front-facing” means the maintained human entry surface: `README.md`,
   `INSTALL.md`, `FUTUREPROOFING.md`, `SHOGGOTH.md`, `PROMISE_MACHINE.md`,
   `docs/how-to-help-shoggoth.md`, `docs/fiat-in-plain-english.md`,
   `docs/the-promise-machine-explained-properly.md`, all 17 first-party plugin
   `README.md` files, and the generated contributor PDF. Agent contracts,
   canonical `SKILL.md` files, ADRs, audits, historical studies, runbooks, and
   specimens are factual sources, not surfaces to restyle. Factual changes
   still propagate to any canonical contract or host metadata that owns the
   fact.
3. “All headers need All Caps” applies to every ATX heading on that maintained
   human entry surface. It does not rewrite headings in normative agent
   instructions, audit evidence, ADR history, or specimens.
4. The current authoritative roster is the discovered repository topology:
   17 plugin manifests and 26 `SKILL.md` directories carrying an
   `EVOLUTION.md`. The identity split is therefore 17 canonical/domain agents
   and 9 Hexaemeron phase agents, 26 governed first-party agents in all. The
   four Fiat workers and five vendored Pashov skills are described separately
   and are not added to that member count.
5. Dokimasia is pending because the user says it is pending. No occurrence,
   plugin manifest, governed skill, issue, pull request, or public contract was
   found in the current repository or the public `wildcat-finance` GitHub
   organisation. The prototype may foreshadow the name and pending state once,
   but it may not invent a function, count it as a member, or promise a route.
   A canonical contract or other user-supplied authoritative record is the
   resolver for any richer description.
6. A “real-data demonstration” is an executable path over preserved bytes
   originating in an actual chain, protocol, repository, audit, or production
   run. Its source identity, digest or chain anchor, command, expected result,
   and non-claim must be checkable offline. A demo with a constructed corpus,
   an unrelated target corpus, or a synthetic substitute is classified as
   `mixed` or `constructed`, not promoted by good prose.
7. The old “So, You Want To Build God?” front door supplies voice and ordering,
   not current facts. Its 15-plugin/24-skill counts, old install command, long
   warning block, and historical Atlas details are not copied forward.
8. The prototype couples two capabilities deliberately: public claims and
   governed demonstration evidence. A prose-only front door would immediately
   drift again; a demo registry with no humane front door would not answer the
   user. The implementation may split them into auditable steps, but the final
   demo proves the joined path.

## 1. Problem statement

The public front door currently reads like a complete technical catalogue
placed before the invitation. A new reader meets 2,655 words, five abstract
capability narratives, a full roster, repeated links, and Promise Machine
detail before reaching `## Contribute` at line 289 of 396, about 73% of the way
through the file. Fifteen plugin or skill targets are linked twice. The
engineering roster gives Protasis a much larger paragraph than its neighbours.
Anamnesis alone receives a 960-pixel-wide portrait inside the root roster, even
though the collective identity contract places a member portrait on that
member's own landing page. The visible headings are sentence case. The prose
also says 16 plugins and 25 governed skills after Anamnesis made the current
topology 17 and 26.

The immediate users are:

- a curious person who needs to understand what the Shoggoth is in one breath;
- a potential contributor who needs the invitation and safe route before the
  machinery;
- an engineer looking for one real operation with checked evidence rather than
  a list of possible compositions;
- an existing operator who needs the full technical map later, without losing
  the Promise Machine, identity, installation, and authority boundaries; and
- a maintainer who needs public claims to stop drifting away from what the
  repository can actually demonstrate.

A working prototype has four joined outcomes.

First, the root README becomes a front door, not the building. It keeps the
Shoggoth portrait, opens with no more than 150 plain words explaining what the
collective is and does, then puts `## SO, YOU WANT TO BUILD GOD?` and the
external-contributor route within the first 220 words. The exact old chirp,
“Ask the Atlas for a number. Pick your harness. Finish what you start.”, is a
tone anchor worth retaining. At least one additional short, self-aware line
appears before the first technical section. The first mention of the Promise
Machine contract and the first roster/catalogue link come after contribution
and demonstrations. The file is at most 1,400 words, no identical link target
appears twice, and it does not inline the complete governed roster.

Second, `## WHAT CAN IT DO?` shows three executable real-data cards, each with
one command or one governed runner invocation, a named preserved source, one
concrete observed result, and one sentence saying what the result does not
establish. The initial candidates are:

1. Anamnesis rebuilding the committed pilot from real public audit records and
   checking both consumer projections;
2. Lazarus rebuilding and verifying the Goldfinch v1 Ethereum mainnet receipt
   fixture at block `0xc7da16`; and
3. Alexandria rebuilding `credit-history-v0` from preserved Goldfinch and
   Clearpool inputs through its checked release, index, query, and Probitas
   handoff.

The cards are accepted only if the new governed runner verifies them at the
integration tree. Lazarus is not advertised as a frictionless macOS command
until the current `/var` to `/private/var` temporary-directory failure is
closed by the runner or the owned Lazarus path. Berean remains `mixed` today
because its chain reads are real but its document corpus is a demonstration
corpus rather than captured Wildcat material. Synkrisis remains `constructed`
until its held production-cohort job lands. Those distinctions appear in the
technical frontier, not under a “real data” heading.

Third, each of the 26 governed first-party skills gains an independently
versioned demonstration ledger beside its `EVOLUTION.md`. The ledger carries a
closed executable record and a separate `Next demonstration job`. A new
`demo-frontier` lane can fund real-data proof without replacing or silently
advancing the skill's behaviour frontier. When one existing `{skill}-next` job
will also satisfy the demo frontier, both ledgers may point to the same issue
and Fiat run; each ledger still advances only against its own acceptance
evidence. A demo-only job uses a governed `{skill}-demo` title and
`demo-frontier` label after the queue decision lands. Kronos ranks this lane
only when explicitly asked for the demo lane; its current behaviour-frontier
operation remains unchanged.

Fourth, the rest of the maintained public surface is reconciled rather than
blindly rewritten. All public headings use the agreed all-caps house style;
all mutable count claims derive from the discovered 17/26 topology; the full
technical catalogue lives once in `FUTUREPROOFING.md`; Anamnesis's root portrait
is removed while its contextual member-page portrait and character section
remain; its stale “source admission only” README paragraph is corrected to the
shipped whole seed path; Dokimasia is foreshadowed as pending without a promise;
the contributor guide and PDF retain the external-human identity boundary; and
the portable package is tested through `wildcat-finance/skills-runtime` rather
than by recommitting the ignored generated runtime.

The proving path for the joined prototype is:

```bash
python3 scripts/check_public_front_door.py --root .
python3 scripts/demonstrations.py check --root .
python3 scripts/demonstrations.py run --showcase \
  --report .hexaemeron/reports/showcase.json
python3 scripts/run_checks.py --full
```

The first command proves ordering, word and link budgets, all-caps public
headings, one full technical catalogue, portrait placement, derived counts,
and the bounded Dokimasia statement. The second discovers exactly the same 26
governed skills as the existing evolution tests and checks every demonstration
ledger. The third runs only entries marked `real-data` and named by the root
public-demo list, with network denied by default, and fails if a card, record,
source, command, expected result, or non-claim disagrees. The final checked runner
closes the repository's normal dependency map.

## 2. Prior art

### Current repository evidence

`README.md` is 396 lines, 2,655 words, and 20,434 bytes at the starting ref.
The relevant H2 sequence is `What can it do today?` at line 23, `How the
collective works` at 114, `Meet the collective` at 149, `Try it` at 255, and
`Contribute` at 289. Its 15 repeated link targets and the anomalous Anamnesis
image are direct, counted facts. `tests/test_marketplace_prose.py` currently
requires the problem: it hard-codes the sentence-case headings and 25-member
text, demands that `README.md` link every plugin, and demands all 26 governed
skill targets plus four workers and five upstream skills inside the root
roster. The test must move completeness to the technical catalogue and test
the front-door properties instead.

The last major README before the current rewrite is `daa64e5f^:README.md`, 421
lines and 3,428 words. It puts `## So, You Want To Build God?` at line 40 and
opens that section with the three short Atlas sentences above. It then becomes
too long itself. Its useful prior art is the confident, self-aware invitation
and the order (identity, contribution, explanation), not its old counts or bulk.

The maintained surface is already layered in principle. `INSTALL.md` owns
host-specific installation and publication; `FUTUREPROOFING.md` owns the deep
member-by-member present/evidence/future map; `docs/how-to-help-shoggoth.md`
owns the detailed contributor route; `docs/fiat-in-plain-english.md` owns the
delivery explanation; and `docs/the-promise-machine-explained-properly.md`
owns the longer Promise Machine explanation. The root duplicates too much of
all five instead of introducing and linking them.

The count sources agree even though the prose does not. Both marketplace
manifests contain 17 plugins. Discovery finds 26 `EVOLUTION.md`-backed skills:
17 canonical plugin entry skills, including Fiat as Hexaemeron's entry, and 9
additional Hexaemeron phase skills. Stale 25/16 text is present in
`README.md`, `SHOGGOTH.md`, `docs/how-to-help-shoggoth.md`,
`docs/the-promise-machine-explained-properly.md`, and
`.agents/skills/promise-machine/SKILL.md`. Counts must be derived by the test,
not replaced with a new unguarded literal.

Three real-data demo paths already exist:

- `plugins/anamnesis/docs/demo.md` names the exact whole-path command. It builds
  the pilot twice, checks every component byte, verifies the committed release,
  reads Elenchus and Synkrisis views, and states that it does not prove corpus
  completeness, finding truth, or remedy effectiveness.
- `plugins/lazarus/examples/goldfinch-v1/demo.py` is the audited offline
  Ethereum mainnet path. It reconstructs 224 contiguous receipts, target index
  `0xbf`, 110 target logs, and the exact five-log projection, while transaction
  hash attribution remains recorded RPC metadata rather than a proved header
  identity.
- `plugins/alexandria/examples/credit-history-v0/README.md` names the root-safe
  build and verify commands. The release contains 522 events and 31 position
  observations; the query contains 11 Clearpool events; Probitas emits 11
  transaction records; and the record says Goldfinch is partial for 25
  unsupported native records, Clearpool finality is unknown, and neither
  source authenticity nor canonical-chain finality is established.

Anamnesis's public README contradicts its own frontier and demo: the top says
the whole seed path ships, while the bottom says only source admission exists
and curation/release refuse. That is an in-scope factual repair. The top-level
Anamnesis picture is not needed: `SHOGGOTH.md` says a member's own landing page
is the canonical portrait home, and `plugins/anamnesis/README.md` provides a
long contextual `Character` section immediately below that image.

All 26 evolution ledgers already provide one behaviour frontier. The versioning
contract defines its line and digest as normative inputs, and Kronos discovers that
shape. Berean's current ledger and issue #411 explicitly require captured
Wildcat documents and market reads. Synkrisis's ledger explicitly requires a
captured production cohort. Tabularium issue #398 requires an offline Ethereum
USDC specimen. These are useful real-data jobs, but forcing every demo gap into
the one behaviour frontier would displace unrelated held work and rewrite
existing digests. That is the case for a parallel demonstration lane.

The generated Agent Skills payload is no longer tracked here. Current
`INSTALL.md` correctly points at `wildcat-finance/skills-runtime`, and
`.agents/skills/promise-machine/runtime/` is ignored. Source changes are tested
by building a package into a disposable output through
`scripts/portable_promise_machine.py package --out <path>` and by the checked
runner; `portable_promise_machine.py check` correctly fails when aimed at the
absent source-tree runtime. Issue #971 remains open for the now-stale Fiat
generator-aggregate entry. This run does not quietly solve that controller
issue; it avoids relying on the stale command and carries #971 forward by URL.

### Last two merged pull requests that changed the subject

1. [PR #1003](https://github.com/wildcat-finance/skills/pull/1003), “docs:
   rewrite Shoggoth as a contributor-ready crypto R&D collective”, merged as
   `1c1137898bce9086c34310bd29b5cf8a889f800c` on 31 August 2026. It changed
   the entire maintained public surface, all plugin landing pages, source and
   generated Promise Machine prose, tests, metadata, and the contributor PDF.
   Its stated goal was a non-technical entry before contracts, but the result
   placed the contribution route after the complete roster. Its PR body also
   froze the now-stale 16-plugin/25-skill count. No reviews, comments, or
   `Carried forward` section exist. Carry forward the intended progressive
   disclosure; refuse the duplicated catalogue, stale count, and length.
2. [PR #1037](https://github.com/wildcat-finance/skills/pull/1037), “Add
   Anamnesis character to collective readmes”, merged as
   `42ac62a0e472402db93e5ff8ee7fcb6d8cf98a6d` on 31 August 2026. It added
   the portrait to the member README, skill, generated runtime, and root
   README. Its source is mascot-imagegen-kit PR #10 and its public derivative
   is 960 by 640. No reviews, comments, or carryover block exist. Keep the
   sourced portrait at Anamnesis's own contextual landing page; remove the
   uncontextualised root insertion the user rejected.

### In-scope audit records

`python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .`
exited zero before any synopsis was used. Every source/synopsis digest in the
repository was current. Modern round records below were read through their
verified synopses. The legacy Shoggoth contributor-guide section was read
directly from `audit/AUDIT.md:7832` because its root synopsis flags missing
legacy fields and omits the finding records. Those missing legacy fields stay
unknown.

- **Shoggoth contributor guide, `audit/AUDIT.md:7832-7995`, source read.**
  Findings `SCG-S1-R1-01`, `SCG-S1-R1-02`, `SCG-S2-R1-01`,
  `SCG-S2-R1-02`, and `SCG-S3-R1-01` were fixed; later rounds found nothing
  and no leads remained. The reviewed concerns were selection overclaim,
  attribution, wave drift, duplicate work, scope widening, mascot identity,
  issue authority, and binary review. Solidity security work was waived. The
  record preserves two obligations here: external contributors keep their own
  authorship, and regenerated public images/PDFs receive a committed-tree
  Horos scan plus rendered visual inspection.
- **Primer removal,
  `audit/rounds/fiat-975-remove-the-child-or-golden-retriever-primer.synopsis.md`,
  synopsis read.** Verdicts by round were `null`, `unguarded`, `null`.
  `S1-R1-01` was accepted and filed as #978 because repairing an already
  receipted split trailer required history rewrite; `S1-R2-01` was fixed;
  `S1-R2-02` was accepted because the receipted runbook omitted the advisory
  Horos candidates file. Security work was waived. The product choice to
  remove the primer without replacement and the rendered appearance of the
  resulting README were explicitly **not checked**. This run does not restore
  the condescending child/golden-retriever framing or deleted assets. It fills
  the admitted entry gap with a direct adult explanation and adds rendered
  README review.
- **Large generated prose packet,
  `audit/rounds/fiat-972-let-a-prose-phase-survive-a-large-generated.synopsis.md`,
  synopsis read.** Both rounds had a `null` verdict and no findings. It proved
  that authored prose can be selected while large generated-copy deletion is
  filtered, and that a missing generated runtime is current topology. It did
  not establish that the 4,096-path ceiling is ideal or that Scribe works at
  that maximum. Those remain outside this prototype; use the existing checked
  packet and package builder rather than hand-editing a runtime.
- **Skills-runtime siting and move,
  `fiat-940-...synopsis.md` and `fiat-949-...synopsis.md`, synopses read.**
  #940 verdicts were `passed`, then `null`; `S1-R1-01` was fixed. Its package
  sizing, symlink, and ref-less install observations were superseded by the
  separate runtime repository. #949 verdicts were `guarded/null` for each of
  three steps. `S1-R1-01`, `S1-R1-02`, `S2-R1-01`, `S2-R1-02`, and
  `S3-R1-01` were fixed; `S3-R1-02` was left to issue #971. Its remaining
  leads are publisher authenticity, scheduled-job observation, copy ordering,
  and the generator aggregate. They are not front-door facts this prototype can
  repair.
  The public install link must remain `wildcat-finance/skills-runtime` and
  #971 remains the named carryover.
- **Anamnesis seed,
  `audit/rounds/fiat-anamnesis-source-bound-curation-and-release-of-a.synopsis.md`,
  synopsis read.** Verdicts were `guarded`, `guarded`, `passed`, `null` in
  Step 1; `guarded`, `guarded`, `null` in Step 2; and `guarded`, `passed`,
  `null` in Step 3. Findings `S1-R1-01` through `S1-R1-03`, `S1-R2-01`,
  `S1-R2-02`, `S1-R3-01`, `S2-R1-01` through `S2-R1-04`, `S2-R2-01`,
  `S2-R2-02`, `S3-R1-01`, `S3-R1-02`, and `S3-R2-01` were fixed. Covered
  work includes rights admission, byte drift, evidence strengthening,
  duplicate and fix-state separation, many-to-many relations, private egress,
  partial release, taxonomy drift, cohort leakage, and adapter overreach.
  Security work, source-lawfulness, and the truth/completeness of the selected
  41 findings were not established. Leads retained here are exact: the
  unknowns map is digest-covered but needs recuration to establish its
  correctness; staged promotion has a narrower directory-race guarantee than
  descriptor-held promotion; one path refusal reads like a path rule rather
  than a manifest rule. The root card repeats the demo's non-claim and does not
  turn a rebuild into corpus truth.
- **Lazarus Goldfinch receipt proof,
  `audit/rounds/fiat-383-prove-receipts-against-the-captured-header-s.synopsis.md`,
  synopsis read.** The record has 33 rounds. Step 1 verdicts were
  `guarded/inconclusive/guarded/guarded/guarded/guarded/null`; Step 2 was
  `guarded/guarded`; Steps 3 and 4 were guarded in all eight rounds; Step 5
  was guarded in rounds 1 through 7 and `null` in round 8. The initially open
  `S1-R1-01` was closed by narrowing transaction hashes to recorded RPC
  metadata, and `S2-R1-03` was closed by a receipted amendment. Every other
  finding was fixed and guarded: `S1-R1-02`, `S1-R2-01`, `S1-R3-01`,
  `S1-R4-01`, `S1-R5-01`, `S1-R6-01`, `S1-R6-02`; `S2-R1-01`,
  `S2-R1-02`; `S3-R1-01` through `S3-R1-04`, `S3-R2-01` through
  `S3-R2-04`, `S3-R3-01` through `S3-R3-05`, `S3-R4-01` through
  `S3-R4-03`, `S3-R5-01`, `S3-R5-02`, `S3-R6-01` through
  `S3-R6-07`, `S3-R7-01`, `S3-R8-01`, `S3-R8-02`; `S4-R1-01`
  through `S4-R1-04`, `S4-R2-01` through `S4-R2-04`, `S4-R3-01`
  through `S4-R3-03`, `S4-R4-01` through `S4-R4-04`, `S4-R5-01`
  through `S4-R5-04`, `S4-R6-01` through `S4-R6-03`, `S4-R7-01`,
  `S4-R8-01`, `S4-R8-02`; and `S5-R1-01` through `S5-R1-05`,
  `S5-R2-01`, `S5-R2-02`, `S5-R3-01`, `S5-R3-02`, `S5-R4-01`
  through `S5-R4-03`, `S5-R5-01` through `S5-R5-04`, `S5-R6-01`
  through `S5-R6-03`, and `S5-R7-01` through `S5-R7-03`. Final coverage
  spans receipt-set completeness, fork-aware encoding, header/root/index/log
  binding, recorded-only metadata, evidence counts, legacy compatibility,
  provider and file bounds, atomic capture/release, Ariadne parity, and public
  prose. A new live RPC capture, transaction-trie expansion, empty-block case,
  canonical-chain and provider-independence claims, hosted CI, publication,
  and controller mutation were not checked. Round 8 retained no admissible
  unresolved lead. The root card therefore names the fixed block and receipt
  proof and repeats the canonical-chain/provider-independence non-claim.
- **Alexandria/Probitas joined demo,
  `audit/rounds/fiat-391-unified-live-and-archive-collection.synopsis.md`,
  synopsis read.** Verdicts were `unguarded/null`, `passed/passed/null`,
  `guarded/null`, and `passed/null` across four steps. Findings `S1-R1-01`,
  `S1-R1-02`, `S2-R1-01`, `S2-R1-02`, `S2-R1-03`, `S2-R2-01`,
  `S3-R1-01`, `S3-R1-02`, `S3-R1-03`, `S4-R1-01`, and `S4-R1-02`
  were fixed. Coverage included row collapse, unrequested network, schema
  refusal, release identities, overlap attribution, gap counting, demo receipt
  drift, and Markdown injection. The final battery rebuilt and verified the
  Alexandria demonstration. Remaining leads are not erased: coverage fields
  have no common length ceiling; gates rely on the loader's coverage-list
  shape check; the archive-only unreached note remains terse because changing
  it changes pinned demo digests; an index venue unknown to the registry is
  dropped; and the Alexandria evolution citation is thinner than its Probitas
  sibling. The public card does not claim complete venue or source coverage,
  and any receipt-changing repair must advance its own evidence.

### Organisation prior art

The public Shoggoth Wave Atlas demonstrates useful provenance fields: a
selected source mode, source revision, build revision, and generated time. It
selects open issue work; it does not prove that a skill has a real-data demo.
The existing `held-job` label and `{skill}-next` issues are behaviour-frontier
work. They remain authoritative for their lane. A new demo lane should borrow
the explicit revision and evidence shape without pretending the Atlas already
governs demonstration status.

### Outside prior art

- GitHub's “About READMEs” documentation says a repository README should tell
  readers why the work is useful, what they can do with it, and how to begin;
  only start-here material belongs there, with longer documentation elsewhere.
- Diátaxis separates tutorials, how-to guides, reference, and explanation and
  recommends a short orientation that links into the mode a reader needs. That
  supports moving the full roster, install matrix, and Promise Machine
  explanation behind the front door rather than deleting them.
- NISO RP-31-2021 supplies a vocabulary for distinguishing available,
  functional, and reproduced research artefacts. The Systems Research
  Artifacts guidance similarly expects exact automated workflows and separates
  “it runs” from “it reproduces a result”. Neither taxonomy maps perfectly to
  these skills, but both reject one vague `demo` label. The Shoggoth status set
  keeps the source-specific distinction explicit: `real-data`, `mixed`,
  `constructed`, `absent`, or `not-applicable` with a reason.

## 3. Constraints and non-goals

### Constraints

- Start from exact ref `a2b634d8e039af988bf30c8316defccf70071d8d`.
- Use the exact CPython `3.14.6` named by `.python-version` and the standard
  checked runner. Do not substitute an ambient interpreter.
- Preserve the Promise Machine `promise-machine/v1` evidence boundary and
  every plugin's `AGENTS.md` ownership boundary.
- Preserve the external-human contribution rule: the contributor remains
  “not Shoggoth”, keeps their own Git author, signing identity, and GitHub
  account, and does not receive private Shoggoth credentials.
- Preserve `wildcat-finance/skills-runtime` as the portable installation source.
  Build and test generated packages in disposable directories; do not commit
  `.agents/skills/promise-machine/runtime/` here.
- Preserve all existing `EVOLUTION.md` frontier lines and digests unless this
  run actually completes that exact behaviour frontier. The demonstration lane
  is additive and independently versioned.
- Preserve historical audits, studies, runbooks, ADR bodies, specimens, and
  content-addressed releases. Public corrections describe current truth; they
  do not rewrite old evidence.
- Discover governed skills and plugin counts from the tree. A new governed
  skill must fail coverage until its current count and demonstration ledger are
  reconciled.
- Keep every root claim weaker than or equal to its selected demonstration
  record. A successful runner cannot strengthen source completeness, chain
  finality, finding truth, remedy correctness, protocol safety, or underwriting
  merit.
- Treat demonstration manifests, sources, subprocess arguments, and output
  paths as untrusted. Execute argv arrays without a shell, deny network by
  default, bound bytes/time/output, and write reports atomically below an
  operator-selected directory.
- The new public-heading style is checked only over the explicit maintained
  surface. It must not churn operational contracts and history to satisfy an
  aesthetic rule.
- Public images and the contributor PDF remain Horos-classified binary assets.
  Regenerate and visually inspect the PDF after source prose changes.

### Non-goals

- Do not implement Dokimasia or infer what it will own.
- Do not make every governed skill real-data-ready in this first prototype.
  Classify all 26 honestly, prove the initial three, and leave an explicit demo
  frontier for the rest.
- Do not turn a demo into a certification, security badge, maturity score, or
  protocol recommendation.
- Do not replace the current behaviour frontier, Wave Atlas, Promise Machine,
  or Fiat controller with the demonstration lane.
- Do not automatically open, close, or publish GitHub issues in the checker.
  Queue changes and issue filing remain explicit, reviewed actions.
- Do not solve issue #971, the Lazarus provider/canonical-chain limits, the
  Alexandria coverage leads, Berean's held Wildcat release, or Synkrisis's held
  production cohort unless a runbook step explicitly takes that work and its
  owner contract admits it.
- Do not restore the deleted child/golden-retriever primer, its assets, or its
  patronising register.
- Do not flatten the technical documents into a second short README. The
  progressive path is easy first and technical later, not easy only.
- Do not hand-edit generated portable copies or historical package bytes.

## 4. Design options

The closed selection record is `.hexaemeron/design-evidence.json`. Every cell
below is asserted by a named report under `.hexaemeron/reports/`; the table is
the source those report commands check. `complete-ledger-coverage` means every
discovered governed skill has an explicit demonstration state.
`preserves-evolution-digests` means the construction adds no field to the
existing `EVOLUTION.md` frontier grammar. `stale-claim-blocked` means a public
real-data card cannot pass when its demo record is absent, downgraded, or fails
verification. `update-owner-hops` counts independent ownership locations a
maintainer must edit to advance one skill's demo. `global-registry-files`
counts central inventory files whose merge surface grows with every skill.

```design-properties
editorial-only | false | true | false | 0 | 0
central-registry | true | true | true | 2 | 1
evolution-embedded | true | false | true | 1 | 0
per-skill-demo-ledger | true | true | true | 1 | 0
```

### Candidate: editorial-only

Rewrite the public prose, link the three current commands, and rely on ordinary
frontier prose to keep them current. This has the smallest implementation and
no new format. It cannot discover omitted skills and has no refusal when a
source, demo command, classification, or public card drifts. It fails the
correctness and recovery gates. It would produce the same kind of ungoverned
rewrite that created the current problem.

### Candidate: central-registry

Put one suite-level registry under the repository root, with an entry for every
governed skill, and make the root README and runner consume it. This gives
complete coverage and fail-closed public claims while leaving evolution
digests alone. It makes a central file the owner of facts that belong to 26
skills, creates a permanent merge hotspot, and requires a maintainer to update
both the skill's own surface and the central registry. It survives the hard
gates but loses both comparative measures to the selected design.

### Candidate: evolution-embedded

Add demonstration status, source, commands, and a demo frontier directly to
every `EVOLUTION.md`. The facts stay beside the owning skill and require one
owner hop. The existing versioning grammar hashes the current frontier and is
consumed by Kronos, marketplace tests, issue review, and Fiat version
resolution. Adding a second frontier to that record changes the meaning and
digest of every skill's established behaviour lane. It fails compatibility.

### Candidate: per-skill-demo-ledger

Add `DEMONSTRATION.md` beside each governed `EVOLUTION.md`. Each file has a
human ledger plus one fenced, strict `shoggoth-demonstration/v1` object. The
object names the skill, status, source class and identity, source digests or
chain anchor, network policy, argv arrays, expected observations, public claim
id, non-claim, and per-command timeout. The ledger independently carries
demonstration version, frontier status/revision, current demonstration, next
demonstration job, and history digest.

A suite checker discovers the same 26 governed skill directories as the
evolution tests and requires exactly one record per directory. A runner opens
only the selected record, rejects symlinks and non-regular sources, executes
argv without a shell in a private temporary root, denies sockets unless the
record's capture phase explicitly allows a named endpoint, and emits a closed
report. `check-public` requires each root demo marker to bind a record digest
whose current status is `real-data`; it never grades free-form voice.

This candidate adds local files but no global inventory: discovery is the
registry. One skill owner advances one demonstration ledger. Existing
`EVOLUTION.md` bytes and Kronos behaviour ranking remain intact. A new explicit
demo-lane operation reads only demonstration ledgers; a behaviour job may
co-deliver a demo by satisfying both independent records. It is the unique
non-dominated candidate after the hard gates and is selected.

The selected record must use these closed status meanings:

- `real-data`: every material input is a preserved real-world source and the
  registered offline path reproduces the named result;
- `mixed`: at least one real-world source is present, but a constructed or
  target-mismatched component is material to the result;
- `constructed`: the whole executable example is built from fixtures or model
  records created for the example;
- `absent`: no complete executable demonstration exists; and
- `not-applicable`: the owner gives a checked reason why a real-data input
  would not make sense for that skill. This is not a synonym for unfinished.

The root README is hand-written for voice. It contains one hidden marker per
demo card binding the skill id, claim id, and demonstration-record digest. The
checker owns structural truth for status, source, command, result, non-claim,
and link uniqueness. Imprimatur, Vulgate, Brevitas, rendered review, and human
audit own the prose. Generated text is not allowed to sand the Shoggoth back
into generic product copy.

## 5. Risk register seed

```risk-register
claim-without-demo | root capability cards against per-skill demonstration records | a missing, stale, mixed, constructed, or failing record blocks a real-data public claim
demo-class-inflation | status assigned to preserved or constructed inputs | every material input has a source class and a mixed component prevents real-data status
source-drift | preserved chain, audit, repository, and lending inputs | declared byte digests or chain anchors are checked before a command runs
frontier-lane-collision | EVOLUTION.md behaviour state beside DEMONSTRATION.md state | advancing either lane leaves the other digest and held job unchanged unless both accept the same evidence
count-drift | manifests and governed skill discovery against public count prose | tests derive 17 canonical and 26 governed agents and reject stale mutable literals
generated-copy-drift | source prose against the separately published skills-runtime package | a disposable package rebuild and package tests replace hand edits to the ignored runtime
external-data-egress | demos that could reach RPC, HTTP, models, or credentials | network is denied by default and any capture exception names an allowlisted endpoint and secret environment without recording its value
subprocess-execution | argv loaded from a demonstration record | strict argv arrays run without a shell under timeout and bounded output in a private execution root
partial-demo-output | demonstration build and report destinations | existing outputs are refused and new outputs stage privately then publish atomically or remain visibly incomplete
front-door-regression | root order, length, links, headings, and catalogue boundary | a dedicated checker guards the 150-word intro, 220-word contribution position, 1400-word file, unique link targets, and one technical catalogue
pending-member-overclaim | Dokimasia mention against absent current contract | the name appears once as pending, carries no capability or route, and is excluded from the discovered count
portrait-inconsistency | collective root imagery against member landing portraits | root admits only collective art while member portraits remain on contextual member pages
historical-record-rewrite | current prose corrections beside audits, ADRs, fixtures, and old runbooks | checks constrain edits to mutable surfaces and preserve digest-bound or append-only evidence bytes
demo-skip-as-pass | optional dependency or missing specimen during public demo execution | a registered public demo missing its command, source, or dependency fails rather than skips
real-data-nonclaim-loss | concise root cards derived from detailed demo boundaries | each card binds and displays the record's non-claim before public checks pass
queue-duplication | demo frontier issue against an existing behaviour frontier issue | the ledger points to one canonical issue and reuses it when both acceptance sets can be satisfied by one run
visual-surface-drift | Markdown and regenerated PDF after mechanical heading and layout changes | rendered root and every PDF page are inspected for hierarchy, overflow, anomalous images, and broken links
```

Warden must enumerate every id. A concern can be not applicable only with the
candidate-specific reason; “docs only” does not dispose of the demo runner,
generated package, queue, or binary PDF boundaries.

## 6. Glossary seeds

**Front door.** The bounded root README that explains, invites, demonstrates,
and then links deeper; it is not the complete catalogue.

**Maintained public surface.** The explicit current source documents and PDF
listed in assumption 2, excluding historical and agent-operational records.

**Governed skill.** A first-party skill directory carrying both `SKILL.md` and
`EVOLUTION.md`; discovery finds 26 at the starting ref.

**Canonical/domain agent.** The one canonical entry skill for each shipped
plugin, with Fiat as Hexaemeron's entry; discovery finds 17.

**Phase agent.** One of the nine additional governed Hexaemeron disciplines,
not an extra plugin.

**Real-data demonstration.** An executable, source-bound, reproducible path
whose material inputs came from a real chain, protocol, repository, audit, or
production run.

**Mixed demonstration.** An executable path in which real data and a material
constructed or target-mismatched input coexist.

**Demonstration ledger.** One skill-owned `DEMONSTRATION.md` containing the
current evidence record and its independent demo frontier/history.

**Behaviour frontier.** The existing `EVOLUTION.md` held job that changes what
a skill can do.

**Demo frontier.** The independent held job that improves what a skill can
show over real data without pretending its behaviour changed.

**Co-delivery.** One Fiat run satisfying both a behaviour frontier and a demo
frontier while each ledger verifies and advances independently.

**Public demo set.** The small set of `real-data` records named by root capability
cards and run by the joined proving command.

**Claim id.** A stable identifier joining one hand-written public card to the
bounded claim and non-claim in its demonstration record.

**Pending member.** A name acknowledged by the user but absent from current
governed topology; it has no counted membership or capability promise.

## 7. Sources

Repository and history:

- `README.md`, especially lines 18-23, 114-149, 170-179, 210-241, 255, and
  289 at `a2b634d8e039af988bf30c8316defccf70071d8d`.
- `git show daa64e5f^:README.md`, especially the old line-40 contribution
  heading and opening.
- `tests/test_marketplace_prose.py`, including plugin discovery, hard-coded
  headings/counts, root plugin mapping, and complete-roster assertions.
- `.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json`, and
  all 26 `plugins/*/skills/*/EVOLUTION.md` files.
- `plugins/hexaemeron/skills/VERSIONING.md` and
  `plugins/hexaemeron/skills/kronos/SKILL.md` for the existing one-lane
  behaviour frontier.
- `SHOGGOTH.md`, especially current roster and portrait placement.
- `INSTALL.md`, `.gitignore`, `distribution/skills-runtime/sync.yml`,
  `scripts/portable_promise_machine.py`, and `tests/test_skills_sh_package.py`
  for the current external generated-package boundary.
- `plugins/anamnesis/README.md`, `plugins/anamnesis/docs/demo.md`, and
  `plugins/anamnesis/skills/anamnesis/EVOLUTION.md`.
- `plugins/lazarus/README.md`,
  `plugins/lazarus/examples/goldfinch-v1/demo.py`, and the v1 fixture/release.
- `plugins/alexandria/README.md` and
  `plugins/alexandria/examples/credit-history-v0/README.md`.
- `plugins/berean/skills/berean/EVOLUTION.md`,
  `plugins/synkrisis/skills/synkrisis/EVOLUTION.md`, and open issues
  [#411](https://github.com/wildcat-finance/skills/issues/411) and
  [#398](https://github.com/wildcat-finance/skills/issues/398).
- [PR #1003](https://github.com/wildcat-finance/skills/pull/1003) and
  [PR #1037](https://github.com/wildcat-finance/skills/pull/1037), including
  bodies, files, commits, reviews, and comments.
- [Issue #971](https://github.com/wildcat-finance/skills/issues/971), retained
  as a separate framework carryover.
- A repository search plus `gh search issues/prs 'Dokimasia
  org:wildcat-finance'`, both of which returned no result on 31 August 2026.

Audit evidence, with reading choice recorded in Section 2:

- `audit/AUDIT.md:7832-7995`, authoritative legacy contributor-guide source.
- `audit/rounds/fiat-975-remove-the-child-or-golden-retriever-primer.md` and
  its verified synopsis.
- `audit/rounds/fiat-972-let-a-prose-phase-survive-a-large-generated.md` and
  its verified synopsis.
- `audit/rounds/fiat-940-site-the-generated-skills-sh-payload.md` and its
  verified synopsis.
- `audit/rounds/fiat-949-move-the-skills-sh-payload-to-its-own-reposi.md` and
  its verified synopsis.
- `audit/rounds/fiat-anamnesis-source-bound-curation-and-release-of-a.md` and
  its verified synopsis.
- `audit/rounds/fiat-383-prove-receipts-against-the-captured-header-s.md` and
  its verified synopsis.
- `audit/rounds/fiat-391-unified-live-and-archive-collection.md` and its
  verified synopsis.

Organisation and outside sources:

- `wildcat-finance/shoggoth-wave-atlas` current README at commit
  `95a3fcf...`, for source/build revision and selection provenance, not demo
  proof.
- GitHub Docs, “About READMEs”:
  <https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes>.
- Diátaxis, “Start here”: <https://diataxis.fr/start-here/>.
- NISO RP-31-2021, “Reproducibility Badging and Definitions”:
  <https://www.niso.org/publications/rp-31-2021-badging>.
- Systems Research Artifacts guidance:
  <https://sysartifacts.github.io/eurosys2026/call> and
  <https://sysartifacts.github.io/cais2026/badges>.

## 8. Signals, and the questions behind them

This has an unattended surface: CI public-demo execution and any explicitly
started demo-frontier ranking loop. The source contract is
`plugins/hexaemeron/skills/ephoros/SKILL.md`; implementation cites it rather
than copying its event rules.

The on-call questions are:

1. Which skill, claim id, demonstration version, source digest/anchor, and
   repository revision did the runner select?
2. Did it finish, time out, refuse before execution, or fail verification, and
   what exact rule and recovery action apply?
3. Did a root card bind a record whose status or digest changed since the card
   was written?
4. Did the run request network or credentials, and which declared boundary
   admitted or refused that request?

The checker step emits one bounded `demonstration.public_claim.checked` event
per card. The runner emits `demonstration.selected`, `started`, `verified`, or
`refused`, all sharing a correlation id and the fields above. It records
duration and peak RSS as observations, not success claims, and never records
source bytes, credential values, raw provider responses, or unbounded stderr.
The frontier selector emits the chosen lane, skill, revision, canonical issue,
and whether the job is demo-only or co-delivered. A no-eligible-job result is a
normal bounded event rather than a silent loop.

## 9. Boundaries, per capability

The source contract is `plugins/hexaemeron/skills/phylax/SKILL.md`; the build
uses that contract for the concrete control review.

- **Public prose.** Worth taking: concise current claims and links. Control:
  cards bind claim ids and record digests; the checker handles structure while
  audit checks that free prose does not strengthen evidence.
- **Demonstration record parsing.** Worth taking: one closed, local,
  owner-specific record. Control: bounded regular-file reads, duplicate-key
  refusal, depth and byte caps, exact field sets, portable relative paths, and
  no symlink traversal.
- **Preserved inputs.** Worth taking: exact audit, chain, repository, or
  protocol bytes. Control: source class plus SHA-256 or chain/block/address
  anchors verified before work; real-data status refuses when a material input
  has no provenance.
- **Subprocesses.** Worth taking: fixed Python or repository commands named by
  the owner. Control: JSON argv arrays, no shell, pinned interpreter, private
  working root, minimal environment, timeout, bounded stdout/stderr, and
  process-group teardown.
- **Network and credentials.** Worth taking only in a separately declared
  capture phase. Control: offline verification and public demo runs deny sockets
  by default; an admitted capture names HTTPS endpoint class, chain, secret
  environment names, request ceilings, and redaction without persisting secret
  values.
- **Filesystem output.** Worth taking: a disposable build and one report.
  Control: caller-selected confined report root, refusal of existing targets,
  no-follow component access, private staging, atomic publication, and a
  visible incomplete stage after an unsafe cleanup refusal.
- **GitHub queue.** Worth taking: a canonical issue URL after explicit filing.
  Control: the checker is read-only; queue creation follows the repository's
  issue-body, Sapheneia, Imprimatur, Vulgate, and issue-check gates and reuses an
  existing behaviour issue when acceptance overlaps.
- **Generated package.** Worth taking: a disposable `skills-runtime` package
  built from source. Control: use the package command and package tests in a
  temporary directory; do not invoke the source-tree `check` against an absent
  runtime or commit generated payload bytes here.
- **PDF and image assets.** Worth taking: the existing contributor PDF and
  contextual portraits. Control: deterministic regeneration where available,
  binary signature and link checks, post-commit Horos scan, and visual render
  inspection; no new portrait is generated for this task.

## 10. The budget, or its absence

There is no claim that this change makes an existing skill faster, so there is
no before/after optimisation budget. The content budgets are contract limits,
not Metron performance claims: root README at most 1,400 words, intro at most
150 words, contribution heading within 220 words, no repeated target, and no
complete inline roster. They are measured by:

```bash
python3 scripts/check_public_front_door.py --root .
```

The public demo run does have an operator-time ceiling: all three registered demos
must complete within an aggregate 600,000 milliseconds on the pinned CI runner,
and each record declares a tighter per-command timeout. The runner records a
three-repetition baseline without claiming an improvement:

```bash
python3 scripts/demonstrations.py run --showcase --repeat 3 \
  --report .hexaemeron/reports/showcase-budget.json
```

The report records interpreter, platform, record/source digests, each
repetition, slowest duration, peak RSS, timeout, and exit. Anamnesis's own
duration/RSS remain a baseline with no skill-level threshold; the 10-minute
ceiling belongs only to the front-door demo set. The source contract is
`plugins/hexaemeron/skills/metron/SKILL.md`.

## 11. The fail-closed posture

The source contract is `plugins/hexaemeron/skills/elenchus/SKILL.md`.
Integration stops on a missing or duplicate demonstration ledger; unknown
status or field; unsafe path or argv; source digest/anchor mismatch; unexpected
network request; nonzero command; timeout; absent expected observation; a
skipped public demo; public marker mismatch; mixed or constructed demo presented as
real; count mismatch; stale 16/25 text; a repeated root link target; a
lowercase maintained heading; contribution after the 220-word boundary; a root
Anamnesis portrait; Dokimasia counted or assigned a capability; generated
package failure; broken link; or failed visual/PDF review.

A refusal names the smallest failed relation and a recovery action. It does not
delete a prior good demo, downgrade an unrelated skill, advance either frontier,
or continue to another public card as though the public demo set passed.

Every defect found during implementation gets a minimal bad specimen and a
guard that fails on the entry parent and passes on the fix. The initial
regression corpus includes the current stale count, sentence-case heading,
late contribution heading, duplicate link target, anomalous root portrait,
Anamnesis stale capability paragraph, a `mixed` record labelled `real-data`, a
missing registered demo that tries to skip, a shell-shaped argv string, a
symlinked source, a changed record digest, and a pending member inserted into
the count. Elenchus reports distinguish assertion failure from environment or
dependency failure; an inconclusive parent comparison does not become a
guarded verdict by wording.

## 12. Decisions and their homes

The source contract is `plugins/hexaemeron/skills/hypomnema/SKILL.md`.

- The separate demonstration ledger, status taxonomy, independent frontier,
  co-delivery rule, `{skill}-demo` queue, and explicit Kronos lane are expensive
  to reverse. Record them in
  `docs/decisions/ADR-068-govern-real-data-demonstrations-separately.md` and put
  the normative current policy in
  `plugins/hexaemeron/skills/DEMONSTRATIONS.md`.
- The root README's front-door role, progressive order, word/link budgets, and
  single-catalogue boundary are durable public information architecture.
  Record them in
  `docs/decisions/ADR-069-keep-the-root-readme-as-a-front-door.md`.
- Current skill-specific demo facts and next jobs live in each governed
  `<skill-directory>/DEMONSTRATION.md`; behaviour facts and jobs remain in the
  adjacent `EVOLUTION.md`.
- The complete current technical catalogue lives in `FUTUREPROOFING.md` and is
  discovered/tested there once. `README.md` contains only the introduction,
  contributor invitation, checked demo set, compact mechanism, frontier link,
  install pointer, identity/authority boundary, licence, and thanks.
- Root/member portrait placement remains governed by `SHOGGOTH.md`. Removing
  the root Anamnesis image and retaining the contextual member image does not
  earn a separate ADR.
- Dokimasia remains a bounded pending note in current public prose. Its future
  canonical contract, not this study, is the home for its identity and promise.
- Current testable facts belong in mutable public prose and checks. Historical
  PR bodies, audits, studies, runbooks, ADR histories, and specimens remain
  unchanged even where they record old counts or package topology.
