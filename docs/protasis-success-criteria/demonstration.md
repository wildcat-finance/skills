# Joined controller demonstration

This record is the human-facing companion to the Step 5 proof. The proof
starts the checked-in `hexctl` controller in a disposable Git-backed fixture,
then keeps the command, source, step and descriptor identities beside the
bounded outcomes it observes.

## Positive observation

One registered Exit is shared by three descriptors. A controller `run-exit`
settles all three from one child process, and its attempt names the signed
fixture commit before and after the launch. The terminal receipt replays that
attempt without starting the Exit again.

The fixture creates its own temporary SSH key and trust file. Operator SSH
and OpenPGP defaults do not supply its signing material. Copy mode and a
missing or failed signer allow only an unsigned adapter observation;
`unsigned-fixture-not-admitted` then refuses the joined proof before any report
is published. Production signature checks remain required.

## Refusal observations

The fixture records missing execution, withheld integration, unknown criterion,
wrong step, changed command or source, non-zero exit, timeout, stream overflow,
interruption, stale amendment, and the legacy receipt boundary. It also keeps a
passing descriptor whose command is deliberately vacuous. That pass shows what
the contract permits; it is not a claim that the command proves its criterion.

## Command

```text
python3 docs/protasis-success-criteria/proof.py --candidate controller-capture --criterion joined-demonstration --report .hexaemeron/reports/controller-capture-joined-demonstration.json
```

The resulting report is create-only and carries a companion evidence file. It
identifies the exact controller bytes and disposable source commit, records
bounded stdout and stderr counts and hashes, and states the exclusions. Remote
GitHub and deployment surfaces are not contacted by this fixture.

