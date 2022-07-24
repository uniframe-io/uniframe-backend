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
    -t | --tag)
       shift
       IMAGE_TAG=$1
      ;;      

 esac
 shift
done

PRODUCT_PREFIX=uniframe
AWS_REGION=eu-west-1
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text) 
echo "Account_ID=${ACCOUNT_ID}"
NAMESPACE=nm

DOMAIN_NAME=$(aws ssm get-parameters --names ${PRODUCT_PREFIX}-${DEPLOY_ENV}-ssm-eks-domain-name --query "Parameters[*].Value | [0]" | tr -d '"')
BACKEND_REPO=$(aws ssm get-parameters --names ${PRODUCT_PREFIX}-${DEPLOY_ENV}-ssm-backend-repo-name --query "Parameters[*].Value | [0]" | tr -d '"')

TIMESTAMP=$(date +%Y%m%d%H%M%S)
if [ -z "${IMAGE_TAG}" ]; 
then
    echo "No image tag input. Build image and create a new tag"
    IMAGE_TAG=manual-${TIMESTAMP}
    # build image
    aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com
    docker build --build-arg DEPLOY_ENV=${DEPLOY_ENV} --build-arg PRODUCT_PREFIX=${PRODUCT_PREFIX} --build-arg DOMAIN_NAME=${DOMAIN_NAME} --build-arg IMAGE_TAG=${IMAGE_TAG} -t ${BACKEND_REPO}:${IMAGE_TAG} . -f Dockerfile.deploy

    # push image
    docker tag ${BACKEND_REPO}:${IMAGE_TAG} ${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${BACKEND_REPO}:${IMAGE_TAG}
    docker push ${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${BACKEND_REPO}:${IMAGE_TAG}    
else
    echo "A tag ${IMAGE_TAG} is given. Use it to deploy"
fi


# setup kubectl context
EKS_NAME=$(aws ssm get-parameters --names ${PRODUCT_PREFIX}-${DEPLOY_ENV}-ssm-eks-cluster-name --query "Parameters[0].Value" | tr -d '"')
aws eks update-kubeconfig --name ${EKS_NAME}

kubectl set image -n ${NAMESPACE} deployment/uniframe-${DEPLOY_ENV}-backend-deployment backend=${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${BACKEND_REPO}:${IMAGE_TAG}
kubectl set image -n ${NAMESPACE} deployment/uniframe-${DEPLOY_ENV}-housekeeper-deployment housekeeper=${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${BACKEND_REPO}:${IMAGE_TAG}