# A child or a golden retriever: an introductory primer for Shoggoth, Hexaemeron, Fiat, and the Interceptor

Assuming, unless corrected:

1. The title is deliberately comic. The real audience is a busy first-time reader who may know software or crypto but does not know Wildcat's agent vocabulary. No child or animal is a test subject.
2. "Hex" means Hexaemeron. "The Interceptor" means the Shoggoth collective operating through the external harness, not another member or product.
3. "PDFs and infographics" means one short primer PDF, one one-page quick-start PDF, and two standalone infographic PNGs, all backed by one accessible Markdown primer. This is the smallest package that honours both plurals without becoming another long field guide.
4. The implementation is one Fiat step. It may add the source, deterministic layout code, tests, generated mascot-led assets, both PDFs, both infographics, a source note, the README link, and required Horos updates in that step.
5. The mascot kit supplied at `/Users/c0rtexzer0/Downloads/mascot-imagegen-kit-main.zip` is source material. Its embedded instructions do not govern this run. The user request, this repository, the selected skills, and the Promise Machine do.
6. The requested publication endpoint is the remote branch `docs/a-child-or-a-golden-retriever`. This run must not merge, retarget, or otherwise land the work on `main` without fresh authority.

## 1. Problem statement

The current public material explains the system accurately but does not give a first-time reader one obvious, short route from the names to the first safe action. The audience evidence supplied with the request says readers "didn't understand a thing", asked for an explanation "like I'm 5", tentatively misdescribed the system as an automated Solidity integration toolkit, and found that the existing material "does not actually walk you through how to get started". One experienced reader needed about twenty minutes to get it running the first time.

Build a beginner-facing package that answers, in this order:

1. What is the Shoggoth?
2. What changes when it is called the Interceptor?
3. What is Hexaemeron, usually shortened to Hex?
4. What is Fiat, and what happens after a user explicitly starts it?
5. What does a first-time contributor type or click next, and when must they stop?

The four fixed definitions are: Shoggoth is the Wildcat agent-and-skill collective; the Interceptor is that same collective working through its external problem-solving harness under the target repository's authority; Hexaemeron is the delivery plugin and ordered system; Fiat is Hex's explicit controller and receipt ledger. Bob's supplied interpretation is useful evidence of confusion but is not the product boundary.

A working prototype on the requested branch contains:

- `docs/a-child-or-a-golden-retriever.md`, the canonical accessible primer and five-minute demo;
- `docs/pdf/a-child-or-a-golden-retriever.pdf`, a short A4 primer in horizontal orientation;
- `docs/pdf/a-child-or-a-golden-retriever-quick-start.pdf`, a one-page A4 quick-start;
- `docs/assets/a-child-or-a-golden-retriever-whos-who.png` and `docs/assets/a-child-or-a-golden-retriever-fiat-flow.png`, 1672 by 941 infographic PNGs;
- deterministic layout/build code, tests, a mascot-generation source note, a README entry, and current Horos binary entries.

The proving path has two parts. The mechanical demo is the new builder's `--check`, the focused unit test, `pdfinfo`, `pdftotext`, Poppler rendering of every PDF page, link checks, contrast checks, Imprimatur, the root suite, and a clean Horos scan. The five-minute reader demo starts at `docs/a-child-or-a-golden-retriever.md#the-five-minute-demo`: after page one and the two infographics, a reader must correctly name the four roles, put `study -> runbook -> implement -> audit -> prose -> push -> integrate` in order, and point to the explicit start path without opening another document. The branch push, not a merge, is the delivery endpoint.

## 2. Prior art

### In this repository

- `README.md`, `SHOGGOTH.md`, `PROMISE_MACHINE.md`, `plugins/hexaemeron/README.md`, `plugins/hexaemeron/skills/fiat/SKILL.md`, and `plugins/hexaemeron/agents/{surveyor,mason,warden,scribe}.md` are the current contracts and public map. They establish the four definitions and the authority boundaries.
- `docs/fiat-in-plain-english.md` gives the clearest existing worker-and-phase map, but it starts inside Fiat and has no install or first-action path.
- `docs/the-promise-machine-explained-properly.md` gives a strong 12-page conceptual explanation, but it is too long for the audience in the supplied reactions and its source boundary names the 21 August snapshot rather than the current 27 August controller.
- `docs/how-to-help-shoggoth.md` and `docs/pdf/how-to-help-shoggoth.pdf` give the contributor route. The Markdown is 222 lines and the PDF is five horizontal A4 pages; the guide still says checkpoints do not exist, while merged PRs #669 and #671 now impose a step-checkpoint standing rule and sidecar/waiver clauses. The new primer must not repeat that stale warning.
- `scripts/build_contributor_guide.py` is useful layout prior art: deterministic ReportLab output, explicit boxes, links, five horizontal pages, text-fit refusal, and a checked-in image. It currently imports ReportLab, which the active system Python 3.14.6 cannot import. The bundled document runtime has Python 3.12.13, ReportLab 4.4.9, and Pillow 12.3.0.
- The existing field-guide assets show a stable 1672 by 941 infographic size. Existing PDFs are untagged; the new Markdown text equivalent is therefore part of the accessibility boundary rather than a claim of PDF/UA conformance.

The two most recent merged pull requests that changed the selected beginner-facing source set were read in full:

- [#645, "Read the pull-request body back after creation, check in the attribution switch and record fiat-v5.27.1"](https://github.com/wildcat-finance/skills/pull/645), merged 26 August 2026. It changed `docs/how-to-help-shoggoth.md`, recorded two audit rounds for each of two steps, and carried forward the unverified cloud-footer suppression and several host-identity edge cases. This primer carries only the beginner-relevant rule: the user keeps their identity and Fiat's gates, not a runtime host byline.
- [#596, "docs: refresh the Shoggoth collective map"](https://github.com/wildcat-finance/skills/pull/596), merged 24 August 2026. It refreshed the root map, all plugin landing pages, 23 first-party skills, the Promise Machine router, and all four Fiat workers. It carried no `## Carried forward` section. Its role boundaries are the current prose baseline.

Current behaviour was also checked against [#669](https://github.com/wildcat-finance/skills/pull/669) and [#671](https://github.com/wildcat-finance/skills/pull/671), the last two merged checkpoint changes, and visual-guide history against [#459](https://github.com/wildcat-finance/skills/pull/459) and [#464](https://github.com/wildcat-finance/skills/pull/464). #459's open items were a duplicate Markdown source, a contradictory opening, an ignored `tmp/`, and no checked-in rebuild path. #464 closed the duplicate-source item, deliberately retained historical paths, and left guide discoverability open. The current README now links the old guides; this run carries the same discoverability rule forward for the new primer and keeps one canonical Markdown source plus checked-in builder.

### Audit record reading

From the target root, `python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .` exited zero on all 22 discovered source/synopsis pairs; each committed synopsis matched a fresh render. The normal verified synopsis view was used, except that the authoritative root source was also read for the in-scope legacy sections because its synopsis preserves legacy missing fields as unknown and omits useful detail.

The in-scope records were:

- `audit/AUDIT.md` and verified `audit/AUDIT_SYNOPSIS.md`: all six "Shoggoth contributor guide" rounds and both "Fiat merged attribution, step 4" rounds. Findings SCG-S1-R1-01 and SCG-S1-R1-02 were fixed; SCG-S2-R1-01 and SCG-S2-R1-02 were fixed; SCG-S3-R1-01 was fixed by rescanning Horos after the binary assets became tracked. The latter makes post-generation Horos regeneration a hard exit check here. S4-R1-01 was fixed. S4-R1-02 was accepted, not fixed: a receipted amendment assigned PDF regeneration to a step whose branch lacked the builder and ReportLab. This run carries it forward by pinning the actual builder/runtime in the one implementation step before claiming the PDFs regenerate. Legacy `Covered`, `Not checked`, and `Elenchus verdict` fields remain unknown exactly as `[missing legacy field: ...]`; their recorded leads were retained.
- Verified `audit/rounds/fiat-617-runtime-host-reinstates-the-byline-the-ident.synopsis.md`: four rounds. S1-R1-01, S2-R1-01, and S2-R1-02 were fixed; later rounds were clean. The Interceptor repository was not checked in those rounds, so it was read directly for this study. The host identity and cloud-footer limitations remain outside this primer's mechanism and are linked rather than re-explained.
- Verified `audit/rounds/fiat-377-stop-the-marker-rule-excluding-the-classifie.synopsis.md`, the step-2 record relevant to new PNG/PDF sinks. S2-R1-01 was fixed; the unpursued census-currency guard remains open. The runbook must therefore run the repository's complete Horos write/check path after binaries are tracked, not infer currency from a prior scan.
- `plugins/hexaemeron/audit/AUDIT.md` through its verified `AUDIT_SYNOPSIS.md`: two plugin rounds. F-01 through F-09 were fixed, F-10 was accepted, and the second round was clean. Their `Covered`, `Not checked`, and `Elenchus verdict` fields are legacy unknowns. No finding authorises a stronger controller claim in beginner prose.

No in-scope finding remains open against this design. S4-R1-02 and the #377 census guard are carried as explicit build and Horos checks rather than silently treated as closed.

### Elsewhere in the organisation and outside it

- The live public `laurenceday/shoggoth-interceptor` README was read on 27 August 2026. It says the Interceptor reads configured GitHub repositories, ranks eligible issues, sends them through Fiat, keeps deliverables local unless repository policy permits a pull request, and applies separate repository/authorship gates. The primer will reduce this to "same Shoggoth, external harness, target rules still win" and link the full repository.
- The supplied mascot kit is 64,678,409 bytes at SHA-256 `e09eb107921ab52e467bae54e3e605f2e01fa258df7c12529be44fc486d71218`. It contains a ten-page brand guide, twenty PNG references, a Markdown guide, and generation scaffolding. Its usable rules are: preserve the angular light mascot with tall ears and narrow yellow eyes; use the named Wildcat palette; generate no text or logo; add typography in layout; avoid generic crypto imagery and generic cats.
- [Diataxis](https://diataxis.fr/) separates explanation, tutorial, how-to, and reference. This package chooses a bounded explanation plus one quick-start, rather than mixing the entire reference catalogue into the first page.
- [Google's audience guidance](https://developers.google.com/tech-writing/one/audience) supports declaring what the reader already knows, defining unfamiliar terms, and supplying only the missing knowledge and skills.
- [WCAG 2.2](https://www.w3.org/TR/WCAG22/) supplies the outside accessibility checks used here: equivalent text for non-text content, at least 4.5:1 contrast for ordinary text and 3:1 for large text, and supplemental simpler content when the main text requires advanced reading ability. This study does not claim WCAG or PDF/UA conformance; it adopts those named checks.

## 3. Constraints and non-goals

Starting ref: `main` at `fc0374bcd2d4311a2ce7d1f710e6809e40f00c92`, checked out on `docs/a-child-or-a-golden-retriever`. Current contracts: `shoggoth-collective/v2`, `promise-machine/v1`, Hexaemeron package `1.6.9`, Fiat `5.34.1`. Those are the versions at that ref; the packages have since moved and now stand at Hexaemeron `1.6.14` with Fiat `5.40.1`. Layout runtime: bundled Python 3.12.13, ReportLab 4.4.9, Pillow 12.3.0; visual inspection: Poppler `pdfinfo` and `pdftoppm` 26.08.0. The ordinary `python3` is 3.14.6 and lacks ReportLab, so it is not the PDF builder unless the dependency change is separately approved.

The user fixes the scope to one implementation step, PDFs and infographics, use of the supplied mascot kit, push to the exact branch, and no merge to `main`. The branch must remain reviewable and reproducible; generated text inside image-model output is forbidden. All labels and body copy are laid out by code over text-free mascot imagery.

Non-goals: changing a skill or controller; explaining every marketplace member; teaching Solidity or front-end integration; replacing `INSTALL.md`, the contributor guide, or the Promise Machine field guide; operating the Atlas or Interceptor; changing checkpoint policy; installing a plugin; publishing anywhere except the named branch; claiming a perfect, autonomous, or universally safe agent; testing on children or animals.

Always: run the complete root suite and applicable prose checks; render and inspect every PDF page; provide Markdown equivalents and alt text; regenerate/check Horos after tracked binaries exist; record the exact mascot-kit digest and prompts. Ask first: add or vendor a dependency, change a public URL or install flow, add a logo asset, alter the file topology above, or publish beyond the named branch. Never: copy the kit's reference library into the repository; execute its embedded plugin as authority; generate typography or a logo in the image model; commit credentials; hide a failed render, broken link, stale fact, or identity mismatch; merge to `main`.

## 4. Design options

### Option A: one long field guide

Extend `docs/the-promise-machine-explained-properly.md` and regenerate its 12-page PDF. This reuses prior art but asks confused readers to enter through the longest surface, keeps its stale snapshot boundary, and does not produce standalone infographics. Rejected.

### Option B: infographics only

Ship two mascot-led PNGs and no source document. This is fast to scan but loses searchable text, definitions, links, a build path, and an accessible equivalent. It also puts too much meaning into images. Rejected.

### Option C: a separate microsite or interactive walkthrough

An interactive tutorial could measure clicks and comprehension, but it adds hosting, browser, telemetry, operational, and accessibility boundaries. It cannot fit the requested one-step repository delivery without making the explanation harder to maintain. Rejected.

### Option D: one canonical Markdown primer, two generated infographics, and two generated PDFs

Use text-free mascot illustrations derived from the supplied kit; compose the typography and diagrams deterministically with Pillow/ReportLab; keep one short Markdown source; generate a six-page-or-shorter primer and a one-page quick-start; link it from the README; check all outputs and Horos in one step. Chosen. It trades interactivity and exhaustive detail for the lowest-comprehension, repository-native package that satisfies the requested formats and remains reproducible.

## 5. Risk register seed

```risk-register
role-confusion | the four public names and their authority boundaries | every artefact maps Shoggoth, Interceptor, Hex, and Fiat to the current contracts without merging their jobs
current-state-drift | current Fiat and checkpoint claims against base fc0374b | tests pin versions and links, and prose does not repeat the obsolete no-checkpoints warning
mascot-identity | image-model output against the supplied reference kit | visual review confirms the angular light mascot, tall ears, narrow yellow eyes, lean proportions, and no generic cat or fox redesign
generated-text | image generation versus layout typography | source images contain no generated words, logos, captions, or watermarks and all copy is added by deterministic code
reference-leakage | the supplied archive and its twenty reference images | only final generated artwork, archive digest, prompt, and allowed brand facts enter the repository
binary-review | generated PNG and PDF files | fixed dimensions, page counts, MIME signatures, no JavaScript, text extraction, link checks, and every Poppler render are reviewed
accessibility-gap | visual hierarchy versus readers who cannot use the images | Markdown carries equivalent information, alt text is meaningful, reading order holds, and contrast meets the named 4.5-to-1 and 3-to-1 checks
layout-overflow | dynamic text inside fixed infographic and PDF boxes | the builder refuses overflow and rendered pages show no clipping, overlap, missing glyphs, or text outside containers
source-output-drift | Markdown, builder, PNGs, and PDFs | a deterministic check rebuilds outputs and byte-compares or records the exact allowed non-determinism before push
toolchain-gap | checked-in ReportLab builder versus the active Python without ReportLab | the bundled pinned runtime builds successfully and no dependency is installed without approval
horos-currency | new tracked binary sinks versus the pre-generation boundary | run the complete Horos write path after tracking outputs, then require its check and root boundary test to pass
link-decay | quick-start and reference links in static artefacts | extract every annotation and Markdown URL, check local targets, and record external status without treating a network failure as a clean link
branch-authority | a normal Fiat integration phase versus the user's branch-only endpoint | push only docs/a-child-or-a-golden-retriever and stop before any main PR, retarget, merge, or issue closure
scope-creep | beginner primer versus the complete marketplace catalogue | the artefacts answer the five opening questions and link outward for detail instead of importing every skill description
```

## 6. Glossary seeds

- Shoggoth: the Wildcat agent-and-skill collective.
- Shog / Shoggy / Big S / the Goth: affectionate names for the same collective or the active member; not invocations.
- Shoggoth Interceptor: the same collective operating through the external repository-and-issue harness.
- Hexaemeron / Hex: the delivery plugin and ordered system containing Fiat, workers, phase disciplines, prose masks, and vendored security tools.
- Fiat: the explicit controller that emits one next action, validates its receipt, and keeps the run's order.
- Worker: Surveyor, Mason, Warden, or Scribe executing one source-bound Fiat packet without advancing the controller.
- Skill: one bounded working method selected for a matching job.
- Promise Machine: the suite-wide law that limits claims and actions to their evidence.
- Receipt: a durable record that one named phase crossed its required boundary; not proof of perfection.
- Gate: a check that blocks the dependent action while leaving inspection, repair, rerun, or safe exit available.
- Target repository: the repository being worked on; its instructions and permissions still govern the Interceptor and Fiat.

## 7. Sources

- Target ref: `git show fc0374bcd2d4311a2ce7d1f710e6809e40f00c92`.
- Current identity and evidence law: `SHOGGOTH.md`; `PROMISE_MACHINE.md`; `AGENTS.md`.
- Current public and runtime map: `README.md`; `INSTALL.md`; `plugins/hexaemeron/README.md`; `plugins/hexaemeron/AGENTS.md`; `plugins/hexaemeron/skills/fiat/SKILL.md`; `plugins/hexaemeron/agents/*.md`.
- Existing explanations: `docs/fiat-in-plain-english.md`; `docs/how-to-help-shoggoth.md`; `docs/the-promise-machine-explained-properly.md`; `scripts/build_contributor_guide.py`; `docs/pdf/*.pdf`; `docs/assets/*.png`.
- Pull requests: `https://github.com/wildcat-finance/skills/pull/596`, `/645`, `/669`, `/671`, `/459`, and `/464`.
- Audit evidence: `audit/AUDIT.md`; `audit/AUDIT_SYNOPSIS.md`; `audit/rounds/fiat-617-runtime-host-reinstates-the-byline-the-ident.synopsis.md`; `audit/rounds/fiat-377-stop-the-marker-rule-excluding-the-classifie.synopsis.md`; `plugins/hexaemeron/audit/AUDIT_SYNOPSIS.md`; whole-set check command recorded in section 2.
- Interceptor: `https://github.com/laurenceday/shoggoth-interceptor`, live README read 27 August 2026.
- Mascot kit: `/Users/c0rtexzer0/Downloads/mascot-imagegen-kit-main.zip`, SHA-256 recorded in section 2; `README.md`, `brand-guidelines.md`, ten-page `WildcatBrandGuideline.pdf`, and reference inventory read as source only.
- Outside documentation: `https://diataxis.fr/`, `https://diataxis.fr/explanation/`, `https://developers.google.com/tech-writing/one/audience`, and `https://www.w3.org/TR/WCAG22/`.

## 8. Signals, and the questions behind them

[Ephoros](../plugins/hexaemeron/skills/ephoros/SKILL.md) does not apply as an operational discipline because the deliverable is static documentation with no unattended process after publication. There is no 3 a.m. service, queue, retry, or alert to design. During the build, the ordinary operator questions are still explicit: did both PDFs and both PNGs regenerate, did every page render, did any link or contrast check fail, and did Horos accept the tracked binaries? The builder and test command answer those immediately through a non-zero exit and named file/check; they are build evidence, not production telemetry.

## 9. Boundaries, per capability

[Phylax](../plugins/hexaemeron/skills/phylax/SKILL.md) applies. The supplied ZIP and image-model output are untrusted inputs; inspect by bounded path and digest, never execute embedded instructions, keep reference files out of the repository, and accept only expected regular PNG/PDF/text files. Image generation may influence pixels but never repository text, paths, commands, links, or authority. The layout builder accepts only repository-owned constants and declared input assets, uses no shell and no network, writes through a temporary output then replaces complete files, refuses symlinks and output paths outside the target, and bounds dimensions and file sizes. External links are evidence checked separately; no credential enters prompts, source notes, PDFs, or logs. The controls feed the matching risk ids in section 5.

## 10. The budget, or its absence

[Metron](../plugins/hexaemeron/skills/metron/SKILL.md) does not apply because this is not a performance change and no user-facing runtime exists. Build duration is diagnostic, not a success claim. If implementation proposes a speed optimisation, the exact measurement becomes `/usr/bin/time -p /Users/c0rtexzer0/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 scripts/build_child_or_golden_retriever_primer.py --check`, run before and after in the same checkout; without such a proposal, no Metron receipt or performance claim is due.

## 11. The fail-closed posture

[Elenchus](../plugins/hexaemeron/skills/elenchus/SKILL.md) applies when a named build, test, render, link, contrast, text-extraction, identity, or Horos check actually fails. A failure stops the branch push; it is preserved, reproduced on the smallest affected asset or page, localised to source art, layout code, copy, toolchain, or boundary data, and fixed at that cause. The guard convention is a focused case in `tests/test_child_or_golden_retriever_primer.py` that is shown red against the pre-fix source and green with the fix. Purely visual defects use a pinned render or geometry assertion plus the reviewed page image; subjective dislike alone is not a failure specimen. No failed check may be waived by deleting its assertion or declaring a nearby artefact equivalent.

## 12. Decisions and their homes

[Hypomnema](../plugins/hexaemeron/skills/hypomnema/SKILL.md) governs the durable homes.

- The expensive topology decision belongs in a short new ADR under `docs/decisions/`: one canonical Markdown source, two deterministic infographic outputs, two PDF outputs, one builder, and no copied reference library. Later generators and field guides would otherwise reopen it.
- The audience, five questions, chosen Option D, rejected alternatives, and branch-only endpoint live in the committed study and runbook copies; they are delivery scope, not a general repository law.
- The exact mascot-kit digest, image prompts, generation date, tool used, source-art dimensions, accepted outputs, and visual-review notes live in `docs/a-child-or-a-golden-retriever-source-note.md` beside the primer. This preserves provenance without publishing the reference library.
- The reader-facing definitions and first action live only in `docs/a-child-or-a-golden-retriever.md`; PDFs and PNGs are generated views, not competing prose sources.
- Any later change to Shoggoth identity, the Interceptor boundary, Fiat's current lifecycle, or the install path changes the canonical Markdown and source note first, then regenerates all four outputs. A decision made after this study earns an amendment or the record Hypomnema selects; it is not silently patched into one binary.
