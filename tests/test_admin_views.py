"""Tests for SQLAdmin views, routing, and access control."""

from fastapi.testclient import TestClient
from sqlalchemy import select
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


def test_admin_user_deletion(admin_client: TestClient, db_session: Session):
    """Verify deleting an admin user via SQLAdmin delete endpoint succeeds."""
    superadmin = AdminUser(
        email="superadmin2@toolnest.example",
        password_hash=hash_password("SuperSecret123!"),
        is_active=True,
    )
    target_user = AdminUser(
        email="tobedeleted@toolnest.example",
        password_hash=hash_password("TargetSecret123!"),
        is_active=True,
    )
    db_session.add_all([superadmin, target_user])
    db_session.commit()

    # Login as superadmin
    admin_client.post(
        "/admin/login",
        data={"username": "superadmin2@toolnest.example", "password": "SuperSecret123!"},
        follow_redirects=True,
    )

    # Delete target user via SQLAdmin delete endpoint
    del_resp = admin_client.delete(f"/admin/admin-user/delete?pks={target_user.id}")
    assert del_resp.status_code == 200

    # Verify target user was deleted from the database
    deleted = db_session.scalar(select(AdminUser).where(AdminUser.id == target_user.id))
    assert deleted is None


def test_admin_self_deletion_prevented(admin_client: TestClient, db_session: Session):
    """Verify that an admin cannot delete their own authenticated account."""
    self_admin = AdminUser(
        email="selfadmin@toolnest.example",
        password_hash=hash_password("SuperSecret123!"),
        is_active=True,
    )
    db_session.add(self_admin)
    db_session.commit()

    admin_client.post(
        "/admin/login",
        data={"username": "selfadmin@toolnest.example", "password": "SuperSecret123!"},
        follow_redirects=True,
    )

    # Attempt to delete own account
    del_resp = admin_client.delete(f"/admin/admin-user/delete?pks={self_admin.id}")
    assert "error" in del_resp.text.lower() or del_resp.status_code != 200

    # Account remains in database
    persisted = db_session.scalar(select(AdminUser).where(AdminUser.id == self_admin.id))
    assert persisted is not None
