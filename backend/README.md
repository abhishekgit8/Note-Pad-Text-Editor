# Backend notes

This backend uses FastAPI + SQLAlchemy.

Migration instructions (simple SQL):
- Run the SQL in `migrations/001_add_timestamps.sql` against your database (psql or supabase SQL editor).

Recommended (production) steps:
- Use Alembic for managed migrations (scaffold is included in `backend/alembic`).
  - Create a revision after model changes: `cd backend && alembic revision --autogenerate -m "describe change"`
  - Apply migrations: `cd backend && alembic upgrade head` (ensure `DATABASE_URL` is set in env)
  - To run automatically in Docker/local compose, set `MIGRATE_ON_START=true` in your compose env or service settings; the image will run `python run_migrations.py` before starting the app.
- Add application logging and structured error handling.
- Validate environment variables at startup and fail fast if missing.
- Use gunicorn/uvicorn with multiple workers for production, and configure a message broker (Redis) for websockets if scaling across instances.
- Configure CORS properly for production origins.

Running tests:
- Install dev requirements (pytest)
- Run `pytest backend/tests` from the repository root
