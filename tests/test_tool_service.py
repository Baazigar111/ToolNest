"""Tests for ToolService lookup and backend kill-switch control."""

import pytest
from sqlalchemy.orm import Session

from app.errors import ToolDisabledError
from app.models.tool import Tool
from app.services.tool_service import ToolNotFoundError, ToolService


def test_tool_service_kill_switch(db_session: Session):
    """Verify that toggling tool active flag enforces instant kill-switch."""
    ToolService.clear_cache()
    tool = Tool(
        name="PDF to Image",
        slug="pdf-to-image",
        tool_type="pdf",
        endpoint="/api/pdf/to-image",
        is_active=True,
    )
    db_session.add(tool)
    db_session.commit()

    # Tool is initially accessible
    accessible = ToolService.ensure_tool_accessible("pdf-to-image", session=db_session)
    assert accessible.slug == "pdf-to-image"
    assert ToolService.is_tool_active("pdf-to-image", session=db_session) is True

    # Activate kill switch
    updated = ToolService.set_tool_active("pdf-to-image", is_active=False, session=db_session)
    assert updated is True
    assert ToolService.is_tool_active("pdf-to-image", session=db_session) is False

    # Immediate access attempt must raise ToolDisabledError (503)
    with pytest.raises(ToolDisabledError, match="temporarily disabled"):
        ToolService.ensure_tool_accessible("pdf-to-image", session=db_session)

    # Reactivate tool
    ToolService.set_tool_active("pdf-to-image", is_active=True, session=db_session)
    reactivated = ToolService.ensure_tool_accessible("pdf-to-image", session=db_session)
    assert reactivated.is_active is True


def test_tool_service_not_found(db_session: Session):
    """Verify non-existent tool raises ToolNotFoundError."""
    with pytest.raises(ToolNotFoundError):
        ToolService.ensure_tool_accessible("non-existent-tool", session=db_session)
