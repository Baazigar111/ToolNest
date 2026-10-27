"""Tests for UsageService in-memory buffering and batch flushing."""

from datetime import date

from sqlalchemy.orm import Session

from app.models.tool import Tool
from app.services.usage_service import UsageService


def test_usage_buffering_and_batch_flush(db_session: Session):
    """Verify in-memory buffer aggregates operations and flushes batch to DB."""
    UsageService.reset_buffer()

    tool = Tool(
        name="Merge PDF",
        slug="merge-pdf",
        tool_type="pdf",
        endpoint="/api/pdf/merge",
        is_active=True,
    )
    db_session.add(tool)
    db_session.commit()

    today = date(2026, 10, 27)

    # Record 3 successful operations and 1 error in memory
    UsageService.record_usage(tool.id, is_error=False, bytes_count=1024, usage_date=today)
    UsageService.record_usage(tool.id, is_error=False, bytes_count=2048, usage_date=today)
    UsageService.record_usage(tool.id, is_error=True, bytes_count=512, usage_date=today)

    snapshot = UsageService.get_buffered_totals()
    assert (today, tool.id) in snapshot
    assert snapshot[(today, tool.id)]["uses"] == 3
    assert snapshot[(today, tool.id)]["errors"] == 1
    assert snapshot[(today, tool.id)]["bytes"] == 3584

    # Flush buffer to PostgreSQL
    updated = UsageService.flush_counters(session=db_session)
    assert updated == 1

    # Buffer should now be empty
    assert len(UsageService.get_buffered_totals()) == 0

    # Verify analytics summary reflects the flushed data
    summary = UsageService.get_analytics_summary(session=db_session, days=7)
    assert len(summary) >= 1
    tool_stat = next(s for s in summary if s["slug"] == "merge-pdf")
    assert tool_stat["total_uses"] == 3
    assert tool_stat["total_errors"] == 1
    assert tool_stat["total_bytes"] == 3584
    assert tool_stat["error_rate_pct"] == 33.33
