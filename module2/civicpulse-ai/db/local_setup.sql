-- Run this ONCE if you use your own (local) PostgreSQL instead of Docker.
--   psql -U postgres -f db/local_setup.sql
-- PostGIS must be installed first (see README, "Option B").

CREATE DATABASE civicpulse;
\connect civicpulse
CREATE EXTENSION IF NOT EXISTS postgis;
