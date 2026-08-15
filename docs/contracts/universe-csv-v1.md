# Universe CSV Contract v1

Status: locked for Phase 1 fixtures. Version: `v1`.

`universe.csv` uses the shared CSV representation contract and this exact
header:

```text
universe_code,snapshot_date,exchange,symbol,series,isin,company_name,industry
```

All columns are required except `industry`, which may be `NA`. `universe_code`
is `NIFTY 500` for V1; `snapshot_date` is the selected current constituent
snapshot date; `exchange` is currently `NSE`; `series` is exactly `EQ`; and
`isin` is an uppercase 12-character ISIN. `company_name` and `industry` are
NFC text.

Sort by `universe_code`, `snapshot_date`, `exchange`, `symbol`, `series`, and
`isin`; the key must be unique. New source columns remain only in immutable raw
artifacts until a reviewed schema-version change adds them here.

```text
NIFTY 500,2026-08-14,NSE,ACME,EQ,INE000A01010,Acme Limited,Industrials
```
