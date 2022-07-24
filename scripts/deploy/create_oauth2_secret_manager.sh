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

# Github
# the json file is like: {"OAUTH2_GITHUB_CLIENT_ID":"YOUR_ID","OAUTH2_GITHUB_CLIENT_SECRET":"YOUR_SECRET"}
aws secretsmanager create-secret --name ${PRODUCT_PREFIX}-${DEPLOY_ENV}-oauth-github-client-secret  --secret-string file://./scripts/deploy/oauth_github_secret_${DEPLOY_ENV}.json