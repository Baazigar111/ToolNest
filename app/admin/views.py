"""SQLAdmin Model Views for ToolNest Administration."""

from typing import Any

from sqladmin import ModelView

from app.models.admin_user import AdminUser
from app.models.blog_post import BlogPost
from app.models.category import Category
from app.models.daily_usage import DailyUsage
from app.models.faq import FAQ
from app.models.publish_log import PublishLog
from app.models.site_setting import SiteSetting
from app.models.tool import Tool
from app.services.settings_service import SettingsService
from app.services.tool_service import ToolService


class AdminUserAdmin(ModelView, model=AdminUser):
    """Admin User Management."""

    name = "Admin User"
    name_plural = "Admin Users"
    icon = "fa-solid fa-user-shield"

    column_list = [
        AdminUser.email,
        AdminUser.is_active,
        AdminUser.created_at,
        AdminUser.updated_at,
    ]
    column_searchable_list = [AdminUser.email]
    column_sortable_list = [AdminUser.email, AdminUser.created_at, AdminUser.is_active]
    form_columns = [AdminUser.email, AdminUser.is_active]


class CategoryAdmin(ModelView, model=Category):
    """Tool Category Management."""

    name = "Category"
    name_plural = "Categories"
    icon = "fa-solid fa-folder-tree"

    column_list = [
        Category.sort_order,
        Category.name,
        Category.slug,
        Category.is_active,
        Category.created_at,
    ]
    column_searchable_list = [Category.name, Category.slug]
    column_sortable_list = [Category.sort_order, Category.name, Category.is_active]
    form_columns = [
        Category.name,
        Category.slug,
        Category.description,
        Category.sort_order,
        Category.is_active,
    ]


class ToolAdmin(ModelView, model=Tool):
    """Tool Configuration and Kill Switch Management."""

    name = "Tool"
    name_plural = "Tools"
    icon = "fa-solid fa-toolbox"

    column_list = [
        Tool.name,
        Tool.slug,
        Tool.tool_type,
        Tool.endpoint,
        Tool.category,
        Tool.is_active,
        Tool.updated_at,
    ]
    column_searchable_list = [Tool.name, Tool.slug, Tool.description]
    column_sortable_list = [Tool.name, Tool.slug, Tool.tool_type, Tool.is_active]

    form_columns = [
        Tool.name,
        Tool.slug,
        Tool.category,
        Tool.tool_type,
        Tool.endpoint,
        Tool.is_active,
        Tool.description,
        Tool.intro_text,
        Tool.how_to_steps,
        Tool.long_description,
        Tool.seo_title,
        Tool.meta_description,
        Tool.canonical_path,
    ]

    async def after_model_change(self, data: dict, is_created: bool, request: Any) -> None:
        """Invalidate in-memory tool cache when a tool is modified or killed."""
        ToolService.clear_cache()


class FAQAdmin(ModelView, model=FAQ):
    """Tool FAQ Management."""

    name = "FAQ"
    name_plural = "FAQs"
    icon = "fa-solid fa-circle-question"

    column_list = [
        FAQ.tool,
        FAQ.sort_order,
        FAQ.question,
        FAQ.is_active,
    ]
    column_searchable_list = [FAQ.question, FAQ.answer]
    column_sortable_list = [FAQ.sort_order, FAQ.is_active]
    form_columns = [
        FAQ.tool,
        FAQ.question,
        FAQ.answer,
        FAQ.sort_order,
        FAQ.is_active,
    ]


class BlogPostAdmin(ModelView, model=BlogPost):
    """Blog & SEO Guide Articles Management."""

    name = "Guide Article"
    name_plural = "Guide Articles"
    icon = "fa-solid fa-newspaper"

    column_list = [
        BlogPost.title,
        BlogPost.slug,
        BlogPost.status,
        BlogPost.published_at,
        BlogPost.created_at,
    ]
    column_searchable_list = [BlogPost.title, BlogPost.slug, BlogPost.description]
    column_sortable_list = [BlogPost.title, BlogPost.status, BlogPost.published_at]
    form_columns = [
        BlogPost.title,
        BlogPost.slug,
        BlogPost.status,
        BlogPost.description,
        BlogPost.body,
        BlogPost.seo_title,
        BlogPost.meta_description,
        BlogPost.published_at,
    ]


class SiteSettingAdmin(ModelView, model=SiteSetting):
    """Central Site Configuration, Limits, GST Rates, and Switches."""

    name = "Site Setting"
    name_plural = "Site Settings"
    icon = "fa-solid fa-sliders"

    column_list = [
        SiteSetting.key,
        SiteSetting.value,
        SiteSetting.description,
        SiteSetting.updated_at,
    ]
    column_searchable_list = [SiteSetting.key, SiteSetting.description]
    column_sortable_list = [SiteSetting.key, SiteSetting.updated_at]
    form_columns = [
        SiteSetting.key,
        SiteSetting.value,
        SiteSetting.description,
    ]

    async def after_model_change(self, data: dict, is_created: bool, request: Any) -> None:
        """Invalidate 5-minute settings cache immediately upon configuration change."""
        SettingsService.invalidate_cache()


class DailyUsageAdmin(ModelView, model=DailyUsage):
    """Aggregated Daily Usage Metrics (Read Only)."""

    name = "Daily Usage Counter"
    name_plural = "Daily Usage Analytics"
    icon = "fa-solid fa-chart-line"

    can_create = False
    can_delete = False
    can_edit = False

    column_list = [
        DailyUsage.date,
        DailyUsage.tool,
        DailyUsage.uses,
        DailyUsage.errors,
        DailyUsage.bytes,
    ]
    column_sortable_list = [
        DailyUsage.date,
        DailyUsage.uses,
        DailyUsage.errors,
        DailyUsage.bytes,
    ]


class PublishLogAdmin(ModelView, model=PublishLog):
    """Static Site Publishing Logs (Read Only)."""

    name = "Publish Log"
    name_plural = "Publish History"
    icon = "fa-solid fa-cloud-arrow-up"

    can_create = False
    can_delete = False
    can_edit = False

    column_list = [
        PublishLog.created_at,
        PublishLog.status,
        PublishLog.admin_user,
        PublishLog.changed_files,
        PublishLog.error_text,
    ]
    column_sortable_list = [PublishLog.created_at, PublishLog.status]
