"""Tests for SettingsService 5-minute cache and persistence."""

from sqlalchemy.orm import Session

from app.services.settings_service import SettingsService


def test_settings_service_fallback_defaults():
    """Verify fallback to config defaults when key is not in DB."""
    SettingsService.invalidate_cache()
    daily_uses = SettingsService.get_daily_server_uses()
    assert daily_uses == 20

    gst = SettingsService.get_gst_rates()
    assert gst == [0, 5, 18, 40]

    ads = SettingsService.get_ads_enabled()
    assert ads is False


def test_settings_service_db_persistence_and_cache_invalidation(db_session: Session):
    """Verify set_setting persists to database and refreshes the cache."""
    SettingsService.invalidate_cache()

    # Update GST rates in database
    new_rates = [0, 5, 12, 18, 28]
    SettingsService.set_setting("gst_rates", new_rates, session=db_session)

    # Cached value should immediately reflect the change
    cached_rates = SettingsService.get_gst_rates(session=db_session)
    assert cached_rates == new_rates

    # Check database direct read
    from sqlalchemy import select

    from app.models.site_setting import SiteSetting
    db_rec = db_session.scalar(select(SiteSetting).where(SiteSetting.key == "gst_rates"))
    assert db_rec.value == new_rates


def test_settings_service_ads_switch(db_session: Session):
    """Verify ads_enabled toggle via SettingsService."""
    SettingsService.invalidate_cache()
    assert SettingsService.get_ads_enabled(session=db_session) is False

    SettingsService.set_setting("ads_enabled", True, session=db_session)
    assert SettingsService.get_ads_enabled(session=db_session) is True
