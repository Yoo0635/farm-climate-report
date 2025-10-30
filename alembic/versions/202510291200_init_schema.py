"""initial schema

Revision ID: 202510291200
Revises: 
Create Date: 2025-10-29 12:00:00
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "202510291200"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "profiles",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("phone", sa.String(length=32), nullable=False),
        sa.Column("region", sa.String(length=128), nullable=False),
        sa.Column("crop", sa.String(length=128), nullable=False),
        sa.Column("stage", sa.String(length=128), nullable=False),
        sa.Column("language", sa.String(length=8), nullable=False, server_default="ko"),
        sa.Column(
            "opt_in", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_profiles_phone", "profiles", ["phone"], unique=False)

    op.create_table(
        "briefs",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column(
            "profile_id",
            sa.String(length=64),
            sa.ForeignKey("profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("horizon_days", sa.Integer(), nullable=False, server_default="14"),
        sa.Column("link_id", sa.String(length=64), nullable=False),
        sa.Column("date_range", sa.String(length=64), nullable=False),
        sa.Column("triggers", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_briefs_profile_id", "briefs", ["profile_id"], unique=False)
    op.create_index("ix_briefs_link_id", "briefs", ["link_id"], unique=False)

    op.create_table(
        "brief_actions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "brief_id",
            sa.String(length=64),
            sa.ForeignKey("briefs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=256), nullable=False),
        sa.Column("timing_window", sa.String(length=128), nullable=False),
        sa.Column("trigger", sa.String(length=256), nullable=False),
        sa.Column("icon", sa.String(length=64), nullable=True),
        sa.Column("source_name", sa.String(length=256), nullable=False),
        sa.Column("source_year", sa.String(length=16), nullable=False),
    )
    op.create_index(
        "ix_brief_actions_brief_id", "brief_actions", ["brief_id"], unique=False
    )

    op.create_table(
        "brief_signals",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "brief_id",
            sa.String(length=64),
            sa.ForeignKey("briefs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("type", sa.String(length=16), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=True),
        sa.Column("notes", sa.String(length=256), nullable=True),
    )
    op.create_index(
        "ix_brief_signals_brief_id", "brief_signals", ["brief_id"], unique=False
    )

    op.create_table(
        "draft_reports",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column(
            "brief_id",
            sa.String(length=64),
            sa.ForeignKey("briefs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_draft_reports_brief_id", "draft_reports", ["brief_id"], unique=False
    )

    op.create_table(
        "refined_reports",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column(
            "draft_id",
            sa.String(length=64),
            sa.ForeignKey("draft_reports.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "interactions",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("phone", sa.String(length=32), nullable=False),
        sa.Column("keyword", sa.String(length=32), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("response", sa.Text(), nullable=True),
    )
    op.create_index("ix_interactions_phone", "interactions", ["phone"], unique=False)
    op.create_index(
        "ix_interactions_received_at", "interactions", ["received_at"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_interactions_received_at", table_name="interactions")
    op.drop_index("ix_interactions_phone", table_name="interactions")
    op.drop_table("interactions")

    op.drop_table("refined_reports")

    op.drop_index("ix_draft_reports_brief_id", table_name="draft_reports")
    op.drop_table("draft_reports")

    op.drop_index("ix_brief_signals_brief_id", table_name="brief_signals")
    op.drop_table("brief_signals")

    op.drop_index("ix_brief_actions_brief_id", table_name="brief_actions")
    op.drop_table("brief_actions")

    op.drop_index("ix_briefs_link_id", table_name="briefs")
    op.drop_index("ix_briefs_profile_id", table_name="briefs")
    op.drop_table("briefs")

    op.drop_index("ix_profiles_phone", table_name="profiles")
    op.drop_table("profiles")
