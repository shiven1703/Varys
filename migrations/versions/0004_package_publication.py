"""Add recoverable package-publication records.

Revision ID: 0004_package_publication
Revises: 0003_run_dispatch
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_package_publication"
down_revision: str | None = "0003_run_dispatch"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "packages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("state", sa.String(32), nullable=False),
        sa.Column("relative_path", sa.String(256)),
        sa.Column("size_bytes", sa.BigInteger()),
        sa.Column("sha256", sa.String(64)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["runs.id"]),
        sa.CheckConstraint(
            "kind IN ('daily', 'universe', 'backfill')", name="ck_packages_kind"
        ),
        sa.CheckConstraint("version > 0", name="ck_packages_version"),
        sa.CheckConstraint(
            "state IN ('BUILDING', 'VERIFYING', 'READY', 'READY_WITH_WARNINGS', "
            "'FAILED', 'QUARANTINED', 'SUPERSEDED')",
            name="ck_packages_state",
        ),
        sa.CheckConstraint(
            "(state IN ('READY', 'READY_WITH_WARNINGS') "
            "AND relative_path IS NOT NULL AND size_bytes > 0 AND sha256 IS NOT NULL) "
            "OR (state NOT IN ('READY', 'READY_WITH_WARNINGS'))",
            name="ck_packages_ready_metadata",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_packages_state_created_at", "packages", ["state", "created_at"])
    op.create_table(
        "package_files",
        sa.Column("package_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("row_count", sa.Integer()),
        sa.ForeignKeyConstraint(["package_id"], ["packages.id"]),
        sa.CheckConstraint("size_bytes > 0", name="ck_package_files_size"),
        sa.CheckConstraint(
            "row_count IS NULL OR row_count >= 0", name="ck_package_files_rows"
        ),
        sa.PrimaryKeyConstraint("package_id", "name"),
    )


def downgrade() -> None:
    op.drop_table("package_files")
    op.drop_index("ix_packages_state_created_at", table_name="packages")
    op.drop_table("packages")
