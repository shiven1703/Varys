"""Persist daily-run trade dates and prevent duplicate nonterminal requests.

Revision ID: 0005_daily_run_trade_date
Revises: 0004_package_publication
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_daily_run_trade_date"
down_revision: str | None = "0004_package_publication"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("runs", sa.Column("trade_date", sa.Date()))
    op.execute(
        "CREATE UNIQUE INDEX uq_runs_nonterminal_daily_trade_date ON runs (trade_date) "
        "WHERE kind = 'daily' AND state IN ('QUEUED', 'RUNNING', "
        "'WAITING_FOR_SOURCE', 'PAUSED', 'SOURCE_BLOCKED')"
    )


def downgrade() -> None:
    op.execute("DROP INDEX uq_runs_nonterminal_daily_trade_date")
    op.drop_column("runs", "trade_date")
