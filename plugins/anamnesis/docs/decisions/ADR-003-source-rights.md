# ADR-003: Admit a source only against an explicit rights basis

## Status

Accepted, 2026-08-31.

## Context

Most audit reports worth preserving are readable on the public internet. It
does not follow that they may be copied into a redistributable corpus. GitHub's
own guidance is that a public repository without a licence reserves its
author's rights, and Sherlock states that its published reports carry protocol
teams' permission, which is a permission held by Sherlock rather than one
granted to every reader.

Some material is worse than merely unlicensed. A report under embargo, or one
naming an unfixed live vulnerability, must not be admitted at all, and the
corpus has to be able to say so rather than quietly excluding it.

A corpus that guesses here fails in a way nobody notices until it is
distributed.

## Decision

Every source carries an explicit `rights_basis` from a closed set: a licence, a
written permission, a contract, or the digest-only rule that preserves an
identifier and a hash while refusing the bytes. Public visibility is not a
rights basis and is not accepted as one.

Every source also carries a `disclosure` class. `public` admits derived text.
`restricted` admits identifiers and digests alone, and its bytes never reach a
release or an adapter. `embargoed` is refused at admission.

Admission is fail-closed. A missing, unknown or unrecognised basis is a
refusal. So is a digest mismatch, a size above the declared cap, a symlink or
other non-regular path, and a path that escapes the policy root.

Preservation and release are separate decisions. A source may be admitted for
preservation under digest-only rights and still be refused at release.

## Alternatives

**Treat public as permissive.** It is what most scraped datasets do. It is
wrong on the law, and it puts the obligation on whoever redistributes the
corpus next rather than on the person who built it.

**Store bytes and decide rights at release.** Defers the question to the point
where the corpus is largest and the answer is most expensive. It also means the
corpus holds bytes it may never have been allowed to hold.

## Consequences

The pilot is smaller than the available material, and some genuinely useful
reports enter as identifier and digest alone. That is the intended trade.

A rights basis is a recorded claim, not a legal opinion. Admission establishes
that a basis was declared and recognised; it does not establish that
redistribution is lawful beyond what that basis records.

Egress control has one place to live, and a restricted source cannot reach an
output by accident because the check runs before the write rather than after.
