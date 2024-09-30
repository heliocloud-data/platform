#!/bin/bash

HC_INSTANCE_FILENAME=instance/${HC_INSTANCE}.yaml

cat ${HC_INSTANCE_FILENAME} > /dev/null || (echo "error: Unable to locate file ${HC_INSTANCE_FILENAME}"; exit 1)

REGION_OF_HC_INSTANCE=$(cat ${HC_INSTANCE_FILENAME} | grep region -m 1 | sed 's#[[:space:]]*region:[[:space:]]*##')
if [[ "${REGION_OF_HC_INSTANCE}" == "" ]]; then
  echo "error: Unable to locate AWS region in ${HC_INSTANCE_FILENAME}"
  exit 2
fi

INSTANCE_NAME=$(aws ec2 describe-instances --filters 'Name=tag:Name,Values=*/Daskhub/DaskhubInstance' 'Name=instance-state-name,Values=running' --region=${REGION_OF_HC_INSTANCE} --query 'Reservations[*].Instances[*].InstanceId' --output text)

echo aws ssm start-session --target ${INSTANCE_NAME} --region=${REGION_OF_HC_INSTANCE}
aws ssm start-session --target ${INSTANCE_NAME} --region=${REGION_OF_HC_INSTANCE}
