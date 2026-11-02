# Constructed fee fields

| Field | Meaning | Limit |
| --- | --- | --- |
| `event_family` | `fee-collection`, repayment, or exit execution; V2 also has `pool-state` | Actions remain independent |
| `parties` on fee rows | One `pool` party | Recipient or actor unestablished |
| `amounts` on collection | Native `assets` in underlying base units | Missing asset context stays null with a gap |
| `amounts` on V2 Bips | Empty array | No percentage conversion or invented cash leg |
| `mapping_records[].decoded` | Complete decoded native values | Bips stays an integer string |
| `provenance.adapter_version` | `1.1.0` | Verification selects that interpretation |
| `source.scope` | `constructed-fixture` | No retained historical observation |
| `coverage.unsupported_events` | Attribution and omitted-log gaps | Counts may overlap mapped rows |
