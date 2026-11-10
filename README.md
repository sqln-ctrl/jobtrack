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

## What is built

**Phase 1, foundation:** Google sign-in, JWT in an HTTP-only cookie, CSRF double-submit protection, protected routes, Alembic migrations, user table.
**Phase 2, manual tracker:** application CRUD, platforms (7 defaults plus custom), 9 statuses with history, search, filters and sorting, dashboard stats, details page with timeline, interviews.
**Phase 3, Gmail:** separate read-only OAuth consent (`gmail.readonly`), Fernet-encrypted tokens, 90-day initial sync, incremental sync via the History API with fallback on expired history IDs, rule-based classifier behind an interface, company/title extraction, confidence-scored matching, automatic status updates recorded in history, manual match/ignore for ambiguous emails, Sync Now, disconnect with revocation.

## Behaviour worth knowing

- **Ambiguous emails are never auto-applied.** Two candidate applications, or only a weak company mention, sends the email to *Needs review*.
- **Emails only move statuses forward.** They never downgrade progress or overwrite Rejected, Offer or Withdrawn.
- **Saving a job never marks it Applied.** A confirmation email does (reliable evidence).
- **Unrelated mail is never stored.** Only job-related emails are saved, with a 1,500-character excerpt.
- Gmail sync is manual (Sync Now) plus once after connecting. Scheduled polling is Phase 4.

## Layout

`backend/app/{api/v1,core,models,schemas,services/{auth,gmail,email_classifier,applications},db}` and `frontend/src/{pages,components,hooks,services,context,layouts,utils}`.
