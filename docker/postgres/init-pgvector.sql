-- Legal Agent — first-boot initialization for local Postgres (pgvector image).
-- Runs via docker-entrypoint-initdb.d when the data volume is empty.
CREATE EXTENSION IF NOT EXISTS vector;
