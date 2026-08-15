"""Fixture parsers and deterministic canonical CSV writers for Phase 1."""

from __future__ import annotations

import csv
import io
import re
import unicodedata
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from varys.sources import SourceReference

CanonicalValue = str | date | Decimal | int | None
CanonicalRecord = Mapping[str, CanonicalValue]

_ISIN = re.compile(r"[A-Z0-9]{12}")
_LEGACY_BHAVCOPY_HEADER = (
    "SYMBOL",
    "SERIES",
    "OPEN",
    "HIGH",
    "LOW",
    "CLOSE",
    "LAST",
    "PREVCLOSE",
    "TOTTRDQTY",
    "TOTTRDVAL",
    "TIMESTAMP",
    "TOTALTRADES",
    "ISIN",
)
_UDIFF_BHAVCOPY_HEADER = (
    "TradDt",
    "BizDt",
    "Sgmt",
    "Src",
    "FinInstrmTp",
    "FinInstrmId",
    "ISIN",
    "TckrSymb",
    "SctySrs",
    "XpryDt",
    "FininstrmActlXpryDt",
    "StrkPric",
    "OptnTp",
    "FinInstrmNm",
    "OpnPric",
    "HghPric",
    "LwPric",
    "ClsPric",
    "LastPric",
    "PrvsClsgPric",
    "UndrlygPric",
    "SttlmPric",
    "OpnIntrst",
    "ChngInOpnIntrst",
    "TtlTradgVol",
    "TtlTrfVal",
    "TtlNbOfTxs",
    "FinInstrmDelivQty",
    "FinInstrmDelivPct",
)
_INDEX_REPORT_HEADER = (
    "Index Name",
    "Index Date",
    "Open Index Value",
    "High Index Value",
    "Low Index Value",
    "Closing Index Value",
    "Points Change",
    "Change(%)",
    "Volume",
    "Turnover (Rs. Cr.)",
)
_UNIVERSE_HEADER = ("Company Name", "Industry", "Symbol", "Series", "ISIN Code")


class ParserError(ValueError):
    """Base exception for invalid fixture source content."""


class SchemaChangedError(ParserError):
    """The raw source header is not a reviewed fixture schema."""


@dataclass(frozen=True, slots=True)
class CanonicalCsvSchema:
    header: tuple[str, ...]
    sort_key: tuple[str, ...]
    date_columns: frozenset[str]
    decimal_columns: frozenset[str]
    count_columns: frozenset[str]
    optional_columns: frozenset[str]


EQUITY_SCHEMA = CanonicalCsvSchema(
    header=(
        "trade_date",
        "exchange",
        "symbol",
        "series",
        "isin",
        "previous_close",
        "open_price",
        "high_price",
        "low_price",
        "last_price",
        "close_price",
        "total_traded_quantity",
        "turnover",
        "number_of_trades",
        "source_report",
        "source_format_version",
    ),
    sort_key=("trade_date", "exchange", "symbol", "series", "isin"),
    date_columns=frozenset({"trade_date"}),
    decimal_columns=frozenset(
        {
            "previous_close",
            "open_price",
            "high_price",
            "low_price",
            "last_price",
            "close_price",
            "turnover",
        }
    ),
    count_columns=frozenset({"total_traded_quantity", "number_of_trades"}),
    optional_columns=frozenset(),
)
INDEX_SCHEMA = CanonicalCsvSchema(
    header=(
        "trade_date",
        "index_code",
        "index_name",
        "open",
        "high",
        "low",
        "close",
        "volume_or_shares_traded_if_available",
        "turnover_if_available",
        "source_report",
        "source_format_version",
    ),
    sort_key=("trade_date", "index_code", "index_name"),
    date_columns=frozenset({"trade_date"}),
    decimal_columns=frozenset(
        {"open", "high", "low", "close", "turnover_if_available"}
    ),
    count_columns=frozenset({"volume_or_shares_traded_if_available"}),
    optional_columns=frozenset(
        {"volume_or_shares_traded_if_available", "turnover_if_available"}
    ),
)
UNIVERSE_SCHEMA = CanonicalCsvSchema(
    header=(
        "universe_code",
        "snapshot_date",
        "exchange",
        "symbol",
        "series",
        "isin",
        "company_name",
        "industry",
    ),
    sort_key=("universe_code", "snapshot_date", "exchange", "symbol", "series", "isin"),
    date_columns=frozenset({"snapshot_date"}),
    decimal_columns=frozenset(),
    count_columns=frozenset(),
    optional_columns=frozenset({"industry"}),
)


def parse_capital_market_bhavcopy(
    content: bytes, reference: SourceReference
) -> list[dict[str, CanonicalValue]]:
    """Parse a reviewed legacy or UDiFF bhavcopy by its actual header."""
    header, rows = _read_raw_csv(content)
    if header == _LEGACY_BHAVCOPY_HEADER:
        return _parse_legacy_bhavcopy(rows, reference)
    if header == _UDIFF_BHAVCOPY_HEADER:
        return _parse_udiff_bhavcopy(rows, reference)
    raise SchemaChangedError("unrecognised Capital Market bhavcopy schema")


def parse_index_report(
    content: bytes, reference: SourceReference
) -> list[dict[str, CanonicalValue]]:
    _require_source_format(reference, "nifty-indices-report-v1")
    rows = _read_expected_csv(content, _INDEX_REPORT_HEADER)
    records: list[dict[str, CanonicalValue]] = []
    for row in rows:
        identity = _index_identity(_required_text(row, "Index Name"))
        if identity is None:
            continue
        trade_date = _parse_source_date(_required_text(row, "Index Date"))
        if trade_date != reference.trade_date:
            raise ParserError("index report trade date does not match its reference")
        index_code, index_name = identity
        records.append(
            {
                "trade_date": trade_date,
                "index_code": index_code,
                "index_name": index_name,
                "open": _required_decimal(row, "Open Index Value"),
                "high": _required_decimal(row, "High Index Value"),
                "low": _required_decimal(row, "Low Index Value"),
                "close": _required_decimal(row, "Closing Index Value"),
                "volume_or_shares_traded_if_available": _optional_count(row, "Volume"),
                "turnover_if_available": _optional_decimal(row, "Turnover (Rs. Cr.)"),
                "source_report": _required_reference_value(reference.source_report),
                "source_format_version": reference.source_format_version,
            }
        )
    if {record["index_code"] for record in records} != {"NIFTY 50", "NIFTY 500"}:
        raise ParserError("index report must contain NIFTY 50 and NIFTY 500")
    return records


def parse_nifty500_universe(
    content: bytes, reference: SourceReference
) -> list[dict[str, CanonicalValue]]:
    _require_source_format(reference, "nifty-500-universe-v1")
    rows = _read_expected_csv(content, _UNIVERSE_HEADER)
    records: list[dict[str, CanonicalValue]] = []
    for row in rows:
        if _required_text(row, "Series") != "EQ":
            continue
        records.append(
            {
                "universe_code": "NIFTY 500",
                "snapshot_date": reference.trade_date,
                "exchange": "NSE",
                "symbol": _required_text(row, "Symbol"),
                "series": "EQ",
                "isin": _required_isin(row, "ISIN Code"),
                "company_name": _required_text(row, "Company Name"),
                "industry": _optional_text(row, "Industry"),
            }
        )
    if not records:
        raise ParserError("universe source contains no EQ rows")
    return records


def write_equity_csv(records: Iterable[CanonicalRecord]) -> bytes:
    return write_canonical_csv(EQUITY_SCHEMA, records)


def write_index_csv(records: Iterable[CanonicalRecord]) -> bytes:
    return write_canonical_csv(INDEX_SCHEMA, records)


def write_universe_csv(records: Iterable[CanonicalRecord]) -> bytes:
    return write_canonical_csv(UNIVERSE_SCHEMA, records)


def write_canonical_csv(
    schema: CanonicalCsvSchema, records: Iterable[CanonicalRecord]
) -> bytes:
    """Encode validated canonical records with the locked V1 representation."""
    encoded_records = [_encode_record(schema, record) for record in records]
    encoded_records.sort(
        key=lambda record: tuple(record[column] for column in schema.sort_key)
    )
    previous_key: tuple[str, ...] | None = None
    for record in encoded_records:
        key = tuple(record[column] for column in schema.sort_key)
        if key == previous_key:
            raise ParserError("duplicate canonical sort key")
        previous_key = key

    lines = [_encode_csv_row(tuple((column, False) for column in schema.header))]
    lines.extend(
        _encode_csv_row(
            tuple(
                (
                    record[column],
                    record["__missing__" + column] == "0" and record[column] == "NA",
                )
                for column in schema.header
            )
        )
        for record in encoded_records
    )
    return ("\n".join(lines) + "\n").encode("utf-8")


def _parse_legacy_bhavcopy(
    rows: Sequence[Mapping[str, str]], reference: SourceReference
) -> list[dict[str, CanonicalValue]]:
    records: list[dict[str, CanonicalValue]] = []
    for row in rows:
        if _required_text(row, "SERIES") != "EQ":
            continue
        trade_date = _parse_source_date(_required_text(row, "TIMESTAMP"))
        _require_trade_date(trade_date, reference)
        records.append(
            _equity_record(
                trade_date=trade_date,
                symbol=_required_text(row, "SYMBOL"),
                isin=_required_isin(row, "ISIN"),
                previous_close=_required_decimal(row, "PREVCLOSE"),
                open_price=_required_decimal(row, "OPEN"),
                high_price=_required_decimal(row, "HIGH"),
                low_price=_required_decimal(row, "LOW"),
                last_price=_required_decimal(row, "LAST"),
                close_price=_required_decimal(row, "CLOSE"),
                quantity=_required_count(row, "TOTTRDQTY"),
                turnover=_required_decimal(row, "TOTTRDVAL"),
                trades=_required_count(row, "TOTALTRADES"),
                reference=reference,
                source_format_version="capital-market-bhavcopy-legacy-v1",
            )
        )
    return records


def _parse_udiff_bhavcopy(
    rows: Sequence[Mapping[str, str]], reference: SourceReference
) -> list[dict[str, CanonicalValue]]:
    records: list[dict[str, CanonicalValue]] = []
    for row in rows:
        if _required_text(row, "SctySrs") != "EQ":
            continue
        if _required_text(row, "Sgmt") != "CM":
            continue
        trade_date = _parse_source_date(_required_text(row, "BizDt"))
        _require_trade_date(trade_date, reference)
        records.append(
            _equity_record(
                trade_date=trade_date,
                symbol=_required_text(row, "TckrSymb"),
                isin=_required_isin(row, "ISIN"),
                previous_close=_required_decimal(row, "PrvsClsgPric"),
                open_price=_required_decimal(row, "OpnPric"),
                high_price=_required_decimal(row, "HghPric"),
                low_price=_required_decimal(row, "LwPric"),
                last_price=_required_decimal(row, "LastPric"),
                close_price=_required_decimal(row, "ClsPric"),
                quantity=_required_count(row, "TtlTradgVol"),
                turnover=_required_decimal(row, "TtlTrfVal"),
                trades=_required_count(row, "TtlNbOfTxs"),
                reference=reference,
                source_format_version="capital-market-bhavcopy-udiff-v1",
            )
        )
    return records


def _equity_record(
    *,
    trade_date: date,
    symbol: str,
    isin: str,
    previous_close: Decimal,
    open_price: Decimal,
    high_price: Decimal,
    low_price: Decimal,
    last_price: Decimal,
    close_price: Decimal,
    quantity: int,
    turnover: Decimal,
    trades: int,
    reference: SourceReference,
    source_format_version: str,
) -> dict[str, CanonicalValue]:
    return {
        "trade_date": trade_date,
        "exchange": "NSE",
        "symbol": symbol,
        "series": "EQ",
        "isin": isin,
        "previous_close": previous_close,
        "open_price": open_price,
        "high_price": high_price,
        "low_price": low_price,
        "last_price": last_price,
        "close_price": close_price,
        "total_traded_quantity": quantity,
        "turnover": turnover,
        "number_of_trades": trades,
        "source_report": _required_reference_value(reference.source_report),
        "source_format_version": source_format_version,
    }


def _read_raw_csv(content: bytes) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ParserError("source content is not UTF-8") from error
    reader = csv.reader(io.StringIO(text, newline=""))
    try:
        header = tuple(next(reader))
    except StopIteration as error:
        raise SchemaChangedError("source CSV is empty") from error
    if not header or any(not column for column in header):
        raise SchemaChangedError("source CSV has an invalid header")
    rows: list[dict[str, str]] = []
    for row in reader:
        if len(row) != len(header):
            raise ParserError("source CSV row does not match its header")
        rows.append(dict(zip(header, row, strict=True)))
    return header, rows


def _read_expected_csv(
    content: bytes, expected_header: tuple[str, ...]
) -> list[dict[str, str]]:
    header, rows = _read_raw_csv(content)
    if header != expected_header:
        raise SchemaChangedError("source CSV schema differs from the reviewed fixture")
    return rows


def _required_text(row: Mapping[str, str], column: str) -> str:
    value = _normalise_text(row[column])
    if not value:
        raise ParserError(f"{column} is required")
    return value


def _optional_text(row: Mapping[str, str], column: str) -> str | None:
    value = _normalise_text(row[column])
    return value or None


def _required_isin(row: Mapping[str, str], column: str) -> str:
    isin = _required_text(row, column)
    if _ISIN.fullmatch(isin) is None:
        raise ParserError(f"{column} is not an uppercase 12-character ISIN")
    return isin


def _required_decimal(row: Mapping[str, str], column: str) -> Decimal:
    value = _optional_decimal(row, column)
    if value is None:
        raise ParserError(f"{column} is required")
    return value


def _optional_decimal(row: Mapping[str, str], column: str) -> Decimal | None:
    text = _normalise_text(row[column])
    if text in {"", "-", "NA"}:
        return None
    value = _parse_decimal(text, column)
    return value


def _required_count(row: Mapping[str, str], column: str) -> int:
    value = _optional_count(row, column)
    if value is None:
        raise ParserError(f"{column} is required")
    return value


def _optional_count(row: Mapping[str, str], column: str) -> int | None:
    text = _normalise_text(row[column])
    if text in {"", "-", "NA"}:
        return None
    if not text.isdecimal():
        raise ParserError(f"{column} is not a non-negative integer")
    return int(text)


def _parse_decimal(text: str, column: str) -> Decimal:
    try:
        value = Decimal(text)
    except InvalidOperation as error:
        raise ParserError(f"{column} is not a Decimal") from error
    if not value.is_finite() or value < 0:
        raise ParserError(f"{column} is not a non-negative Decimal")
    return value


def _parse_source_date(text: str) -> date:
    for format_string in ("%Y-%m-%d", "%d-%b-%Y", "%d-%B-%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(text, format_string).date()
        except ValueError:
            continue
    raise ParserError("source date is invalid")


def _require_trade_date(trade_date: date, reference: SourceReference) -> None:
    if trade_date != reference.trade_date:
        raise ParserError("bhavcopy trade date does not match its reference")


def _require_source_format(reference: SourceReference, expected: str) -> None:
    if reference.source_format_version != expected:
        raise SchemaChangedError("source format does not match the reviewed parser")


def _required_reference_value(value: str) -> str:
    normalised = _normalise_text(value)
    if not normalised:
        raise ParserError("source reference value is required")
    return normalised


def _index_identity(raw_name: str) -> tuple[str, str] | None:
    name = raw_name.upper()
    if name in {"NIFTY 50", "NIFTY 500"}:
        return name, name
    return None


def _encode_record(
    schema: CanonicalCsvSchema, record: CanonicalRecord
) -> dict[str, str]:
    if set(record) != set(schema.header):
        raise SchemaChangedError("canonical record does not match the locked schema")
    encoded: dict[str, str] = {}
    for column in schema.header:
        encoded[column], missing = _encode_value(schema, column, record[column])
        encoded["__missing__" + column] = "1" if missing else "0"
    return encoded


def _encode_value(
    schema: CanonicalCsvSchema, column: str, value: CanonicalValue
) -> tuple[str, bool]:
    if value is None:
        if column not in schema.optional_columns:
            raise ParserError(f"{column} is required")
        return "NA", True
    if column in schema.date_columns:
        if type(value) is not date:
            raise ParserError(f"{column} must be a date")
        return value.isoformat(), False
    if column in schema.decimal_columns:
        if type(value) is not Decimal or not value.is_finite() or value < 0:
            raise ParserError(f"{column} must be a non-negative Decimal")
        return _format_decimal(value), False
    if column in schema.count_columns:
        if type(value) is not int or value < 0:
            raise ParserError(f"{column} must be a non-negative integer")
        return str(value), False
    if type(value) is not str:
        raise ParserError(f"{column} must be text")
    text = _normalise_text(value)
    if not text:
        raise ParserError(f"{column} is required")
    return text, False


def _format_decimal(value: Decimal) -> str:
    if value.is_zero():
        return "0"
    return format(value.normalize(), "f")


def _encode_csv_row(cells: Sequence[tuple[str, bool]]) -> str:
    return ",".join(
        _encode_csv_cell(value, force_quote) for value, force_quote in cells
    )


def _encode_csv_cell(value: str, force_quote: bool) -> str:
    if force_quote or any(character in value for character in ',"\r\n'):
        return '"' + value.replace('"', '""') + '"'
    return value


def _normalise_text(value: str) -> str:
    return unicodedata.normalize("NFC", value.strip())
