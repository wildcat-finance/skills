# Support macOS and Linux checkpoint sandboxes

Assuming, unless corrected:

1. This run answers [Skills #1794](https://github.com/wildcat-finance/skills/issues/1794) on `66f52785813a8453e7c7d54f2371aa8f6e465640`. Its five acceptance conditions are the authorised scope.
2. The existing boundary denies network operations by the independent verifier and its descendants. It gives no promise about hostile archive containment, filesystem confinement, aggregate descendant resources, service acceptance or the Elenchus worker sandbox.
3. The initial measured Linux profile is Ubuntu 24.04, native x86-64, with an unprivileged caller and the apt Bubblewrap package. The macOS profile to revalidate is macOS 15 arm64. Other Linux ABIs remain unsupported; other host profiles acquire no passing claim from these measurements.
4. Python means the repository's exact 3.14.6 interpreter with `plugins/hexaemeron/tests/requirements.lock`. The installed Hexaemeron 1.6.64 controller supplies Fiat 6.70.1 and Protasis 6.15.1 throughout this run. The older portable installation does not control it.
5. A focused GitHub Actions matrix can supply the missing macOS executor. Listing existing workflows succeeded. Reading Actions administration permissions returned 403; the ability to publish and run the new workflow remains unproved until attempted. That unknown does not supply a passing host result.

## 1. Problem, user and proving path

Checkpoint contributors need release conformance to run on supported Linux and macOS hosts. At the starting commit, `checkpoint_authority/network.py` accepts only Darwin and always launches `/usr/bin/sandbox-exec`. The release report validator and its synthetic test builder call that preparation function. A resource-ceiling unit case therefore errors on Linux before checking the ceiling.

The exact issue reproduction ran twice with Python 3.14.6. Both attempts exited 1 with `network-denial-unavailable`; their identical log digest is `80b505c524cb8adb870726a0c9dba8c15ff0b9af809f7c2373fcc95a52139ee2`. The commands and raw logs are in `.hexaemeron/sources/study/linux-baseline.json` and its two named logs. This is the current failure to repair, not a requirement to obtain a macOS baseline before starting.

A working prototype selects one explicit host backend, refuses unavailable capabilities without running the verifier, proves the four existing IPv4/IPv6 bind/connect operations are denied in the verifier and an executed descendant, and binds that observation to the executed policy and host. Report-shape unit cases construct explicit fixtures independently of a host launcher. Positive conformance still executes the real launcher and pinned cosign.

The proving command remains:

```bash
python3 plugins/hexaemeron/tests/checkpoint_authority_conformance.py --candidate ordered-replay --criterion released-interoperability --report .hexaemeron/reports/ordered-replay-released-interoperability.json
```

It runs the owned release suite, exact discovered case denominator, real five-case cosign comparison and three fresh-process workload samples. Its design report and adjacent conformance evidence must agree, bind the actual source/fixture set, and contain no failures, errors, skips, expected failures or incomplete cases. A raw report that merely contains the right counters is insufficient.

Negative demonstrations cover an ineffective policy, missing launcher/capability, unsupported ABI, changed launcher or policy, wrong mechanism, missing or altered probe evidence, incomplete execution, timeout, excess output and descendants surviving their leader. The original four operations remain individually observable even if Linux refuses at socket creation before the requested bind/connect. An unrelated error such as connection refusal never counts as policy denial.

The delivery has two steps. Step 1 contains the support specification, executable scaffold and smallest complete Linux backend plus report-fixture repair, with the regenerated release inputs required for every local check to pass. Step 2 adds independent hostile cases and the focused two-host conformance workflow. A scaffold-only first step would leave the known Linux failure in the mandatory Hexaemeron suite. Each step must end with passing root and Hexaemeron suites; pending hosted evidence blocks integration.

```success-criteria
{
  "schema": "protasis-success-criteria/v1",
  "criteria": [
    {
      "id": "backend-and-fixture-repair",
      "claim": "Linux host selection and host-independent report fixtures pass their regression guards, with unsupported hosts and changed evidence refused.",
      "step": 1,
      "command": "python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report .hexaemeron/reports/step-1-hexaemeron.json"
    },
    {
      "id": "step-one-local-green",
      "claim": "The smallest complete backend, release regeneration and declared ownership pass every selected repository check.",
      "step": 1,
      "command": "python3 scripts/run_checks.py --scope hexaemeron --jobs 8 --report .hexaemeron/reports/step-1-checks.json"
    },
    {
      "id": "complete-regression-suite",
      "claim": "The complete Hexaemeron regression suite passes after the independent hostile and hosted-evidence checks are added.",
      "step": 2,
      "command": "python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report .hexaemeron/reports/step-2-hexaemeron.json"
    },
    {
      "id": "step-two-local-green",
      "claim": "The independent hostile tests, focused workflow, interpreter inventory and generated release are covered by passing selected repository checks.",
      "step": 2,
      "command": "python3 scripts/run_checks.py --scope hexaemeron --jobs 8 --report .hexaemeron/reports/step-2-checks.json"
    }
  ]
}
```

## 2. Prior art and inherited work

The two latest merged pull requests on this subject were read in full through their preserved GitHub API bodies: [PR #1770](https://github.com/wildcat-finance/skills/pull/1770), merged 2026-09-19 at 21:03:39 UTC, released the protocol and real network-denied interoperability; [PR #1730](https://github.com/wildcat-finance/skills/pull/1730), merged at 21:03:24 UTC, supplied ordered replay. Their response bytes are `.hexaemeron/sources/study/pr-1770.json` and `pr-1730.json`. The release changes most directly relevant here are commits `4c45438d562ffecdfe9ca97385a8b00c583c837e` and `957b84a2dc1e67d5c0b5b79355ad49b300cb2fb6` from PR #1770.

PR #1770's macOS result passed 59 tests and 352 subtests with evidence digest `ad3d6e3dd3929ae576822b378a93bcbf8a68c8edff45323fde506afae1f2ae4a`. That is historical evidence for its pinned source, not a fresh result for this run. PR #1730's Ariadne comparison concerns parsed JSON values, not byte equality. Historical acceptance does not establish current eligibility; missing freshness stays unknown and missing presence stays unavailable.

The Surveyor read every byte of these three authoritative audit sources, without applying the reading boundary:

| Source | Rounds | Review record |
| --- | --- | --- |
| `plugins/hexaemeron/audit/AUDIT.md` | 2 | Plugin controller and hook history |
| `audit/rounds/fiat-1676-publish-checkpoint-authority-protocol-and-r.md` | 8 | Complete checkpoint-authority delivery |
| `audit/rounds/fiat-1755-repair-checkpoint-key-marker-false-positive.md` | 3 | Adjacent checkpoint retry and key-marker repair |

The source hashes, every round heading, finding row with its original status, `Covered`, `Not checked`, `Elenchus verdict` and `Leads not pursued` are preserved in `.hexaemeron/sources/study/audit-source-review.json`. Missing legacy fields remain explicitly unknown. The pinned-Python whole-set synopsis check exited 0 for 99 rows; `.hexaemeron/sources/study/audit-synopsis-check.log` has digest `6dad676481ae3cfed388206a47eed2b066f2f3e319bfc946352db551ef59da8e`. The inventory uses those current portable views, while this review used the complete authoritative sources.

The fixed findings remain fixed. Plugin findings F-01 through F-09 retain their recorded fixes; F-10 remains the accepted, documented fail-open hook behavior. Checkpoint finding S2-R1-01 remains fixed in `f84f11d702de47e7140cb1327f17f0eec300e3bb` and `991bf9492bc4a4f88ae3258102a1557604dafad1`: cleanup signals an exited leader's process group, handles Darwin's unreaped-leader permission race, and preserves the original output-limit refusal. Retain the verifier and reporter descendant guards and the permission-retry guard. S4-R1-01 and S4-R1-02 remain the package-count and parsed-JSON wording fixes in `23f55f3439e5aa238f5b6eb2bc08c5cefcf4065f`. S5-R1-01 and S5-R1-02 remain fixed in `a684890d10f663380a3e78a1e2ddd25f5bb1e993`; retain both transitive-path/row validation guards and the historically qualified package measurements. The #1755 rounds recorded no findings.

The S2-R1, S4-R1 and S5-R1 Elenchus verdicts remain `inconclusive`: all 12 worker launches were refused under the pinned no-child sandbox. Independent red/green checks did not change those verdicts. [#1541](https://github.com/wildcat-finance/skills/issues/1541) remains open; this run neither changes that sandbox nor establishes the historical cause. Legacy missing coverage fields do not become clean coverage. Other deferred leads in the preserved source, including trusted-local native diagnostics, self-derived hostile codes, bounded parse-before-verify, package-version resolution, warning output and shared harness report output, retain their original scope and disposition.

Current issue states were fetched into `.hexaemeron/sources/study/carryover-status.json`. Skills #1676 and #1755 are now closed; their historical references remain unchanged. Service intake stays with [Skills #862](https://github.com/wildcat-finance/skills/issues/862) and [fiat-checkpoints #1](https://github.com/wildcat-finance/fiat-checkpoints/issues/1). Worker isolation stays with [#873](https://github.com/wildcat-finance/skills/issues/873); production issuer/custody and storage work tracked by [#863](https://github.com/wildcat-finance/skills/issues/863) and [#992](https://github.com/wildcat-finance/skills/issues/992) is outside this boundary. Native diagnostic, custody/pathname and restore-concurrency limitations remain open in [#1647](https://github.com/wildcat-finance/skills/issues/1647), [#1648](https://github.com/wildcat-finance/skills/issues/1648) and [#1649](https://github.com/wildcat-finance/skills/issues/1649). The separate native-guard-admission run remains halted until this prerequisite clears its baseline. [fiat-checkpoints PR #4](https://github.com/wildcat-finance/fiat-checkpoints/pull/4) and its signed checkpoint are preserved. [#1756](https://github.com/wildcat-finance/skills/issues/1756) remains separate checkpoint work.

Independent review found no still-open source finding in this complete reviewed set that this implementation must inoculate. `.hexaemeron/sources/study/expected-finding-ids.json` records the independently derived empty set. The closed claim below means only that; it does not say Linux support already works or that #1794 is absent. #1794 is a new compatibility requirement with a reproduced present failure and a Step 1 behavioral guard. No invented audit round or reopened fixed finding supplies its identity. The parent must join this inventory to the real runbook through `load_checked_inventory(..., expected_ids=[])` before product work.

```known-failure-inventory
{
  "schema": "protasis-known-failure-inventory/v1",
  "source_views": [
    {
      "id": "plugin-audit",
      "path": "plugins/hexaemeron/audit/AUDIT_SYNOPSIS.md",
      "source_sha256": "8acff29ed567c97902941a85d72e41171c10850de6aa898b5d50564248eac28f",
      "view_sha256": "2e919d920cd952a837bee6069251b710a9543df37514d7248a996d61766138cd"
    },
    {
      "id": "checkpoint-release",
      "path": "audit/rounds/fiat-1676-publish-checkpoint-authority-protocol-and-r.synopsis.md",
      "source_sha256": "5578e5ead1ecf97b56368c38f32c1ea5934406e4b2852be081bae9bff1b0c4d7",
      "view_sha256": "b6a449a7901d6c8636ba46da999cf5d21e66a1c6d31b60f34e6354689a5070a9"
    },
    {
      "id": "checkpoint-key-marker",
      "path": "audit/rounds/fiat-1755-repair-checkpoint-key-marker-false-positive.synopsis.md",
      "source_sha256": "d6d7740138bac3e87d0437a9b7caa6386d59f6d71cba0b49c90c3001765c14cc",
      "view_sha256": "017110f75f527ccc9a9a49264ae0aa43b05000c74a4cb7bf1fc0553da0b439a1"
    }
  ],
  "findings": [],
  "no_known_findings": {
    "source_views": [
      {
        "id": "plugin-audit",
        "source_sha256": "8acff29ed567c97902941a85d72e41171c10850de6aa898b5d50564248eac28f",
        "view_sha256": "2e919d920cd952a837bee6069251b710a9543df37514d7248a996d61766138cd"
      },
      {
        "id": "checkpoint-release",
        "source_sha256": "5578e5ead1ecf97b56368c38f32c1ea5934406e4b2852be081bae9bff1b0c4d7",
        "view_sha256": "b6a449a7901d6c8636ba46da999cf5d21e66a1c6d31b60f34e6354689a5070a9"
      },
      {
        "id": "checkpoint-key-marker",
        "source_sha256": "d6d7740138bac3e87d0437a9b7caa6386d59f6d71cba0b49c90c3001765c14cc",
        "view_sha256": "017110f75f527ccc9a9a49264ae0aa43b05000c74a4cb7bf1fc0553da0b439a1"
      }
    ],
    "consuming_step": 1,
    "surveyor_assertion": "no-known-findings"
  }
}
```

Outside the organisation, [Bubblewrap's upstream contract](https://github.com/containers/bubblewrap) describes a mechanism whose protection depends on the caller's arguments. Its network namespace alone retains loopback, which the local probe confirmed. The [version 0.9.0 manual source](https://github.com/containers/bubblewrap/blob/v0.9.0/bwrap.xml) describes the seccomp descriptor and namespace arguments used here. The [kernel seccomp contract](https://docs.kernel.org/userspace-api/seccomp_filter.html) supplies filter inheritance across fork/exec and requires checking syscall architecture. [Firejail](https://github.com/netblue30/firejail) is another apt-available tool, but its broader profile/runtime model was not executed in this study. It is prior art, not a scored candidate. Plain `unshare --user --map-root-user --net` refused the UID-map write on this host; that observation supplies no passing alternate construction.

## 3. Constraints and non-goals

The exact starting commit is `66f52785813a8453e7c7d54f2371aa8f6e465640`, on the run worktree named in `.hexaemeron/study-next.json`. The repository requires Python 3.14.6 and minor `==3.14.*`. The locked test dependencies are attrs 26.1.0, jsonschema 4.25.1, jsonschema-specifications 2025.9.1, referencing 0.37.0, rpds-py 2026.6.3 and typing-extensions 4.16.0. Commands that launch `python3` must inherit the pinned interpreter at the front of PATH. The prepared temporary venv and cosign path are execution conveniences, not portable product paths.

The measured Linux host is Ubuntu 24.04, kernel `6.8.0-139-generic`, x86_64, glibc 2.39. `/usr/bin/bwrap` is apt package `bubblewrap 0.9.0-1ubuntu0.3 amd64`, launcher SHA-256 `e318903862396f96de3df57264e0158682b952fd3fb53ac23d876413e7b30f71`. The real Linux cosign 3.1.3 binary matches the committed tool profile at `4629c757b7618056f8ddd7e2625ae9fdd94c0372a65049520bc7d9df9efc7f71`. Do not repin a tool to make a test pass. The profile's Linux arm64 cosign entry does not establish a Linux arm64 sandbox backend.

Always select by an explicit supported platform/ABI, validate capabilities by execution, preserve fixed time/output budgets, bind the launcher and verifier before and after launch, and keep generated files under their owners. Ask first only if completion would require a new privilege model, a new ABI promise, broader containment, unrelated controller changes or service deployment; none is necessary for the selected construction. Never fall back to an unsandboxed verifier, treat `--offline` as denial proof, turn a positive case into a skip, edit old receipts/source pins, or broaden Elenchus to permit children.

An unprivileged product caller must be able to create the namespaces and install the filter. The apt package may need administrator installation; the verifier invocation does not use sudo, raise the caller's privileges or require container-runtime privileges. Missing package, user-namespace/AppArmor restriction, absent kernel seccomp capability, unavailable launcher and unknown ABI cause an actionable refusal. OS package custody and the kernel remain trusted. Same-user concurrent binary replacement is detected where observed by the existing pin checks; this change does not make pathname execution race-free against a hostile host.

The implementation is a normal Fiat generation increment from 6.70.1, with the corresponding Hexaemeron package release generated through repository owners. The `delegated-task-identity` frontier, its digest, open status and [held job #1212](https://github.com/wildcat-finance/skills/issues/1212) stay unchanged. Solidity and the vendored Solidity audit/fuzz tools are inapplicable to this Python/workflow change; the controller records the precise waiver.

## 4. Candidate constructions and selected contract

Two constructions were executed with the same final filesystem, PID and session arguments. Both retain the existing macOS backend; they differ only in the Linux network restriction.

| Candidate | Construction and trade |
| --- | --- |
| `bubblewrap-netns` | Apt Bubblewrap network/PID namespaces with `/` and `/dev` bound. No filter bytes, but loopback bind succeeds, so it cannot satisfy this release boundary. |
| `bubblewrap-seccomp` | The same launcher plus the measured native x86-64 seccomp filter. It denies socket/network and io_uring syscalls, at the cost of an explicit ABI policy and 392 filter bytes. |

The exact comparison command was `python3 .hexaemeron/sources/study/selection_probe.py`. It uses an in-memory boundary substitution around the unchanged `signatures._run` and `demo.interoperability`; this is feasibility evidence, not product conformance. Its source, observations and supporting artifacts are pinned in `.hexaemeron/sources/study/selection-inputs.json`. Every resolved matrix report was produced by its recorded `design_report.py` command; their execution ledger is `selection-report-executions.json` in the same directory.

| Measured criterion | Namespace only | Namespace plus seccomp |
| --- | --- | --- |
| Four EPERM results, direct and after exec | Fails | Passes |
| Complete existing demo, including five real cosign outcomes | Refuses at denial probe | Passes, 871.490 ms |
| Three-sample median launch wall time | 40.021 ms | 40.302 ms |
| Policy filter bytes | 0 | 392 |
| Exited leader releases descendant lock | Passes, 40.945 ms | Passes, 39.188 ms |
| 300 ms timeout refuses and releases descendant lock | Passes, 319.454 ms | Passes, 316.676 ms |
| 70,000-byte stdout hits existing output cap | Passes, 24.208 ms | Passes, 24.786 ms |

The time reports round each raw median upward to 41 integer milliseconds because Protasis's unit requires integers. No performance advantage is claimed. `.hexaemeron/design-evidence.json` contains two candidates, nine criteria and all 18 cells. Five selection criteria cover correctness, time, space, compatibility and recovery; ten executed reports resolve them. The failed denial and interoperability gates eliminate `bubblewrap-netns`, leaving `bubblewrap-seccomp` as the unique eligible candidate. Report-projection validation first rejected fractional milliseconds; the original reports and reason are retained under `.hexaemeron/sources/study/report-shape-failure/`.

The Linux construction is:

```text
/usr/bin/bwrap --unshare-net --unshare-pid --bind / / --dev-bind /dev /dev --die-with-parent --new-session --cap-drop ALL --seccomp 0 -- <pinned-verifier> <fixed-arguments>
```

The current bounded runner passes filter bytes through its existing `input_bytes` temporary-file stdin. Bubblewrap consumes and closes descriptor 0. Earlier experiments failed real cosign because the root bind made `/dev/null` unusable when the Go runtime reopened closed stdin. `device-controls.json` proves the cause; adding the explicit `/dev` bind made all five verifier cases agree. Preserve those failed experiments and the final successful captures. This interface is valid for the current fixed cosign invocation, which consumes files rather than stdin; a future stdin-consuming verifier requires a separate interface decision.

The filter checks native audit architecture `0xc000003e`, kills a non-native or x32 syscall ABI, returns EPERM for native syscall numbers 41 through 55, 288, 299, 307, 425, 426 and 427, and permits other native calls. These numbers cover the native socket operations and the io_uring entry points that could otherwise submit network work. The research filter digest is `8b97e4880f19e22990d9994580127bd38249e9f51594f1e3f63218edcd286412`. Retain a reviewed, deterministic source for the filter; do not depend on a compiler or architecture guess at runtime.

The shipped Linux policy identity must bind the ABI, exact fixed launcher argument vector and exact seccomp bytes together, rather than calling the filter digest the whole policy. Keep the filter digest available for diagnosis. Its policy digest may therefore differ from the research filter digest. The macOS policy remains `(version 1)(allow default)(deny network*)` with the existing launcher. A closed backend descriptor owns preparation, argv construction, policy identity, actual launcher pin and expected probe identity. Do not accept a mechanism solely because a report names it.

Preparation and validation have distinct inputs. Pure report validation receives an explicit expected descriptor prepared by the execution owner; its unit fixtures construct that descriptor without launching a sandbox. The positive `execute()` path prepares and validates the actual host, executes the real suite, and checks the returned network observation against that descriptor. Recheck source and tool identities around execution. Both the direct four-operation probe and an executed descendant must be bound to the conformance evidence with exact result/count expectations. The original four-operation probe can remain as the direct test, with separately named descendant evidence; neither fixture construction nor a mocked probe supplies the positive result.

Keep exact report field sets, type checks, source denominators and refusal semantics. A changed policy/argv/ABI, wrong mechanism, altered launcher, wrong executable, missing result, extra field, wrong count, wrong error, stale source or incomplete case list must refuse. The validator should report the boundary that failed without exposing raw fixture contents or host paths.

Four conformance criteria remain pending. `product-linux` and `hostile-evidence` must resolve before Step 2 opens; `hosted-linux` and `hosted-macos` block integration. Their exact commands and future report paths are already in the design record. Step 1 adds the product and hostile operations of `plugins/hexaemeron/tests/checkpoint_network_design_report.py`; Step 2 adds its hosted-artifact operations. The product criterion reruns the existing release owner and verifies its source-bound evidence. The hostile criterion executes the new regression cases with complete test accounting. Hosted criteria read retained GitHub run/job metadata and downloaded conformance artifacts under `.hexaemeron/sources/ci/ubuntu-24.04/` and `.hexaemeron/sources/ci/macos-15/`; they require the real expected runner profile, completed successful jobs, the exact checked-out Git object, tool hashes, raw release/network outputs and matching product/fixture digests. Record the PR event head and merge identities separately; `GITHUB_SHA` alone does not establish which tree was tested. A missing artifact, wrong checkout, synthetic report, skip or manually asserted macOS value refuses. The unselected candidate's pending cells grant no obligation or approval for that rejected construction.

The focused workflow uses explicit Ubuntu 24.04 x86_64 and macOS 15 arm64 labels, the exact Python pin and the existing cosign profile. It installs only the Linux apt dependency needed by this boundary, runs real conformance on both hosts, and preserves reports and profile data even on failure. Add its ownership/path-filter entries to `tests/test_python_contract.py`; `.github` is already owned by check-map scope `ci`. This adds focused checkpoint coverage without restoring the removed aggregate CI gate. A local result cannot substitute for either named hosted artifact.

The parent must fetch the actual completed jobs and their artifacts from GitHub, retaining run/job URLs, authenticated readback metadata and downloaded-byte digests. The hosted resolver checks those real captures against the checked-out object and raw execution outputs. Its local fixture tests establish parser behavior only; neither a hand-written capture nor a successful JSON validation establishes that a hosted execution happened. If the platform evidence cannot be obtained, the corresponding integration gate stays pending.

## 5. Risk register

```risk-register
backend-selection | OS, ABI and launcher discovery | Supported profiles select one backend; absent capabilities and all other ABIs refuse before verifier execution.
network-denial | Verifier and executed descendant network syscalls | IPv4/IPv6 bind/connect require EPERM; namespace-only and allow-all policies fail the real probe.
filter-abi | Native syscall table and alternate submission paths | Validate audit architecture, reject x32/non-native execution and deny socket plus io_uring entry points.
policy-identity | ABI, launcher arguments and filter bytes | Mutating any policy constituent changes identity and causes evidence validation to refuse.
launcher-pin | Launcher and independent verifier execution | Hash before and after; changed or unavailable files refuse through existing bounded pin checks.
stdin-device-contract | Seccomp descriptor consumption and cosign startup | Real five-case cosign evidence proves the closed stdin and explicit /dev bind construction.
descendant-cleanup | Leader exit, timeout and output overflow | Real lock-holder child cannot retain its lock after cleanup; preserve original cleanup and Darwin retry guards.
fixture-execution-separation | Synthetic report fixtures versus real enforcement | Unit builders need no host launcher; positive criterion must still prepare and execute the actual backend.
report-forgery | Closed conformance report and expected descriptor | Missing, extra, mistyped, stale or altered evidence and incomplete case accounting refuse.
host-profile-evidence | Hosted jobs and downloaded artifacts | Both actual OS profiles, exact source commit and matching artifact digests are required before integration.
resource-ceilings | Native pipes, deadlines and release workload | Existing timeout/output limits and 512 MiB workload RSS ceiling remain enforced without skips or weaker assertions.
release-consistency | Source closure, manifests, copies and consumer lock | Owning generators reproduce every changed release input and the checked runner covers every changed path.
scope-claims | Network denial versus broader isolation | Documentation and reports make no archive, filesystem, service, no-child or untested-ABI claim.
historical-evidence | Existing source pins, fixed findings and receipts | Preserve exact historical bytes/statuses and existing guards; new evidence names its own tested source.
```

## 6. Glossary seeds

| Term | Meaning in this delivery |
| --- | --- |
| Backend | One supported host's launcher, immutable policy description and probe contract. |
| Network denial | Required network operations receive the declared denial, including after verifier exec inheritance. |
| Policy identity | Digest binding the enforced policy's exact constituent bytes, ABI and fixed argv. |
| Host profile | Recorded OS, architecture, kernel/runtime capabilities and launcher identity for an executed result. |
| Selection evidence | Measured research used to choose a construction before product implementation. |
| Conformance evidence | Fresh execution of the owned product suite with complete accounting and checked source/fixture identity. |
| Unsupported | A host or capability for which execution refuses; it is never a skipped positive case. |

## 7. Sources

Repository links below are pinned to the starting commit. Run-local evidence paths are literal paths below `.hexaemeron`; their bytes and digests are preserved with the study.

- [Root repository contract](https://github.com/wildcat-finance/skills/blob/66f52785813a8453e7c7d54f2371aa8f6e465640/AGENTS.md), [Promise Machine](https://github.com/wildcat-finance/skills/blob/66f52785813a8453e7c7d54f2371aa8f6e465640/PROMISE_MACHINE.md), [Hexaemeron contract](https://github.com/wildcat-finance/skills/blob/66f52785813a8453e7c7d54f2371aa8f6e465640/plugins/hexaemeron/AGENTS.md) and [Fiat ledger](https://github.com/wildcat-finance/skills/blob/66f52785813a8453e7c7d54f2371aa8f6e465640/plugins/hexaemeron/skills/fiat/EVOLUTION.md).
- [Existing network backend](https://github.com/wildcat-finance/skills/blob/66f52785813a8453e7c7d54f2371aa8f6e465640/plugins/hexaemeron/skills/fiat/scripts/checkpoint_authority/network.py), [bounded verifier runner](https://github.com/wildcat-finance/skills/blob/66f52785813a8453e7c7d54f2371aa8f6e465640/plugins/hexaemeron/skills/fiat/scripts/checkpoint_authority/signatures.py), [demo](https://github.com/wildcat-finance/skills/blob/66f52785813a8453e7c7d54f2371aa8f6e465640/plugins/hexaemeron/skills/fiat/scripts/checkpoint_authority/demo.py) and [release report validator](https://github.com/wildcat-finance/skills/blob/66f52785813a8453e7c7d54f2371aa8f6e465640/plugins/hexaemeron/skills/fiat/scripts/checkpoint_authority/release_conformance.py).
- [Release tests](https://github.com/wildcat-finance/skills/blob/66f52785813a8453e7c7d54f2371aa8f6e465640/plugins/hexaemeron/tests/test_checkpoint_authority_release.py), [report-validation tests](https://github.com/wildcat-finance/skills/blob/66f52785813a8453e7c7d54f2371aa8f6e465640/plugins/hexaemeron/tests/test_checkpoint_authority_release_conformance.py), [release suite](https://github.com/wildcat-finance/skills/blob/66f52785813a8453e7c7d54f2371aa8f6e465640/plugins/hexaemeron/tests/checkpoint_authority_release_suite.py) and [corpus generator](https://github.com/wildcat-finance/skills/blob/66f52785813a8453e7c7d54f2371aa8f6e465640/plugins/hexaemeron/tests/checkpoint_authority_release_corpus.py).
- [Plugin audit source](https://github.com/wildcat-finance/skills/blob/66f52785813a8453e7c7d54f2371aa8f6e465640/plugins/hexaemeron/audit/AUDIT.md), [#1676 audit source](https://github.com/wildcat-finance/skills/blob/66f52785813a8453e7c7d54f2371aa8f6e465640/audit/rounds/fiat-1676-publish-checkpoint-authority-protocol-and-r.md) and [#1755 audit source](https://github.com/wildcat-finance/skills/blob/66f52785813a8453e7c7d54f2371aa8f6e465640/audit/rounds/fiat-1755-repair-checkpoint-key-marker-false-positive.md). The source-review inventory retains the complete per-round fields.
- `.hexaemeron/sources/preflight/issue-value.json`, `.hexaemeron/sources/study/host-packages.json`, `linux-baseline.json`, `selection-inputs.json`, `selection-probe.json`, `selection-report-executions.json` and the retained failed projection reports establish the local observations. The selection observation digest is `284bffdadb69f8aab34840cbb855c49ced790b6e5d99bf85877e5de1c964184f`.
- `.hexaemeron/sources/linux-feasibility/bubblewrap-probe.json`, `prototype-integration.json`, `prototype-native-runs.json`, `prototype-limits.json`, `device-controls.json` and the v1/v2/v3 failed prototypes preserve the independent feasibility sequence. Their scope remains research.
- [Bubblewrap](https://github.com/containers/bubblewrap), its [0.9.0 manual](https://github.com/containers/bubblewrap/blob/v0.9.0/bwrap.xml), the [kernel seccomp documentation](https://docs.kernel.org/userspace-api/seccomp_filter.html), [Firejail](https://github.com/netblue30/firejail) and [GitHub's hosted-runner profile reference](https://docs.github.com/en/actions/reference/runners/github-hosted-runners) supply the external prior art and planned executor contract. Actual executor identity must still come from each run.

## 8. Ephoros: questions and signals

Apply the [Ephoros contract](https://github.com/wildcat-finance/skills/blob/66f52785813a8453e7c7d54f2371aa8f6e465640/plugins/hexaemeron/skills/ephoros/SKILL.md). This is a bounded CLI and CI workflow; it needs reports and actionable refusals, not a new alert service.

| Operator question | Evidence to retain |
| --- | --- |
| Which backend and policy actually ran? | Supported profile, mechanism, launcher/verifier digests, complete policy identity, probe digest and source commit. |
| Did denial apply to descendants, and was a weak policy caught? | Named direct/exec operation outcomes, exact expected errno/count, and separate ineffective-policy negative result. |
| Did a bound stop execution and release its children? | Existing refusal code, timeout/output cap, elapsed observation and descendant lock-release result. |
| Which required host result is missing? | Workflow run/job identity, actual runner OS/architecture, exact head SHA, artifact digests and a pending/refused conformance criterion. |

Use existing bounded completion/refusal events and extend the closed evidence that owns the backend. Correlate by source commit, policy digest and run/job identity; do not log tokens, raw signatures, arbitrary child output or unbounded paths. Preserve fixed error codes and place short installation/capability guidance in the release guide. A failed CLI gate or workflow job is the operator-visible signal.

## 9. Phylax: boundaries and controls

Apply the [Phylax contract](https://github.com/wildcat-finance/skills/blob/66f52785813a8453e7c7d54f2371aa8f6e465640/plugins/hexaemeron/skills/phylax/SKILL.md). The trusted components are the kernel, installed launcher package, pinned Python/tool binaries and reviewed policy constructor. Inputs crossing the boundary are host capability facts, subprocess results, fixture reports and hosted artifacts.

Construct argv as a fixed list with a literal separator and no shell. Keep the runner's restricted environment, closed inherited descriptors, temporary files, output caps, deadline and process-group cleanup. The PID namespace adds Linux descendant teardown; it does not replace the runner's existing cleanup. The root and device binds preserve filesystem access already held by the caller. Explicitly deny namespace fallback and weaker policy retries.

Require exact closed report shapes, source and fixture digests, actual operation outcomes and the expected backend descriptor at admission. Fixture-only descriptors cannot enter the execution owner as successful host evidence. Validate artifact/run identity before interpreting a hosted passing report; artifact names alone are untrusted. Changed sources require fresh evidence. Continue the existing no-follow bounded file readers and transitive-path validation; this delivery must not weaken their guards.

CI obtains the pinned cosign binary from its existing declared distribution and verifies its digest before execution. Preserve the committed historical native fixture pin. Provisioning can use the runner's package manager; the sandbox command itself remains unprivileged. No service credential, App key, signing key or network credential belongs in the workflow or artifact.

## 10. Metron: budgets and measurement

Apply the [Metron contract](https://github.com/wildcat-finance/skills/blob/66f52785813a8453e7c7d54f2371aa8f6e465640/plugins/hexaemeron/skills/metron/SKILL.md). This task makes no optimisation claim. Preserve the existing verifier timeout of 60 seconds, probe timeout of 10 seconds, stdout cap of 65,536 bytes, stderr cap of 16,384 bytes and release-execution deadline of 1,800 seconds. Preserve the declared peak-RSS ceiling of 512 MiB and current workload bounds.

The complete released-interoperability command in section 1 remains the product measurement command. It executes the unchanged 9,225-record, 18,807,776-byte workload in three fresh processes, retains no record bodies and records the environment, median, nearest-rank p95 and per-sample peak RSS. With three samples, p95 is the maximum; it is not a population latency claim. The research comparison uses three identical `print('ready')` launches per candidate and records raw elapsed times. Contention is uncontrolled, so those measurements justify no throughput or latency improvement.

The Linux filter adds 392 bytes in the measured construction; the final complete policy encoding also includes its ABI and argv. No aggregate descendant memory/CPU guarantee is added. If the fixed conformance deadline or RSS ceiling fails on either supported host, preserve the failed sample and find the cause; do not enlarge the ceiling or drop the workload to obtain green.

## 11. Fail-closed behavior and Elenchus guards

Apply the [Elenchus contract](https://github.com/wildcat-finance/skills/blob/66f52785813a8453e7c7d54f2371aa8f6e465640/plugins/hexaemeron/skills/elenchus/SKILL.md). A launch denial, incorrect errno, ineffective policy, unsupported ABI, changed input, failed child or incomplete report stops the release criterion. Retrying after a dependency or host configuration repair means rerunning the complete affected criterion; it never promotes old or partial evidence.

Before the Step 1 product edit, preserve a focused pure-Python behavioral guard that fails on the parent for the Linux host-selection or fixture-construction bug and passes only after its repair. It may stub trusted capability/pin readers and construct synthetic report descriptors; it must not spawn a native child inside the no-child guard runner or claim that its stub proves enforcement. Preserve the twice-reproduced real baseline separately. The independent real direct/descendant/ineffective-policy, timeout and cosign cases supply enforcement evidence through the conformance owner and CI.

Retain `test_timeout_reaps_descendants_after_verifier_parent_exits`, `test_group_permission_after_exit_is_retried_without_ignoring_denial`, `test_execution_reaps_descendants_after_reporter_parent_exits`, `test_transitive_paths_refuse_before_opening_any_component` and `test_malformed_transitive_rows_refuse_before_opening_any_component`. Their old findings are already fixed and must not be falsely presented as current parent-red inoculations.

New tests must fail under the corresponding weakened implementation: omitted Linux backend, host-coupled fixture builder, removed filter, allow-all filter, wrong ABI/argv identity, changed launcher, missing descendant proof, forged result/count, incomplete case accounting and omitted cleanup. Unsupported profiles have explicit refusal cases. The integrated Linux and macOS execution cases cannot use mocks or skips to pass. If an Elenchus run is inconclusive, retain that verdict and its actual reason; separate test passes cannot rename it guarded.

## 12. Hypomnema: decisions and homes

Apply the [Hypomnema contract](https://github.com/wildcat-finance/skills/blob/66f52785813a8453e7c7d54f2371aa8f6e465640/plugins/hexaemeron/skills/hypomnema/SKILL.md). The expensive decisions are the narrow two-profile support contract, syscall/ABI policy ownership, stdin filter transport, explicit `/dev` bind, and separation of fixture validation from execution evidence. Their accepted construction and rejected namespace-only alternative belong in the next normal generation row of `plugins/hexaemeron/skills/fiat/EVOLUTION.md`. That existing ledger is the durable decision home; no second ADR scheme is introduced.

```design-bridge
schema | hypomnema-design-bridge/v1
decision | bubblewrap-seccomp
record | plugins/hexaemeron/skills/fiat/EVOLUTION.md
```

Step 1 writes the support/refusal/operator contract into `docs/checkpoint-authority/release.md` and `plugins/hexaemeron/skills/fiat/references/checkpoint-authority.md`, with API docstrings beside the backend/validator signatures. Explain the nodev/stdin trap at the fixed argv construction. The release guide names tested profiles, package/capability setup, exact conformance command, missing evidence and the filesystem/service limits. Step 2 documents the focused workflow and how to recover its host reports.

The corpus owner `plugins/hexaemeron/tests/checkpoint_authority_release_corpus.py --write` regenerates affected demo/corpus manifests, release manifest and consumer-lock example in dependency order; its `--check` must reproduce them. Register any new source in the complete conformance dependency set and package inventory. Generate the portable runtime with `scripts/portable_promise_machine.py sync`, keep plugin manifests and marketplace versions consistent through their owners, and regenerate Horos boundary when classified bytes change and census before every recorded green. `scripts/run_checks.py` must own every changed path; the workflow's interpreter/path-filter inventory lives in `tests/test_python_contract.py`.

The study, design record, all ten selection reports, raw observations, source review and failed experiments remain distinct from later product acceptance. Sapheneia shapes the complete candidate, Imprimatur checks it, Vulgate changes only the surface and a final Imprimatur pass checks the exact accepted bytes. Protected identifiers, hashes, dates, findings/statuses, unknowns, links and all required fences survive those passes. Brevitas does not shorten away this completeness-bound study. The parent alone admits the study, derives the runbook and writes controller receipts.
