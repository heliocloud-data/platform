#!/bin/bash

source ./app.config

AWS_REGION=$(curl -s curl http://169.254.169.254/latest/meta-data/placement/region)

# Get instance id associated with EC2 instance currently logged into
INSTANCE_ID=$(wget -q -O - http://169.254.169.254/latest/meta-data/instance-id)

CLOUDFORMATION_ARN=$(aws ec2 describe-instances --region $AWS_REGION --instance-id $INSTANCE_ID --query "Reservations[0].Instances[0].Tags[?Key=='aws:cloudformation:stack-id'].Value | [0]" --output text)
CLOUDFORMATION_NAME=$(echo $CLOUDFORMATION_ARN | sed 's/^.*stack\///' | cut -d'/' -f1)

########################################
# 2. Setup Daskhub configuration files #
########################################

# Setup Daskhub configuration files (copy templates)
echo ------------------------------
echo Copying daskhub configuration files...
cp dh-secrets.yaml.template dh-secrets.yaml
cp dh-config.yaml.template dh-config.yaml
cp dh-auth.yaml.template dh-auth.yaml

echo ------------------------------
echo Putting Docker container location in dh-config.yaml...
sed -i "s|<GENERIC_DOCKER_LOCATION>|$GENERIC_DOCKER_LOCATION|g" dh-config.yaml
sed -i "s|<GENERIC_DOCKER_VERSION>|$GENERIC_DOCKER_VERSION|g" dh-config.yaml
sed -i "s|<ML_DOCKER_LOCATION>|$ML_DOCKER_LOCATION|g" dh-config.yaml
sed -i "s|<ML_DOCKER_VERSION>|$ML_DOCKER_VERSION|g" dh-config.yaml

# Generate API keys for daskhub secrets
API_KEY1=$(openssl rand -hex 32)
API_KEY2=$(openssl rand -hex 32)

echo ------------------------------
echo Putting API keys in dh-secrets.yaml...
sed -i "s|<INSERT_API_KEY1>|$API_KEY1|g" dh-secrets.yaml
sed -i "s|<INSERT_API_KEY2>|$API_KEY2|g" dh-secrets.yaml

# Setup Daskhub auth file with Cognito information
echo ------------------------------
echo Getting Cognito user pool...
COGNITO_USER_POOL_ID=$(aws cloudformation describe-stacks --stack-name $CLOUDFORMATION_NAME --query 'Stacks[0].Outputs[?OutputKey==`CognitoUserPoolId`].OutputValue' --output text)
COGNITO_CLIENT_ID=$(aws cloudformation describe-stacks --stack-name $CLOUDFORMATION_NAME --query 'Stacks[0].Outputs[?OutputKey==`CognitoClientId`].OutputValue' --output text)
COGNITO_DOMAIN_PREFIX=$(aws cloudformation describe-stacks --stack-name $CLOUDFORMATION_NAME --query 'Stacks[0].Outputs[?OutputKey==`CognitoDomainPrefix`].OutputValue' --output text)

COGNITO_CLIENT_SECRET=$(aws cognito-idp describe-user-pool-client --user-pool-id $COGNITO_USER_POOL_ID --client-id $COGNITO_CLIENT_ID --query 'UserPoolClient.ClientSecret' --output text)

echo ------------------------------
echo Replacing values in dh-auth.yaml...
sed -i "s|<INSERT_AWS_COGNITO_CLIENT_ID>|$COGNITO_CLIENT_ID|g" dh-auth.yaml
sed -i "s|<INSERT_AWS_COGNITO_CLIENT_SECRET>|$COGNITO_CLIENT_SECRET|g" dh-auth.yaml
sed -i "s|<INSERT_AWS_COGNITO_DOMAIN>|$COGNITO_DOMAIN_PREFIX|g" dh-auth.yaml
sed -i "s|<INSERT_AWS_REGION>|$AWS_REGION|g" dh-auth.yaml
sed -i "s|<INSERT_HOST_NAME>|$ROUTE53_DASKHUB_PREFIX.$ROUTE53_HOSTED_ZONE|g" dh-auth.yaml
sed -i "s|<INSERT_ADMIN_USER>|$DASKHUB_ADMIN_USER|g" dh-auth.yaml
sed -i "s|<INSERT_CONTACT_EMAIL>|$ADMIN_USER_EMAIL|g" dh-auth.yaml

# Add helm repo
echo ------------------------------
echo Adding Dask helm repo...
helm repo add dask https://helm.dask.org/

# Changes the Cognito user pool app client URLs to match what is being put in the daskhub configs
# Must re-specify client configurations because if value not set, will use default values (do not want this)
echo ------------------------------
echo Amending cognito user pool app client urls...
NO_OUTPUT=$(aws cognito-idp update-user-pool-client --user-pool-id $COGNITO_USER_POOL_ID --client-id $COGNITO_CLIENT_ID --callback-urls https://$ROUTE53_DASKHUB_PREFIX.$ROUTE53_HOSTED_ZONE/hub/oauth_callback --logout-urls https://$ROUTE53_DASKHUB_PREFIX.$ROUTE53_HOSTED_ZONE/logout --allowed-o-auth-flows "code" --allowed-o-auth-scopes "phone" "email" "openid" "profile" "aws.cognito.signin.user.admin" --supported-identity-providers "COGNITO" --allowed-o-auth-flows-user-pool-client)


# Deploy with auth (can deploy without)
echo ------------------------------
echo Deploying Daskhub helm chart with auth
helm upgrade daskhub dask/daskhub --namespace=$KUBERNETES_NAMESPACE --values=dh-config.yaml --values=dh-secrets.yaml --values=dh-auth.yaml --version=2022.8.2 --install
#### To deploy without Authentication & Authorization comment out line above and use this one instead without of the lines below it
#helm upgrade daskhub dask/daskhub --namespace=$KUBERNETES_NAMESPACE --values=dh-config.yaml --values=dh-secrets.yaml --version=2022.8.2 --install

LOADBALANCER_URL=$(kubectl --namespace=$KUBERNETES_NAMESPACE get svc proxy-public --output jsonpath='{.status.loadBalancer.ingress[0].hostname}')

echo ------------------------------
echo Ping for loadbalancer address, wait until loaded...
while [[ $LOADBALANCER_URL != *.com ]]
do
    sleep 20s
    LOADBALANCER_URL=$(kubectl --namespace=$KUBERNETES_NAMESPACE get svc proxy-public --output jsonpath='{.status.loadBalancer.ingress[0].hostname}')
    echo $LOADBALANCER_URL
done

FINAL_LOADBALANCER_URL=$(kubectl --namespace=$KUBERNETES_NAMESPACE get svc proxy-public --output jsonpath='{.status.loadBalancer.ingress[0].hostname}')


if [[ $LOADBALANCER_URL != $FINAL_LOADBALANCER_URL ]]; then
    echo These following values should match, othwerwise there is a problem
    echo $LOADBALANCER_URL
    echo $FINAL_LOADBALANCER_URL
    echo Exit, something wrong has occurred, may be a timing issue and should retry script
else
    # Copy and alter Route 53 record file
    echo ------------------------------
    echo Creating Route53 record...
    cp route53_record.json.template route53_record.json
    sed -i "s|<INSERT_DASKHUB_DNS_NAME>|$ROUTE53_DASKHUB_PREFIX.$ROUTE53_HOSTED_ZONE|g" route53_record.json
    sed -i "s|<INSERT_LOADBALANCER_URL>|$LOADBALANCER_URL|g" route53_record.json

    # Send an upsert to add/update subdomain DNS link to Route 53
    echo ------------------------------
    echo Upserting Route53 record...
    ROUTE53_HOSTED_ZONE_ID=$(aws route53 list-hosted-zones-by-name | jq --arg name "$ROUTE53_HOSTED_ZONE." -r '.HostedZones | .[] | select(.Name=="\($name)") | .Id')
    aws route53 change-resource-record-sets --hosted-zone-id $ROUTE53_HOSTED_ZONE_ID --change-batch file://route53_record.json

    echo ------------------------------
    echo Complete! --- may take a few minutes to propoagate
fi