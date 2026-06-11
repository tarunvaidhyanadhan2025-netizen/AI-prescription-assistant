"""initial tables

Revision ID: 0001_initial
Revises: 
Create Date: 2026-05-31

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "prescriptions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("file_path", sa.String(512), nullable=False),
        sa.Column("raw_text", sa.Text, nullable=True),
        sa.Column("cleaned_text", sa.Text, nullable=True),
        sa.Column("detected_medicines", sa.JSON, nullable=True),
        sa.Column("ocr_confidence", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("patient_age", sa.Integer, nullable=True),
        sa.Column("language", sa.String(10), nullable=False, server_default="en"),
        sa.Column("analysis_done", sa.Boolean, nullable=False, server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )

    op.create_table(
        "analysis_results",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("prescription_id", sa.String(36), nullable=False, index=True),
        sa.Column("medicine_name", sa.String(255), nullable=False),
        sa.Column("drug_class", sa.String(255), nullable=True),
        sa.Column("explanation", sa.Text, nullable=True),
        sa.Column("use_case", sa.Text, nullable=True),
        sa.Column("side_effects", sa.JSON, nullable=True),
        sa.Column("warnings", sa.JSON, nullable=True),
        sa.Column("dosage_info", sa.Text, nullable=True),
        sa.Column("severity_level", sa.String(20), nullable=False, server_default="low"),
        sa.Column("causes_drowsiness", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("provider_used", sa.String(50), nullable=False, server_default="template"),
        sa.Column(
            "created_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )

    op.create_index(
        "ix_analysis_results_prescription_id",
        "analysis_results",
        ["prescription_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_analysis_results_prescription_id", table_name="analysis_results")
    op.drop_table("analysis_results")
    op.drop_table("prescriptions")
