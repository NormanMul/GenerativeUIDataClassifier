"""Initial schema — core tables for MetaCatalog.

Revision ID: 0001
Revises: None
Create Date: 2024-01-01 00:00:00.000000
"""
from __future__ import annotations

from typing import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # API Keys
    op.create_table(
        "api_keys",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("key_hash", sa.String(128), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("scopes", ARRAY(sa.Text), server_default="{}"),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Data Assets
    op.create_table(
        "data_assets",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("qualified_name", sa.String(512), nullable=False, unique=True),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("source_instance", sa.String(255)),
        sa.Column("database_name", sa.String(255)),
        sa.Column("schema_name", sa.String(128), server_default="public"),
        sa.Column("description", sa.Text),
        sa.Column("tags", ARRAY(sa.Text), server_default="{}"),
        sa.Column("quality_score", sa.Float, server_default="0.0"),
        sa.Column("row_count", sa.BigInteger),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_data_assets_source_type", "data_assets", ["source_type"])
    op.create_index("ix_data_assets_name", "data_assets", ["name"])

    # Column Metadata
    op.create_table(
        "column_meta",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("asset_id", UUID(as_uuid=True), sa.ForeignKey("data_assets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("data_type", sa.String(100)),
        sa.Column("is_nullable", sa.Boolean, server_default="true"),
        sa.Column("is_primary_key", sa.Boolean, server_default="false"),
        sa.Column("is_foreign_key", sa.Boolean, server_default="false"),
        sa.Column("null_percentage", sa.Float),
        sa.Column("unique_percentage", sa.Float),
        sa.Column("is_pii", sa.Boolean, server_default="false"),
        sa.Column("pii_type", sa.String(50)),
        sa.Column("classification", sa.String(100)),
        sa.Column("sample_values", JSONB),
    )
    op.create_index("ix_column_meta_asset_id", "column_meta", ["asset_id"])

    # Lineage Edges
    op.create_table(
        "lineage_edges",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("source_asset_id", UUID(as_uuid=True), sa.ForeignKey("data_assets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_asset_id", UUID(as_uuid=True), sa.ForeignKey("data_assets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("transformation_type", sa.String(50)),
        sa.Column("transformation_logic", sa.Text),
        sa.Column("column_mappings", JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_lineage_source", "lineage_edges", ["source_asset_id"])
    op.create_index("ix_lineage_target", "lineage_edges", ["target_asset_id"])

    # Glossary Terms
    op.create_table(
        "glossary_terms",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("term", sa.String(255), nullable=False, unique=True),
        sa.Column("definition", sa.Text, nullable=False),
        sa.Column("domain", sa.String(100)),
        sa.Column("synonyms", ARRAY(sa.Text), server_default="{}"),
        sa.Column("owner", sa.String(255)),
        sa.Column("status", sa.String(50), server_default="'draft'"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # KPI Formulas
    op.create_table(
        "kpi_formulas",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
        sa.Column("formula", sa.Text, nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("unit", sa.String(50)),
        sa.Column("domain", sa.String(100)),
        sa.Column("source_columns", ARRAY(sa.Text), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Quality Reports
    op.create_table(
        "quality_reports",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("asset_id", UUID(as_uuid=True), sa.ForeignKey("data_assets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("overall_score", sa.Float, nullable=False),
        sa.Column("passed", sa.Boolean, nullable=False),
        sa.Column("checks", JSONB, server_default="'[]'"),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("generated_by", sa.String(100), server_default="'system'"),
    )
    op.create_index("ix_quality_reports_asset_id", "quality_reports", ["asset_id"])


def downgrade() -> None:
    op.drop_table("quality_reports")
    op.drop_table("kpi_formulas")
    op.drop_table("glossary_terms")
    op.drop_table("lineage_edges")
    op.drop_table("column_meta")
    op.drop_table("data_assets")
    op.drop_table("api_keys")
