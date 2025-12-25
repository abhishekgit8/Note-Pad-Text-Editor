#!/usr/bin/env bash
set -e

if [ "${MIGRATE_ON_START}" = "true" ]; then
  echo "MIGRATE_ON_START is true: running migrations"
  python run_migrations.py
fi

exec "$@"
