#!/usr/bin/env bash
set -euo pipefail

: "${POSTGRES_USER:?POSTGRES_USER is required}"
: "${POSTGRES_DB:?POSTGRES_DB is required}"
: "${SIGEM_APP_PASSWORD:?SIGEM_APP_PASSWORD is required}"

psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v app_password="$SIGEM_APP_PASSWORD" -v db_name="$POSTGRES_DB" <<'SQL'
SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'sigem_app') AS role_exists \gset
\if :role_exists
ALTER ROLE sigem_app WITH LOGIN PASSWORD :'app_password';
\else
CREATE ROLE sigem_app LOGIN PASSWORD :'app_password';
\endif
ALTER ROLE sigem_app SET search_path = public;
GRANT USAGE, CREATE ON SCHEMA public TO sigem_app;
GRANT ALL PRIVILEGES ON DATABASE :"db_name" TO sigem_app;
ALTER DEFAULT PRIVILEGES FOR ROLE sigem IN SCHEMA public GRANT ALL ON TABLES TO sigem_app;
ALTER DEFAULT PRIVILEGES FOR ROLE sigem IN SCHEMA public GRANT ALL ON SEQUENCES TO sigem_app;
ALTER DEFAULT PRIVILEGES FOR ROLE sigem IN SCHEMA public GRANT ALL ON FUNCTIONS TO sigem_app;
SQL

psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" <<'SQL'
DO $$
DECLARE
    obj RECORD;
BEGIN
    FOR obj IN SELECT tablename FROM pg_tables WHERE schemaname = 'public' LOOP
        EXECUTE format('GRANT ALL ON TABLE public.%I TO sigem_app', obj.tablename);
    END LOOP;
    FOR obj IN SELECT sequencename FROM pg_sequences WHERE schemaname = 'public' LOOP
        EXECUTE format('GRANT ALL ON SEQUENCE public.%I TO sigem_app', obj.sequencename);
    END LOOP;
END
$$;
SQL
