# Equity CSV Contract v1

Status: locked for Phase 1 fixtures. Version: `v1`.

`equity_market_data.csv` uses the shared CSV representation contract and this
exact header:

```text
trade_date,exchange,symbol,series,isin,previous_close,open_price,high_price,low_price,last_price,close_price,total_traded_quantity,turnover,number_of_trades,source_report,source_format_version
```

| Column | Rule |
| --- | --- |
| `trade_date` | Required date. |
| `exchange` | Required, currently `NSE`. |
| `symbol` | Required NFC text. |
| `series` | Required and exactly `EQ`. |
| `isin` | Required uppercase 12-character ISIN. |
| `previous_close` through `close_price` | Required non-negative Decimal price. |
| `total_traded_quantity`, `number_of_trades` | Required non-negative count. |
| `turnover` | Required non-negative Decimal. |
| `source_report` | Required logical source-report identifier. |
| `source_format_version` | Required identifier from the source-adapter contract. |

VWAP and delivery fields are excluded. Sort by `trade_date`, `exchange`,
`symbol`, `series`, `isin`; this key must be unique. Example row:

```text
2026-08-14,NSE,ACME,EQ,INE000A01010,100,101.25,103,99.5,102,102.5,2000,205000,42,capital-market-bhavcopy-2026-08-14.zip,capital-market-bhavcopy-udiff-v1
```
