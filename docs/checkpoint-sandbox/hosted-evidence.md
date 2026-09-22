# Hosted checkpoint evidence

`checkpoint-conformance.yml` runs the owned release suite on `ubuntu-24.04`
x86_64 and `macos-15` arm64. Linux installs `bubblewrap` and
`apparmor-profiles` through apt. It loads the packaged ABI 4.0
`bwrap-userns-restrict` profile after checking SHA-256
`11d39094f044f0cda0febb3ad517b830301da6b2ce929664af09ee9e4dd264f9`.
That profile permits Bubblewrap setup and denies capabilities to its children.
The global `kernel.apparmor_restrict_unprivileged_userns` setting stays `1`,
both profile-local override files must be absent, and the verifier runs
without sudo. The workflow checks that both `bwrap` and `unpriv_bwrap` are
loaded in enforce mode.

Both jobs use the interpreter in `.python-version`, the test dependency lock
and the platform asset from the cosign profile. Missing tools, profile drift,
denied namespace creation and ineffective network denial fail the job. No
positive case may skip.

The workflow checks out the pull request head explicitly. `host.json` records
that actual Git object separately from the event SHA, event head and event
merge SHA. The collector checks the host OS, architecture, tool hashes, source
inventory and fixtures around execution. On Ubuntu, `sandbox_setup` also binds
the installed profile digest, absent local overrides and enabled global user-
namespace restriction before and after execution. GitHub metadata must show
the policy preparation step succeeded. Event identities are recorded context;
the authenticated run's head and the checked source inventory bind the tested
checkout.

## Execution evidence

Each artifact preserves eight files: `host.json`, `direct.stdout`,
`direct.stderr`, `descendant.stdout`, `descendant.stderr`, `release.stdout`,
`release.stderr` and `tests.log`. The streams are the actual process bytes.
The release report's log digest must match `tests.log`. Direct probes and executed
descendant probes each prove all four IPv4/IPv6 bind/connect operations were
denied. The release suite runs all five cosign comparisons and three fresh
workload processes under the existing 512 MiB resident ceiling.

## Admit a completed run

Use a clean checkout of the exact tested head and an authenticated `gh` session.
Get the completed workflow run, attempt and profile artifact ID from GitHub.
The artifact name includes the profile, run ID and attempt:
`checkpoint-ubuntu-24.04-RUN-ATTEMPT` or `checkpoint-macos-15-RUN-ATTEMPT`.

Create `request.json` under `.hexaemeron/sources/ci/ubuntu-24.04/` and another
under `.hexaemeron/sources/ci/macos-15/`. Replace the example IDs and SHA with
those observed for the matching artifact:

```json
{"schema":"checkpoint-hosted-request/v1","run_id":123,"run_attempt":1,"artifact_id":456,"checkout_sha":"0123456789012345678901234567890123456789"}
```

Run the two selected resolvers:

```bash
python3 plugins/hexaemeron/tests/checkpoint_network_design_report.py \
  --candidate bubblewrap-seccomp --criterion hosted-linux \
  --evidence .hexaemeron/sources/ci/ubuntu-24.04 \
  --report .hexaemeron/reports/conformance/bubblewrap-seccomp-hosted-linux.json
python3 plugins/hexaemeron/tests/checkpoint_network_design_report.py \
  --candidate bubblewrap-seccomp --criterion hosted-macos \
  --evidence .hexaemeron/sources/ci/macos-15 \
  --report .hexaemeron/reports/conformance/bubblewrap-seccomp-hosted-macos.json
```

Each resolver authenticates to `github.com`, fetches the run attempt, jobs and
artifact metadata, then downloads the archive by its numeric ID. It requires
the same repository, checkout, attempt, successful job and execution step,
runner label, source inventory and fixture digests. It checks the archive
against GitHub's digest and rereads the metadata before admitting it. Local
metadata files and parser fixtures cannot replace those reads.

GitHub's artifact REST row associates an artifact with a run. It does not
attest which job produced it. The checked workflow, unique artifact name,
matching runner and successful job time window supply that association.
Artifacts from fork repositories remain outside this admission profile.

## Limits and recovery

The ZIP and each member are bounded to 65,536 bytes, with at most 262,144
expanded bytes across the exact eight flat regular members. Admission extracts
nothing to disk. It refuses links, extra or missing members, duplicate JSON
keys, nesting beyond 16 containers and malformed or incomplete execution.
GitHub responses have a 65,536-byte stdout cap, 16,384-byte stderr cap and
60-second command deadline; job discovery refuses more than 100 jobs. The
native report keeps its separate 16,384-byte ceiling. Arbitrary valid Unicode
host labels may still exceed that ceiling and refuse.

Each attempt retains a new `observation-*` directory with the request, API
responses and downloaded archive. Refused observations remain available for
inspection. The collector retains partial output when execution fails. Repair the named
source, tool or host condition, run a fresh workflow attempt, and supply its
new artifact IDs. Never relabel an earlier artifact or overwrite an accepted
design report. A failed or missing host leaves its integration criterion open.

This evidence covers the named executions and their network-denial boundary.
It establishes no archive or filesystem confinement, service acceptance,
aggregate descendant resource limit, production latency or throughput.
