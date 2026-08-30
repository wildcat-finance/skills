# ADR-055: Stage the portable sync and check mirror closure differentially

## Status

Accepted, 2026-08-30. Closes the tooling gap recorded as `S4-R1-03` during the
skills#329 run and filed as
[skills#854](https://github.com/wildcat-finance/skills/issues/854).

## Context

Two generated artefacts could describe a tree that does not exist, and both
reported success while doing it.

`portable_promise_machine.py sync` writes the portable runtime mirror.
`horos.py scan` builds its universe from `git ls-files`, which reads the index.
Run in that order without a stage between them, the scan cannot see what the
sync just wrote, so the boundary describes the previous tree and `horos check`
agrees with it, because it recomputes from the same index. The failure is
silent locally and loud in CI, which is the wrong way round for a generated
artefact: the person who could fix it in one command sees green.

Separately, `check` compares a declared file set against digests and never asks
whether the mirrored sources resolve their own relative imports. The mirror's
file set is built from the tracked sources, so an untracked source never
reaches it while the files importing it do. During skills#329 that left the
mirrored `HonestAccessHook.sol` importing `./IRoleProvider.sol` with no such
file beside it, a runtime that could not compile, and `check` exited 0 over it.

## Decision

`sync` stages the mirror directory it writes, so the documented order is
correct as written. The pathspec is the mirror alone and the call goes through
the existing `_git_environment()`. Where git cannot answer for the root, or
where the repository ignores the mirror, staging is skipped with a named reason
and `sync` still exits 0.

`check` resolves the relative imports in the mirrored Solidity sources and
refuses when a target resolves in the canonical source and not in the mirror.
The check is differential, not absolute. A target is normalised and refused
when it is absolute or when the result escapes the tree root; a `..` that stays
inside resolves normally.

## Alternatives

Making `scan` refuse while untracked files sit under a classified path was
rejected. It fires in every working tree holding an untracked file under such a
path, which is most of them during ordinary work, and a gate that fires
constantly is one people learn to pass with a flag.

Documenting the alternation loop was rejected. A document does not move the
signal, and the signal arriving after a push is the defect.

Failing on any dangling import was rejected because it is not implementable
against this tree. `plugins/horos/examples/fixture-sol/Market.sol` imports
`./interfaces/IERC20.sol` and `./libraries/MathUtils.sol`, and neither exists in
the mirror or in the source. It is a single-file fixture for the Solidity
outline extractor whose imports were never meant to resolve, so an absolute
check would have gone red on the tree it shipped with. Closing that would have
needed an exclusion list that rots, or an edit to a fixture that is correct as
it stands.

Refusing every `..` segment was rejected on measurement: 218 of the mirror's
265 relative imports use one, so the rule would have skipped 82 per cent of the
surface and the check would have passed by not looking.

## Consequences

`sync` now writes to the git index, which its name does not advertise. A caller
running it in a dirty tree finds mirror paths staged that they did not stage.
That is the cost of making the obvious order correct, and it is bounded to one
directory.

Differential closure says nothing about an import that resolves in neither
tree. `Market.sol` holds two of those and will continue to. A reader who wants
absolute closure has to understand why the weaker property was chosen, which is
what this record is for.

The check reads Solidity as text rather than parsing it, so an import inside a
block comment or a string literal would be read as an import. The mirror
carries none today. Buying comment awareness would mean a Solidity toolchain
dependency this packaging script does not otherwise need.

Non-relative imports stay out of scope. A bare-scope or remapped target is
skipped, and resolving one belongs to whoever owns the Solidity build.
