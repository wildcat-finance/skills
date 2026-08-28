# The Horos rule-classes run, the study

This run executes Horos's held frontier job: add evidence-bearing rule
classes for text assets and machine-emitted migration SQL, holding zero
false exclusions against the recorded wildcat-app-v2 bundle. At its close it
records the maintainer-directed successor job: the TypeScript outline
extractor, internal to Horos.

## Assumptions

Proceeding on these unless corrected:

1. The two rule classes are exactly the capture's quantified misses. Text
   assets means SVG, the only text-asset family the bundle evidences; fonts
   and raster images are already caught by null byte.
2. The capture target for the second recorded scan is the same shallow clone
   at commit `9b8b6d5d6db06428c5b539f267623277b65315cd`, still on this
   machine and unchanged.
3. The maintainer directed this session that TypeScript skeletons return as
   an outline extractor internal to Horos: verbatim source slices, confessed
   unparsed regions, stdlib-only shipping, a dev-time differential corpus.
   That supersedes the recorded refusal's premise (parsing TS or taking a
   dependency) without contradicting it, and becomes the next held job.
4. The completed job increments evolution: `horos-v1.1.0` becomes
   `horos-v2.1.0`, generation and epoch retained.

## 1. Problem statement

The v1.1.0 capture left 503,249 bytes of evidenced sinks readable: 97 SVG
text assets (204,371 bytes) and 17 machine-emitted prisma migration SQL
files (298,878 bytes), about 15% of what remained after the scan. This run
teaches the classifier both families, with the same fail-open discipline as
every existing rule, and records a second capture proving the improvement on
the same tree with zero false exclusions.

The two rules, stated so a test can refuse them:

- **Text asset (SVG).** A file whose name ends `.svg` and whose bounded
  prefix carries an `<svg` root element is category `asset`. Evidence names
  the root element and the prefix. A `.svg` without the root element, or an
  `<svg` fragment under any other name, stays readable.
- **Migration SQL.** A file whose name ends `.sql` and whose path contains a
  directory segment named exactly `migrations` is category `generated`.
  Evidence names the segment. Hand-kept SQL outside a migrations segment
  stays readable, as does anything non-SQL inside one.

A working prototype means: both rules earn their entries on the shipped
example fixture and in unit tests with near-misses; the second capture is
committed and machine-checked like the first; the ledger advances to
`horos-v2.1.0` holding the outline-extractor job; and every surface agrees.

## 2. Prior art

The first two Horos runs: the classifier's rule-class shape, the evidence
bundle with machine-readable capture lines, and the consistency test that
pins prose to the committed boundary. GitHub Linguist treats SVG as
`generated` in diffs for the same reading-cost reason. The outline-extractor
design recorded as the next job follows this session's assessment: verbatim
slices need a lexer, not a grammar, and confessed coverage converts silent
wrongness into visible incompleteness.

## 3. Constraints and non-goals

- Stdlib only; two rules, no new verbs, no map changes.
- The shipped example grows one specimen per new rule and its committed
  boundary is regenerated; everything else in the example holds.
- The first capture's bundle and boundary are immutable evidence behind the
  v1.1.0 ledger row; the second capture lands beside them, never over them.
- Non-goals: the outline extractor itself (next job, recorded not built),
  any reclassification of the 12 remaining readable megabytes the bundle
  does not evidence, and re-scanning in CI.

## 4. Design options

**A. Two narrow rules as stated, second capture beside the first.** Chosen.
Trade: narrowness caps recall (a `.svgz`, an unmarked SQL dump outside
`migrations/`, and any other text-asset family stay readable), which is the
fail-open contract working as designed.

**B. A general text-asset heuristic (extension allowlist without content
check).** Rejected: name-only rules carry no evidence line worth quoting,
and the house rule is that only evidence excludes.

**C. Fold migration SQL into a general generated-directory name rule.**
Rejected: `migrations` directories hold hand-written files in many stacks;
the SQL suffix gate keeps the rule inside what the evidence supports.

## 5. Risk register seed

- False exclusion is the failure that matters: the acceptance re-checks that
  no hand-written `src/` TypeScript is excluded and that only `.svg` and
  `.sql` paths joined the entry list against the first capture.
- The example fixture's regenerated boundary must be reproduced byte for
  byte by the discipline test, as before.
- The two bundles must not share machine-line names in one file; they live
  in separate files with one consistency test parametrised over both.
- The SKILL.md refusal paragraph must be superseded in place, dated, naming
  the maintainer direction, so the record shows a decision revised rather
  than erased.
- The ledger digest is script-computed, as before.

## 6. Glossary seeds

- Text asset: a text-encoded file that is an asset rather than code; SVG is
  the only family this run evidences.
- Migrations segment: a path directory named exactly `migrations`.
- Outline extractor: the recorded next job; a lexer-accurate TS outliner
  quoting declaration slices verbatim with confessed unparsed regions,
  internal to Horos.

## 7. Boundaries

- **Always.** Both suites and the three tree lints before a commit;
  imprimatur on every shipped document; digests by script.
- **Ask first.** Any rule beyond the two stated; touching the map verb;
  changing either committed capture.
- **Never.** Rewrite the v1.1.0 bundle or boundary; re-scan inside a test;
  weaken a near-miss test to make a rule fit.

## 8. Success criteria

1. `python3 -m unittest discover -s tests` passes, holding the v2.1.0
   ledger row and surface agreement.
2. `python3 -m unittest discover -s plugins/horos/tests -t plugins/horos`
   passes, including the new rule tests, the regenerated example boundary
   and the two-bundle consistency test.
3. `python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests`
   and the ephoros equivalent exit clean.
4. Demo path: `python3 -m unittest plugins.horos.tests.test_evidence -v`
   proves both captures' quoted numbers against their committed boundaries,
   and the second capture's classified share exceeds the first's 80.3%.

## 9. Sources

The v1.1.0 evidence bundle at `plugins/horos/docs/evidence/wildcat-app-v2.md`
and its ledger row. The maintainer's directions this session: run the held
job, and place the TypeScript slicer internal to Horos. The clone at commit
`9b8b6d5d6db06428c5b539f267623277b65315cd`. GitHub Linguist's generated
handling of SVG. The versioning contract at
`plugins/hexaemeron/skills/VERSIONING.md`.
