"""UDC PolicyGuard — Compliance report generation."""

import html
from datetime import datetime, timezone
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class ComplianceReporter:
    """Generate compliance reports from audit data.

    Produces reports covering actions taken, policy violations,
    and agent trust scores over a given time period.
    """

    QUERY_SQL = """
        SELECT agent_id, session_id, action_type, resource,
               decision, reason, user_role, created_at
        FROM audit_log
        WHERE created_at >= $1 AND created_at <= $2
    """

    def __init__(self, pg_pool: Any | None = None) -> None:
        self._pg_pool = pg_pool

    async def generate_json_report(self, filters: dict[str, Any]) -> dict:
        """Generate a JSON compliance report.

        Args:
            filters: Query filters (time range, agent_id, etc.).

        Returns:
            Compliance report as a dictionary.
        """
        rows = await self._query_audit_log(filters)

        total = len(rows)
        allowed = sum(1 for r in rows if r["decision"] == "allow")
        denied = total - allowed

        # Top actors by action count
        actor_counts: dict[str, int] = {}
        action_counts: dict[str, int] = {}
        for r in rows:
            actor_counts[r["agent_id"]] = actor_counts.get(r["agent_id"], 0) + 1
            action_counts[r["action_type"]] = action_counts.get(r["action_type"], 0) + 1

        top_actors = sorted(actor_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        top_actions = sorted(action_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "filters": filters,
            "total_actions": total,
            "allowed_count": allowed,
            "denied_count": denied,
            "denial_rate": round(denied / total * 100, 2) if total else 0.0,
            "top_actors": [{"agent_id": a, "count": c} for a, c in top_actors],
            "top_actions": [{"action_type": a, "count": c} for a, c in top_actions],
        }
        logger.info("reporter.json_report", total=total)
        return report

    async def generate_html_report(self, filters: dict[str, Any]) -> str:
        """Generate an HTML compliance report.

        Args:
            filters: Query filters (time range, agent_id, etc.).

        Returns:
            Rendered HTML report string.
        """
        data = await self.generate_json_report(filters)

        rows_html = ""
        for actor in data["top_actors"]:
            rows_html += (
                f"<tr><td>{html.escape(actor['agent_id'])}</td>"
                f"<td>{actor['count']}</td></tr>\n"
            )

        report_html = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><title>UDC Compliance Report</title>
<style>
  body {{ font-family: sans-serif; margin: 2rem; }}
  table {{ border-collapse: collapse; width: 100%; }}
  th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
  th {{ background: #4a90d9; color: #fff; }}
  .metric {{ display: inline-block; margin: 1rem; padding: 1rem; background: #f5f5f5; border-radius: 4px; }}
</style></head>
<body>
<h1>UDC PolicyGuard — Compliance Report</h1>
<p>Generated: {html.escape(data['generated_at'])}</p>
<div>
  <div class="metric"><strong>Total Actions</strong><br>{data['total_actions']}</div>
  <div class="metric"><strong>Allowed</strong><br>{data['allowed_count']}</div>
  <div class="metric"><strong>Denied</strong><br>{data['denied_count']}</div>
  <div class="metric"><strong>Denial Rate</strong><br>{data['denial_rate']}%</div>
</div>
<h2>Top Actors</h2>
<table><tr><th>Agent ID</th><th>Actions</th></tr>
{rows_html}</table>
</body></html>"""
        logger.info("reporter.html_report", total=data["total_actions"])
        return report_html

    async def _query_audit_log(self, filters: dict[str, Any]) -> list[dict]:
        """Query audit_log table with the given filters."""
        start = filters.get("start_time", datetime.min.replace(tzinfo=timezone.utc))
        end = filters.get("end_time", datetime.now(timezone.utc))

        if self._pg_pool is None:
            logger.warning("reporter.no_pg_pool")
            return []

        query = self.QUERY_SQL
        args: list[Any] = [start, end]
        idx = 3

        agent_filter = filters.get("agent_id")
        if agent_filter:
            query += f" AND agent_id = ${idx}"
            args.append(agent_filter)
            idx += 1

        action_filter = filters.get("action_type")
        if action_filter:
            query += f" AND action_type = ${idx}"
            args.append(action_filter)
            idx += 1

        query += " ORDER BY created_at DESC"

        try:
            async with self._pg_pool.acquire() as conn:
                records = await conn.fetch(query, *args)
            return [dict(r) for r in records]
        except Exception as exc:
            logger.error("reporter.query_error", error=str(exc))
            return []
