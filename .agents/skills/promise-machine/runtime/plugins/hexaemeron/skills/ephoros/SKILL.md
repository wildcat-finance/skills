---
name: ephoros
description: >-
  Decide what a step must emit so its behaviour is visible afterwards: the
  on-call questions first, then structured events, bounded metrics, correlation
  across the whole path, and alerts on what someone actually feels. Use when
  adding logging, metrics, tracing or alerting, when shipping anything that
  runs unattended, or when an incident could not be explained from what was
  recorded. Do not use it to instrument a failure you are chasing right now,
  which belongs to elenchus, and do not use it to measure something slow, which
  belongs to metron.
metadata:
  version: "1.2.0"
---

<p align="center">
  <img src="../../assets/characters/ephoros.png" width="1200">
</p>

# Ephoros

From *ephoros*, the overseer whose office was to watch and report. Watching is
the whole job. It does not make the system faster or safer, and without it the
first incident becomes archaeology.

## Where this sits

Ephoros owns the telemetry that stays: what a step emits, in what shape, and
what wakes someone up.

Fiat and Mason apply it while implementing anything that runs unattended, and
Warden reruns its mechanical gate in non-Solidity rounds. Elenchus may add
temporary instrumentation while chasing one failure; Ephoros decides what
remains afterwards. Metron measures performance, and Phylax guards the data and
secrets the telemetry boundary crosses.

The Synkrisis specification allows a future finding to suggest that a signal
is missing or late. Its current scaffold emits no finding, and even a future
suggestion cannot decide what telemetry a step keeps.

Its version, held frontier, next job, and maturity state live in
[EVOLUTION.md](EVOLUTION.md).

**Current state.** Five rules are executable: E001 to E003 read Python only, E004 reads the supported block-YAML subset, and E005 reads Python, supported block-YAML label keys and the TypeScript surface through the shared masked lexer, running clean over this marketplace and the pinned application clone. TypeScript parity for E001 to E003 remains open.

## Write the questions before the code

Telemetry with no question behind it is volume. Write two to four questions
someone will ask at three in the morning, then emit only what answers them.

```text
Step: fee submission service
1. Did the last cycle submit, and did what it submitted land?
2. When one fails, is it a revert, a timeout, or a stuck nonce?
3. Is the subgraph behind the chain, and by how many blocks?
```

Cannot name the questions? Then the step is not ready to instrument. You will
emit everything and learn nothing.

## One signal per question

| Signal | Answers | Cost |
| --- | --- | --- |
| Event | What happened in this one case | Grows with volume |
| Metric | How often, how slow, in aggregate | Fixed per series |
| Trace | Where the time went across hops | Sampled |

Metrics say something is wrong, traces say where, events say why.

## Events, not sentences

An event carries a stable name and fields a query can reach. A sentence with
values baked into it carries neither.

```python
# unreachable by query, and the values are welded into the string
log.info(f"harvested {n} blocks for {market} in {secs}s")

# stable name, machine-readable fields
log.info("harvest_interval_done", extra={
    "event": "harvest_interval_done",
    "run_id": run_id,
    "venue": venue,
    "blocks": n,
    "duration_s": round(secs, 3),
})
```

Levels carry meaning, so spend them carefully. `error` means an invariant broke
and somebody may need to act on it now. `warn` means degraded but handled: a
retry that worked, a fallback taken, a slow dependency ridden out. `info` marks
an event the business cares about. `debug` stays off outside development.

## Correlation or it is unreadable

Interleaved output without a shared identifier cannot be reassembled. Mint one
at each boundary and carry it through every line, span and outbound call.

The identifier differs by surface. A route takes or generates a request id and
returns it in the response header. A harvest mints a run id and stamps every
interval under it. A submission carries the nonce and, once broadcast, the
transaction hash, because that is the identifier the chain itself will use.

## What never appears

`phylax` sets this rule and this skill inherits it. No key, no mnemonic, no RPC
or database credential, no session token, no signed payload. An exception
handler that prints the request it failed on prints the header it failed with.

One rule belongs here rather than there. Do not index telemetry by wallet
address. Recording who asked about which address, or pairing an address with a
resolved name in a log the team greps, builds exactly the linkage Probitas
refuses to produce. Where an address is genuinely needed to diagnose, it goes
in an event, never in a metric label or a dashboard axis.

## Metrics, and the label that kills them

Instrument rate, errors and duration on every route and every dependency you
call. For pools, queues and workers, watch utilisation, saturation and errors.

Every distinct label combination is a separate series, so labels come from
small fixed sets: the route template, a status class, a venue name, a chain id.
Never a wallet address, a transaction hash, a run id, a raw URL, or the text of
an error. Those belong in events, where high cardinality is the point.

Record durations as histograms and read them at p95 and p99. An average is the
number that hides the people having the worst time.

## The three surfaces

**A route.** Rate, errors and duration per route template, plus the same for
Prisma and for every call out to the subgraph or an RPC. A route that fails
because a dependency failed should say which.

**A long-running job.** Progress is the signal, not completion. Emit the
interval just finished, how far behind head it is, and when it last advanced. A
harvester that stops is indistinguishable from a slow one unless staleness is
measured.

**A signer.** The highest stakes surface here, because it moves money. Record
the intent before broadcast, the hash on broadcast, and the receipt on
inclusion, each under the same nonce. Count submitted, landed, reverted and
still pending, and record the age of the oldest pending item. Under a process
manager, logs are files someone will read later, so the rule above about keys
is not advice.

## Alert on what someone feels

Page on symptoms, put causes on a dashboard. A cause fires when nothing is
wrong and stays quiet during failures nobody predicted.

- User-facing error rate above a threshold, sustained. Page.
- Oldest pending submission older than a stated number of blocks. Page.
- A harvester that has not advanced in a stated interval. Page.
- Subgraph lag beyond the point where displayed numbers mislead. Page.
- Host CPU, memory, or one restarted process. Dashboard.

Every alert earns its place: it is actionable, it links to three lines saying
what to check first, and its threshold comes from an objective or from history
rather than from taste. Two severities are enough. A third teaches people to
ignore the first.

## Verify the telemetry

Instrumentation is code and can be wrong. Before receipting, exercise it.

Force an error and find it by its correlation id, confirming the fields
arrived as fields. Send traffic and confirm the series appear with the labels
you expect and no others. Follow one request end to end with no gap where a
context was dropped. Fire each new alert once, by moving its threshold, and
confirm it arrives where it should.

Then read a sample of real output with `phylax`'s rule in hand, looking for a
credential or an address that should not be there.

## The mechanical subset

Five of these rules are settled by a parser. Run the lint over the paths a
step touched, and require exit 0.

```bash
python3 "$PLUGIN_ROOT/skills/ephoros/scripts/ephoros.py" src tests
```

It reports a log message assembled by formatting, a metric label drawn from an
unbounded source, a duration summarised as a mean, and E004 for each supported
block-YAML list entry starting with `alert:` that lacks its own nested
`annotations.runbook` Markdown path. Comments, block scalars, top-level keys
and neighbouring alert entries do not satisfy E004. The YAML pass establishes
presence only: Hypomnema H003 resolves the path and H007 checks the target's
answers. E001 to E003 read Python only.

E005 reports telemetry keyed by wallet address: an address-shaped name or a
40-hex literal used as a metric label, a dashboard key or a log index. It
reads Python, address-named keys directly under a supported block-YAML
`labels:` mapping, and `.ts`/`.tsx` source through the shared masked lexer
phylax already uses, with the same input boundary: at most 1 MiB per
TypeScript file, and a file the lexer cannot read or terminate reports E000
and fails the run. Address-shaped metric labels that E002 used to claim now
report E005, so one concern carries one code; every other unbounded fragment
keeps E002. Where the line between this lint and phylax runs over the same
TypeScript files is decided once, in
[ADR-010](../../../../docs/decisions/ADR-010-split-address-telemetry-from-boundary-control.md).

Three limits are part of the rule rather than defects in it. The finding
message says wallet address for any address-fragment key, so `ip_address`
draws the same words. Recognition under a YAML `labels:` mapping is
direct-children-only, so a key nested one mapping deeper passes silently. And
the `s?` suffix family E005 shares with E002 misses `-es` plurals, so
`addresses` passes where `address` fires.

Two things it deliberately leaves alone. A `print` in Python and `console.*`
in TypeScript are command-line output rather than telemetry, and this
marketplace writes a great deal of the first. A mean of something that is not
a duration is arithmetic, so sentence lengths and layout positions pass
untouched.

Deliberate exceptions state a reason: `# ephoros: allow <why>` in Python and
YAML, `// ephoros: allow <why>` as a genuine line comment in TypeScript, on
the finding line or the one above it. A bare pragma suppresses nothing, in
either form. Everything else here stays judgement, and a clean exit says only
that these five found nothing.

## Rationalisations

- "Logging goes in after it works." After means after the first incident,
  which is the most expensive moment to discover you are blind.
- "More logs, more visibility." Unstructured volume slows an incident down.
  Three queryable events beat three hundred lines of prose.
- "A print statement is fine for now." It cannot be filtered, correlated or
  alerted on, and it outlives the afternoon that added it.
- "We will look at the dashboard when it breaks." A dashboard built without
  questions shows everything except the answer.
- "Alert on it all and tune later." The tuning does not happen. The ignored
  page does.
- "Address as a label makes debugging easier." It also multiplies the series
  without bound and builds the linkage the marketplace refuses.
- "Tracing is overkill for two services." Two services is already a question
  about which one spent the time.

## Red flags

- A step that adds retries, a queue or an external call and emits nothing new.
- Log lines assembled by formatting instead of fields.
- No correlation identifier, so every line stands alone.
- Metric labels carrying addresses, hashes, run ids or error text.
- Latency reported as an average.
- Alerts that fire daily and get acknowledged without action.
- Pages on host metrics while user-facing errors go unwatched.
- Credentials, signed payloads or wallet addresses sitting in output.
- Long-running jobs with no staleness signal.

## Before the step is receipted

Report the count, then name every item that failed.

- [ ] The on-call questions are written down, and each signal answers one.
- [ ] Output is structured, with stable event names and a correlation id.
- [ ] Rate, errors and duration exist for each new route and dependency.
- [ ] Label sets are bounded, with no address, hash or free text among them.
- [ ] Durations are histograms, and p95 and p99 are queryable.
- [ ] Long-running jobs report progress and staleness, not just completion.
- [ ] A signer records intent, broadcast and receipt under one nonce.
- [ ] Each new alert is symptom-based, carries a runbook link, and was fired once.
- [ ] Sampled real output contains no credential and no address used as a key.

## Hand back

Lead with the state: instrumented against the questions you wrote, or open on a
named gap. List the questions and the signal answering each.

Separate what you verified from what you added. A signal you triggered and then
found in the output is established. One that merely exists in the diff is
asserted, and saying which is which costs a sentence.

End with one action: the alert still needing a threshold, the question with no
signal behind it, or the sampled output someone should read.

## Promise Machine contract

### ephoros-mechanical-gate

- Promise: A zero-exit Ephoros lint establishes that the bounded parser found none of its specified formatted-log, unbounded-metric-label or mean-duration patterns in the selected Python paths, no supported block-YAML alert entry without its own nested runbook annotation, and no wallet-address key on a metric label, dashboard key or log index in the selected Python, TypeScript and supported block-YAML label surfaces.
- Evidence: The exact lint version, arguments, selected paths, structured findings and zero exit status.
- Evidence classes: checked
- Boundary: A clean lint covers only the four implemented Python rules, E004 annotation presence and E005 address-key recognition in the supported block-YAML subset, and E005 alone on the TypeScript surface; it does not prove useful observability, safe output, correct alerting, a resolving or useful runbook, general YAML semantics or any other rule in another language.
- Authorises: Passing the mechanical Ephoros gate for the exact paths and checker version recorded.
- Consequence: 1
- Refuses: Unreadable or oversized input, an unexplained suppression, a non-zero result or any broader observability claim.
- Recovery: Repair the offending signal or add a narrowly reasoned suppression when the rule is inapplicable, then rerun the same bounded lint.
- Exceptions: none

### ephoros-observability-review

- Promise: A completed observability review establishes that the step's on-call questions have bounded signals, correlation and user-symptom alerts, and that emitted samples were checked for sensitive or unbounded data.
- Evidence: The question-to-signal map, event and metric definitions, trace correlation, alert test, sampled output, staleness signal for long jobs and unresolved-gap list.
- Evidence classes: checked, inferred, recorded
- Boundary: The review covers the named step and exercised signals; it does not prove future telemetry availability, alert thresholds under every workload or absence of sensitive data outside the samples reviewed.
- Authorises: Operating the reviewed step with the recorded signals and escalating through the named runbooks.
- Consequence: 2
- Refuses: A new unattended path with no signal, unbounded labels, mean-only duration, missing correlation, untested alerts, absent runbooks or sensitive values in emitted output.
- Recovery: Write the unanswered on-call question, add or bound the missing signal, exercise the alert, inspect real output and repeat the review.
- Exceptions: none
