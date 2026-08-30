# ADR-055: Publish the skills.sh payload from its own repository

## Status

Accepted, 2026-08-30. Supersedes ADR-054. Extends ADR-040, which stays accepted.

## Context

ADR-054, accepted earlier the same day, kept the generated payload in this tree.
It was reviewed and reversed. Two of its grounds did not hold.

It said a separate repository "breaks both the root grouping and the ref-less
install, because neither can name a skill that is not on the default branch."
That is true of this repository's grouping only. A separate repository carries
its own `skills.sh.json` and its own install address, so discovery moves rather
than ends.

It said the arrangement needs a fine-grained token, because a full mirror cannot
run under `GITHUB_TOKEN`. That applies to a cross-repository push. This
repository is public, so the job runs in the destination, clones the source, and
commits to itself with its own token.

What ADR-054 measured stands. The payload was 999 tracked files and 21,789,732
bytes against a tracked tree of 3,102 files and 121,305,325 bytes: 32.2% of the
files and 18.0% of the bytes.

## Decision

The generated runtime is published from `wildcat-finance/skills-runtime` and no
longer committed here. The documented install becomes:

```
npx skills add wildcat-finance/skills-runtime --skill promise-machine
```

A scheduled job in the destination clones this repository hourly, regenerates
the package with `scripts/portable_promise_machine.py package`, verifies it, and
commits only when the bytes changed. A failed verification publishes nothing.
An install can therefore be up to an hour behind this repository's `main`. That
lag is the accepted cost of the split.

Four authored files stay here at their existing paths:
`.agents/plugins/marketplace.json`,
`.agents/skills/promise-machine/SKILL.md`,
`.agents/skills/promise-machine/PORTABLE.md` and
`.agents/skills/promise-machine/scripts/verify_runtime.py`. `repo_contract.py`
binds two of them by constant, the Promise contract names the router inside a
closed quotable set replicated across five documents, and
`plugins/sapheneia/tests/test_sapheneia.py` reads it. Moving them would be a
contract change for no packaging benefit. Only the generated runtime is heavy,
and only it leaves.

The router keeps working in a source checkout. ADR-040 records that it detects
one and reads the real tree; the generated runtime exists to serve installs.
This repository therefore stops advertising a skills.sh install, and
`skills.sh.json` is removed, because it would otherwise name a skill this tree
cannot serve.

## What the destination cannot do for itself

`GITHUB_TOKEN` cannot write under `.github/workflows/`, so the job cannot update
its own definition. That is worth keeping: a compromised generation step cannot
widen what runs next. The consequence is that a workflow change needs a person
holding `workflow` scope to push it to the destination. Its canonical copy is
`distribution/skills-runtime/sync.yml` here, and the job compares itself against
that copy on every run and fails when they differ.

Two organisation rulesets initially refused the destination's pushes, `16257211`
on `main` and `16257446` on every branch, neither carrying bypass actors.
`skills-runtime` is now excluded from both. That exception is confined to a
repository holding only generated files, written only by its own job, and it
does mean the destination has no signed-commit or required-review enforcement.
The source keeps both.

## Alternatives

- **Keep the payload in tree.** ADR-054's position. Rejected: the per-clone cost
  above is paid by everyone, on every clone and every cold read, to serve
  installs alone.
- **Push from this repository on merge.** Needs a fine-grained token stored as a
  secret, and buys latency below the hour already accepted.
- **Publish release tarballs.** The skills CLI's archive path applies 25 MiB and
  1,000-file extract caps, which the package sits close to at 21,513,368 bytes
  and 994 files, and a `github` source install would stop working.
- **A submodule.** Ordinary clones still fetch the payload, so the saving is
  largely notional, and copy-mode installers do not traverse submodules.

## Consequences

Clones of this repository lose 995 files and roughly 21 MB. The generator is now
the only thing that produces a package, and the package guarantees are asserted
against a tree generated during the test run rather than one committed here, so
they stay true of what is actually published.

An install can be an hour stale. The destination records the exact source commit
in its `README.md`, so which commit a published package came from is answerable
from the artefact. Issue #836 records that same question as unanswerable for the
older marketplace mirror.

The sync ordering and import-closure faults #854 records move with the generator
and are not repaired here.
