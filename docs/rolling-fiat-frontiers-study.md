# Rolling Fiat frontiers for the Wildcat Labs marketplace

## Problem statement

The marketplace has nine plugins, but its published frontier prose is copied
across landing pages, canonical skills, portable entries, runtime contracts,
guides and the repository selection table. A merged implementation can make
those copies stale immediately. Probitas still names Euler v1/v2 as future
work after pull request 65 shipped the adapters, while Tabularium's ordered
Euler preservation work from issue 57 did not ship. Hexaemeron's repository
overview still says Fiat files issues, although the current controller has no
issue phase. Before this change, Fiat's browsing README had also diverged from
its canonical `SKILL.md`.

The delivery adds one rolling Fiat command to every plugin landing README.
Each command names the next evidenced repair or implementation step and makes
the final marketplace-wide cold read part of that future Fiat topic. The
landing page is authoritative for the current frontier and next job. Tests
keep those fields present, unique and synchronised without copying the command
into canonical or vendored skill prose.

The browsing `README.md` copies beside canonical `SKILL.md` files are removed.
They exist only to make a skill directory render on GitHub, and Fiat's current
copy shows that byte-equality checks have not removed their drift cost. Plugin
landing pages remain because they are the marketplace overview and the sole
home of the rolling command.

A working result has nine plugin landing READMEs, including a new short Hermes
landing page; nine commands with the exact common suffix; current frontier
sentences reconciled across every mutable marketplace copy; and repository
tests that fail when a landing page, root table or context copy drifts. The
full repository test matrix, Pandects Foundry checks, prose gates and protected
file comparisons must pass before the pull request opens.

## Prior art

- Pull request 64 and issue 63 introduced `marketplace-context` blocks, the
  nine-plugin selection table and `tests/test_marketplace_prose.py`.
- `tests/test_marketplace_prose.py` checks plugin inventory, host descriptions,
  canonical skill handoffs, selected README/SKILL mirrors and the digest-bound
  Lazarus example README. It does not require plugin landing pages, rolling
  Fiat commands or exact frontier agreement.
- Before this change, eight plugin landing pages used `## In one line`.
  Hermes had no `plugins/hermes/README.md`; its only browsing document was a
  copy beside the canonical skill.
- Pull request 65 implemented Euler v1/v2 Probitas adapters and closed issue
  57 without changing Tabularium.
- The Pandects audit records a missing law for fees that reduce pooled lender
  claims below open withdrawal obligations.
- Lemma's `INVARIANTS.md` records that callable-surface ABI validation does not
  independently check return types or state mutability.
- Fiat already requires a prose pass before each push. The requested design
  places marketplace refresh inside each published job prompt rather than
  adding a controller phase that would affect unrelated repositories.

## Constraints and non-goals

- Start from fetched `origin/main` at `6d751b3` in the isolated worktree.
- Reuse `https://github.com/wildcat-finance/skills/issues/63` for the
  repository issue-first gate.
- Deliver one atomic implementation step and one pull request.
- Do not add a controller phase or change Fiat state, receipt or schema
  formats.
- Do not place the rolling command in bundled or vendored skill READMEs.
- Remove first-party shadow README files whose only source is a sibling
  `SKILL.md`; keep plugin landing pages and substantive standalone READMEs.
- Do not rewrite vendored Pashov prose, historical audit findings, legal
  attribution or `plugins/lazarus/examples/aave-v4-spoke-v0/README.md`.
- Change an authoritative template or renderer before regenerating prose.
- Do not claim a plugin implementation exists merely because its next job is
  named.
- This delivery changes no Solidity. The Fiat security suite is waived, while
  the repository's Pandects Foundry checks remain required.

## Design options

### 1. Commands in every copied context block

This makes the job visible everywhere but creates more copies of the most
frequently changing text. It would increase the drift surface the feature is
meant to reduce and would alter vendored or canonical browsing material.

### 2. A marketplace-only Fiat controller phase

The controller could require a frontier receipt before every final push. Fiat
is used outside this marketplace, so the phase would impose Wildcat-specific
work on unrelated target repositories and change the state contract the user
excluded.

### 3. Authoritative landing command with repository enforcement

Add one rolling job field to each plugin landing page. The common command
suffix tells that future run to cold-read all mutable marketplace prose and
replace completed or stale jobs before it finishes. Offline tests require all
nine fields, their exact shape, unique topics and frontier agreement across
the copied marketplace prose. This is the selected design because it adds one
changing command per plugin and no new runtime state.

The same construction removes shadow skill READMEs and changes repository
contracts to point directly at canonical `SKILL.md` files. Tests assert those
shadows stay absent instead of asserting byte equality.

## Selected frontier jobs

- Alexandria: the specified production Compound v3 harvester.
- Ariadne: the dataset predicate, keeping signing external.
- Hermes: a complete reproducible live Wildcat evidence bundle.
- Hexaemeron: retire shadow skill README copies and remove stale issue prose.
- Lemma: total callable-surface ABI comparison for outputs and mutability.
- Lazarus: an Ariadne state-fixture predicate in an end-to-end Aave v4
  preservation release.
- Pandects: the missing pooled-claims versus open-withdrawals law.
- Probitas: fail-closed Morpho Midnight fixed-maturity coverage.
- Tabularium: the unshipped Euler v1/v2 preservation work from issue 57.

## Risk register seed

- A parser may accept commands outside the marked `In one line` block or miss
  duplicated fields.
- Markdown table links and punctuation may make two frontier sentences look
  equivalent while allowing them to drift.
- A broad prose replacement may modify the Lazarus manifest-bound README,
  vendored Pashov material or historical audit text.
- A broad README deletion may remove a substantive plugin landing page,
  template guide or vendored upstream document rather than a shadow skill
  copy.
- Generated Pandects or Probitas prose may be edited downstream instead of at
  its renderer or template.
- The command topics may overstate unbuilt behavior. Each must remain an
  imperative future job, while current prose continues to describe only what
  ships.
- A live issue reference may close while work remains. The Tabularium sentence
  must state the unshipped work rather than treating issue state as evidence of
  completion.

## Glossary seeds

- **Landing README:** `plugins/<name>/README.md`, the public plugin overview
  containing `## In one line`.
- **Current frontier:** a factual statement of the most important unshipped
  repair or implementation boundary.
- **Rolling Fiat job:** the executable prompt that advances a plugin and refreshes
  marketplace prose before the run finishes.
- **Marketplace context:** the marked identity, handoff and frontier prose
  copied into first-party documents.
- **Mutable first-party prose:** Wildcat-authored text excluding vendored,
  historical, legal and digest-bound material.
- **Shadow skill README:** a browsing-only copy of a sibling `SKILL.md`; these
  copies are removed in this delivery.

## Sources

- `AGENTS.md` and every `plugins/*/AGENTS.md` on `origin/main`.
- `README.md`, `plugins/*/README.md` and
  `tests/test_marketplace_prose.py` on `origin/main`.
- `plugins/hexaemeron/skills/fiat/SKILL.md` and the browsing copy removed by
  this change.
- `plugins/lemma/INVARIANTS.md`.
- `plugins/pandects/audit/AUDIT.md`, especially the step 5 audit leads.
- `plugins/probitas/skills/probitas/references/venues.md`.
- Wildcat Finance skills issues 4, 57 and 63; pull requests 23, 64 and 65.
- `laurenceday/wildcat-skills-todo` issue 16 and pull request 122.
