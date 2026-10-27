"""Command-line script to bootstrap or reset an administrator account."""

import argparse
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from app.config import DatabaseConfigurationError
from app.db import get_session_factory
from app.models import AdminUser
from app.security import hash_password


def create_or_update_admin(email: str, password: str) -> None:
    """Create a new admin user or update password if email already exists."""
    email_clean = email.strip().lower()
    if not email_clean or "@" not in email_clean:
        print(f"Error: Invalid email address '{email}'.", file=sys.stderr)
        sys.exit(1)

    if len(password) < 8:
        print("Error: Password must be at least 8 characters long.", file=sys.stderr)
        sys.exit(1)

    try:
        session_factory = get_session_factory()
    except DatabaseConfigurationError as e:
        print(f"Configuration Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Database Connection Error: {e}", file=sys.stderr)
        sys.exit(1)

    with session_factory() as session:
        user = session.scalar(select(AdminUser).where(AdminUser.email == email_clean))
        hashed = hash_password(password)

        if user:
            user.password_hash = hashed
            user.is_active = True
            session.commit()
            print(f"Admin user '{email_clean}' password successfully updated.")
        else:
            new_user = AdminUser(
                email=email_clean,
                password_hash=hashed,
                is_active=True,
            )
            session.add(new_user)
            session.commit()
            print(f"Admin user '{email_clean}' created successfully.")


def main() -> None:
    parser = argparse.ArgumentParser(description="ToolNest Admin Account CLI")
    parser.add_argument("--email", required=True, help="Admin email address")
    parser.add_argument("--password", required=True, help="Admin plaintext password (min 8 characters)")
    args = parser.parse_args()

    create_or_update_admin(args.email, args.password)


if __name__ == "__main__":
    main()
