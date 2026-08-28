# ADR-010: Split address telemetry shape from boundary control over shared TypeScript files

## Status

Accepted, 2026-08-21. Superseded by a later numbered record once it stops being
true.

## Context

Two lints now read the same TypeScript files. Phylax has read `.ts`/`.tsx`
since its off-chain boundary work landed P005 through P007, through the
attributed lexer vendored at `plugins/hexaemeron/lib/typescript_lexer.py`.
The wallet-address telemetry run gave Ephoros the same surface for E005, an
address used as a metric label, a dashboard key or a log index.

The address rule could plausibly have lived in either skill. Phylax already
owns the personal-data and address-linkage judgement, including caches that
pair addresses with resolved names, and its checker already had the TypeScript
machinery. Ephoros owns the prose rule the checker mechanises: do not index
telemetry by wallet address, stated in its SKILL.md before any parser read it.
A rule that two skills could claim ends up either duplicated or orphaned, and
finding codes are interfaces other tools cite, so the claim had to be settled
before E005 shipped.

## Decision

Telemetry shape belongs to Ephoros and boundary control belongs to Phylax,
whatever language the file is written in. E005, the one address rule that is
telemetry shape rather than boundary control, is an Ephoros code. Secrets in
source or output (P004), raw HTML and sanitisers (P005), session credentials
in persisted storage (P006), fetch hosts (P007), and the personal-data and
address-linkage judgement including linkage caches stay Phylax. One concern
carries one code, the same file may carry findings from both lints, and no
pattern is owned by both.

## Alternatives

- **Folding the address rule into phylax.** The checker with the TypeScript
  machinery would have gained one more pattern, cheaply. It lost because the
  rule is about where an address sits in emitted telemetry, not about data
  crossing a trust boundary, and because the prose rule it mechanises lives in
  Ephoros's contract. A finding code enforcing one skill's rule from another
  skill's checker leaves two ledgers each owning half a decision, and the two
  skills evolve on separate frontiers.
- **A shared rule engine both lints call.** One walk, one suppression grammar,
  no duplication. It lost because it creates a third surface that evolves on
  no ledger of its own, and the two checkers already share exactly the part
  that is safe to share -- the masked lexer -- while their rules, walks and
  pragma grammars stay citable per skill.
- **Duplicating the pattern in both lints.** Nothing slips through. It lost
  because the same line then draws two codes from two tools, a reasoned pragma
  for one leaves the other firing, and every deliberate exception has to be
  stated twice and kept in step. A double-reported finding trains people to
  suppress rather than fix.

## Consequences

A TypeScript file can carry findings from both lints, and the audit evidence
says the split holds in practice: a mixed secret-plus-address specimen draws
exactly one code from each. The pragma namespaces stay distinct --
`ephoros: allow` answers E005 and `phylax: allow` answers P-codes -- so an
exception states its reason to the lint that owns the concern.

Both checkers keep reading through the one vendored lexer, so a defect there
is contained twice at each checker's own fail-closed boundary (`E000`, `P000`)
and fixed once on the owning surface.

Moving a rule across this line later is expensive by design: it changes
recorded findings, so it takes an evolution row on both ledgers and a record
superseding this one.
