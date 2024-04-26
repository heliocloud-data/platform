#!/bin/bash
#
# The following script is responsible for injecting CloudFormation outputs
# into the various configuration files and scripts.  The CloudFormation
# outputs should include the various identifiers and parameters of resources
# that are only available at CDK deploy time (not CDK synth time).  This
# script should only ever need to be called one time immediately after
# deployment of the Daskhub Admin instance.
#
# CNF template variables are denoted via the following syntax:
#   <<CNF_OUTPUT_[id]>>
#
# It works by fetch the outputs from the working CloudFormation tempate,
# iterates over each output, and replaces all template variables with their
# resolved value.  Any templated configuration file or script must be
# included in the 'FILES' array.  Subsequent revisions of this script may
# remove this constraint.
#
# Special care was taken when attempting to capture the Cognito Secrets
# created during the CDK deployment.  For that reason, resolution of
# what should be a CloudFormation output for 'CognitoClientSecret' is
# resolved via an AWS call.
#
# Author: Nicholas Lenzi

AWS_REGION=$(aws ec2 describe-availability-zones --output text --query 'AvailabilityZones[0].[RegionName]')

INSTANCE_ID=$(wget -q -O - http://169.254.169.254/latest/meta-data/instance-id)

CLOUDFORMATION_ARN=$(aws ec2 describe-instances --region $AWS_REGION --instance-id $INSTANCE_ID --query "Reservations[0].Instances[0].Tags[?Key=='aws:cloudformation:stack-id'].Value | [0]" --output text)

CLOUDFORMATION_NAME=$(echo $CLOUDFORMATION_ARN | sed 's/^.*stack\///' | cut -d'/' -f1)

aws cloudformation describe-stacks --stack-name $CLOUDFORMATION_NAME --query 'Stacks[0].Outputs' --output text > stack.txt

# grep -lr 'CNF_OUTPUT_'
FILES=(\
  /home/ssm-user/eksctl/overlays/production/kustomization.yaml
  /home/ssm-user/eksctl-iamidentitymappings/overlays/production/kustomization.yaml
  /home/ssm-user/daskhub-storage/overlays/production/kustomization.yaml
  /home/ssm-user/daskhub/values-production.yaml
  /home/ssm-user/monitoring/values-production.yaml
  /home/ssm-user/00-delete-efs-mount-targets.sh
  /home/ssm-user/02-deploy-daskhub-storage.sh
)

while read p; do
    KEY=$(echo $p | sed 's#^\([A-Za-z0-9]*\)[[:space:]]*.*#\1#g')
    VALUE=$(echo $p | sed 's#^\([A-Za-z0-9]*\)[[:space:]]*##g')

    echo "${KEY}: ${VALUE}"

    for i in "${FILES[@]}"
    do
        sed "s#<<CNF_OUTPUT_${KEY}>>#${VALUE}#g" -i ${i}
    done
done < stack.txt

# Inject 'CognitoClientSecret' which at the moment isn't a CNF Output, but is available and
# Inject it into the necessary resources.
COGNITO_USER_POOL_ID=$(aws cloudformation describe-stacks --stack-name $CLOUDFORMATION_NAME --query 'Stacks[0].Outputs[?OutputKey==`CognitoUserPoolId`].OutputValue' --output text)
COGNITO_CLIENT_ID=$(aws cloudformation describe-stacks --stack-name $CLOUDFORMATION_NAME --query 'Stacks[0].Outputs[?OutputKey==`CognitoClientId`].OutputValue' --output text)
COGNITO_CLIENT_ID_KUBECOST=$(aws cloudformation describe-stacks --stack-name $CLOUDFORMATION_NAME --query 'Stacks[0].Outputs[?OutputKey==`CognitoClientIdKubeCost`].OutputValue' --output text)
COGNITO_DOMAIN_PREFIX=$(aws cloudformation describe-stacks --stack-name $CLOUDFORMATION_NAME --query 'Stacks[0].Outputs[?OutputKey==`CognitoDomainPrefix`].OutputValue' --output text)

COGNITO_CLIENT_SECRET=$(aws cognito-idp describe-user-pool-client --user-pool-id $COGNITO_USER_POOL_ID --client-id $COGNITO_CLIENT_ID --query 'UserPoolClient.ClientSecret' --output text)

echo $COGNITO_CLIENT_SECRET

COGNITO_CLIENT_SECRET_KUBECOST=$(aws cognito-idp describe-user-pool-client --user-pool-id $COGNITO_USER_POOL_ID --client-id $COGNITO_CLIENT_ID_KUBECOST --query 'UserPoolClient.ClientSecret' --output text)

KEY=CognitoClientSecret
VALUE=${COGNITO_CLIENT_SECRET}

keys=("CognitoClientSecret" "CognitoClientSecretKubeCost")
secrets=("${COGNITO_CLIENT_SECRET}" "${COGNITO_CLIENT_SECRET_KUBECOST}")

for ((i = 0; i < 2; i++))
do
    cognito_key="${keys[i]}"
    cognito_secret="${secrets[i]}"
    for j in "${FILES[@]}"
    do
        sed "s#<<CNF_OUTPUT_${cognito_key}>>#${cognito_secret}#g" -i ${j}
    done
done

