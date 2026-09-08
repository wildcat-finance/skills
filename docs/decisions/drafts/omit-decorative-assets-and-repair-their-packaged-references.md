# Decision: Omit the character portraits and repair their packaged references

## Status

Draft, 2026-09-08. Numbered at integration, because this repository assigns
decision numbers against the default branch at merge.

## Context

The generated skills.sh payload measures 24,956,643 bytes against the
26,214,400-byte `SKILLS_EXTRACT_MAX_BYTES` default, 95.2020 per cent, leaving
1,257,757 bytes. The sibling file ceiling in `tests/test_skills_sh_package.py`
has moved four times, and its comment records why each raise stayed honest: the
pressure is repository-wide, no per-plugin trim closes it, and shipped package
content is not trimmed to hold a file count. The byte figure cannot be answered
that way, because it is another project's default rather than this
repository's constant. Filed as
[#1467](https://github.com/wildcat-finance/skills/issues/1467).

Measured from the manifest, 32 character portraits under `assets/characters`
directories account for 8,788,268 bytes, 35.21 per cent of the payload and its
largest single class. `.horos/boundary.json` already classifies every one as
`"category": "binary"`, `"grade": "hard"`, so the repository's own reading
boundary states that no agent reads them. They are also not what is growing:
the published package at `wildcat-finance/skills-runtime` carries the same 32
images at the same byte total as this tree.

Omitting them leaves 27 `<img src=...>` references in packaged documents
pointing at files the package no longer carries: 26 in a `SKILL.md` and one in
`plugins/hexaemeron/AGENTS.md`. An operator decision taken on 2026-09-08 refused
that outcome and required the references to be removed or rewritten in the
packaged copies. This record covers both halves, because the second is the
condition on which the first was accepted.

The accepted design and its comparison evidence are recorded in the study and
design record this delivery commits.

## Decision

Three parts.

**Omit the portraits.** Declare `assets/characters/**` and
`plugins/*/assets/characters/**` a ninth omission class in
`scripts/portable_promise_machine.py`, with its reason in the generated
manifest, and drop `assets/characters/promise-machine.png` from `ROOT_FILES`.
The files stay tracked in this repository, as the eight existing omission
classes keep theirs. Nothing is deleted to buy margin.

**Repair the references in the packaged copies.** Inside `expected_files()`,
which is the single place packaged bytes are produced and digested, replace each
`<img>` tag whose resolved target is absent from the published set with an HTML
comment naming the omitted path. A remote or `data:` source is left alone; so is
a tag whose target still ships. The repository's own copies of those documents
are unchanged, and the transform is deterministic, idempotent and confined to
the matched tag span, each checked by measurement rather than argued.

**Restate the source binding rather than drop it.**
`test_manifest_binds_every_runtime_file_to_source_bytes` asserts at line 188
that every packaged file equals its repository source byte for byte, and asserts
at lines 205 to 210 that the packaged router equals
`.agents/skills/promise-machine/SKILL.md`. A rewritten document fails both. Each
manifest row therefore carries the transform it was built under, and the amended
assertion checks that applying the declared transform to the source bytes yields
the packaged bytes. Deleting the assertion instead would trade a dangling
reference for a lost guarantee.

Separately, move the byte assertion in `tests/test_skills_sh_package.py` off
`MAX_BYTES` onto a stated threshold of 20,971,520 bytes, so the guard fails with
5,242,880 bytes of margin left rather than at the ceiling.

## Alternatives

Omitting the portraits and leaving the references dangling recovers 970 more
bytes and needs no transform. It is refused by the operator decision of
2026-09-08, which is why this record exists in the form it does.

Splitting the runtime into two published packages recovers more headroom, but
breaks ADR-040's dependency closure: a two-way partition leaves 14 links in
authoritative documents resolving outside their own package, and it changes the
published install address, which cannot be undone by a commit in this
repository alone.

Documenting `github` as the only supported install route, and moving the guard
threshold without omitting anything, each recover no margin at all and leave the
next delivery meeting the same assertion with no remedy in its own scope.

Deleting content to buy margin is refused by the filing observation and by the
reasoning the package test's own comment has applied four times.

## Consequences

The payload falls to 1,291 files and 16,169,345 bytes, 61.68 per cent of the
extract cap, margin 10,045,055. The compressed transfer falls from 12,872,124
bytes to about 4,027,666, from 122.8 per cent of the 10,485,760-byte
`SKILLS_DOWNLOAD_MAX_BYTES` default to about 38.4, so the transfer stage of the
`download` route stops refusing this package; the compressed figure was measured
without the repair's 970 extra uncompressed bytes. The file count stays above
that CLI's 1,000 default, so that route is not fully restored and this record
does not claim it is. No `<img src=...>` in any of the 458 packaged Markdown
documents resolves to a path the package does not carry.

The cost is a weakened guarantee about packaged bytes. Until now every packaged
file was a verbatim copy of a tracked file and a shipped assertion said so;
afterwards the guarantee is "verbatim, or the declared transform of verbatim".
Every later question about what an install received is answered under the weaker
rule, and a second transform will be cheaper to add than this one was. That, not
the reversal cost, is why this decision earns a record.

Four bindings were checked and do not collide. `SOURCES.md` holds no per-file
digests. No audit document is packaged, so the byte-pinned audit records are out
of reach; `plugins/*/audit/**` is an existing omission class and top-level
`audit/` is never enumerated. The Horos census and `.horos/boundary.json` take
their universe from `git ls-files`, and `.gitignore` excludes the generated
runtime, so a packaged-only transform never reaches them. The router-selection
corpus holds its quoted sentences against repository copies, not packaged ones,
and quotes no `<img>` line.

Reversing the omission means republishing a larger payload to installs that have
already taken the smaller one. The threshold integer is not part of that cost
and can be moved by a commit.
