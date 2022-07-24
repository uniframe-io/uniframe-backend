#!/bin/bash
set -e

PGPASSWORD=${POSTGRES_PASSWORD} psql -v ON_ERROR_STOP=1 -h ${POSTGRES_HOST} -U ${POSTGRES_USER} -d ${POSTGRES_DB} -f ${NAME_MATCHING_HOME}/scripts/database/postgres/init.sql
