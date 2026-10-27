"""Tests for SQLAdmin views, routing, and access control."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.admin_user import AdminUser
from app.models.tool import Tool
from app.security import hash_password


def test_admin_redirects_unauthenticated(admin_client: TestClient):
    """Verify accessing /admin/ when unauthenticated redirects to /admin/login."""
    response = admin_client.get("/admin/", follow_redirects=False)
    assert response.status_code in (302, 303, 307)
    assert "/admin/login" in response.headers.get("location", "")


def test_admin_login_page_renders(admin_client: TestClient):
    """Verify /admin/login renders successfully."""
    response = admin_client.get("/admin/login")
    assert response.status_code == 200
    assert "login" in response.text.lower()


def test_admin_authenticated_access(admin_client: TestClient, db_session: Session):
    """Verify that logging in grants access to protected admin model views."""
    # Seed an admin user and tool in the test database
    user = AdminUser(
        email="superadmin@toolnest.example",
        password_hash=hash_password("SuperSecret123!"),
        is_active=True,
    )
    tool = Tool(
        name="Compress Image",
        slug="compress-image",
        tool_type="image",
        endpoint="/api/image/compress",
        is_active=True,
    )
    db_session.add_all([user, tool])
    db_session.commit()

    # Post login form to SQLAdmin
    login_resp = admin_client.post(
        "/admin/login",
        data={"username": "superadmin@toolnest.example", "password": "SuperSecret123!"},
        follow_redirects=True,
    )
    assert login_resp.status_code == 200

    # Access tool admin list view
    tools_list = admin_client.get("/admin/tool/list")
    assert tools_list.status_code == 200
    assert "Compress Image" in tools_list.text

    # Access categories list view
    cat_list = admin_client.get("/admin/category/list")
    assert cat_list.status_code == 200

    # Access site settings list view
    settings_list = admin_client.get("/admin/site-setting/list")
    assert settings_list.status_code == 200
