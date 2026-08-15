"""Add PostgreSQL-backed run dispatch state.

Revision ID: 0003_run_dispatch
Revises: 0002_authentication
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_run_dispatch"
down_revision: str | None = "0002_authentication"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("state", sa.String(32), nullable=False),
        sa.Column("worker_id", sa.String(128)),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True)),
        sa.Column("heartbeat_at", sa.DateTime(timezone=True)),
        sa.Column("requested_action", sa.String(16)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "state IN ('QUEUED', 'RUNNING', 'WAITING_FOR_SOURCE', 'PAUSED', "
            "'SOURCE_BLOCKED', 'COMPLETED', 'COMPLETED_WITH_WARNINGS', "
            "'FAILED', 'CANCELLED')",
            name="ck_runs_state",
        ),
        sa.CheckConstraint(
            "requested_action IS NULL OR requested_action IN ('PAUSE', 'CANCEL')",
            name="ck_runs_requested_action",
        ),
        sa.CheckConstraint(
            "(state = 'RUNNING' AND worker_id IS NOT NULL "
            "AND lease_expires_at IS NOT NULL AND heartbeat_at IS NOT NULL) "
            "OR (state != 'RUNNING' AND worker_id IS NULL "
            "AND lease_expires_at IS NULL AND heartbeat_at IS NULL)",
            name="ck_runs_worker_lease",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_runs_one_active ON runs ((true)) "
        "WHERE state IN ('RUNNING', 'WAITING_FOR_SOURCE', 'PAUSED', 'SOURCE_BLOCKED')"
    )
    op.create_index("ix_runs_state_created_at", "runs", ["state", "created_at"])
    op.create_table(
        "run_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("from_state", sa.String(32)),
        sa.Column("to_state", sa.String(32)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["runs.id"]),
        sa.CheckConstraint("sequence > 0", name="ck_run_events_sequence"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("run_id", "sequence"),
    )
    op.execute(
        """
        CREATE FUNCTION prevent_run_event_mutation()
        RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'run_events are append-only';
        END;
        $$ LANGUAGE plpgsql
        """
    )
    op.execute(
        """
        CREATE TRIGGER run_events_append_only
        BEFORE UPDATE OR DELETE ON run_events
        FOR EACH ROW EXECUTE FUNCTION prevent_run_event_mutation()
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER run_events_append_only ON run_events")
    op.execute("DROP FUNCTION prevent_run_event_mutation")
    op.drop_table("run_events")
    op.drop_index("ix_runs_state_created_at", table_name="runs")
    op.execute("DROP INDEX uq_runs_one_active")
    op.drop_table("runs")
