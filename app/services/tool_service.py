"""Tool service for querying tools, managing active status, and enforcing the backend kill switch."""


from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import ToolDisabledError, ToolNestError
from app.models.tool import Tool

# In-memory kill switch cache for instant backend lookups without querying DB on every sub-millisecond request:
# { slug: is_active }
_tool_active_cache: dict[str, bool] = {}


class ToolNotFoundError(ToolNestError):
    def __init__(self, message: str = "The requested tool was not found") -> None:
        super().__init__(
            code="NOT_FOUND",
            message=message,
            status_code=404,
        )


class ToolService:
    """Provides methods for tool lookup and backend kill-switch control."""

    @staticmethod
    def get_tool_by_slug(slug: str, session: Session) -> Tool | None:
        """Fetch a tool by its unique URL slug."""
        clean_slug = slug.strip().lower()
        tool = session.scalar(select(Tool).where(Tool.slug == clean_slug))
        if tool:
            _tool_active_cache[clean_slug] = tool.is_active
        return tool

    @staticmethod
    def get_all_tools(session: Session, active_only: bool = False) -> list[Tool]:
        """Fetch all tools ordered by name."""
        stmt = select(Tool).order_by(Tool.name)
        if active_only:
            stmt = stmt.where(Tool.is_active.is_(True))
        tools = list(session.scalars(stmt).all())
        for tool in tools:
            _tool_active_cache[tool.slug] = tool.is_active
        return tools

    @classmethod
    def is_tool_active(cls, slug: str, session: Session) -> bool:
        """Check whether a tool is active, using cache or falling back to database query."""
        clean_slug = slug.strip().lower()
        if clean_slug in _tool_active_cache:
            return _tool_active_cache[clean_slug]

        tool = cls.get_tool_by_slug(clean_slug, session)
        if tool is None:
            return False
        return tool.is_active

    @classmethod
    def set_tool_active(cls, slug: str, is_active: bool, session: Session) -> bool:
        """
        Kill-switch toggle: Enable or disable a tool instantly without rebuilding static site.
        Returns True if tool exists and was updated, False otherwise.
        """
        clean_slug = slug.strip().lower()
        tool = session.scalar(select(Tool).where(Tool.slug == clean_slug))
        if not tool:
            return False

        tool.is_active = is_active
        session.commit()
        session.refresh(tool)

        # Update cache immediately
        _tool_active_cache[clean_slug] = is_active
        return True

    @classmethod
    def ensure_tool_accessible(cls, slug: str, session: Session) -> Tool:
        """
        Validate that the tool exists and is active.
        Raises ToolNotFoundError if not found, or ToolDisabledError if killed/disabled.
        """
        clean_slug = slug.strip().lower()
        tool = cls.get_tool_by_slug(clean_slug, session)
        if not tool:
            raise ToolNotFoundError(f"Tool '{clean_slug}' not found.")
        if not tool.is_active:
            raise ToolDisabledError(
                f"The tool '{tool.name}' is temporarily disabled for maintenance. Please check back soon."
            )
        return tool

    @staticmethod
    def clear_cache() -> None:
        """Reset the in-memory active cache."""
        _tool_active_cache.clear()
