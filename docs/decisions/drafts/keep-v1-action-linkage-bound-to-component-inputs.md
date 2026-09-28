# Decision: Keep the V1 action linkage bound to its component inputs

## Status

Accepted, 2026-09-28, for issue #1963. Step 1 publishes it in the numberless draft home; integration assigns its number.

## Context

Issue #1963 maps the historical Wildcat V1 estate for issues #1378 and #1387. No single Git commit reproduces that estate. Four accepted compiler inputs cover seven concrete contexts: the factory input carries the market, controller and factory; the sentinel input carries the sentinel and the escrow it creates; the arch controller and the mixed-source lens each have their own. The lens input matches no whole-tree commit, and five equivalent core commits cannot identify the factory deployer's checkout. The accepted corpus is private. The study at `docs/kickoff/1963/study.md` records these limits.

## Decision

Store each accepted input's source-reference manifest once, and have each concrete context name the input it binds to (`shared-input-index`).

- Every source-file row carries path, SHA-256, size and line count, never source text. The checker pins each input's projection independently of the bundle manifest.
- The callable denominator is derived from compiler ABI and AST output, separately from the authored action and linkage rows. The checker pins its count and projection digest, so a joint omission from both refuses.
- A reviewer other than the linkage producer reviews the final linkage bytes. The review binds their exact digest, so any later semantic edit invalidates it.
- Raw archive members, compiler inputs and compiler outputs stay in ignored local research. Admission against them reports digests and counts only.

## Alternatives

`component-copies` gives every context a complete copy of its input's source-reference manifest, so each context reads alone. Its selection recipe was 29,333 bytes against 16,678 for the shared index, with a median of 7 ms against 4 ms for seven samples of 100 parse-and-hash loops. Both kept four recoverable input identities, bound all seven contexts and carried no source payload. The copies lost because they repeat identity records without adding evidence. These single-machine probe values say nothing about the final checker's performance.

## Consequences

A context cannot drift from its input: the checker refuses a context bound to another input, a file marked as a context that no context names, and a source reference outside its input's recorded files and lines. Eventless and unresolved actions stay in the denominator with their reasons. The accepted exceptions remain explicit rather than resolved: the lens mixed-source limit, the sentinel's own pin and the unresolved core commit.

The checker establishes byte identity, membership and a recorded review binding. It does not prove the reviewer's identity or judgement, observed execution, capture completeness, source-to-bytecode identity, runtime emitter fidelity or protocol safety. Recovering source bytes requires the private accepted corpus; losing it would need a separate preservation choice.
