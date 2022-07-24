#!/bin/bash
set -e

PGPASSWORD=postgres psql -v ON_ERROR_STOP=1 -h db -U postgres -d nm -f ./scripts/database/postgres/init.sql
