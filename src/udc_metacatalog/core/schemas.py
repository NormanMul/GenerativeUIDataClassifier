"""UDC MetaCatalog — Pydantic v2 schemas for request/response validation."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# --- Column schemas ---


class ColumnBase(BaseModel):
    """Base column schema."""

    name: str = Field(..., min_length=1, max_length=255)
    data_type: str = Field(..., max_length=100)
    description: str | None = None
    is_nullable: bool = True
    is_primary_key: bool = False
    is_foreign_key: bool = False
    foreign_key_ref: str | None = None
    tags: list[str] = Field(default_factory=list)


class ColumnResponse(ColumnBase):
    """Column response with profiling data."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    null_percentage: float | None = None
    unique_percentage: float | None = None
    is_pii: bool = False
    pii_type: str | None = None
    classification: str | None = None
    sample_values: list[str] = Field(default_factory=list)
    glossary_terms: list[str] = Field(default_factory=list)


# --- Data Asset schemas ---


class DataAssetCreate(BaseModel):
    """Schema for creating a data asset."""

    name: str = Field(..., min_length=1, max_length=255)
    qualified_name: str = Field(..., min_length=1, max_length=500)
    source_type: str = Field(..., pattern="^(postgres|sap|fabric)$")
    source_instance: str | None = None
    database_name: str | None = None
    schema_name: str | None = None
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
    owner: str | None = None
    properties: dict[str, str] = Field(default_factory=dict)
    columns: list[ColumnBase] = Field(default_factory=list)


class DataAssetUpdate(BaseModel):
    """Schema for updating a data asset."""

    name: str | None = None
    description: str | None = None
    tags: list[str] | None = None
    owner: str | None = None
    properties: dict[str, str] | None = None


class DataAssetResponse(BaseModel):
    """Schema for data asset response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    qualified_name: str
    source_type: str
    source_instance: str | None
    database_name: str | None
    schema_name: str | None
    description: str | None
    tags: list[str]
    quality_score: float
    owner: str | None
    columns: list[ColumnResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class PaginatedResponse(BaseModel):
    """Generic paginated response."""

    items: list[DataAssetResponse]
    total_count: int
    page: int
    page_size: int


# --- Quality schemas ---


class QualityCheckResult(BaseModel):
    """Single quality check result."""

    check_name: str
    check_type: str
    column_name: str | None = None
    passed: bool
    score: float = 0.0
    expected: str | None = None
    actual: str | None = None
    details: str | None = None
    severity: str = "info"


class QualityReportResponse(BaseModel):
    """Quality report response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    asset_id: UUID
    overall_score: float
    passed: bool
    checks: list[QualityCheckResult]
    generated_by: str | None
    execution_time_ms: int | None
    created_at: datetime


# --- Glossary schemas ---


class GlossaryTermCreate(BaseModel):
    """Create a glossary term."""

    name: str = Field(..., min_length=1, max_length=255)
    definition: str
    owner: str | None = None
    aliases: list[str] = Field(default_factory=list)


class GlossaryTermResponse(BaseModel):
    """Glossary term response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    definition: str
    owner: str | None
    aliases: list[str]
    related_columns: list[str]
    version: int
    created_at: datetime
    updated_at: datetime
