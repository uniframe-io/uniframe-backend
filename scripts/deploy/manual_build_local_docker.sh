# This script build image for docker compose local environment

if [ $# -eq 0 ]; then
    echo "You must at least input --deploy_env=prod|dev"
    exit 1
fi

while [ "$1" != "" ]; do
 case $1 in
    -e | --deploy-env)
       shift
       DEPLOY_ENV=$1
      ;;

 esac
 shift
done

PRODUCT_PREFIX=uniframe
AWS_REGION=eu-west-1
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text) 
echo "Account_ID=${ACCOUNT_ID}"


aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

BACKEND_REPO=$(aws ssm get-parameters --names ${PRODUCT_PREFIX}-${DEPLOY_ENV}-ssm-backend-local-repo-name --query "Parameters[*].Value | [0]" | tr -d '"')
docker build --build-arg DEPLOY_ENV=dev --build-arg PRODUCT_PREFIX=${PRODUCT_PREFIX} -t ${BACKEND_REPO} . -f Dockerfile
docker tag ${BACKEND_REPO}:latest ${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${BACKEND_REPO}:latest
docker push ${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${BACKEND_REPO}:latest

PG_REPO=$(aws ssm get-parameters --names ${PRODUCT_PREFIX}-${DEPLOY_ENV}-ssm-pg-local-repo-name --query "Parameters[*].Value | [0]" | tr -d '"')
docker build -t ${PG_REPO} . -f Dockerfile.PG
docker tag ${PG_REPO}:latest ${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${PG_REPO}:latest