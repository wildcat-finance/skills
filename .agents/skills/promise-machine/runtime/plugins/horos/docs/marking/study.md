# The three-repository marking, the study

This run executes the reopened frontier's last job: the improvement the
maintainer wanted all along. Horos stops being a tool that could mark
repositories and becomes the tool that has marked them: graded boundaries,
candidates, censuses and adoption stanzas committed into v2-protocol,
wildcat-app-v2 and this skills repository itself, with the recaptures
recorded as evidence and the frontier closed mature at the end.

## Assumptions

Proceeding on these unless corrected:

1. The two product repositories are marked through fresh clones of their
   default branches, one branch and one pull request each, opened with the
   house markers. Their branch protections may require review; the run
   closes with those pull requests open and named if they cannot merge, and
   that does not block maturity, because the artefacts and the record are
   the deliverable this repository owns.
2. The skills repository is marked in place on this run's own step branch:
   `.horos/boundary.json`, `.horos/candidates.json`, `.horos/census.json`
   at the root, and the adoption stanza appended to `AGENTS.md`.
3. All scans run under the tracked universe, which is the refined default.
4. The completed job increments evolution: `horos-v8.2.2` becomes
   `horos-v9.2.2`, generation and epoch retained, status `mature`, next job
   `None -- mature`. The reopened scope is then complete; reopening again
   requires new evidence recorded as an epoch entry.

## 1. Problem statement

Every capture so far lived in this plugin's evidence folder; no repository
actually carries a boundary an agent could consult. This run commits the
artefacts where agents work. For each of the three trees: scan under the
tracked universe with the graded classifier, write the three artefacts,
place the adoption stanza in the repository's agent instructions, and
record what the refined classifier found (hard bytes, candidate bytes,
universe) as a machine-checked evidence bundle beside the older captures.

A working prototype means: the skills repository carries its own committed
boundary that `check` verifies clean; both product-repository pull requests
exist with artefacts and stanzas; the recapture bundle is machine-checked
by the suite; and the ledger closes mature with every surface agreeing.

## 2. Prior art

The two schema-1 captures of wildcat-app-v2 and the v2-protocol census are
the before picture; this run records the after. The adoption stanza shipped
at v2.2.0 is the bridge; this run finally pastes it where it binds.

## 3. Constraints and non-goals

- The recorded schema-1 captures stay immutable; the recaptures land as new
  files beside them.
- Non-goals: merging the product-repository pull requests past their own
  gates (their reviews are theirs), boundary adoption in any further
  repository, and any classifier change.

## 4. Design options

**A. One branch and pull request per product repository, the skills
repository marked in-run.** Chosen. Trade: the product pull requests may
outlive the run awaiting review; the bundle records their URLs and states
rather than pretending a merge.

**B. Push artefacts straight to the product default branches.** Rejected:
never merge past a gate, and those repositories own their review rules.

## 5. Risk register seed

- The skills repository's own boundary must not disturb the suites: the
  `.horos` directory is never scanned, and nothing in the tests walks the
  repository root. `check` from the root must pass after the commit.
- The `AGENTS.md` stanza must not break the marketplace prose contracts;
  the root suite is the arbiter.
- Product clones are fresh and shallow; pushing a new branch from a
  shallow clone works on GitHub, and the run unshallows if a push is
  refused.
- The bundle records each repository's commit, universe, hard and candidate
  totals, and the pull request URLs; the suite checks the totals against
  committed artefact copies.
- Maturity closes on the ledger only after the demo criteria pass; the
  closing row names the open pull requests honestly.

## 6. Glossary seeds

- Marking: committing the boundary, candidates, census and stanza into a
  repository agents work in.
- Recapture: the schema-2, tracked-universe scan of a tree already
  captured once under schema 1.

## 7. Boundaries

- **Always.** Both suites and the three tree lints before a commit;
  imprimatur on every shipped document this repository owns; the stanza
  text verbatim from the scanner.
- **Ask first.** Pushing anything beyond one branch and one pull request
  per product repository; touching product code.
- **Never.** Merge a product pull request past its gates; rewrite the
  schema-1 captures; close mature with a failing demo.

## 8. Success criteria

1. `python3 -m unittest discover -s tests` passes.
2. `python3 -m unittest discover -s plugins/horos/tests -t plugins/horos`
   passes, including the recapture-bundle tests.
3. `python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests`
   and the ephoros equivalent exit clean.
4. Demo path: `python3 plugins/horos/skills/horos/scripts/horos.py check .`
   passes from the repository root against the committed boundary, and the
   recapture bundle at
   `plugins/horos/docs/evidence/three-repository-marking.md` is
   machine-checked by the suite.

## 9. Sources

The v8.2.2 ledger row holding this job in the maintainer's words. The
schema-1 captures and censuses as the before picture. The adoption stanza
as shipped. Fresh clones of wildcat-finance/v2-protocol and
wildcat-finance/wildcat-app-v2 at their default branches.
