"""Settings service with 5-minute in-memory caching and database synchronization."""

import time
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.site_setting import SiteSetting

# Cache storage: { key: (value, expire_timestamp) }
_settings_cache: dict[str, tuple[Any, float]] = {}
CACHE_TTL_SECONDS = 300.0  # 5 minutes, as required by PRD Section 3 & 7.3


class SettingsService:
    """Manages cached access and updates to dynamic site settings."""

    @staticmethod
    def get_setting(key: str, default: Any = None, session: Session | None = None) -> Any:
        """
        Retrieve setting value. Checks 5-minute cache first, then database,
        and finally falls back to the default or application config.
        """
        now = time.monotonic()
        if key in _settings_cache:
            val, expires_at = _settings_cache[key]
            if now < expires_at:
                return val

        # Try fetching from database if session is provided or available
        if session is not None:
            try:
                db_setting = session.scalar(select(SiteSetting).where(SiteSetting.key == key))
                if db_setting is not None:
                    _settings_cache[key] = (db_setting.value, now + CACHE_TTL_SECONDS)
                    return db_setting.value
            except Exception:
                # If database is temporarily sleeping or offline, fall through to default
                pass

        # Fallback to defaults defined in app.config
        cfg = get_settings()
        fallback_map: dict[str, Any] = {
            "daily_server_uses": cfg.daily_server_uses_per_visitor,
            "image_max_bytes": cfg.image_max_bytes,
            "pdf_max_bytes": cfg.pdf_max_bytes,
            "request_max_bytes": cfg.request_max_bytes,
            "max_files_per_request": cfg.max_files_per_request,
            "max_pdf_to_image_pages": cfg.max_pdf_to_image_pages,
            "max_processing_seconds": cfg.max_processing_seconds,
            "gst_rates": [0, 5, 18, 40],
            "ads_enabled": False,
            "api_base_url": cfg.api_base_url,
        }
        res = fallback_map.get(key, default)
        _settings_cache[key] = (res, now + CACHE_TTL_SECONDS)
        return res

    @staticmethod
    def set_setting(key: str, value: Any, session: Session, description: str | None = None) -> SiteSetting:
        """Create or update a setting in the database and immediately refresh/invalidate cache."""
        setting = session.scalar(select(SiteSetting).where(SiteSetting.key == key))
        if setting:
            setting.value = value
            if description:
                setting.description = description
        else:
            setting = SiteSetting(key=key, value=value, description=description)
            session.add(setting)

        session.commit()
        session.refresh(setting)

        # Update cache with new value and fresh TTL
        _settings_cache[key] = (value, time.monotonic() + CACHE_TTL_SECONDS)
        return setting

    @staticmethod
    def invalidate_cache(key: str | None = None) -> None:
        """Clear cache for a specific key, or all keys if key is None."""
        global _settings_cache
        if key:
            _settings_cache.pop(key, None)
        else:
            _settings_cache.clear()

    @classmethod
    def get_gst_rates(cls, session: Session | None = None) -> list[int | float]:
        """Get Indian GST slab rates from settings (default: [0, 5, 18, 40])."""
        rates = cls.get_setting("gst_rates", default=[0, 5, 18, 40], session=session)
        if isinstance(rates, list):
            return rates
        return [0, 5, 18, 40]

    @classmethod
    def get_ads_enabled(cls, session: Session | None = None) -> bool:
        """Get ads_enabled switch status (default: False)."""
        val = cls.get_setting("ads_enabled", default=False, session=session)
        return bool(val)

    @classmethod
    def get_daily_server_uses(cls, session: Session | None = None) -> int:
        """Get daily server uses limit per visitor (default: 20)."""
        val = cls.get_setting("daily_server_uses", default=20, session=session)
        return int(val)
