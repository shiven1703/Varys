# CSV Representation Contract v1

Status: locked for Phase 1 fixtures. Version: `v1`.

This contract applies to every canonical CSV in a Varys package, including the
preparation report. Raw source artifacts are unchanged and are not canonical
CSVs.

## Bytes and cells

- Encode UTF-8 without a BOM, separate fields with `,`, and use LF (`\n`) for
  every record terminator, including the final record.
- Use RFC 4180 quoting: quote a field only when it contains comma, quote, CR,
  or LF; represent an embedded quote as `""`.
- A missing value is exactly `NA`. A source value equal to the literal string
  `NA` must be quoted as `"NA"` so it is distinguishable from a null.
- Dates are Gregorian calendar dates formatted `YYYY-MM-DD`.
- Text is Unicode NFC. Trim surrounding whitespace from parsed source values;
  preserve internal whitespace and case.

## Numbers

Canonical numeric values are parsed and serialized as Decimal values, never
binary floating point. They use fixed-point notation with no thousands
separators, no leading `+`, no scientific notation, no unnecessary trailing
fractional zeroes, and `0` instead of negative zero. No contract writer rounds:
an input that cannot be represented without rounding is invalid.

Count fields are non-negative base-10 integers. Price and turnover fields are
non-negative Decimal values. `NA` is permitted only where the corresponding
schema marks the column optional.

Examples: `100.5000` becomes `100.5`; `-0.00` becomes `0`; `1000` remains
`1000`; `1E+3` is never emitted.

## Ordering

Emit the exact schema header and column order in the applicable contract. Sort
rows ascending by the documented key, comparing text by Unicode code point and
dates by their `YYYY-MM-DD` value. Duplicate sort keys are invalid unless the
applicable contract explicitly includes extra key fields that distinguish them.

Writers must produce byte-identical output for identical canonical records.
