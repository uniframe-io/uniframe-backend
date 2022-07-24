#!/bin/bash
set -e

PGPASSWORD=postgres psql -v ON_ERROR_STOP=1 -h localhost -U postgres -d test_nm <<-EOSQL
    SELECT * from users;
EOSQL
