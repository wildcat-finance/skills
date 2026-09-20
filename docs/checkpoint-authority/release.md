# Checkpoint authority protocol release

This is the public guide to verifying one released checkpoint authority
protocol offline. It covers what the release contains, how a consumer pins it,
what the offline verifier establishes, and what it refuses to establish.

The protocol version is `checkpoint-authority/v1` and the signature profile is
`dsse-p256-sha256-der/v1`. The selected verification model is `ordered-replay`,
recorded in `adr/verify-checkpoint-authority-by-ordered-replay`.

## What the release contains

[`release-manifest.json`](../../plugins/hexaemeron/skills/fiat/checkpoint-authority/release-manifest.json)
lists every component by exact bytes under seven names:

- `schemas`: one closed JSON Schema per record type, nineteen in all.
- `verifier`: the `checkpoint_authority` package and its command line.
- `fixtures`: the four corpus manifests, which bind their own fixture files transitively.
- `capabilities`: the native capability and limit record.
- `native`: the native source pin, separate from the authority pin.
- `tools`: the cosign and schema-oracle tool profile.
- `documentation`: this guide, the protocol reference and the two corpus READMEs.

The manifest never hashes itself. Its `external_pins` field names the two
values a consumer must hold elsewhere: `source_commit` and
`release_manifest_sha256`.

## How a consumer pins the release

[`protocol.lock.json`](protocol.lock.json) is the example consumer lock. Copy
it, then replace `authority.source_commit` with the full 40- or 64-character
commit that carries the release. The example ships forty zeros because no file
inside a release can name the commit that contains it.

Authority and native toolchain pins stay separate. `authority.source_commit` is
the Skills commit for this protocol; `native.source_commit`,
`native.executable_sha256` and `native.profile` pin the native checkpoint
release, which versions independently. A lock refuses any mutable reference:
`main`, `latest`, `HEAD` and a `refs/` path are all rejected before a digest is
read.

Verify a checkout against a lock:

```bash
python3 plugins/hexaemeron/skills/fiat/scripts/checkpoint_authority.py release
python3 plugins/hexaemeron/skills/fiat/scripts/checkpoint_authority.py lock \
  --lock docs/checkpoint-authority/protocol.lock.json --source-commit <commit>
```

`release` rebuilds every component digest from the tree and refuses an altered,
missing, extra or stale component. `lock` adds the lock comparison and refuses
a mixed component set, an unsupported native pin, an unsupported cosign or
Python pin, and a source commit that disagrees with the one the caller
asserted. Neither command runs Git; the commit is the caller's own answer.

## Verifying a history offline

```bash
python3 plugins/hexaemeron/skills/fiat/scripts/checkpoint_authority.py verify \
  --history history.jsonl --bootstrap bootstrap.json --tools tools.json \
  --native native.json --freshness freshness.json --presence presence.json
```

Every operand is a file the caller names. The verifier follows no link, opens
nothing a record carries, fetches nothing, signs nothing and writes nothing
except a report named with `--out`, which it creates exclusively and never
replaces. `--history` is JSON Lines, one DSSE envelope per line.
`--bootstrap` carries the operator-approved trust roots. `--tools` pins each
public-key verifier by absolute path and SHA-256; a record can never select
one.

The two optional operands are the ones that decide current state:

- Without `--freshness`, every accepted row keeps `current_eligibility:
  unknown` and `current_eligibility_established` stays false. Offline evidence
  cannot show that a newer denial does not exist.
- Without `--presence`, a complete publication reports `unavailable`. Copy
  availability is the caller's own scoped read-back observation, never an
  inference from a historical copy claim.

A successful history is reported as `historical: valid`. That is a statement
about the past. It is not an acceptance, a stream permit or a current
authorization.

## Reproducing the demonstration

```bash
python3 plugins/hexaemeron/skills/fiat/scripts/checkpoint_authority.py demonstrate \
  --tools tools.json --cosign /path/to/cosign --cosign-sha256 <digest>
```

The demonstration rebuilds the release manifest twice from the same tree,
checks the example lock, replays the committed history from files alone, runs
every declared hostile release case, and agrees with one independent pinned
verifier under network denial. It reports its own wall time, JSON decode count,
traced allocation peak and peak resident set size, and the declared ceilings
those ran under. Those are observations on one machine, not a latency or
throughput claim.

[`fixtures/release-hostile.json`](../../plugins/hexaemeron/skills/fiat/checkpoint-authority/fixtures/release-hostile.json)
records eighteen hostile lock cases with the code each must refuse by. The five
cosign cases are a valid envelope, an altered payload, an untrusted key, a
wrong payload type and a double-hashed payload. Transparency log checking is
disabled, so no keyless identity or transparency claim follows.

The demonstration selects macOS `sandbox-exec` or Linux x86_64 Bubblewrap
with a seccomp filter. Before cosign runs, IPv4 and IPv6 bind/connect probes
must each receive `EPERM`, directly and again after a descendant executes.
Namespace isolation alone permits loopback and fails this gate. The closed
report binds the host ABI, launcher, complete policy, filter and both probe
programs by SHA-256. Its policy identity includes the fixed launcher arguments.
Missing, changed, incomplete or mismatched evidence refuses.

On Ubuntu 24.04, install the packaged launcher with `sudo apt-get install
bubblewrap`. The measured package is `0.9.0-1ubuntu0.3`; each execution hashes
the actual installed binary and proves the policy works. The caller needs
unprivileged namespace creation and kernel seccomp support. The verifier does
not run with sudo, and the program does not change host security settings.
An absent package, denied namespace capability or unsupported ABI refuses;
there is no unsandboxed retry. Linux arm64 is not a supported backend.

The Linux filter checks its syscall ABI, refuses x32 and other architectures,
and denies socket operations and io_uring submission. Bubblewrap consumes
stdin to install it; the fixed cosign command reads files. The explicit `/dev`
bind lets the Go runtime reopen `/dev/null` afterwards. Network and PID
namespaces, a new session and dropped capabilities accompany the filter;
existing timeout, output and process cleanup limits still apply.

The macOS policy remains `(version 1)(allow default)(deny network*)` on its
existing arm64 and x86_64 backends. The measured Linux profile is Ubuntu 24.04
x86_64. Fresh hosted Ubuntu 24.04 x86_64 and macOS 15 arm64 conformance remain
integration gates for this delivery; no new macOS x86_64 execution is claimed.
Report-shape fixtures construct an explicit descriptor without preparing a
host. Positive conformance still prepares and executes the actual backend.

Hosts without an available mechanism refuse with `network-denial-unavailable`;
an ineffective mechanism refuses with `network-denial-probe`. Changed launcher
or policy identity refuses with `network-denial-changed`. Check the package and
namespace/seccomp permissions, then rerun the complete criterion. An offline
flag supplies no denial evidence. The ordinary history verifier does not depend
on this demonstration mechanism. The root and device binds retain the caller's
filesystem permissions; they do not establish archive or filesystem containment,
service acceptance, or aggregate descendant resource limits.

Regenerate the corpus, the manifest and the lock example together, in that
order, and check them without writing:

```bash
python3 plugins/hexaemeron/tests/checkpoint_authority_release_corpus.py --write
python3 plugins/hexaemeron/tests/checkpoint_authority_release_corpus.py --check
```

The conformance resolver for the criterion is:

```bash
python3 plugins/hexaemeron/tests/checkpoint_authority_conformance.py \
  --candidate ordered-replay --criterion released-interoperability \
  --report .hexaemeron/reports/ordered-replay-released-interoperability.json
```

The criterion also measures
[`study-workload.json`](../../plugins/hexaemeron/skills/fiat/checkpoint-authority/fixtures/study-workload.json).
Its mapping covers the study's exact 1,280-event schedule across 512 decisions:
256 authorize/finalize/permit/deny sequences and 256 cancellations. Required
protocol evidence brings the complete history to 9,225 signed records and
18,807,776 envelope bytes. The original unsigned study corpus and its
measurements remain unchanged. The reporter reproduces that corpus's digest,
checks every mapped event against its authenticated record, and compares the
final decision projection with the study's digest.

Three fresh processes replay the same committed bytes. The report preserves
each wall time, traced allocation peak and peak resident set size, plus median
and nearest-rank p95 wall time, hardware, runtime and host-contention limits.
With three samples, p95 is the largest observed value. The criterion requires
each resident peak below 512 MiB, zero retained record bodies and one
journal-body decode per signed record. Each body is decoded inside its signed
statement; envelope carriers require separate JSON parses. The report counts
carriers, statements, additional body parses, native results and producer
ledger lines separately, and includes the total JSON parses. These measurements
establish no latency or throughput improvement.

## Supported limits

The release declares its ceilings in the manifest's `limits` and
`resource_limits` fields. A verification refuses by a named limit rather than
degrading: at most 65,536 journal entries and 256 MiB of envelope bytes per
invocation, 64 KiB per control record, JSON nesting depth 32, 64 MiB per
component file, 1 MiB for the release manifest and 16 KiB for a consumer lock.
The declared peak resident ceiling is 512 MiB. A partial replay never produces
a complete-head verdict.

## Dependency handoff

| Consumer | Depends on | Does not receive |
| --- | --- | --- |
| Service A | The released schemas, the offline verifier, the lock format and the record vocabulary. | Service HTTP, SQL, upload or download code, live key custody, deployment. |
| Skills 862 | The protocol release as a pinned dependency of the checkpoint programme, and the native pin kept separate from the authority pin. | Physical removal, controller fencing, operator procedure. |
| Skills 863 | The record definitions and the freshness contract its control journal must satisfy, plus the external signer format. | A production signer, a control journal implementation, cloud deployment. |

A consumer holds the lock and recomputes every digest. It does not trust a
version string, a branch name or a directory listing.

## What this release does not establish

Production issuer roots, cloud retention, live storage independence and service
runtime enforcement remain external obligations. The committed fixtures are
signed with ephemeral test keys and carry synthetic native attestations; no
native command ran and no private key is retained. An Ariadne pass binds
evidence references and predicate gates and authenticates no signature: the
predicate states in its own output that signatures, issuer authority, complete
journal replay and current eligibility were not checked by Ariadne. Native
containment issues #1647, #1648 and #1649 remain open.

## Recovery

If a component disagrees, the command names the component class and the code.
Re-fetch the release at the commit in the lock rather than repairing a file in
place: a repaired file changes the component digest and the manifest is stale
against it. If the release manifest itself is absent or unreadable, the
verification refuses with `manifest-missing`; the lock's
`release_manifest_sha256` is the only value that can confirm a replacement.
