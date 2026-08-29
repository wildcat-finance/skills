# The Horos live-evidence run, the study

This run executes Horos's held frontier job: record a live-repository scan of
wildcat-app-v2 as an evidence bundle, and decide the TypeScript skeleton
parser question. It ships evidence, one decision and a ledger update; it
changes no classifier behaviour.

## Assumptions

Proceeding on these unless corrected:

1. The capture target is the shallow clone of wildcat-finance/wildcat-app-v2
   already on this machine, at commit `9b8b6d5d6db06428c5b539f267623277b65315cd`.
   The bundle records that commit and the capture date; it is evidence of one
   run against one tree, not a gate others can re-run offline.
2. The TypeScript decision was put to the maintainer this session and
   answered: refuse. No TS skeletons without a real parser, and no parser
   dependency or subprocess boundary is justified by a secondary verb.
3. The frontier stays open. The scan's own misses are the evidence: text
   assets and machine-emitted migration SQL stay readable, and adding their
   rule classes is a concrete, evidenced improvement with a checkable
   acceptance. Closing mature would discard what the bundle itself names.
4. Per the versioning contract, the completed job increments evolution:
   `horos-v0.1.0` becomes `horos-v1.1.0`, generation and epoch retained, and
   the SKILL.md metadata follows.

## 1. Problem statement

Horos shipped with a frontier that promised two things it had not done:
scan a live external repository and record the result, and settle whether
TypeScript skeleton maps get built. This run does both. A working prototype
means the bundle is committed with its numbers machine-checked, the decision
is recorded where the ledger contract can hold it, every marketplace surface
agrees on the new frontier, and both suites plus the tree lints are green.

The scan already ran as study input. Against 17,053,779 bytes outside
`.git`, Horos classified 13,696,504 bytes as sinks: **80.3% of readable
bytes**, through 16 evidence-bearing entries, with zero hand-written
TypeScript or TSX excluded. The largest entries are the checked-in Storybook
build (7,567,063 bytes by directory name), `package-lock.json` (1,895,425 by
lockfile name), the single-line legal-entity dataset (1,448,802 by blob
geometry) and nine binary assets by null byte. The study criterion from the
first run asked for at least 60%; the live tree gives 80.3%.

What stayed readable and should not have, by a human's judgement: 97 SVG
text assets (204,371 bytes, verified against the clone) and 17 prisma
migration SQL files (298,878 bytes, machine-emitted, no marker). Both are fail-open misses by design, and both
become the next held job.

## 2. Prior art

The first Horos run built everything this run uses: the scanner, the
boundary document, the shipped example. The evidence-bundle shape follows
Hermes's held ambition (a complete, reproducible evidence bundle against a
real target) scaled to what a scan honestly is: one recorded run against one
named commit. The ledger mechanics follow the versioning contract at
`plugins/hexaemeron/skills/VERSIONING.md` and the worked rows in Fiat's own
`EVOLUTION.md`.

## 3. Constraints and non-goals

- No classifier changes in this run. The bundle records what v0.1.0 does;
  improving recall is the next job, not this one.
- Stdlib only, as before. The bundle's consistency test uses `json` and
  `unittest`.
- Non-goals: TS skeletons (refused, recorded), new rule classes (next job),
  re-running the scan in CI (the clone is environmental), and any change to
  the shipped example.

## 4. Design options

**A. Bundle as prose plus committed boundary, machine-checked.** The bundle
markdown carries the story and the numbers; the scan's boundary document is
committed beside it; a test parses both and asserts the quoted totals equal
the document's, so the prose cannot drift from the evidence. Chosen. Trade:
one committed JSON of 2,991 bytes that no runtime reads.

**B. Bundle as prose only.** Rejected: numbers nobody can check are
Metron's definition of an opinion.

**C. Re-scan in CI as a gate.** Rejected: the target is a moving external
repository; the bundle records a capture, and a gate that breaks when
someone else pushes to wildcat-app-v2 is not a gate.

## 5. Risk register seed

- The bundle must name the commit and the tool version; a number without its
  tree is unverifiable by construction.
- The consistency test must read the committed boundary, never re-scan; a
  network- or clone-dependent test would rot.
- The ledger row's digest is over the exact canonical line; compute it, never
  hand-type it.
- Every surface carrying the frontier text must change in the same step, or
  the marketplace prose tests fail on the split.
- The refusal must be recorded so it cannot be mistaken for an omission: the
  SKILL.md frontier section and the ledger row both say refused, with the
  reason.

## 6. Glossary seeds

- Evidence bundle: a committed record of one scan against one named commit,
  with its boundary document and machine-checked totals.
- Capture: the single recorded run; not reproducible once the remote moves.
- Refusal: a decision recorded with its reason, distinct from an omission.

## 7. Boundaries

- **Always.** Both suites and the three tree lints before a commit;
  imprimatur on every shipped document; the digest computed by script.
- **Ask first.** Any classifier change (out of scope here); any dependency;
  reopening the TS decision.
- **Never.** Re-scan inside a test; delete a failing test; claim the scan
  ran on a tree other than the recorded commit.

## 8. Success criteria

1. `python3 -m unittest discover -s tests` passes, holding the new
   ledger row's digest and every surface's frontier agreement.
2. `python3 -m unittest discover -s plugins/horos/tests -t plugins/horos`
   passes, including the bundle-consistency test.
3. `python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests`
   and the ephoros equivalent exit clean.
4. Demo path: the bundle-consistency test run alone,
   `python3 -m unittest plugins.horos.tests.test_evidence -v`, proves the
   quoted numbers equal the committed boundary document's.

## 9. Sources

The live scan of this session (commit
`9b8b6d5d6db06428c5b539f267623277b65315cd`, 2026-08-18). The maintainer's
recorded answer refusing TS skeletons, this session. The Horos study at
`plugins/horos/docs/study.md`. The versioning contract at
`plugins/hexaemeron/skills/VERSIONING.md`. The evolution ledgers of Fiat and
Kronos as worked examples of evolution rows and maturity.
