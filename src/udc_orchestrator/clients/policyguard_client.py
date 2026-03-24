"""Async gRPC client for UDC PolicyGuard service."""

from __future__ import annotations

import os
from typing import Any

import grpc
import structlog
from grpc import aio

from shared_grpc import policy_pb2, policy_pb2_grpc

logger = structlog.get_logger(__name__)


class PolicyGuardClient:
    """Async gRPC client wrapping the PolicyGuardService."""

    def __init__(self, channel: aio.Channel) -> None:
        self._channel = channel
        self._stub = policy_pb2_grpc.PolicyGuardServiceStub(channel)

    @classmethod
    def connect(cls, host: str | None = None, port: int | None = None) -> PolicyGuardClient:
        """Create a client connected to the PolicyGuard gRPC server."""
        host = host or os.environ.get("POLICYGUARD_GRPC_HOST", "localhost")
        port = port or int(os.environ.get("POLICYGUARD_GRPC_PORT", "50056"))
        channel = aio.insecure_channel(f"{host}:{port}")
        logger.info("policyguard_client.connected", host=host, port=port)
        return cls(channel)

    async def close(self) -> None:
        """Close the underlying gRPC channel."""
        await self._channel.close()

    async def evaluate_policy(
        self,
        agent_id: str,
        session_id: str,
        action_type: str,
        resource: str,
        user_role: str = "",
        context: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Evaluate a policy for a given action."""
        try:
            request = policy_pb2.PolicyEvalRequest(
                agent_id=agent_id,
                session_id=session_id,
                action_type=action_type,
                resource=resource,
                user_role=user_role,
                context=context or {},
            )
            response = await self._stub.EvaluatePolicy(request)
            return {
                "allowed": response.allowed,
                "decision": response.decision,
                "reason": response.reason,
                "violated_policies": list(response.violated_policies),
                "applied_policies": list(response.applied_policies),
                "evaluation_time_us": response.evaluation_time_us,
                "updated_trust": _proto_to_dict(response.updated_trust) if response.updated_trust else None,
            }
        except grpc.RpcError as e:
            logger.error("policyguard_client.evaluate_policy.error", code=e.code(), details=e.details())
            raise

    async def get_trust_score(self, agent_id: str, session_id: str) -> dict[str, Any]:
        """Get the current trust score for an agent/session."""
        try:
            request = policy_pb2.GetTrustScoreRequest(
                agent_id=agent_id,
                session_id=session_id,
            )
            response = await self._stub.GetTrustScore(request)
            return {
                "agent_id": response.agent_id,
                "session_id": response.session_id,
                "score": response.score,
                "level": response.level,
                "total_actions": response.total_actions,
                "violations": response.violations,
                "last_updated": response.last_updated,
            }
        except grpc.RpcError as e:
            logger.error("policyguard_client.get_trust_score.error", code=e.code(), details=e.details())
            raise

    async def get_audit_trail(
        self,
        agent_id: str = "",
        session_id: str = "",
        start_time: str = "",
        end_time: str = "",
        action_type: str = "",
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        """Retrieve the audit trail for an agent or session."""
        try:
            request = policy_pb2.GetAuditTrailRequest(
                agent_id=agent_id,
                session_id=session_id,
                start_time=start_time,
                end_time=end_time,
                action_type=action_type,
                page=page,
                page_size=page_size,
            )
            response = await self._stub.GetAuditTrail(request)
            return {
                "entries": [_proto_to_dict(e) for e in response.entries],
                "total_count": response.total_count,
                "page": response.page,
                "page_size": response.page_size,
            }
        except grpc.RpcError as e:
            logger.error("policyguard_client.get_audit_trail.error", code=e.code(), details=e.details())
            raise


def _proto_to_dict(msg: Any) -> dict[str, Any]:
    """Convert a protobuf message to a plain dict."""
    from google.protobuf.json_format import MessageToDict

    return MessageToDict(msg, preserving_proto_field_name=True)
