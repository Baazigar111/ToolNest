"""Tests for PublisherService and /api/publish router."""

import httpx
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.admin_user import AdminUser
from app.models.category import Category
from app.models.publish_log import PublishLog
from app.models.tool import Tool
from app.security import hash_password
from app.services.publisher import PublisherService


def test_publisher_service_local_validation_only(db_session: Session):
    """Verify publisher completes generation and validation, logging success when no token is configured."""
    user = AdminUser(email="pubadmin@toolnest.example", password_hash=hash_password("Pass123!"))
    tool = Tool(name="Merge PDF", slug="merge-pdf", tool_type="pdf", is_active=True)
    db_session.add_all([user, tool])
    db_session.commit()

    result = PublisherService.publish_site(session=db_session, admin_user_id=user.id)
    assert result.status == "success"
    assert any("local-validation-only" in f for f in result.changed_files)

    # Check publish_log table
    from sqlalchemy import select
    log = db_session.scalar(select(PublishLog).where(PublishLog.admin_user_id == user.id))
    assert log is not None
    assert log.status == "success"


def test_publisher_service_mocked_github_api(db_session: Session, monkeypatch):
    """Verify publisher commits only changed files via GitHub Git Data Trees API."""
    monkeypatch.setenv("GITHUB_TOKEN", "mock_gh_token_12345")
    monkeypatch.setenv("GITHUB_REPOSITORY", "Baazigar111/toolnest-site")

    from app.config import get_settings
    get_settings.cache_clear()

    cat = Category(name="PDF Tools", slug="pdf", sort_order=1)
    db_session.add(cat)
    db_session.flush()

    tool = Tool(name="Merge PDF", slug="merge-pdf", category_id=cat.id, tool_type="pdf", is_active=True)
    user = AdminUser(email="gitadmin@toolnest.example", password_hash=hash_password("Pass123!"))
    db_session.add_all([tool, user])
    db_session.commit()

    # Mock GitHub API responses
    def mock_handler(request: httpx.Request):
        url = str(request.url)
        if "/git/refs/heads/main" in url and request.method == "GET":
            return httpx.Response(200, json={"object": {"sha": "commit_sha_1"}})
        if "/git/commits/commit_sha_1" in url and request.method == "GET":
            return httpx.Response(200, json={"tree": {"sha": "tree_sha_1"}})
        if "/git/trees/tree_sha_1" in url and request.method == "GET":
            # Existing tree with an older index.html
            return httpx.Response(200, json={"tree": [{"path": "index.html", "type": "blob", "sha": "old_hash"}]})
        if "/git/blobs" in url and request.method == "POST":
            return httpx.Response(201, json={"sha": "new_blob_sha"})
        if "/git/trees" in url and request.method == "POST":
            return httpx.Response(201, json={"sha": "new_tree_sha"})
        if "/git/commits" in url and request.method == "POST":
            return httpx.Response(201, json={"sha": "new_commit_sha"})
        if "/git/refs/heads/main" in url and request.method == "PATCH":
            return httpx.Response(200, json={"object": {"sha": "new_commit_sha"}})
        return httpx.Response(404)

    mock_client = httpx.Client(transport=httpx.MockTransport(mock_handler))

    res = PublisherService.publish_site(
        session=db_session,
        admin_user_id=user.id,
        github_client=mock_client,
    )
    assert res.status == "success"
    assert len(res.changed_files) > 0
    assert "index.html" in res.changed_files


def test_publish_api_endpoint_auth(admin_client: TestClient, db_session: Session):
    """Verify /api/publish rejects unauthenticated calls and executes when logged in."""
    # 1. Unauthenticated call is rejected (401)
    res_unauth = admin_client.post("/api/publish")
    assert res_unauth.status_code == 401

    # 2. Login as admin
    user = AdminUser(
        email="publisher@toolnest.example",
        password_hash=hash_password("SuperSecret123!"),
        is_active=True,
    )
    tool = Tool(name="Merge PDF", slug="merge-pdf", tool_type="pdf", is_active=True)
    db_session.add_all([user, tool])
    db_session.commit()

    admin_client.post(
        "/admin/login",
        data={"username": "publisher@toolnest.example", "password": "SuperSecret123!"},
        follow_redirects=True,
    )

    # 3. Authenticated call succeeds
    res_auth = admin_client.post("/api/publish")
    assert res_auth.status_code == 200
    data = res_auth.json()
    assert data["status"] == "success"
