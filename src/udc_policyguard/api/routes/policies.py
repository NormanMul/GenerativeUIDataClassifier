"""UDC PolicyGuard — Policy management endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class PolicyCreate(BaseModel):
    """Schema for creating a policy."""

    name: str
    description: str
    rule_type: str
    rules: dict


class PolicyResponse(BaseModel):
    """Schema for policy responses."""

    id: str
    name: str
    description: str
    rule_type: str
    rules: dict
    enabled: bool


@router.get("/")
async def list_policies() -> list[PolicyResponse]:
    """List all policies."""
    raise NotImplementedError


@router.post("/", status_code=201)
async def create_policy(policy: PolicyCreate) -> PolicyResponse:
    """Create a new policy."""
    raise NotImplementedError


@router.get("/{policy_id}")
async def get_policy(policy_id: str) -> PolicyResponse:
    """Get a policy by ID."""
    raise NotImplementedError


@router.put("/{policy_id}")
async def update_policy(policy_id: str, policy: PolicyCreate) -> PolicyResponse:
    """Update an existing policy."""
    raise NotImplementedError


@router.delete("/{policy_id}", status_code=204)
async def delete_policy(policy_id: str) -> None:
    """Delete a policy."""
    raise NotImplementedError
