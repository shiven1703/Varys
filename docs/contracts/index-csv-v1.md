# Index CSV Contract v1

Status: locked for Phase 1 fixtures. Version: `v1`.

`index_ohlc.csv` uses the shared CSV representation contract and this exact
header:

```text
trade_date,index_code,index_name,open,high,low,close,volume_or_shares_traded_if_available,turnover_if_available,source_report,source_format_version
```

`trade_date`, `index_code`, `index_name`, `open`, `high`, `low`, `close`,
`source_report`, and `source_format_version` are required. OHLC values are
non-negative Decimals. The volume and turnover columns are optional: emit `NA`
when the verified source does not supply that metric; otherwise volume is a
non-negative count and turnover is a non-negative Decimal. Do not infer either
metric from another field.

V1 package generation includes exactly `NIFTY 50` and `NIFTY 500`; their source
codes are preserved in `index_code`. Sort by `trade_date`, `index_code`, and
`index_name`; the key must be unique.

```text
2026-08-14,NIFTY 50,NIFTY 50,24500,24600,24400,24550,NA,NA,nifty-indices-2026-08-14.csv,nifty-indices-report-v1
```
