# Manifest Contract v1

Status: locked for Phase 1 fixtures. Version: `v1`.

Every ready package contains `manifest.json`. It is UTF-8 JSON, encoded without
a BOM, with LF final newline, object keys sorted lexicographically, and no
insignificant whitespace. Timestamps use RFC 3339 UTC with a `Z` suffix and
whole-second precision.

## Required shape

```json
{
  "artifacts": [
    {"name": "equity_market_data.csv", "row_count": 1, "sha256": "<64 lowercase hex characters>", "size_bytes": 123}
  ],
  "package": {
    "id": "<UUID>",
    "kind": "daily",
    "schema_version": "v1",
    "version": 1
  },
  "prepared_at": "2026-08-14T18:30:00Z",
  "provenance": {
    "configuration_fingerprint": "<64 lowercase hex characters>",
    "raw_source_sha256": ["<64 lowercase hex characters>"],
    "source_format_versions": ["capital-market-bhavcopy-udiff-v1"]
  }
}
```

`package.kind` is one of `daily`, `universe`, or `backfill`. `version` is a
positive integer. Artifacts are sorted by `name`; each has a unique safe
basename, positive `size_bytes`, lowercase SHA-256, and `row_count` for CSV
members only. The manifest does not list itself or the enclosing ZIP.

Daily packages list `equity_market_data.csv`, `index_ohlc.csv`, and
`preparation_report.csv`; universe packages list `universe.csv` and
`preparation_report.csv`; backfills additionally list every yearly equity CSV.
`prepared_at` is provenance, not market-data content. The final ZIP checksum,
size, and relative ready path are database publication metadata, not manifest
members.
