# Source Adapter Contract v1

Status: locked for Phase 1 fixtures. Version: `v1`.

Adapters isolate discovery and network acquisition from parsing and package
generation. V1 adapter roles are `Nifty500UniverseSource`,
`CapitalMarketBhavcopySource`, `IndexReportSource`, and
`SecurityWiseRepairSource`. Each supplies `discover(date)`, `download(reference)`,
`classify(response)`, and `verify(file)`; implementations may use typed local
equivalents but must preserve these inputs and outcomes.

`classify` returns one of `VALID_FILE`, `NOT_PUBLISHED_YET`,
`KNOWN_NON_TRADING_DATE`, `NOT_FOUND`, `SESSION_EXPIRED`, `RATE_LIMITED`,
`ACCESS_DENIED`, `CHALLENGE_RESPONSE`, `TRANSIENT_SERVER_ERROR`,
`INVALID_CONTENT`, `CORRUPT_ARCHIVE`, or `SCHEMA_CHANGED`. `verify` records
the SHA-256, original filename, byte size, logical source report, and parser
format identifier; it never mutates raw bytes.

Canonical source-format identifiers are:

```text
capital-market-bhavcopy-legacy-v1
capital-market-bhavcopy-udiff-v1
nifty-indices-report-v1
nifty-500-universe-v1
security-wise-report-v1
```

Parser choice is based on verified columns/content, never only a filename.
Verified raw content is immutable and content-addressed; identical hashes are
reused, while different bytes for one logical source/date create a reviewable
conflict. Fixture adapters use this same contract and never contact live NSE.
