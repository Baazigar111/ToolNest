"""Privacy-focused usage analytics service with in-memory buffering and batch database flushing."""

import threading
import uuid
from datetime import date, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.daily_usage import DailyUsage
from app.models.tool import Tool

_lock = threading.Lock()
# Buffer: { (date, tool_id): {"uses": int, "errors": int, "bytes": int} }
_usage_buffer: dict[tuple[date, uuid.UUID], dict[str, int]] = {}


class UsageService:
    """Aggregates and persists daily usage counters without logging PII, IPs, or file details."""

    @staticmethod
    def record_usage(
        tool_id: uuid.UUID,
        is_error: bool = False,
        bytes_count: int = 0,
        usage_date: date | None = None,
    ) -> None:
        """
        Record a tool execution in the in-memory buffer.
        Thread-safe and lightweight to avoid frequent PostgreSQL writes.
        """
        target_date = usage_date or date.today()
        key = (target_date, tool_id)

        with _lock:
            if key not in _usage_buffer:
                _usage_buffer[key] = {"uses": 0, "errors": 0, "bytes": 0}
            _usage_buffer[key]["uses"] += 1
            if is_error:
                _usage_buffer[key]["errors"] += 1
            _usage_buffer[key]["bytes"] += max(0, bytes_count)

    @staticmethod
    def get_buffered_totals() -> dict[tuple[date, uuid.UUID], dict[str, int]]:
        """Return a snapshot copy of current in-memory buffered counters."""
        with _lock:
            return {k: dict(v) for k, v in _usage_buffer.items()}

    @classmethod
    def flush_counters(cls, session: Session) -> int:
        """
        Flush in-memory counters to PostgreSQL daily_usage table.
        Merges existing database counters with buffered increments.
        Returns number of database records modified.
        """
        with _lock:
            if not _usage_buffer:
                return 0
            items_to_flush = list(_usage_buffer.items())
            _usage_buffer.clear()

        records_updated = 0
        try:
            for (target_date, tool_id), counts in items_to_flush:
                record = session.scalar(
                    select(DailyUsage).where(
                        DailyUsage.date == target_date,
                        DailyUsage.tool_id == tool_id,
                    )
                )
                if record:
                    record.uses += counts["uses"]
                    record.errors += counts["errors"]
                    record.bytes += counts["bytes"]
                else:
                    record = DailyUsage(
                        date=target_date,
                        tool_id=tool_id,
                        uses=counts["uses"],
                        errors=counts["errors"],
                        bytes=counts["bytes"],
                    )
                    session.add(record)
                records_updated += 1

            session.commit()
            return records_updated
        except Exception:
            session.rollback()
            # Restore counts back into buffer so data is not lost on transient DB failure
            with _lock:
                for (target_date, tool_id), counts in items_to_flush:
                    key = (target_date, tool_id)
                    if key not in _usage_buffer:
                        _usage_buffer[key] = {"uses": 0, "errors": 0, "bytes": 0}
                    _usage_buffer[key]["uses"] += counts["uses"]
                    _usage_buffer[key]["errors"] += counts["errors"]
                    _usage_buffer[key]["bytes"] += counts["bytes"]
            raise

    @staticmethod
    def get_analytics_summary(session: Session, days: int = 30) -> list[dict[str, Any]]:
        """
        Retrieve aggregated analytics per tool for the last N days.
        Used by the admin panel to view usage and error rates.
        """
        start_date = date.today() - timedelta(days=days)

        stmt = (
            select(
                Tool.id,
                Tool.name,
                Tool.slug,
                func.coalesce(func.sum(DailyUsage.uses), 0).label("total_uses"),
                func.coalesce(func.sum(DailyUsage.errors), 0).label("total_errors"),
                func.coalesce(func.sum(DailyUsage.bytes), 0).label("total_bytes"),
            )
            .join(DailyUsage, Tool.id == DailyUsage.tool_id, isouter=True)
            .where((DailyUsage.date >= start_date) | (DailyUsage.date.is_(None)))
            .group_by(Tool.id, Tool.name, Tool.slug)
            .order_by(func.coalesce(func.sum(DailyUsage.uses), 0).desc())
        )

        rows = session.execute(stmt).all()
        summary = []
        for row in rows:
            uses = int(row.total_uses)
            errors = int(row.total_errors)
            total_bytes = int(row.total_bytes)
            error_rate = round((errors / uses * 100), 2) if uses > 0 else 0.0

            summary.append({
                "tool_id": str(row.id),
                "name": row.name,
                "slug": row.slug,
                "total_uses": uses,
                "total_errors": errors,
                "error_rate_pct": error_rate,
                "total_bytes": total_bytes,
                "total_mb": round(total_bytes / (1024 * 1024), 2),
            })
        return summary

    @staticmethod
    def reset_buffer() -> None:
        """Clear the in-memory buffer (useful in tests)."""
        with _lock:
            _usage_buffer.clear()
