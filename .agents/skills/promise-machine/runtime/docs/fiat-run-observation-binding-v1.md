# Fiat run-observation binding

This interface binds one selected companion observation prefix to one Fiat
ledger receipt. It does not make observation data a delivery precondition.

## Prepare the stream

Write the JSONL stream beneath `.hexaemeron/observations/`. Use the controller's
derived identity as every event's `run_id`:

```bash
python3 plugins/hexaemeron/skills/fiat/scripts/hexctl.py status --json
python3 scripts/run_observation.py check-prefix .hexaemeron/observations/run.jsonl
```

The status object exposes `observation_run_id`. `check-prefix` permits a missing
final `run.finished`; it still requires `run.started`, contiguous sequence
numbers, closed capabilities, backward references, bounded fields, and safe
path bytes.

## Bind an available prefix

Run the command immediately after the Fiat receipt the prefix describes:

```bash
python3 plugins/hexaemeron/skills/fiat/scripts/hexctl.py observe \
  --artifact .hexaemeron/observations/run.jsonl \
  --capture-status accepted \
  --redaction-status passed
```

The path must be canonical, relative, regular, and beneath
`.hexaemeron/observations/`. Parent and file symlinks, devices, path escapes,
unstable reads, and files above the byte ceiling refuse before state changes.
The transition appends `record:run-observation` and does not change the current
phase.

Later selected receipts may bind strictly longer prefixes of the same stream.
The earlier bytes and their digest must remain exact.

## Record a non-available capture

Do not invent an empty digest. Record the state and a bounded reason:

```bash
python3 plugins/hexaemeron/skills/fiat/scripts/hexctl.py observe \
  --capture-status unavailable \
  --redaction-status unknown \
  --reason-code observer-unavailable
```

The accepted capture status requires a passing redaction result. Gap, refused,
unknown, and unavailable statuses accept no artifact and authorise no
observation claim.

## Verify the two claims separately

```bash
python3 plugins/hexaemeron/skills/fiat/scripts/hexctl.py verify
python3 plugins/hexaemeron/skills/fiat/scripts/hexctl.py verify --observations
```

The first command checks only the controller state and ledger. It remains valid
for legacy runs and failed observers. The second recomputes every selected
prefix and reports later bytes as an unbound tail.

| Code | Meaning | Recovery |
| --- | --- | --- |
| `FOB001` | No selected observation binding exists | Record one available or explicit non-available receipt |
| `FOB002` | The companion path is unsafe, missing, unstable, or over limit | Publish one stable regular run-local file |
| `FOB003` | Contract, run, receipt, interval, or count metadata diverges | Restore the exact receipt-bound metadata and prefix |
| `FOB004` | Bound bytes were replaced, reordered, or truncated | Restore those bytes or bind a later receipt |
| `FOB005` | Capture, validation, or redaction is unavailable or failed | Produce an accepted checked prefix before claiming it |

Findings do not repeat rejected paths, event values, or gate payloads. A clean
binding is recorded evidence about exact bytes and one receipt association. It
is not evidence that the events are true or complete, and it does not
strengthen Fiat's delivery receipt.
