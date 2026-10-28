# ToolNest

ToolNest is a free online tools website providing everyday PDF tools, image utilities, QR code generation, text utilities, and financial calculators.

## Architecture

- **Public Frontend**: High-performance static HTML pages served on Cloudflare Pages (`.pages.dev` or custom domain).
- **Backend & Administration**: FastAPI application running on Render's web service tier with SQLAdmin.
- **Database**: Serverless PostgreSQL hosted on Neon's free tier.
- **Dependency Management**: Astral `uv` for reproducible environments and locking.

---

## Access Points & URLs

| Portal / Service | Local Development | Production / Live |
| :--- | :--- | :--- |
| **Public Website** | Open `dist/index.html` or `http://localhost:3000` | `https://toolnest-h75.pages.dev` (or custom domain) |
| **Admin Dashboard** | `http://localhost:8000/admin` | `https://toolnest-4w95.onrender.com/admin` |
| **Interactive API Docs** | `http://localhost:8000/docs` | `https://toolnest-4w95.onrender.com/docs` |
| **API Health Check** | `http://localhost:8000/health` | `https://toolnest-4w95.onrender.com/health` |
| **Publish Endpoint** | `POST http://localhost:8000/api/publish` | `POST https://toolnest-4w95.onrender.com/api/publish` |

---

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
- `FRONTEND_ORIGIN`: Public domain/origin for CORS (e.g. `https://toolnest-h75.pages.dev`).
- `GITHUB_TOKEN`: GitHub Personal Access Token (for the site publisher).
- `GITHUB_REPOSITORY`: Target repository (e.g. `username/toolnest-site`).

---

## Database Migrations & Seeding

### 1. Apply Database Migrations
Apply schema migrations using Alembic:

```bash
uv run alembic upgrade head
```

Generate SQL script offline without connecting to PostgreSQL:

```bash
uv run alembic upgrade head --sql
```

### 2. Seed 15 Core Tools and Default Settings
Populates categories, tool definitions, SEO metadata, and site switches:

```bash
uv run python scripts/seed_tools.py
```

---

## Administration & Daily Operations

### 1. Create or Reset Admin User
Create an administrator account with secure Argon2 hashing:

```bash
uv run python scripts/create_admin.py --email admin@example.com --password <your_password>
```

### 2. Accessing the Admin Panel
1. Start the API server:
   ```bash
   uv run uvicorn app.main:app --reload --port 8000
   ```
2. Navigate in your browser to:
   **`http://localhost:8000/admin`**
3. Log in with your admin credentials.

### 3. What You Can Manage in the Admin Panel
- **Tool Kill Switch (`/admin/tool`)**: Toggle `is_active` to instantly disable a tool with a graceful `503 Unavailable` message.
- **Usage Analytics (`/admin/daily-usage-counter`)**: View real-time daily counts for uses, error rates, and total bytes processed per tool without cookies.
- **Content & Guides (`/admin/guide-article`)**: Draft and publish SEO guides and tutorials.
- **FAQs (`/admin/faq`)**: Add and manage tool-specific FAQs that render visible dropdowns and Google FAQ Schema.
- **Site Settings (`/admin/site-setting`)**:
  - `ads_enabled`: Toggle AdSense banner slots globally.
  - `gst_rates`: Update Indian GST tax slabs (0%, 5%, 18%, 40%).

---

## Static Site Building & Publishing

### Build Static Pages Locally
Generate all static HTML pages, assets, redirects, and sitemaps into the `dist/` directory:

```bash
uv run python site_builder/build.py
```

Preview the generated static site locally:

```bash
# Using Python's built-in HTTP server
uv run python -m http.server 3000 --directory dist
```

### One-Click Static Publishing
When changes are made in the admin panel (new blog post, tool description tweak, etc.):
1. Make an authenticated `POST` request to `/api/publish` (or trigger it from the admin interface).
2. The publisher validates all pages with `SiteValidator` (ensuring single H1, valid metadata, and zero leaked secrets).
3. Changes are committed to GitHub, triggering an automatic Cloudflare Pages deployment worldwide.

---

## Running Tests & Code Quality

```bash
# Run test suite
uv run pytest -v

# Run code quality and lint checks
uv run ruff check .
```
