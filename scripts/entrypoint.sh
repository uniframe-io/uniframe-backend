#!/usr/bin/env bash

# Global defaults and back-compat
: "${NAME_MATCHING_HOME:="/opt/uniframe-backend"}"
: "${NAME_MATCHING_INIT_SCRIPT:="${NAME_MATCHING_HOME}/scripts/init-database-deploy.sh"}"


# Install custom python package if requirements.txt is present
if [ -e "/requirements.txt" ]; then
    $(command -v pip) install --user -r /requirements.txt
fi

# We install uniframe-backend package in dockerfile, skip it here
# $(command -v pip) install -e .


if [ -z "${PRODUCT_PREFIX}" ]; then
    echo "Init error: PRODUCT_PREFIX is empty"
    exit 1
fi
if [ -z "${DEPLOY_ENV}" ]; then
    echo "Init error: DEPLOY_ENV is empty"
    exit 1
fi
if [ -z "${DOMAIN_NAME}" ]; then
    echo "Init error: DOMAIN_NAME is empty"
    exit 1
fi

# Init environment variables
SECRET_MANAGER_ID=${PRODUCT_PREFIX}-${DEPLOY_ENV}-api-db-secret
SECRET_OUTPUT=$(aws secretsmanager   get-secret-value --secret-id ${SECRET_MANAGER_ID} --region eu-west-1 --query SecretString --output text)
export POSTGRES_USER=$(echo ${SECRET_OUTPUT} | jq .username | tr -d '"')
export POSTGRES_PASSWORD=$(echo ${SECRET_OUTPUT} | jq .password | tr -d '"')

# Get oauth2 client id and secret

OAUTH_GITHUB_SECRET=$(aws secretsmanager get-secret-value --secret-id ${PRODUCT_PREFIX}-${DEPLOY_ENV}-oauth-github-client-secret --region eu-west-1 --query SecretString --output text)
export OAUTH2_GITHUB_CLIENT_ID=$(echo ${OAUTH_GITHUB_SECRET} | jq .OAUTH2_GITHUB_CLIENT_ID | tr -d '"')
export OAUTH2_GITHUB_CLIENT_SECRET=$(echo ${OAUTH_GITHUB_SECRET} | jq .OAUTH2_GITHUB_CLIENT_SECRET | tr -d '"')

# get db host and name from parameter store
export POSTGRES_HOST=$(aws ssm get-parameters --names ${PRODUCT_PREFIX}-${DEPLOY_ENV}-ssm-api-db-dns --query "Parameters[*].Value | [0]" | tr -d '"')
export POSTGRES_DB=$(aws ssm get-parameters --names ${PRODUCT_PREFIX}-${DEPLOY_ENV}-ssm-api-db-name --query "Parameters[*].Value | [0]" | tr -d '"')

# get API jwt token secret key
export API_JWT_TOKEN_SECRET=$(aws secretsmanager get-secret-value --secret-id ${PRODUCT_PREFIX}-${DEPLOY_ENV}-api-token-secret --region eu-west-1 --query SecretString --output text)

# get RapidAPI proxy secret key
export RAPIDAPI_PROXY_SECRET=$(aws secretsmanager get-secret-value --secret-id ${PRODUCT_PREFIX}-${DEPLOY_ENV}-rapidapi-proxy-secret --region eu-west-1 --query SecretString --output text)

# get Redis secret key
export K8S_REDIS_PASSWORD=$(aws secretsmanager get-secret-value --secret-id ${PRODUCT_PREFIX}-${DEPLOY_ENV}-redis-secret --region eu-west-1 --query SecretString --output text)


if [ -z "${POSTGRES_USER}" ]; then
    echo "Init error: POSTGRES_USER is empty"
    exit 1
fi
if [ -z "${POSTGRES_PASSWORD}" ]; then
    echo "Init error: POSTGRES_PASSWORD is empty"
    exit 1
fi
if [ -z "${POSTGRES_HOST}" ]; then
    echo "Init error: POSTGRES_HOST is empty"
    exit 1
fi
if [ -z "${POSTGRES_DB}" ]; then
    echo "Init error: POSTGRES_DB is empty"
    exit 1
fi
if [ -z "${API_JWT_TOKEN_SECRET}" ]; then
    echo "Init error: API_JWT_TOKEN_SECRET is empty"
    exit 1
fi
if [ -z "${K8S_REDIS_PASSWORD}" ]; then
    echo "Init error: K8S_REDIS_PASSWORD is empty"
    exit 1
fi
if [ -z "${OAUTH2_GITHUB_CLIENT_ID}" ]; then
    echo "Init error: OAUTH2_GITHUB_CLIENT_ID is empty"
    exit 1
fi
if [ -z "${OAUTH2_GITHUB_CLIENT_SECRET}" ]; then
    echo "Init error: OAUTH2_GITHUB_CLIENT_SECRET is empty"
    exit 1
fi



init_metadata_db() {
  chmod +x ${NAME_MATCHING_INIT_SCRIPT}
  ${NAME_MATCHING_INIT_SCRIPT}
  cd ${NAME_MATCHING_HOME}
  alembic upgrade head
}

case "$1" in
  backend-internal)
    init_metadata_db
    exec uvicorn server.api.main:app --port 8000
    ;;
  backend-public)
    init_metadata_db
    exec uvicorn server.api.main:app --port 8000 --host 0.0.0.0 --log-level warning
    ;;
  start-rq-realtime-worker)
    exec rq worker nm_realtime_worker --url redis://localhost:6379  --path /opt/uniframe-backend
    ;;
  start-rq-batch-worker)
    exec rq worker nm_batch_worker --url redis://localhost:6379  --path /opt/uniframe-backend
    ;;
  start-housekeeper)
    python ./server/compute/housekeeper.py
    ;;
  *)
    # Just run it in the right environment.
    exec "$@"
    ;;
esac
