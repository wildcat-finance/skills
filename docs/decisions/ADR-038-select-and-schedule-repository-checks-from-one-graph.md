# ADR-038: Select and schedule repository checks from one graph

## Status

Accepted, 2026-08-25.

## Context

The repository lists its checks as serial commands in `AGENTS.md`. That list
does not say which changed paths own a check, which other scopes consume the
changed surface, or which independent commands may run together. Contributors
therefore tend to run unrelated suites, while the largest Python suite still
runs in one process.

The same test tree creates disposable Git repositories for fixture history.
Those repositories inherited contributor signing configuration, even though
their commits are neither release evidence nor signature test subjects. A
default signer could prompt, stall or fail before the intended assertion ran.

Test discovery is not static. Audit work can add, remove or rename tests, and
some current IDs are generated dynamically and cannot be imported as dotted
names. Source may also change while a local run is in flight. A scheduler must
separate ordinary change between invocations from a changed source during one
attempt, and it must prove that a green result covers the exact tests it found.

## Decision

Use one versioned, declarative graph for repository ownership, checks and named
downstream dependencies. A single runner will combine requested scope with all
actual changed paths, close that set over the graph, take an independent
disposable snapshot, and execute the resulting plan under one process budget.
The graph must account for every governed path mechanically. It will not infer
ownership from runtime imports.

Each attempt discovers a fresh ordered test manifest from its snapshot.
Workers rediscover that same snapshot, verify the complete manifest identity,
and select already discovered test objects by canonical index. Each worker
also derives fixture domains from its own discovery and refuses an assignment
that intersects only part of one of those domains. Matching IDs and a matching
manifest digest are not enough to prove fixture atomicity when import-time
state can change which fixture hooks exist. The coordinator must prove that
assignments are disjoint and that every discovered test has one terminal
disposition before it can report green. An ID either starts and completes
exactly once, or is `fixture-blocked` by a standard class- or module-fixture
`SkipTest` recorded at `unittest`'s suite-owned fixture hook and whose holder
scope matches that discovered test object. A test object calling the result
API directly cannot mint that evidence. Started, completed and fixture-blocked
IDs remain distinct; an ordinary fixture error, unrecognised holder, missing
proof, overlap or duplicate is a scheduler error. The public Elenchus counters
keep standard `unittest` meaning, so a fixture-blocked method is not added to
`testsRun`.

Discovery may use a custom suite iterator, because the coordinator and every
worker consume and compare its resulting manifest. A suite wrapper that
overrides `unittest` execution hooks is refused using raw class-MRO bindings,
not a metaclass-controlled attribute lookup: flattening that wrapper into
shards would discard behavior that can create failures. The checked hook set
includes module transitions and class- or module-fixture exception creation,
not only the public `run` method. Custom `TestCase` execution remains attached
to the selected leaf object and runs normally. The scheduler keeps tests under
a resolved module fixture on one worker and, without one, keeps tests under a
non-default class fixture on one worker. A module with dynamic attribute
lookup, a test class with a custom metaclass, or a class fixture supplied by a
descriptor is conservatively fixture-bearing. Class fixture proof reads raw
class-MRO bindings, so descriptor lookup cannot change between proof and
execution after the scope has already been split. Tests with neither fixture
remain independent timing units. If a required fixture scope reappears later
in the manifest, the smallest containing canonical interval is one domain
rather than two concurrent copies of that fixture state. A module cleanup
registered during discovery has suite-global state in `unittest`, so its
presence conservatively makes the current manifest one domain. Private
assignment and result files live outside the invocation checkout. That
boundary is proved by walking opened directory descriptors to the physical
invocation-root identity, rather than comparing path spellings, so aliases on
a case-insensitive filesystem cannot put worker files inside the checkout.

Cleanup registration can also occur while a test method is running. Before
partitioning, the scheduler inspects inert code objects defined by each test
module for the standard `addModuleCleanup`, `enterModuleContext`,
`addClassCleanup` and `enterClassContext` names, including nested code and
literal attribute names. It follows referenced exact Python functions through
their inert global-helper graph, including directly imported functions,
functions selected from imported modules and exact `functools.partial` or
`partialmethod` wrappers. Referenced function defaults, keyword defaults,
closure cells, bound Python methods and the named instance state used by a raw
Python `__call__` are part of the same inert graph; callable identity ends
cycles. An opaque callable supplies no inert evidence of a cleanup reference
and does not create a fixture domain on that basis alone. A possible module
cleanup makes that module one domain. A possible class cleanup makes its
registering class one domain. The same inert graph retains any concrete
`TestCase` class named through globals, imported modules, defaults, closures,
bound methods, containers or callable state; a registration from one class to
another joins both classes into one domain. This keeps the target registry in
the process where it was registered without collapsing unrelated classes into
one shard.

The inoculation bootstrap treats its AST count as a structural prefilter, not
as proof of runtime discovery. It executes the exact content-bound guard bytes
in an isolated interpreter and requires each mapped method name to appear once
in default `unittest` discovery. The interpreter then wraps only those mapped
methods with runner-owned sentinels that call the original bound guard and
drives the selected cases through the default suite lifecycle. Each sentinel
carries the original method's `unittest` skip and expected-failure metadata,
and static proof refuses direct dunder attribute mutation. Every sentinel and
original guard must execute once and pass, with no method or fixture skip,
setup failure or overridden lookup/dispatch bypass. Import-time decorators or
other side effects therefore cannot leave a skipped, deleted or merely
enumerated guard authorised by its earlier syntax. A guard class may not
replace `TestCase.run`, `TestCase.__call__` or the internal
`TestCase._callTestMethod` dispatch hook, because it could then enumerate the
method or distinguish the verifier's sentinel from the original guard without
executing that original guard. Once the isolated interpreter exits, the
bootstrap drains only result bytes already available on its bounded channel;
a forked descendant retaining the writer cannot extend the discovery call
beyond the configured subprocess timeout. Its direct Python interface
also takes an explicit expected guard-digest map so an exact-parent Elenchus
overlay can bind the overlaid test bytes without changing the verifier's
compiled identity. The command-line path never supplies that argument and
remains bound to the compiled digest map.

A later invocation may have a different manifest without error. A source
change during an attempt supersedes that attempt and permits one fresh retry;
repeated change ends as `unstable-source`, not as a failed test.

An unexpected success is a test failure, not a pass. Each worker also owns an
isolated process group. Once that worker exits, the coordinator gives all
readers one bounded drain interval, requests termination of the original
worker process group, and reports a scheduler error whenever an output
descriptor was retained. The exited worker leader remains waitable and
unreaped until those group signals finish, so its process-group identity cannot
be reused for an unrelated process before signalling. A descendant can create
a new session and escape that group. Its retained descriptor still produces a
bounded red result, with an explicit possible-detachment diagnostic; the
runner does not claim to have terminated that detached process. This keeps
output loss and blocked runner completion outside the green state without
overstating the portable process boundary.

The public Elenchus report stays inside the invocation checkout but outside
every Git control namespace. Existing no-follow, descriptor-bound creation
prevents replacement of worktree paths; excluding `.git` components also
prevents a fresh report from becoming a ref, lock or other repository-control
file.

The runner will derive a conservative default budget from available CPU and
quota signals, apply the same safety cap used for explicit overrides, and
accept a positive explicit override. For cgroup v2 it resolves the current
process's membership from `/proc/self/cgroup` and the cgroup2 controller root
and mount point from `/proc/self/mountinfo`, then reads `cpu.max` from the
member through that mount's controller root. For cgroup v1 it resolves the CPU
controller membership and mount, then reads each `cpu.cfs_quota_us` and
`cpu.cfs_period_us` pair from the member through that mount's controller root.
Both forms use the smallest positive quota. The additive capacity object
exposes the safety cap with the observed signals and effective budget. One
global counter covers suite processes, shards and ordered command groups.
Timing history may balance the current manifest only. It cannot select a test,
suppress execution or retain a pass verdict.

The cumulative bootstrap binds each required regression guard to a fixed guard
surface and one statically provable `unittest` case. A module-level call to a
locally defined helper is treated as dynamic discovery behavior rather than
proof: its import-time effects could replace an otherwise valid static class
binding before `unittest` sees the module. Module discovery hooks and
non-built-in method decorators are refused for the same reason. Bounded record
JSON turns decoder resource failures into one bootstrap refusal. Archive
commit, tree and blob reads recompute their named Git object identities, and a
strict reachable-object check binds nested archive trees before their bytes
can support a current target. Each bounded filesystem read binds a no-follow
pre-open identity to the opened regular descriptor before accepting its
content, so a regular-file replacement cannot substitute bytes between path
inspection and descriptor use.

Snapshot repositories and non-signature test fixtures set repository-local
`commit.gpgsign=false` immediately after creation and before their first
commit. Signature-verification fixtures keep their existing signed, unsigned
and invalid-signature cases. The source checkout, global Git configuration and
contributor keys remain outside this boundary.

## Alternatives

- Set a process-wide signing override and keep the serial command list. This
  could hide a signature-verification defect, leaves fixture construction
  dependent on unmanaged sites, and does not address suite scheduling.
- Select changed files and pass divided dotted IDs to `python -m unittest`.
  Generated IDs are not importable names, separate launchers can exceed the
  intended process limit, and the scheme cannot prove that workers discovered
  the same tests.
- Commit one fixed manifest and permanent shards. Test changes would require
  scheduler maintenance, and new tests could be omitted by stale membership.
- Infer ownership from imports. Imports do not express prose checks, ordered
  build commands, shared contracts or every downstream consumer, so the
  inferred graph would be incomplete without a reviewable place to state the
  missing edges.
- Use the source checkout or a linked worktree as the execution snapshot.
  Either permits source movement during the attempt, and linked worktrees share
  repository configuration with the checkout they came from.

## Consequences

Maintainers gain one reviewable place to update ownership and dependencies.
Unknown or multiply owned paths, stale commands, dependency cycles, manifest
mismatches and incomplete or unproved dispositions refuse green. New, removed
and renamed tests need no scheduler constant; the fresh manifest is
authoritative for its own invocation.

Snapshot creation and worker rediscovery add work before assertions begin, and
the declarative graph becomes a maintained interface. In return, reports can
name the source, plan, capacity, assignments and exact execution record that
produced a verdict. The same record shows fixture-blocked IDs separately and
never describes them as executed. Timing data remains disposable scheduling
advice.

Disposable fixture commits no longer invoke contributor signers. This does not
weaken signed delivery commits or signature-verification tests. Hosted CI,
third-party dependencies and existing direct suite entrypoints remain
unchanged by this decision.
