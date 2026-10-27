# ToolNest

ToolNest is a free online tools website providing everyday PDF tools, image utilities, QR code generation, text utilities, and financial calculators.

## Architecture

- **Public Frontend**: High-performance static HTML pages served on Cloudflare Pages (`.pages.dev`).
- **Backend & Administration**: FastAPI application running on Render's free web service tier.
- **Database**: Serverless PostgreSQL hosted on Neon's free tier.
- **Dependency Management**: Astral `uv` for reproducible environments and locking.

## Getting Started

### Prerequisites

- Python 3.12+
- Astral `uv` (e.g., `pip install uv` or official standalone binary)

### Installation

Clone the repository and install dependencies using `uv`:

```bash
uv sync
```

### Environment Configuration

Copy `.env.example` to `.env` and set your configuration variables:

```bash
cp .env.example .env
```

Key environment variables:
- `DATABASE_URL`: Neon PostgreSQL connection string.
- `ADMIN_SECRET_KEY`: Cryptographic signing secret for admin sessions.
- `ENVIRONMENT`: `development` | `production` | `testing`.
- `FRONTEND_ORIGIN`: Public domain/origin for CORS.

### Running the API Server

```bash
uv run uvicorn app.main:app --reload --port 8000
```

- API Health Check: `http://localhost:8000/health`
- Interactive OpenAPI Docs: `http://localhost:8000/docs`

### Database Migrations

Apply database migrations using Alembic:

```bash
uv run alembic upgrade head
```

Generate SQL script offline without connecting to PostgreSQL:

```bash
uv run alembic upgrade head --sql
```

### Admin User Setup

Create or reset an administrator account:

```bash
uv run python scripts/create_admin.py --email admin@example.com --password <your_password>
```

### Seed 15 Core Tools and Settings

```bash
uv run python scripts/seed_tools.py
```

### Running Tests & Linting

```bash
# Run test suite
uv run pytest -v

# Run code quality and lint checks
uv run ruff check .
```
