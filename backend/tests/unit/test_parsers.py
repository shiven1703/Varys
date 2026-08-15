from datetime import date
from decimal import Decimal

import pytest

from varys.parsers import (
    EQUITY_SCHEMA,
    CanonicalValue,
    ParserError,
    SchemaChangedError,
    parse_capital_market_bhavcopy,
    parse_index_report,
    parse_nifty500_universe,
    write_canonical_csv,
)
from varys.sources import SourceReference

TRADE_DATE = date(2026, 8, 14)
BHAVCOPY_REFERENCE = SourceReference(
    trade_date=TRADE_DATE,
    source_report="capital-market-bhavcopy-2026-08-14.zip",
    filename="capital-market-bhavcopy-2026-08-14.zip",
    source_format_version="capital-market-bhavcopy-udiff-v1",
)
INDEX_REFERENCE = SourceReference(
    trade_date=TRADE_DATE,
    source_report="nifty-indices-2026-08-14.csv",
    filename="nifty-indices-2026-08-14.csv",
    source_format_version="nifty-indices-report-v1",
)
UNIVERSE_REFERENCE = SourceReference(
    trade_date=TRADE_DATE,
    source_report="nifty-500-universe-2026-08-14.csv",
    filename="nifty-500-universe-2026-08-14.csv",
    source_format_version="nifty-500-universe-v1",
)
LEGACY_BHAVCOPY = (
    b"SYMBOL,SERIES,OPEN,HIGH,LOW,CLOSE,LAST,PREVCLOSE,TOTTRDQTY,TOTTRDVAL,"
    b"TIMESTAMP,TOTALTRADES,ISIN\n"
    b"ACME,EQ,101.2500,103,99.50,102.5,102,100,2000,205000.00,14-AUG-2026,42,"
    b"INE000A01010\n"
    b"PREFERENCE,BE,9,10,8,9,9,8,3,27,14-AUG-2026,1,INE000B01011\n"
)
UDIFF_BHAVCOPY = b",".join(
    (
        b"TradDt",
        b"BizDt",
        b"Sgmt",
        b"Src",
        b"FinInstrmTp",
        b"FinInstrmId",
        b"ISIN",
        b"TckrSymb",
        b"SctySrs",
        b"XpryDt",
        b"FininstrmActlXpryDt",
        b"StrkPric",
        b"OptnTp",
        b"FinInstrmNm",
        b"OpnPric",
        b"HghPric",
        b"LwPric",
        b"ClsPric",
        b"LastPric",
        b"PrvsClsgPric",
        b"UndrlygPric",
        b"SttlmPric",
        b"OpnIntrst",
        b"ChngInOpnIntrst",
        b"TtlTradgVol",
        b"TtlTrfVal",
        b"TtlNbOfTxs",
        b"FinInstrmDelivQty",
        b"FinInstrmDelivPct\n",
    )
) + (
    b"2026-08-14,2026-08-14,CM,FINAL,ST,INE000A01010,INE000A01010,ACME,EQ,"
    b",,,,Acme Limited,101.2500,103,99.50,102.5,102,100,,,,,2000,205000.00,"
    b"42,,\n"
)
INDEX_REPORT = (
    b"Index Name,Index Date,Open Index Value,High Index Value,Low Index Value,"
    b"Closing Index Value,Points Change,Change(%),Volume,Turnover (Rs. Cr.)\n"
    b"NIFTY 500,14-Aug-2026,200,205,198,204,4,2,5000,100000\n"
    b"NIFTY 50,14-Aug-2026,24500,24600,24400,24550,50,0.2,-,-\n"
    b"NIFTY BANK,14-Aug-2026,50000,50100,49000,49500,-500,-1,100,200\n"
)
UNIVERSE = b"""Company Name,Industry,Symbol,Series,ISIN Code
 Acme Limited ,Industrials,ACME,EQ,INE000A01010
Preference Shares,Financials,PREFERENCE,BE,INE000B01011
"""


def test_legacy_and_udiff_bhavcopies_have_equivalent_equity_semantics() -> None:
    legacy = parse_capital_market_bhavcopy(LEGACY_BHAVCOPY, BHAVCOPY_REFERENCE)
    udiff = parse_capital_market_bhavcopy(UDIFF_BHAVCOPY, BHAVCOPY_REFERENCE)

    assert len(legacy) == len(udiff) == 1
    assert legacy[0] | {"source_format_version": ""} == udiff[0] | {
        "source_format_version": ""
    }
    assert legacy[0]["series"] == "EQ"


def test_index_and_universe_parsers_keep_only_locked_v1_rows() -> None:
    index_records = parse_index_report(INDEX_REPORT, INDEX_REFERENCE)
    universe_records = parse_nifty500_universe(UNIVERSE, UNIVERSE_REFERENCE)

    assert {record["index_code"] for record in index_records} == {
        "NIFTY 50",
        "NIFTY 500",
    }
    assert universe_records == [
        {
            "universe_code": "NIFTY 500",
            "snapshot_date": TRADE_DATE,
            "exchange": "NSE",
            "symbol": "ACME",
            "series": "EQ",
            "isin": "INE000A01010",
            "company_name": "Acme Limited",
            "industry": "Industrials",
        }
    ]


def test_schema_drift_and_malformed_required_fields_fail_safely() -> None:
    unexpected_column = LEGACY_BHAVCOPY.replace(b"\n", b",unexpected\n")
    malformed_quantity = LEGACY_BHAVCOPY.replace(b",2000,205000.00", b",two,205000.00")

    with pytest.raises(SchemaChangedError):
        parse_capital_market_bhavcopy(unexpected_column, BHAVCOPY_REFERENCE)
    with pytest.raises(ParserError, match="TOTTRDQTY"):
        parse_capital_market_bhavcopy(malformed_quantity, BHAVCOPY_REFERENCE)


def test_common_writer_rejects_unknown_columns_and_quotes_literal_na() -> None:
    record: dict[str, CanonicalValue] = {
        "trade_date": TRADE_DATE,
        "exchange": "NSE",
        "symbol": "ACME",
        "series": "EQ",
        "isin": "INE000A01010",
        "previous_close": Decimal("100"),
        "open_price": Decimal("101.25"),
        "high_price": Decimal("103"),
        "low_price": Decimal("99.5"),
        "last_price": Decimal("102"),
        "close_price": Decimal("102.5"),
        "total_traded_quantity": 2000,
        "turnover": Decimal("205000"),
        "number_of_trades": 42,
        "source_report": "NA",
        "source_format_version": "capital-market-bhavcopy-legacy-v1",
    }

    output = write_canonical_csv(EQUITY_SCHEMA, [record])
    assert b',"NA",capital-market-bhavcopy-legacy-v1\n' in output
    with pytest.raises(SchemaChangedError):
        write_canonical_csv(EQUITY_SCHEMA, [{**record, "unexpected": "column"}])
