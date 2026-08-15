# Preparation Report Contract v1

Status: locked for Phase 1 fixtures. Version: `v1`.

Every package contains `preparation_report.csv`, including one header row even
when no findings exist. It uses the shared CSV representation contract and this
exact header:

```text
severity,code,subject_type,subject_id,message
```

| Column | Rule |
| --- | --- |
| `severity` | `INFO`, `WARNING`, or `ERROR`. |
| `code` | Required stable uppercase snake-case identifier. |
| `subject_type` | `PACKAGE`, `SOURCE_FILE`, `EQUITY_ROW`, `INDEX_ROW`, or `UNIVERSE_ROW`. |
| `subject_id` | Required stable identifier; package findings use the package UUID. |
| `message` | Required human-readable text without secrets or raw response bodies. |

Sort by `severity` rank (`ERROR`, `WARNING`, `INFO`), then `code`,
`subject_type`, `subject_id`, and `message`. A package cannot become ready when
an `ERROR` finding is present. `WARNING` findings may produce
`READY_WITH_WARNINGS`; `INFO` findings do not affect readiness.

```text
WARNING,INDEX_VOLUME_UNAVAILABLE,INDEX_ROW,2026-08-14:NIFTY 50,Verified source did not provide volume
```
