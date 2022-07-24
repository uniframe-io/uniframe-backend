# This script build image for minikube environment

PRODUCT_PREFIX=uniframe
DEPLOY_ENV=dev
AWS_REGION=eu-west-1
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text) 
echo "Account_ID=${ACCOUNT_ID}"

IMAGE_TAG=minikube

eval $(minikube docker-env)   
BACKEND_REPO=$(aws ssm get-parameters --names ${PRODUCT_PREFIX}-${DEPLOY_ENV}-ssm-backend-local-repo-name --query "Parameters[*].Value | [0]" | tr -d '"')
docker build --build-arg DEPLOY_ENV=local --build-arg PRODUCT_PREFIX=${PRODUCT_PREFIX} -t ${BACKEND_REPO} . -f Dockerfile
docker tag ${BACKEND_REPO}:latest ${BACKEND_REPO}:${IMAGE_TAG}
eval $(minikube docker-env -u)