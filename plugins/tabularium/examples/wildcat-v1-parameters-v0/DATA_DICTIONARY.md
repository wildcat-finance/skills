# Constructed parameter release fields

| File or field | Meaning | Limit |
| --- | --- | --- |
| `source/raw-release/` | Complete Alexandria input with declared fixture context and native logs | Constructed only; no retained capture |
| `source.json` | Context, concrete ABI, exact decoded fields and one disposition per native log | No inferred market, role enum or value conversion |
| `capture.json` | Source digest, byte count, scope and adapter `1.2.0` | Describes local fixture custody |
| `events.jsonl` | `pool-state` rows with emitter and emitted parties | Financial `amounts` is always empty |
| `coverage.json` | Digests, mapped counts, rule versions and qualified gaps | Verification reconstructs bytes; no publisher authentication |

An empty decoded key `""` is the unnamed V1 lender address. Native names,
uint widths, strings and zero addresses retain their ABI meanings. These rows
establish neither a new-value/delta interpretation nor a historical event.
