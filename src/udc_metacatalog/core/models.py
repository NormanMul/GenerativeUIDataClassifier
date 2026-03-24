"""UDC MetaCatalog — SQLAlchemy ORM models for metadata storage."""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass


class DataAsset(Base):
    """Represents a data asset (table, view, or dataset) in the catalog."""

    __tablename__ = "data_assets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    qualified_name = Column(String(500), nullable=False, unique=True)
    source_type = Column(String(50), nullable=False, index=True)  # postgres, sap, fabric
    source_instance = Column(String(255))
    database_name = Column(String(255))
    schema_name = Column(String(255))
    description = Column(Text)
    tags = Column(ARRAY(String), default=list)
    quality_score = Column(Float, default=0.0)
    owner = Column(String(255))
    properties = Column(JSONB, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    columns = relationship("ColumnMeta", back_populates="asset", cascade="all, delete-orphan")
    quality_reports = relationship("QualityReportRecord", back_populates="asset", cascade="all, delete-orphan")


class ColumnMeta(Base):
    """Represents a column within a data asset."""

    __tablename__ = "columns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("data_assets.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    data_type = Column(String(100))
    description = Column(Text)
    is_nullable = Column(Boolean, default=True)
    is_primary_key = Column(Boolean, default=False)
    is_foreign_key = Column(Boolean, default=False)
    foreign_key_ref = Column(String(500))
    null_percentage = Column(Float)
    unique_percentage = Column(Float)
    is_pii = Column(Boolean, default=False)
    pii_type = Column(String(50))
    classification = Column(String(50))
    tags = Column(ARRAY(String), default=list)
    sample_values = Column(ARRAY(String), default=list)
    glossary_terms = Column(ARRAY(String), default=list)
    properties = Column(JSONB, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    asset = relationship("DataAsset", back_populates="columns")

    __table_args__ = (UniqueConstraint("asset_id", "name", name="uq_asset_column"),)


class LineageEdge(Base):
    """Represents a column-level lineage relationship."""

    __tablename__ = "lineage_edges"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_asset_id = Column(UUID(as_uuid=True), ForeignKey("data_assets.id"), nullable=False)
    source_column = Column(String(255), nullable=False)
    target_asset_id = Column(UUID(as_uuid=True), ForeignKey("data_assets.id"), nullable=False)
    target_column = Column(String(255), nullable=False)
    edge_type = Column(String(50), default="direct")  # direct, transformation, aggregation
    transformation = Column(Text)
    properties = Column(JSONB, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class GlossaryTerm(Base):
    """Represents a business glossary term."""

    __tablename__ = "glossary_terms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    definition = Column(Text, nullable=False)
    owner = Column(String(255))
    aliases = Column(ARRAY(String), default=list)
    related_columns = Column(ARRAY(String), default=list)
    version = Column(Integer, default=1)
    properties = Column(JSONB, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class KPIFormula(Base):
    """Represents a KPI formula in the formula registry."""

    __tablename__ = "kpi_formulas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    expression = Column(Text, nullable=False)
    description = Column(Text)
    format_string = Column(String(50))
    source_columns = Column(ARRAY(String), default=list)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class QualityReportRecord(Base):
    """Stored quality report for a data asset."""

    __tablename__ = "quality_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("data_assets.id", ondelete="CASCADE"), nullable=False)
    overall_score = Column(Float, nullable=False)
    passed = Column(Boolean, nullable=False)
    checks = Column(JSONB, nullable=False)
    summary = Column(JSONB)
    generated_by = Column(String(255))
    execution_time_ms = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    asset = relationship("DataAsset", back_populates="quality_reports")


class APIKey(Base):
    """API key for service authentication."""

    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key_hash = Column(String(128), nullable=False, unique=True)
    name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)  # business_analyst, data_engineer, data_steward, service
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime)
    metadata_ = Column("metadata", JSONB, default=dict)
