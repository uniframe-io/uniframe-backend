# This script depoloys to ECS dev environment

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

DOMAIN_NAME=$(aws ssm get-parameters --names ${PRODUCT_PREFIX}-${DEPLOY_ENV}-ssm-eks-domain-name --query "Parameters[*].Value | [0]" | tr -d '"')
BACKEND_REPO=$(aws ssm get-parameters --names ${PRODUCT_PREFIX}-${DEPLOY_ENV}-ssm-backend-repo-name --query "Parameters[*].Value | [0]" | tr -d '"')

aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com
docker build --build-arg DEPLOY_ENV=${DEPLOY_ENV} --build-arg PRODUCT_PREFIX=${PRODUCT_PREFIX} --build-arg DOMAIN_NAME=${DOMAIN_NAME} --build-arg IMAGE_TAG=latest -t ${BACKEND_REPO} . -f Dockerfile.deploy
docker tag ${BACKEND_REPO}:latest ${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${BACKEND_REPO}:latest
docker push ${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${BACKEND_REPO}:latest