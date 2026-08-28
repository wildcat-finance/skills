## Step 1, round 1 -- 2026-08-28T06:17:48Z

Audit schema: fiat-audit-round/v2

Covered: jobspec-substitution=reviewed; policy-derivation-drift=reviewed; transport-confusion=not-applicable; frame-exhaustion=not-applicable; schema-smuggling=not-applicable; credential-crossing=not-applicable; origin-confusion=reviewed; dns-rebinding=not-applicable; redirect-tunnel=not-applicable; feature-escape=reviewed; quota-race=not-applicable; token-undercount=reviewed; cancellation-race=not-applicable; expiry-replay=reviewed; response-flood=not-applicable; response-schema=reviewed; cross-job-state=reviewed; receipt-content=reviewed; diagnostic-consent=reviewed; provider-retention=reviewed; provider-exfiltration=reviewed; dependency-smuggling=reviewed; partial-receipt=not-applicable; secret-response-echo=not-applicable; cleanup-gap=not-applicable

Not checked: the Pashov Solidity suite was waived because issue #700 is an off-chain model-proxy delivery and Step 1 produces no Solidity; guest framing, live credentials, DNS and TLS, redirects, provider transport and responses, quota concurrency, cancellation, runtime expiry, durable receipts, and cleanup belong to Steps 2 through 4; the #698 signed-JobSpec join, #699 VM channel, #702 Fiat adapter, a live provider, native Windows, and a slow remote regular filesystem were not exercised; provider non-retention and non-exfiltration are not claimed

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R1-01 | medium | plugins/hexaemeron/skills/phylax/scripts/model_proxy_lib/canonical.py | The bounded reader opened an accepted-job candidate before checking its file kind without nonblocking mode, so a FIFO with no writer held activation indefinitely instead of refusing with `MP100`. | fixed in this commit; FIFO timeout guard parent-red and fixed-green |
| S1-R1-02 | medium | plugins/hexaemeron/skills/phylax/scripts/model_proxy.py | Argument parsing ran outside the value-free diagnostic boundary, so an unknown option echoed its supplied value, including the synthetic credential canary, in free-form stderr. | fixed in this commit; no-echo and exact-option guard parent-red and fixed-green |
| S1-R1-03 | low | plugins/hexaemeron/skills/phylax/scripts/model_proxy_lib/canonical.py | The exported canonicalizer called `.encode()` on a non-string object name and leaked an `AttributeError` traceback instead of returning the bounded wrong-scalar refusal. | fixed in this commit; non-string-key guard parent-red and fixed-green |

Leads not pursued: POSIX nonblocking mode prevents special-file open hangs but does not impose a wall-clock deadline on reads from a slow regular filesystem; no remote-filesystem input profile exists in this component, so the trusted local supervisor boundary remains explicit rather than claiming a time bound it does not enforce. Repeated `--accepted-job` or `--expect` options still use argparse's last value; no untrusted argv merger or supervisor adapter exists in Step 1, and #702 owns construction of that fixed trusted invocation. Policy compilation validates the accepted expiry and duration but does not compare expiry with the current clock; Step 4 owns activation-time and per-admission wall and monotonic expiry enforcement. The synthetic accepted-job evidence is not a signed #698 acceptance receipt, the loopback profile makes no live provider call, and the provider non-exfiltration limitation remains explicit.

## Step 1, round 2 -- 2026-08-28T07:13:17Z

Audit schema: fiat-audit-round/v2

Covered: jobspec-substitution=reviewed; policy-derivation-drift=reviewed; transport-confusion=not-applicable; frame-exhaustion=not-applicable; schema-smuggling=not-applicable; credential-crossing=not-applicable; origin-confusion=reviewed; dns-rebinding=not-applicable; redirect-tunnel=not-applicable; feature-escape=reviewed; quota-race=not-applicable; token-undercount=reviewed; cancellation-race=not-applicable; expiry-replay=reviewed; response-flood=not-applicable; response-schema=reviewed; cross-job-state=reviewed; receipt-content=reviewed; diagnostic-consent=reviewed; provider-retention=reviewed; provider-exfiltration=reviewed; dependency-smuggling=reviewed; partial-receipt=not-applicable; secret-response-echo=not-applicable; cleanup-gap=not-applicable

Not checked: the Pashov Solidity suite was waived because issue #700 is an off-chain model-proxy delivery and Step 1 produces no Solidity; guest framing, live credentials, DNS and TLS, redirects, provider transport and responses, quota concurrency, cancellation, runtime expiry, durable receipts, and cleanup belong to Steps 2 through 4; the #698 signed-JobSpec join, #699 VM channel, #702 Fiat adapter, a live provider, native Windows, and a slow remote regular filesystem were not exercised; provider non-retention and non-exfiltration are not claimed

Elenchus verdict: null

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

Leads not pursued: POSIX nonblocking mode prevents special-file open hangs but does not impose a wall-clock deadline on reads from a slow regular filesystem; no remote-filesystem input profile exists in this component, so the trusted local supervisor boundary remains explicit rather than claiming a time bound it does not enforce. Repeated `--accepted-job` or `--expect` options still use argparse's last value; no untrusted argv merger or supervisor adapter exists in Step 1, and #702 owns construction of that fixed trusted invocation. Policy compilation validates the accepted expiry and duration but does not compare expiry with the current clock; Step 4 owns activation-time and per-admission wall and monotonic expiry enforcement. The synthetic accepted-job evidence is not a signed #698 acceptance receipt, the loopback profile makes no live provider call, and the provider non-exfiltration limitation remains explicit.

## Step 2, round 1 -- 2026-08-28T08:33:34Z

Audit schema: fiat-audit-round/v2

Covered: jobspec-substitution=reviewed; policy-derivation-drift=reviewed; transport-confusion=reviewed; frame-exhaustion=reviewed; schema-smuggling=reviewed; credential-crossing=not-applicable; origin-confusion=not-applicable; dns-rebinding=not-applicable; redirect-tunnel=not-applicable; feature-escape=reviewed; quota-race=not-applicable; token-undercount=reviewed; cancellation-race=not-applicable; expiry-replay=not-applicable; response-flood=not-applicable; response-schema=reviewed; cross-job-state=reviewed; receipt-content=not-applicable; diagnostic-consent=reviewed; provider-retention=not-applicable; provider-exfiltration=not-applicable; dependency-smuggling=reviewed; partial-receipt=not-applicable; secret-response-echo=not-applicable; cleanup-gap=not-applicable

Not checked: the Pashov Solidity suite was waived because issue #700 is an off-chain model-proxy delivery and Step 2 produces no Solidity; live credentials, DNS, TLS, HTTP, redirects, provider-native requests and responses, atomic quotas, concurrency, cancellation, runtime expiry, durable receipts, secret-echo checks, and terminal cleanup belong to Steps 3 and 4; the #698 signed-JobSpec join, #699 VM channel, #702 Fiat adapter, a live provider, arbitrary code inside the trusted proxy process, and concurrent calls into the ordered-stream parser were not exercised; provider non-retention and non-exfiltration are not claimed

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R1-01 | medium | plugins/hexaemeron/skills/phylax/scripts/model_proxy_lib/framing.py | Frame activation trusted equality among caller-replaceable `CompiledPolicy` fields. Replacing both JobSpec digest fields and recomputing the public policy bytes and digest produced a self-consistent substituted policy that `FramingCore` accepted without replaying compiler input. | fixed in this commit; accepted-evidence replay guard parent-red and fixed-green |
| S2-R1-02 | low | plugins/hexaemeron/skills/phylax/scripts/model_proxy_lib/framing.py | `TextRequest._owner` was returned inside a public dataclass and survived `dataclasses.replace()`. In the reproducer, a copied request selected an issued sequence and one issued object emitted repeated responses, so response authority was neither exact-object nor one-shot. | fixed in this commit; copied-request and repeated-response guard parent-red and fixed-green |
| S2-R1-03 | low | plugins/hexaemeron/skills/phylax/scripts/model_proxy_lib/framing.py | The exported `check_framing_manifest(None)` path passed the wrong scalar type into `Path` and leaked a raw `TypeError` instead of returning the fixed content-free `MP218` refusal. | fixed in this commit; invalid-path guard parent-red and fixed-green |

Leads not pursued: replay establishes that the frame policy matches the captured accepted-job evidence, not that #698 signed it or that #702 supplied it through the trusted supervisor channel. The Python objects remain a trusted-process interface rather than a sandbox against arbitrary code already executing inside the proxy; #699 must keep the guest behind the serialised frame channel. `FramingCore.feed` assumes the abstract ordered stream serialises calls and makes no thread-safety claim. Aggregate quotas, output reservation, cancellation, expiry, receipt durability, and cleanup remain Step 4 work rather than framing claims.

## Step 2, round 2 -- 2026-08-28T09:09:03Z

Audit schema: fiat-audit-round/v2

Covered: jobspec-substitution=reviewed; policy-derivation-drift=reviewed; transport-confusion=reviewed; frame-exhaustion=reviewed; schema-smuggling=reviewed; credential-crossing=not-applicable; origin-confusion=not-applicable; dns-rebinding=not-applicable; redirect-tunnel=not-applicable; feature-escape=reviewed; quota-race=not-applicable; token-undercount=reviewed; cancellation-race=not-applicable; expiry-replay=not-applicable; response-flood=not-applicable; response-schema=reviewed; cross-job-state=reviewed; receipt-content=not-applicable; diagnostic-consent=reviewed; provider-retention=not-applicable; provider-exfiltration=not-applicable; dependency-smuggling=reviewed; partial-receipt=not-applicable; secret-response-echo=not-applicable; cleanup-gap=not-applicable

Not checked: the Pashov Solidity suite was waived because issue #700 is an off-chain model-proxy delivery and Step 2 produces no Solidity; live credentials, DNS, TLS, HTTP, redirects, provider-native requests and responses, atomic quotas, concurrent calls, cancellation, runtime expiry, durable receipts, secret-echo checks, and terminal cleanup belong to Steps 3 and 4; the #698 signed-JobSpec join, #699 VM channel, #702 Fiat adapter, a live provider, and arbitrary code inside the trusted proxy process were not exercised; provider non-retention and non-exfiltration are not claimed

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R2-01 | medium | plugins/hexaemeron/skills/phylax/scripts/model_proxy_lib/framing.py | The core accepted any exact unconsumed issued request, so after one concatenated read a caller could encode sequence 2 before sequence 1. That reordered responses and supplied the multiplexing the Step 2 exit says is unavailable. | fixed in this commit; admission-order response guard parent-red and fixed-green |

Leads not pursued: the three round-1 policy-replay, one-shot request-object, and invalid-manifest-path failures remain guarded on this tree. Replay establishes that the frame policy matches the captured accepted-job evidence, not that #698 signed it or that #702 supplied it through the trusted supervisor channel. The Python objects remain a trusted-process interface rather than a sandbox against arbitrary code already executing inside the proxy; #699 must keep the guest behind the serialised frame channel. Thread-safe admission and response scheduling, aggregate quotas, output reservation, cancellation, expiry, receipt durability, and cleanup remain Step 4 work rather than framing claims.

## Step 2, round 3 -- 2026-08-28T09:40:23Z

Audit schema: fiat-audit-round/v2

Covered: jobspec-substitution=reviewed; policy-derivation-drift=reviewed; transport-confusion=reviewed; frame-exhaustion=reviewed; schema-smuggling=reviewed; credential-crossing=not-applicable; origin-confusion=not-applicable; dns-rebinding=not-applicable; redirect-tunnel=not-applicable; feature-escape=reviewed; quota-race=not-applicable; token-undercount=reviewed; cancellation-race=not-applicable; expiry-replay=not-applicable; response-flood=not-applicable; response-schema=reviewed; cross-job-state=reviewed; receipt-content=not-applicable; diagnostic-consent=reviewed; provider-retention=not-applicable; provider-exfiltration=not-applicable; dependency-smuggling=reviewed; partial-receipt=not-applicable; secret-response-echo=not-applicable; cleanup-gap=not-applicable

Not checked: the Pashov Solidity suite was waived because issue #700 is an off-chain model-proxy delivery and Step 2 produces no Solidity; live credentials, DNS, TLS, HTTP, redirects, provider-native requests and responses, atomic aggregate quotas, concurrent calls, cancellation, runtime expiry, durable receipts, secret-echo checks, and terminal cleanup belong to Steps 3 and 4; the #698 signed-JobSpec join, #699 VM channel, #702 Fiat adapter, a live provider, and arbitrary code inside the trusted proxy process were not exercised; provider non-retention and non-exfiltration are not claimed

Elenchus verdict: null

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

Leads not pursued: S2-R1-01, S2-R1-02, S2-R1-03, and S2-R2-01 remain closed on this exact tree: accepted-evidence replay rejects self-consistent policy substitution; exact-object issuance and one-shot consumption reject copied and reused requests; an invalid manifest scalar path returns `MP218`; and `_next_response_sequence` rejects response inversion. Replay establishes a match to the captured accepted-job evidence, not that #698 signed it or that #702 supplied it through the trusted supervisor channel. The Python objects remain a trusted-process interface rather than a sandbox against arbitrary code already executing inside the proxy; #699 must keep the guest behind the serialised frame channel. Thread-safe admission and response scheduling, aggregate quotas, output reservation, cancellation, expiry, receipt durability, and cleanup remain Step 4 work rather than framing claims.

## Step 3, round 1 -- 2026-08-28T10:55:19Z

Audit schema: fiat-audit-round/v2

Covered: jobspec-substitution=reviewed; policy-derivation-drift=reviewed; transport-confusion=reviewed; frame-exhaustion=reviewed; schema-smuggling=reviewed; credential-crossing=reviewed; origin-confusion=reviewed; dns-rebinding=reviewed; redirect-tunnel=reviewed; feature-escape=reviewed; quota-race=not-applicable; token-undercount=reviewed; cancellation-race=not-applicable; expiry-replay=not-applicable; response-flood=reviewed; response-schema=reviewed; cross-job-state=reviewed; receipt-content=not-applicable; diagnostic-consent=reviewed; provider-retention=reviewed; provider-exfiltration=reviewed; dependency-smuggling=reviewed; partial-receipt=not-applicable; secret-response-echo=reviewed; cleanup-gap=reviewed

Not checked: waived: issue #700 is an off-chain model-proxy delivery and will produce no Solidity; no live provider or network call; #698 signed-JobSpec acceptance, #699 VM egress, and the #702 Fiat adapter; atomic aggregate quotas, concurrent admission, cancellation, absolute and elapsed expiry, durable receipts, late-response withholding, and terminal process and secret destruction, which belong to Step 4; provider non-retention or non-exfiltration; arbitrary code already executing inside the trusted proxy process; an independently enforced wall-clock deadline around the operating-system resolver

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S3-R1-01 | high | plugins/hexaemeron/skills/phylax/scripts/model_proxy_lib/provider.py | A framing refusal poisoned the frame core but left earlier provider admissions live. After `finish()` refused a trailing partial prefix with `MP202`, `generate()` still read the credential and completed one provider exchange before the frame core stopped guest release with `MP216`. | fixed in this commit; `test_framing_refusal_poisoned_pending_provider_requests` was parent-red and is fixed-green |
| S3-R1-02 | medium | plugins/hexaemeron/skills/phylax/scripts/model_proxy_lib/transport.py | The connector resolved the fixed hostname once per request rather than once per job. A changing resolver selected `8.8.8.8` for the first request and `1.1.1.1` for the second, so the first validated address set did not remain the job pin. | fixed in this commit; `test_resolution_pin_is_reused_for_every_request_in_the_session` was parent-red and is fixed-green |
| S3-R1-03 | medium | plugins/hexaemeron/skills/phylax/scripts/model_proxy_lib/provider.py | A response-side refusal discarded confirmed transport progress. A terminal 302 followed an 83-byte mapped request, but the provider event reported zero request bytes; an over-returning response adapter likewise reported zero already-read response bytes. | fixed in this commit; `test_response_refusal_records_confirmed_provider_disclosure` was parent-red and is fixed-green |
| S3-R1-04 | low | plugins/hexaemeron/skills/phylax/scripts/model_proxy_lib/transport.py | With one byte left before the response cap, the transport still requested an 8,192-byte chunk. A conforming adapter could therefore return and allocate a full chunk past the application cap before the refusal. | fixed in this commit; `test_response_flood_reads_only_one_sentinel_beyond_the_cap` was parent-red and is fixed-green |

Leads not pursued: the provider layer now clears every pending admission on a framing refusal, pins one validated address on its job-scoped connector, carries bounded content-free progress through response refusals, and limits the final chunked-body probe to one byte. That one-byte sentinel is needed to distinguish an exact-cap end of stream from an over-cap body; it is never appended to the retained response or exposed as content. The default `getaddrinfo` call has operating-system and runtime behaviour but no separate Python wall-clock deadline; no live provider profile was selected, so this round does not claim one. Returning a response confirms mapped-request disclosure under the standard-library exchange contract; an injected adapter is trusted-process test infrastructure, not a sandbox boundary. Exact-secret response rejection is an extra containment check, not proof against provider encoding or transformation. Provider retention and exfiltration remain explicit limitations. Job process identity, concurrent reservations, lifecycle termination, and durable receipt ordering remain Step 4 work. The final tree passed 81 focused provider tests, 460 root tests with three skips, the two-case provider demonstration, portable and Horos checks, full-tree Phylax, Ephoros, and Hypomnema lints, Imprimatur and Brevitas on the normative reference, and 1,458 pinned Python 3.13.15 and Node v26.6.0 Hexaemeron tests with one skip. The exact prior audit prefix remains 14,538 bytes with SHA-256 `a34bfd85cf11813bbef8d67650fad2c55fd9a1c293235530ea56b192049b69e5`.

## Step 3, round 2 -- 2026-08-28T11:18:38Z

Audit schema: fiat-audit-round/v2

Covered: jobspec-substitution=reviewed; policy-derivation-drift=reviewed; transport-confusion=reviewed; frame-exhaustion=reviewed; schema-smuggling=reviewed; credential-crossing=reviewed; origin-confusion=reviewed; dns-rebinding=reviewed; redirect-tunnel=reviewed; feature-escape=reviewed; quota-race=not-applicable; token-undercount=reviewed; cancellation-race=not-applicable; expiry-replay=not-applicable; response-flood=reviewed; response-schema=reviewed; cross-job-state=reviewed; receipt-content=not-applicable; diagnostic-consent=reviewed; provider-retention=reviewed; provider-exfiltration=reviewed; dependency-smuggling=reviewed; partial-receipt=not-applicable; secret-response-echo=reviewed; cleanup-gap=reviewed

Not checked: waived: issue #700 is an off-chain model-proxy delivery and will produce no Solidity; no live provider or network call; #698 signed-JobSpec acceptance, #699 VM egress, and the #702 Fiat adapter; atomic aggregate quotas, concurrent admission, cancellation, absolute and elapsed expiry, durable receipts, late-response withholding, and terminal process and secret destruction, which belong to Step 4; provider non-retention or non-exfiltration; arbitrary code already executing inside the trusted proxy process; an independent wall-clock deadline around the operating-system resolver or incremental response delivery

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S3-R2-01 | medium | plugins/hexaemeron/skills/phylax/scripts/model_proxy_lib/provider.py | `ProviderSession` validated the caller's `CompiledPolicy` at activation but retained its mutable `document` and read live limits during `generate()`. Raising `max_response_bytes` from 32,768 to 131,072 after activation admitted and released a 32,871-byte response beyond the accepted-job cap. | fixed in this commit; `test_provider_session_pins_limits_against_post_activation_mutation` was parent-red and is fixed-green |

Leads not pursued: S3-R1-01 through S3-R1-04 remain closed on this exact tree: a framing refusal clears pending admissions, one connector retains its validated address pin, response refusals preserve confirmed transport progress, and the over-cap read asks for one sentinel byte. A connector is job-scoped by its construction site rather than rejecting reuse by a second `ProviderSession`; Step 4 owns one-process-one-digest activation and second-activation refusal. The operating-system resolver and per-I/O response timeout have no independent total wall deadline; no live profile was selected, so this round makes no live deadline claim. Exact-secret response rejection does not establish protection against encoding or transformation. Provider retention and exfiltration remain explicit limitations. Atomic quotas, concurrency, cancellation, expiry, durable receipts, late-response withholding, terminal process cleanup, and secret destruction remain Step 4 work. The exact prior audit prefix is 19,466 bytes with SHA-256 `c461491bd1f361b1a382a96c0529fa8218d7d0943db5357b48d7f90a739c4d8b`.

## Step 3, round 3 -- 2026-08-28T11:47:26Z

Audit schema: fiat-audit-round/v2

Covered: jobspec-substitution=reviewed; policy-derivation-drift=reviewed; transport-confusion=reviewed; frame-exhaustion=reviewed; schema-smuggling=reviewed; credential-crossing=reviewed; origin-confusion=reviewed; dns-rebinding=reviewed; redirect-tunnel=reviewed; feature-escape=reviewed; quota-race=not-applicable; token-undercount=reviewed; cancellation-race=not-applicable; expiry-replay=not-applicable; response-flood=reviewed; response-schema=reviewed; cross-job-state=reviewed; receipt-content=not-applicable; diagnostic-consent=reviewed; provider-retention=reviewed; provider-exfiltration=reviewed; dependency-smuggling=reviewed; partial-receipt=not-applicable; secret-response-echo=reviewed; cleanup-gap=reviewed

Not checked: waived: issue #700 is an off-chain model-proxy delivery and will produce no Solidity; no live provider or network call; #698 signed-JobSpec acceptance, #699 VM egress, and the #702 Fiat adapter; atomic aggregate quotas, concurrent admission, cancellation, absolute and elapsed expiry, durable receipts, late-response withholding, and terminal process and secret destruction, which belong to Step 4; provider non-retention or non-exfiltration; arbitrary code already executing inside the trusted proxy process; an independent wall-clock deadline around the operating-system resolver or incremental response delivery

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S3-R3-01 | medium | plugins/hexaemeron/skills/phylax/scripts/model_proxy_lib/transport.py | When the provider exchange raised before returning a response object, the connector rethrew a plain `PolicyError`. `ProviderSession` then recorded zero request bytes and zero duration even though the complete mapped request had crossed into the exchange adapter, understating the provider-boundary disclosure. | fixed in this commit; `test_pre_response_transport_refusal_records_mapped_request` was parent-red and is fixed-green |

Leads not pursued: S3-R1-01 through S3-R1-04 and S3-R2-01 remain closed on this exact tree: framing refusal clears pending admissions, one job-scoped connector retains its validated address pin, response refusals retain confirmed progress, the final over-cap read asks for one sentinel byte, and activation replays private limits instead of trusting mutable caller-owned policy data. S3-R3-01 now carries the mapped-request byte count and bounded duration through a value-free refusal when the request has crossed into the exchange adapter but no response object returns. That handoff does not prove how many encrypted bytes reached the provider after a TLS, write, or response timeout; the conservative count prevents an under-report at the proxy boundary. A connector is job-scoped by its construction site rather than rejecting reuse by a second `ProviderSession`; Step 4 owns one-process-one-digest activation and second-activation refusal. The operating-system resolver and per-I/O response timeout have no independent total wall deadline. Exact-secret response rejection does not establish protection against encoding or transformation. Provider retention and exfiltration remain explicit limitations. Atomic quotas, concurrency, cancellation, expiry, durable receipts, late-response withholding, terminal process cleanup, and secret destruction remain Step 4 work. The final tree passed 83 focused model-proxy tests, 460 root tests with three skips, the two-case provider demonstration, portable and Horos checks, full-tree Phylax, Ephoros, and Hypomnema lints, Imprimatur and Brevitas on the normative reference, and 1,460 pinned Python 3.13.15 and Node v26.6.0 Hexaemeron tests with one skip. The exact prior audit prefix is 22,611 bytes with SHA-256 `82b183d3fafd5b4280ac444f6b6fe3b090b7cea14e66472be9ab77875f31b20b`.
