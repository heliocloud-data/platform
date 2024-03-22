# Helper script that deploys daskhub to an EKS cluster that's can be outside of
# the EKS admin instance which typically handles the deployments.  The initial
# purpose will be to support external deployments from our CI/CD servers.
#
# Nicholas Lenzi

STACK_BASE=$1
AWS_REGION=$2

echo "Attempting to lookup CloudFormation stack from base ${STACK_BASE}..."

# Fetch the name of the cloud formation template backing Daskhub
export CLOUDFORMATION_NAME=$(aws cloudformation  \
    describe-stacks \
	--query "Stacks[?starts_with(StackName, '${STACK_BASE}Daskhub')].[StackName]" \
	--output text | \
	grep -v Metrics)

if [[ "${CLOUDFORMATION_NAME}" == "" ]]; then
    echo "error: Unable to detected cloudformation template with base name ${STACK_BASE}"
    exit 1
fi

bash ./02-deploy-daskhub.sh ${CLOUDFORMATION_NAME} ${AWS_REGION}
