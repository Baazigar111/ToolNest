"""Static site publishing service with validation, GitHub commit integration, and audit logging."""

import hashlib
import os
import tempfile
import uuid
from datetime import date, datetime
from pathlib import Path
from typing import Any, NamedTuple

import httpx
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.publish_log import PublishLog
from app.models.tool import Tool
from site_builder.build import SiteBuilder
from site_builder.validator import SiteValidator


class PublishResult(NamedTuple):
    status: str  # "success" or "failed"
    changed_files: list[str]
    message: str
    error_text: str | None = None


class PublisherService:
    """Manages site generation, pre-deployment validation, and GitHub API commits."""

    @staticmethod
    def get_todays_publish_count(session: Session) -> int:
        """Count how many successful publishes occurred today (to guard Cloudflare 500/month build limit)."""
        today = date.today()
        count = session.scalar(
            select(func.count(PublishLog.id)).where(
                func.date(PublishLog.created_at) == today,
                PublishLog.status == "success",
            )
        )
        return int(count or 0)

    @classmethod
    def publish_site(
        cls,
        session: Session,
        admin_user_id: uuid.UUID | None = None,
        github_client: httpx.Client | None = None,
    ) -> PublishResult:
        """
        Builds static site into a temp directory, validates output,
        commits only changed files via GitHub API, and logs the outcome in publish_log.
        """
        settings = get_settings()
        changed_files_list: list[str] = []

        # Check daily threshold (warn if over 10 publishes today)
        todays_publishes = cls.get_todays_publish_count(session)
        daily_warning = ""
        if todays_publishes >= 10:
            daily_warning = f" Notice: {todays_publishes} publishes already deployed today. Cloudflare free tier allows 500 builds/month."

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # 1. Generate Static Files
            try:
                builder = SiteBuilder(output_dir=temp_path, session=session)
                builder.build()
            except Exception as e:
                error_msg = f"Static site generation failed: {e}"
                cls._record_log(session, admin_user_id, status="failed", changed_files=[], error_text=error_msg)
                return PublishResult("failed", [], error_msg, error_msg)

            # 2. Validate Generated Files
            active_tool_slugs = list(session.scalars(select(Tool.slug).where(Tool.is_active.is_(True))).all())
            validator = SiteValidator(temp_path)
            validation = validator.validate(expected_tools=active_tool_slugs)

            if not validation.is_valid:
                error_msg = f"Site validation failed with {len(validation.errors)} errors: " + "; ".join(validation.errors)
                cls._record_log(session, admin_user_id, status="failed", changed_files=[], error_text=error_msg)
                return PublishResult("failed", [], error_msg, error_msg)

            # 3. Detect Changed Files and Deploy to GitHub
            token = settings.github_token
            repo = settings.github_repository

            # If no GitHub credentials configured (e.g. local dev/test environment), skip remote push safely
            if not token or not repo:
                msg = f"Site generation and validation passed successfully ({validation.total_files_checked} files verified). GitHub credentials not configured — skipping remote push.{daily_warning}"
                cls._record_log(
                    session,
                    admin_user_id,
                    status="success",
                    changed_files=["(local-validation-only)"],
                    error_text=None,
                )
                return PublishResult("success", ["(local-validation-only)"], msg)

            # Commit to GitHub generated-site repository
            try:
                changed_files_list = cls._commit_to_github(
                    temp_path=temp_path,
                    repo=repo,
                    token=token,
                    client=github_client,
                )
                status_msg = f"Successfully published {len(changed_files_list)} changed file(s) to GitHub {repo}.{daily_warning}"
                cls._record_log(session, admin_user_id, status="success", changed_files=changed_files_list)
                return PublishResult("success", changed_files_list, status_msg)
            except Exception as e:
                error_msg = f"GitHub publishing failed: {e}"
                cls._record_log(session, admin_user_id, status="failed", changed_files=[], error_text=error_msg)
                return PublishResult("failed", [], error_msg, error_msg)

    @staticmethod
    def _compute_git_sha(file_bytes: bytes) -> str:
        """Compute the Git blob SHA1 hash identical to `git hash-object`."""
        header = f"blob {len(file_bytes)}\0".encode()
        return hashlib.sha1(header + file_bytes).hexdigest()

    @classmethod
    def _commit_to_github(
        cls,
        temp_path: Path,
        repo: str,
        token: str,
        client: httpx.Client | None = None,
    ) -> list[str]:
        """
        Commits only modified or new files to GitHub using the Git Data Trees API.
        Leaves untouched files unmodified to keep Cloudflare build triggers clean.
        """
        http = client or httpx.Client(
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "ToolNest-Publisher",
            },
            timeout=30.0,
        )

        owner_repo = repo.strip().strip("/")
        base_api = f"https://api.github.com/repos/{owner_repo}"

        # 1. Get latest commit SHA on main branch
        ref_res = http.get(f"{base_api}/git/refs/heads/main")
        if ref_res.status_code == 404:
            raise RuntimeError(f"Branch 'main' not found on repository {repo}. Ensure repository is initialized.")
        ref_res.raise_for_status()
        latest_commit_sha = ref_res.json()["object"]["sha"]

        # 2. Get tree of current commit to compare SHAs
        commit_res = http.get(f"{base_api}/git/commits/{latest_commit_sha}")
        commit_res.raise_for_status()
        base_tree_sha = commit_res.json()["tree"]["sha"]

        tree_res = http.get(f"{base_api}/git/trees/{base_tree_sha}?recursive=1")
        tree_res.raise_for_status()
        existing_tree = {item["path"]: item["sha"] for item in tree_res.json().get("tree", []) if item["type"] == "blob"}

        # 3. Identify changed or added files
        new_tree_entries: list[dict[str, Any]] = []
        changed_paths: list[str] = []

        for root, _, files in os.walk(temp_path):
            for file_name in files:
                abs_path = Path(root) / file_name
                rel_path = abs_path.relative_to(temp_path).as_posix()
                content_bytes = abs_path.read_bytes()
                local_sha = cls._compute_git_sha(content_bytes)

                if rel_path not in existing_tree or existing_tree[rel_path] != local_sha:
                    # Upload blob
                    import base64
                    blob_res = http.post(
                        f"{base_api}/git/blobs",
                        json={
                            "content": base64.b64encode(content_bytes).decode("ascii"),
                            "encoding": "base64",
                        },
                    )
                    blob_res.raise_for_status()
                    blob_sha = blob_res.json()["sha"]

                    new_tree_entries.append({
                        "path": rel_path,
                        "mode": "100644",
                        "type": "blob",
                        "sha": blob_sha,
                    })
                    changed_paths.append(rel_path)

        if not new_tree_entries:
            return ["(no files changed)"]

        # 4. Create new tree based on base_tree_sha
        new_tree_res = http.post(
            f"{base_api}/git/trees",
            json={
                "base_tree": base_tree_sha,
                "tree": new_tree_entries,
            },
        )
        new_tree_res.raise_for_status()
        new_tree_sha = new_tree_res.json()["sha"]

        # 5. Create new commit
        commit_msg = f"Site publish: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [{len(changed_paths)} files updated]"
        new_commit_res = http.post(
            f"{base_api}/git/commits",
            json={
                "message": commit_msg,
                "tree": new_tree_sha,
                "parents": [latest_commit_sha],
            },
        )
        new_commit_res.raise_for_status()
        new_commit_sha = new_commit_res.json()["sha"]

        # 6. Update main ref
        update_ref_res = http.patch(
            f"{base_api}/git/refs/heads/main",
            json={"sha": new_commit_sha, "force": False},
        )
        update_ref_res.raise_for_status()

        return changed_paths

    @staticmethod
    def _record_log(
        session: Session,
        admin_user_id: uuid.UUID | None,
        status: str,
        changed_files: list[str],
        error_text: str | None = None,
    ) -> PublishLog:
        """Record an entry in the publish_log table."""
        log = PublishLog(
            admin_user_id=admin_user_id,
            status=status,
            changed_files=changed_files,
            error_text=error_text,
        )
        session.add(log)
        session.commit()
        return log
