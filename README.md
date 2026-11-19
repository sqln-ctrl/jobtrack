# JobTrack

Track job applications across platforms; Gmail replies update the right application automatically.
React + Tailwind frontend, FastAPI + SQLAlchemy backend, PostgreSQL. **Phases 1 to 3 are implemented.**

## Run it

```bash
docker compose up -d                      # PostgreSQL

cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                      # fill in keys (see comments, and docs/google-setup.md)
alembic upgrade head
uvicorn app.main:app --reload             # http://localhost:8000/docs

cd ../frontend
npm install && npm run dev                # http://localhost:5173 (proxies /api to :8000)
```

Tests: `cd backend && pytest` (uses in-memory SQLite, no Google credentials needed).

## Deploy to Vercel

Deploy JobTrack as **two Vercel projects** backed by a managed PostgreSQL database:

| Project | Root directory | Purpose |
| --- | --- | --- |
| Frontend | `frontend` | Vite single-page app and same-origin API proxy |
| Backend | `backend` | FastAPI API |

The production frontend currently uses `https://jobtrack-linkedin.vercel.app` and the API uses `https://jobtrack-clwm.vercel.app`.

### 1. Create the production database

Create a managed PostgreSQL database (for example, Neon or Supabase). Docker Compose is for local development only. Use the provider's pooled connection string, changing its scheme to `postgresql+psycopg://` when necessary.

Run the migrations once with the production environment variables available locally or in CI:

```bash
cd backend
alembic upgrade head
```

Do not run Alembic automatically for every Vercel function invocation.

### 2. Deploy the backend

Import this repository into Vercel as a project with **Root Directory** set to `backend`. Vercel detects the FastAPI application at `app/main.py` and installs dependencies from `requirements.txt`.

Set these environment variables for the backend project's Production environment:

| Variable | Value |
| --- | --- |
| `APP_ENV` | `production` |
| `DATABASE_URL` | Production PostgreSQL URL, using `postgresql+psycopg://...` |
| `SECRET_KEY` | Long random secret |
| `TOKEN_ENCRYPTION_KEY` | Fernet key used to encrypt Gmail tokens |
| `GOOGLE_CLIENT_ID` | Google OAuth web-client ID |
| `GOOGLE_CLIENT_SECRET` | Google OAuth web-client secret |
| `BACKEND_URL` | `https://jobtrack-linkedin.vercel.app` |
| `FRONTEND_URL` | `https://jobtrack-linkedin.vercel.app` |
| `COOKIE_SECURE` | `true` |

`BACKEND_URL` deliberately points at the **frontend** URL. OAuth callbacks go through the frontend's `/api` proxy so the state and session cookies stay on one browser origin. Do not use the backend's `.vercel.app` URL for this setting, and do not include a trailing slash.

After deployment, confirm the API is healthy:

```text
https://jobtrack-clwm.vercel.app/health
```

### 3. Deploy the frontend

Import the same repository as a second Vercel project with **Root Directory** set to `frontend`. Vercel should use the Vite build command `npm run build` and output directory `dist`.

[`frontend/vercel.json`](frontend/vercel.json) proxies every `/api/*` request to the backend before falling back to `index.html` for React Router. This preserves the existing relative API URLs and HTTP-only cookies:

```json
{
  "source": "/api/:path*",
  "destination": "https://jobtrack-clwm.vercel.app/api/:path*"
}
```

If the backend domain changes, update the destination in `frontend/vercel.json` and redeploy the frontend.

### 4. Configure Google OAuth

In Google Cloud Console, edit the OAuth **Web application** whose client ID is configured in the backend. Add these values under **Authorized redirect URIs**:

```text
https://jobtrack-linkedin.vercel.app/api/v1/auth/google/callback
https://jobtrack-linkedin.vercel.app/api/v1/gmail/callback
```

They must exactly match the URLs above: use the frontend domain, HTTPS, and no trailing slash. If you move to a custom frontend domain, update both backend URL environment variables and these Google redirect URIs, then redeploy the backend.

For a private beta, add users as Google OAuth test users. A public launch using Gmail's restricted `gmail.readonly` scope requires Google's OAuth verification and potentially a security assessment; see [the Google setup guide](docs/google-setup.md).

### Deployment checks

- `https://jobtrack-clwm.vercel.app/health` responds with `200`.
- A logged-out request to `https://jobtrack-linkedin.vercel.app/api/v1/auth/me` responds with `401`, not `404`.
- Google sign-in returns to the frontend without `redirect_uri_mismatch`.

## What is built

**Phase 1, foundation:** Google sign-in, JWT in an HTTP-only cookie, CSRF double-submit protection, protected routes, Alembic migrations, user table.
**Phase 2, manual tracker:** application CRUD, platforms (7 defaults plus custom), 9 statuses with history, search, filters and sorting, dashboard stats, details page with timeline, interviews.
**Phase 3, Gmail:** separate read-only OAuth consent (`gmail.readonly`), Fernet-encrypted tokens, 90-day initial sync, incremental sync via the History API with fallback on expired history IDs, rule-based classifier behind an interface, company/title extraction, confidence-scored matching, automatic status updates recorded in history, manual match/ignore for ambiguous emails, Sync Now, disconnect with revocation. LinkedIn job-alert emails are imported into their own Job alerts page, with an Apply link for every detected listing.

## Behaviour worth knowing

- **Gmail matching is automatic.** Each job-related email is linked to the strongest matching application; equally likely matches use the most recently submitted application. Messages with no candidate remain visible as *Unmatched* and are retried after later syncs.
- **Emails only move statuses forward.** They never downgrade progress or overwrite Rejected, Offer or Withdrawn.
- **Saving a job never marks it Applied.** A confirmation email does (reliable evidence).
- **Unrelated mail is never stored.** Only job-related emails are saved, with a 1,500-character excerpt.
- Gmail sync is manual (Sync Now) plus once after connecting. Scheduled polling is Phase 4.
- Job alerts are detected from recent LinkedIn job-alert email messages during each Gmail sync; they are kept separate from application-reply activity.

## Layout

`backend/app/{api/v1,core,models,schemas,services/{auth,gmail,email_classifier,applications},db}` and `frontend/src/{pages,components,hooks,services,context,layouts,utils}`.
