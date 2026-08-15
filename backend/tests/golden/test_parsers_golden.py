from collections.abc import Callable
from datetime import date
from pathlib import Path

from varys.parsers import (
    parse_capital_market_bhavcopy,
    parse_index_report,
    parse_nifty500_universe,
    write_equity_csv,
    write_index_csv,
    write_universe_csv,
)
from varys.sources import SourceReference

_FIXTURES = Path(__file__).with_name("fixtures")
_TRADE_DATE = date(2026, 8, 14)


def test_canonical_csvs_match_golden_bytes_on_repeated_runs() -> None:
    equity_reference = SourceReference(
        _TRADE_DATE,
        "capital-market-bhavcopy-2026-08-14.zip",
        "capital-market-bhavcopy-2026-08-14.zip",
        "capital-market-bhavcopy-udiff-v1",
    )
    index_reference = SourceReference(
        _TRADE_DATE,
        "nifty-indices-2026-08-14.csv",
        "nifty-indices-2026-08-14.csv",
        "nifty-indices-report-v1",
    )
    universe_reference = SourceReference(
        _TRADE_DATE,
        "nifty-500-universe-2026-08-14.csv",
        "nifty-500-universe-2026-08-14.csv",
        "nifty-500-universe-v1",
    )

    output_builders: dict[str, Callable[[], bytes]] = {
        "equity.csv": lambda: write_equity_csv(
            parse_capital_market_bhavcopy(
                (_FIXTURES / "udiff_bhavcopy.csv").read_bytes(), equity_reference
            )
        ),
        "index.csv": lambda: write_index_csv(
            parse_index_report(
                (_FIXTURES / "index_report.csv").read_bytes(), index_reference
            )
        ),
        "universe.csv": lambda: write_universe_csv(
            parse_nifty500_universe(
                (_FIXTURES / "universe_report.csv").read_bytes(), universe_reference
            )
        ),
    }

    for filename, build_output in output_builders.items():
        output = build_output()
        assert output == (_FIXTURES / filename).read_bytes()
        assert output == build_output()
