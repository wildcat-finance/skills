# ADR-054: Keep the generated skills.sh payload in tree

## Status

Superseded, 2026-08-30, by ADR-055. This record's measurements stand; its
refusal of relocation does not. It treated a cost of moving discovery as a
loss of it, and it treated a cross-repository push as the only publication
route. Extends ADR-040, which stays accepted.

## Context

ADR-040 made `.agents/skills/promise-machine/` the supported skills.sh package
and gave `scripts/portable_promise_machine.py` ownership of its generated
payload. The payload is a copy of this repository, committed into this
repository, and it is large enough that people keep rediscovering it and
proposing that it live somewhere else.

Measured at `7e97b5195d5b0e43146b4200f26cd41b89003413`:

```
tracked total   3102 files   121305325 bytes
.agents          999 files    21789732 bytes
manifested       994 files    21513368 bytes
```

The payload is 32.2% of the tracked files and 18.0% of the tracked bytes. Every
clone, worktree and cold read carries the canonical tree and a second
near-complete copy of the parts of it the router can reach.

ADR-040 examined five alternatives and rejected each: leaving the router
source-relative, fetching contracts after installation, duplicating a runtime
under every canonical skill, copying the entire repository beneath the router,
and linking outside the router's directory. Every one of them keeps the payload
inside this repository. Holding it outside was never put next to them, so the
size question has no recorded answer to be read against. Issue #940 asks for one.

## Decision

The generated payload stays in this tree. Relocating it is refused on discovery,
not on effort.

`skills.sh.json` sits at the repository root and groups exactly
`promise-machine`. The skills.sh listing and a ref-less
`npx skills add wildcat-finance/skills` both resolve against the default branch.
This repository is in neither `BLOB_ALLOWED_OWNERS` (`vercel`, `vercel-labs`,
`heygen-com`) nor `BLOB_ALLOWED_REPOS` in the skills CLI, so the command falls
through to a shallow clone of the default branch and discovers skills in that
tree. A payload that is not on `main` is not discoverable, and a thin entrypoint
left on `main` to preserve discovery has to source its runtime elsewhere, which
is fetch-after-install or an outside link under another name. ADR-040 rejected
both.

The documented install command is unchanged:

```
npx skills add wildcat-finance/skills --skill promise-machine
```

## What the size figures do not mean

The package sits at 994 manifested files against a `MAX_FILES` of 1,000 and
21,513,368 bytes against a `MAX_BYTES` of 25 MiB in
`tests/test_skills_sh_package.py`. Those two numbers are the skills CLI's
`SKILLS_EXTRACT_MAX_FILES` and `SKILLS_EXTRACT_MAX_BYTES` defaults, and they are
worth keeping, but they do not gate the command above.

They live in the CLI's `download-source.ts` and apply only to its `well-known`
and `download` source types, which are direct `SKILL.md` and archive URLs. The
`github` source type this repository is installed through never consults them.
A reader who notices 994 against 1,000 should not conclude that installation is
about to fail; the ceiling that would actually bite is the repository's own
test, and it bites deliberately.

The real cost is the one measured above, and it is paid on every clone rather
than at install time. It is paid twice on the install itself, because the
shallow clone brings down all 115.69 MiB of the tracked tree in order to copy
20.52 MiB of it out.

## Alternatives

- **A separate repository, generated and pushed by CI on merge.** Removes the
  payload from this tree and breaks both the root grouping and the ref-less
  install, because neither can name a skill that is not on the default branch.
  Needs a repository and a fine-grained token secret: a full mirror cannot run
  under `GITHUB_TOKEN`, as `.github/workflows/sync-skills-marketplace.yml`
  records. It would also inherit the weakness issue #836 records against that
  mirror, that nothing verifies the copy is current.
- **An orphan distribution branch in this repository.** The CLI accepts
  `owner/repo#ref` and clones `--branch`, and the payload carries no
  `.github/workflows/` file, so `GITHUB_TOKEN` could push it and no new secret
  or repository is needed. It still breaks the root grouping and the ref-less
  install, and it changes the documented command to
  `wildcat-finance/skills#dist`.
- **A submodule.** Ordinary clone flows still fetch it, so the per-clone saving
  is largely notional, and copy-mode installers do not traverse submodules,
  which is ADR-040's link objection again.

## Consequences

The measured cost above is accepted and now recorded, so the next reader who
notices the payload's size finds the reason rather than re-deriving it. A guard
in `tests/test_skills_sh_package.py` holds the tracked footprint under a stated
ceiling and names this record when it fails, so growth is refused with the
figure needed to update it rather than passing quietly.

The coupling this keeps is real and is not repaired here. Issue #854 records two
faults in it: the portable sync writes files a subsequent Horos scan cannot see
unless staging happens between them, so the committed boundary describes the
previous tree and `horos check` agrees with it; and
`portable_promise_machine.py check` does not verify import closure, so a mirror
missing a file its own mirrored sources import still exits 0. The working order
stages between sync and scan, inside an alternation. That issue owns the fix.

This decision is contingent on discovery. If the skills CLI gains a way to
install a skill from a non-default ref while still listing it from the default
branch, or if this repository is added to the CLI's blob allowlist, the
relocation options become live again and this record should be revisited rather
than cited.
