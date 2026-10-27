"""Publish router allowing administrators to trigger static site generation and GitHub deployment."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.admin_user import AdminUser
from app.services.publisher import PublisherService

router = APIRouter(prefix="/api/publish", tags=["Publishing"])


def get_current_admin(request: Request, session: Session = Depends(get_db)) -> AdminUser:
    """Validate authenticated admin session cookie."""
    token = request.session.get("token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to publish static site.",
        )
    try:
        user_uuid = uuid.UUID(str(token))
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session credentials.",
        ) from None

    user = session.get(AdminUser, user_uuid)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Active administrator privileges required.",
        )
    return user


@router.post(
    "",
    summary="Trigger Static Site Build & Publish",
    description="Generates HTML/CSS/JS, validates output, and commits changes to Cloudflare Pages GitHub repository.",
)
def trigger_publish(
    current_admin: AdminUser = Depends(get_current_admin),
    session: Session = Depends(get_db),
) -> dict[str, Any]:
    """Execute site generation and deployment workflow."""
    result = PublisherService.publish_site(session=session, admin_user_id=current_admin.id)
    if result.status == "failed":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error_text or "Publishing failed. Inspect publish_log for details.",
        )

    return {
        "status": "success",
        "message": result.message,
        "changed_files": result.changed_files,
    }
