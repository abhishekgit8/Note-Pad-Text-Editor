-- Migration: add created_at and updated_at columns to notes
ALTER TABLE notes
  ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
  ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL;

-- Optional: update existing rows to set timestamps (if you want to set to now)
UPDATE notes SET created_at = coalesce(created_at, now()), updated_at = coalesce(updated_at, now());

-- Note: For production, use Alembic to generate and run migrations.
